from collections import defaultdict
from decimal import Decimal, localcontext
import re
from statistics import median
from uuid import UUID

from fastest_release.validation import keys, plain_text


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_text(value, label):
    require(plain_text(value), f"{label} must be nonempty single-line text")


def require_digest(value, label):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), f"{label} must be a SHA-256 digest")


def require_list(value, label):
    require(isinstance(value, list), f"{label} must be a list")


def validate_attempts(attempts, phases):
    require_list(attempts, "attempts")
    next_number = dict.fromkeys(phases, 1)
    for attempt in attempts:
        require(isinstance(attempt, dict), "attempt must be an object")
        success = attempt.get("outcome") == "success"
        keys(attempt, "phase number outcome " + ("elapsed_ns" if success else "reason"), "attempt")
        phase, number = attempt["phase"], attempt["number"]
        require(isinstance(phase, str) and phase in phases, "attempt phase must match a fixed-token phase")
        require(type(number) is int and number == next_number[phase], "attempt numbers must be consecutive within each phase")
        next_number[phase] += 1
        if success:
            nanos = attempt["elapsed_ns"]
            require(type(nanos) is int and 0 < nanos < 2**63, "elapsed_ns must be a positive 64-bit integer")
        else:
            require(attempt["outcome"] in ("oom", "timeout", "failed"), "unsupported attempt outcome")
            require_text(attempt["reason"], "attempt.reason")


def summarize_reviews(reviews, rubric):
    require_list(reviews, "quality_reviews")
    outputs = defaultdict(dict)
    digests = {}
    for review in reviews:
        keys(review, "task_id output_id output_sha256 reviewer scores note", "quality review")
        require(review["task_id"] == rubric["task_id"], "quality review task must match the pinned rubric")
        output_id = review["output_id"]
        require_text(output_id, "quality output ID")
        output_digest = review["output_sha256"]
        require_digest(output_digest, "output_sha256")
        require(digests.setdefault(output_id, output_digest) == output_digest, "conflicting digests for one quality output")
        require_text(review["reviewer"], "reviewer pseudonym")
        require_text(review["note"], "quality review note")
        keys(review["scores"], " ".join(rubric["criteria"]), "quality scores")
        require(all(type(score) is bool for score in review["scores"].values()), "quality scores must be true or false")
        reviewers = outputs[output_id]
        require(review["reviewer"] not in reviewers, "duplicate rating for the same output and reviewer")
        reviewers[review["reviewer"]] = review["scores"]

    return {
        "review_count": len(reviews),
        "output_count": len(outputs),
        "accepted_count": sum(all(all(scores.values()) for scores in reviewers.values()) for reviewers in outputs.values()),
        "disagreement_count": sum(
            len({tuple(scores[key] for key in rubric["criteria"]) for scores in reviewers.values()}) > 1
            for reviewers in outputs.values()
        ),
        "reviews": reviews,
    }


def validate_record(record, dataset, cell, kind):
    keys(
        record, "kind cell_id protocol runtime_revision artifact_sha256 source rights runtime_build attempts quality_reviews",
        "pilot record",
    )
    protocol = dataset["protocol"]
    require(record["kind"] == kind, f"build requires {kind} records")
    require(record["protocol"] == protocol["id"], "record protocol must match the pinned protocol")
    require(record["runtime_revision"] == dataset["runtime"]["revision"], "record runtime must match the pinned revision")
    require(
        record["artifact_sha256"] == [shard["sha256"] for shard in dataset["artifact"]["shards"]],
        "record artifact must match both pinned GGUF shard digests",
    )

    source = record["source"]
    keys(source, "locator revision", "record.source")
    require_text(source["locator"], "source.locator")
    require_text(source["revision"], "source.revision")

    rights = record["rights"]
    keys(rights, "decision_id destination core basis", "record.rights")
    require(
        rights["destination"] == "public-release" and rights["core"] == "allow",
        "pilot record requires a public-release allow decision",
    )
    require_text(rights["basis"], "rights.basis")
    require_text(rights["decision_id"], "rights.decision_id")
    require(str(UUID(rights["decision_id"])) == rights["decision_id"], "rights.decision_id must be a canonical UUID")

    runtime = record["runtime_build"]
    keys(
        runtime, "provenance binary_sha256 machine os_driver backend active_devices settings effective_placement",
        "runtime build",
    )
    for field in ("provenance", "machine", "os_driver", "effective_placement"):
        require_text(runtime[field], f"runtime_build.{field}")
    require_digest(runtime["binary_sha256"], "runtime_build.binary_sha256")
    require(runtime["backend"] == cell["backend"], "runtime backend must match the planned machine")
    require(type(runtime["active_devices"]) is int and runtime["active_devices"] == 1, "one active accelerator is required")
    require(
        json_settings_match(runtime["settings"], protocol["settings"]),
        "runner settings must match the pinned protocol",
    )

    validate_attempts(record["attempts"], protocol["phases"])
    require(bool(record["attempts"]), "runner record requires at least one attempt")


def json_settings_match(actual, expected):
    return (
        isinstance(actual, dict) and actual.keys() == expected.keys()
        and all(type(actual[key]) is type(value) and actual[key] == value for key, value in expected.items())
    )


def median_throughput(elapsed_ns, tokens):
    with localcontext() as context:
        context.prec = 28
        return format(median(Decimal(tokens * 10**9) / nanos for nanos in elapsed_ns).normalize(), "f")


def apply_record(record, dataset, cell, kind):
    validate_record(record, dataset, cell, kind)
    protocol = dataset["protocol"]
    by_phase = defaultdict(list)
    for attempt in record["attempts"]:
        if attempt["outcome"] == "success":
            by_phase[attempt["phase"]].append(attempt["elapsed_ns"])

    metrics = cell["metrics"].copy()
    for key, phase in protocol["phases"].items():
        samples = by_phase[key]
        if samples:
            metrics[key] = {
                **metrics[key],
                "status": "available",
                "sample_count": len(samples),
                "statistic": "median",
                "value": median_throughput(samples, phase["input_tokens"] + phase["output_tokens"]),
                "reason": None,
            }
        else:
            metrics[key] = {**metrics[key], "reason": "No successful attempts were recorded for this phase."}

    status = "failed"
    if any(by_phase.values()):
        status = (
            "complete"
            if all(len(by_phase[key]) >= protocol["warm_samples_per_phase"] for key in protocol["phases"])
            else "partial"
        )
    return {
        **cell,
        "status": status,
        "blocker": None,
        "metrics": metrics,
        "attempts": record["attempts"],
        "runtime_build": record["runtime_build"],
        "source": record["source"],
        "rights": record["rights"],
        "quality": summarize_reviews(record["quality_reviews"], dataset["rubric"]),
    }
