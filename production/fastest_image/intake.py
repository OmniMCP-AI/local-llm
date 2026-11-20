from decimal import Decimal
import re
from statistics import median
from urllib.parse import urlsplit
from uuid import UUID

from fastest_release.validation import keys, plain_text


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_text(value, label):
    require(plain_text(value), f"{label} must be nonempty single-line text")


def require_digest(value, label):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), f"{label} must be a SHA-256 digest")


def validate_attempts(attempts, protocol, rubric):
    seeds = [protocol["warmup_seed"], *protocol["repeat_seeds"]]
    require(isinstance(attempts, list) and 0 < len(attempts) <= len(seeds), "record must contain a prefix of the planned attempts")
    for index, attempt in enumerate(attempts):
        require(isinstance(attempt, dict), "attempt must be an object")
        phase = "repeat" if index else "warmup"
        success = attempt.get("outcome") == "success"
        extra = "output_sha256" if success else "reason"
        if success and index:
            extra += " review"
        keys(attempt, "phase seed outcome elapsed_ns phase_end_ns " + extra, "attempt")
        require(attempt["phase"] == phase and type(attempt["seed"]) is int and attempt["seed"] == seeds[index],
                "attempts must follow the pinned warmup and repeat seed order")
        require(not index or attempts[0]["outcome"] == "success", "repeats require a successful warmup")
        elapsed = attempt["elapsed_ns"]
        require(type(elapsed) is int and 0 < elapsed < 2**63, "elapsed_ns must be a positive 64-bit integer")
        endpoints = attempt["phase_end_ns"]
        phases = [phase["id"] for phase in protocol["phase_endpoints"]]
        require(isinstance(endpoints, dict) and set(endpoints) == set(phases[:len(endpoints)]),
                "phase endpoints must be an observed prefix of the pinned timing boundaries")
        previous = 0
        for offset in (endpoints[key] for key in phases[:len(endpoints)]):
            require(type(offset) is int and previous < offset <= elapsed,
                    "phase endpoints must be increasing integer offsets within elapsed time")
            previous = offset
        if success:
            require(len(endpoints) == len(phases), "successful requests require all phase endpoints")
            require(elapsed <= protocol["timeout_s"] * 10**9, "successful request exceeded the pinned deadline")
            require_digest(attempt["output_sha256"], "output_sha256")
            review = attempt.get("review")
            if review is not None:
                keys(review, "reviewer scores note", "image review")
                require_text(review["reviewer"], "reviewer pseudonym")
                require_text(review["note"], "review note")
                keys(review["scores"], " ".join(rubric["criteria"]), "review scores")
                require(all(type(score) is bool for score in review["scores"].values()), "review scores must be booleans")
        else:
            require(attempt["outcome"] in ("oom", "timeout", "interrupted", "failed"), "unsupported attempt outcome")
            require_text(attempt["reason"], "failure reason")


def apply_record(record, dataset, cell, kind):
    keys(record, "kind cell_id protocol runtime_revision workflow_sha256 artifact_sha256 source rights runtime_build attempts", "pilot record")
    require(record["kind"] == kind, f"build requires {kind} records")
    require(record["protocol"] == dataset["protocol"]["id"], "record protocol must match the pinned protocol")
    require(record["runtime_revision"] == dataset["runtime"]["revision"], "record runtime must match the pinned revision")
    require(record["workflow_sha256"] == dataset["workflow"]["sha256"], "record workflow must match the pinned SHA-256")
    require(record["artifact_sha256"] == dataset["artifact"]["sha256"], "record checkpoint must match the pinned SHA-256")

    source = record["source"]
    keys(source, "locator revision", "record.source")
    require_text(source["revision"], "source.revision")
    require(isinstance(source["locator"], str) and re.fullmatch(r"https://[^\s<>\"\\]+", source["locator"]),
            "source.locator must be a public HTTPS URL")
    url = urlsplit(source["locator"])
    require(url.hostname and not url.username and not url.password, "source.locator must be a public HTTPS URL")

    rights = record["rights"]
    keys(rights, "decision_id destination core basis", "record.rights")
    require(rights["destination"] == "public-release" and rights["core"] == "allow",
            "pilot record requires a public-release allow decision")
    require_text(rights["basis"], "rights.basis")
    require_text(rights["decision_id"], "rights.decision_id")
    require(str(UUID(rights["decision_id"])) == rights["decision_id"], "rights.decision_id must be a canonical UUID")

    runtime = record["runtime_build"]
    keys(runtime, "provenance machine os_driver backend active_devices effective_placement flags lock_sha256", "runtime build")
    for field in ("provenance", "machine", "os_driver", "effective_placement"):
        require_text(runtime[field], f"runtime_build.{field}")
    require(runtime["backend"] == cell["backend"] and runtime["active_devices"] == [cell["name"]],
            "runtime backend and one active device must match the planned cell")
    require(runtime["flags"] == dataset["runtime"]["flags"], "runtime flags must match the pinned configuration")
    require(runtime["lock_sha256"] == cell["lock"]["sha256"], "runtime dependencies must match the cell lock SHA-256")
    validate_attempts(record["attempts"], dataset["protocol"], dataset["rubric"])
    return {**cell, "blocker": None, **{key: record[key] for key in ("source", "rights", "runtime_build", "attempts")}}


def metric(unit, boundary, value, samples, missing_reason):
    return {
        "unit": unit, "boundary": boundary, "value": value, "sample_count": samples,
        "status": "known" if value is not None else "missing",
        "reason": None if value is not None else missing_reason,
    }


def seconds(nanoseconds):
    scaled = (nanoseconds / Decimal(10**9)).quantize(Decimal("0.000000001"))
    return format(scaled.normalize(), "f")


def summarize(cell, protocol):
    attempts = cell.get("attempts", [])
    repeats = attempts[1:]
    successes = [attempt for attempt in repeats if attempt["outcome"] == "success"]
    reviews = [attempt["review"] for attempt in successes if attempt["review"] is not None]
    accepted = sum(all(review["scores"].values()) for review in reviews)
    median_seconds = None
    if successes:
        median_seconds = seconds(median([Decimal(attempt["elapsed_ns"]) for attempt in successes]))

    complete = len(repeats) == len(protocol["repeat_seeds"]) and len(reviews) == len(successes)
    status = "blocked" if not attempts else "complete" if complete else "partial"
    per_accepted = seconds(Decimal(sum(attempt["elapsed_ns"] for attempt in repeats)) / accepted) if complete and accepted else None
    missing_accepted = "No accepted image in the completed repeat set." if complete else "All planned repeats and reviews of retrieved images are required."
    return {
        **cell, "status": status, "attempts": attempts, "repeat_count": len(repeats),
        "failure_count": sum(attempt["outcome"] != "success" for attempt in attempts),
        "quality": {"output_count": len(successes), "review_count": len(reviews), "accepted_count": accepted},
        "metrics": {
            "median_completion": metric(
                "s", protocol["boundary"], median_seconds, len(successes),
                cell["blocker"] or "No successful measured request.",
            ),
            "seconds_per_accepted_image": metric(
                "s/image", "Sum of repeat elapsed times including failed and rejected attempts divided by accepted repeats.",
                per_accepted, len(repeats) if per_accepted is not None else 0, cell["blocker"] or missing_accepted,
            ),
        },
    }
