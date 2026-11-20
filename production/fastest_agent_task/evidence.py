import re
from uuid import UUID

from fastest_release.validation import keys, plain_text

from .harness import BUDGET, TASK, demo_attempts, identity, read_tool


def require(condition, message):
    if not condition:
        raise ValueError(message)


def attempt_outcome(attempt, context, demo):
    keys(attempt, "trial attempt wall_ns generated_tokens reasoning_tokens termination answer tool_reads", "attempt")
    termination = attempt["termination"]
    require(
        termination in ("answered", "timeout", "runtime_error", "tool_denied", "invalid_output", "budget_exhausted"),
        "Unknown attempt termination",
    )
    elapsed = attempt["wall_ns"]
    require(type(elapsed) is int and 0 < elapsed < 2**63, "Wall duration must be positive integer nanoseconds")
    require(
        (termination == "timeout") == (elapsed >= BUDGET["wall_ns_per_attempt"]),
        "Timeout status must agree with the pinned wall deadline",
    )
    generated = attempt["generated_tokens"]
    require(
        (generated is None and (demo or termination in ("timeout", "runtime_error")))
        or (type(generated) is int and 0 <= generated <= BUDGET["generated_tokens_per_attempt"]),
        "Attempt exceeded the pinned token budget or omitted token usage",
    )
    reasoning = attempt["reasoning_tokens"]
    require(
        type(reasoning) is int and reasoning == BUDGET["reasoning_tokens_per_attempt"],
        "Attempt must have zero reasoning tokens",
    )
    reads = attempt["tool_reads"]
    require(
        isinstance(reads, list) and len(reads) <= BUDGET["tool_reads_per_attempt"],
        "Attempt exceeded the pinned tool budget",
    )
    for read in reads:
        keys(read, "tool resource", "tool read")
        read_tool(context["id"], read["tool"], read["resource"])

    answer = attempt["answer"]
    if termination != "answered":
        require(answer is None, "An interrupted attempt cannot supply an answer")
        return termination
    require(demo or generated > 0, "An answered attempt must record generated tokens")
    keys(answer, "open_units", "answer")
    require(type(answer["open_units"]) is int and -10**9 < answer["open_units"] < 10**9, "Answer must be a bounded integer")
    accepted = answer == TASK["rubric"]["expected_output"] and all(read in reads for read in context["allowed_reads"])
    return "accepted" if accepted else "rubric_mismatch"


def evaluate_attempts(attempts, context, demo):
    require(isinstance(attempts, list), "Attempts must be an ordered list")
    evidence, trials = [], []
    trial = 1
    retry = 1
    for attempt in attempts:
        outcome = attempt_outcome(attempt, context, demo)
        require(
            type(attempt["trial"]) is int and type(attempt["attempt"]) is int
            and trial == attempt["trial"] and retry == attempt["attempt"] and trial <= BUDGET["trials"],
            "Attempts must follow the pinned trial and retry order",
        )
        accepted = outcome == "accepted"
        if retry == 1:
            trials.append({"trial": trial, "status": "pending_retry", "recorded_attempt_wall_ns": 0})
        trials[-1]["recorded_attempt_wall_ns"] += attempt["wall_ns"]
        evidence.append({
            **{key: value for key, value in attempt.items() if key != "answer"},
            "outcome": outcome,
            "accepted_output": attempt["answer"] if accepted else None,
        })
        if accepted or retry > BUDGET["retries_per_trial"]:
            trials[-1]["status"] = "accepted" if accepted else "failed"
            trial += 1
            retry = 1
        else:
            retry += 1

    return {
        "status": "complete" if trial > BUDGET["trials"] else ("partial" if evidence else "missing"),
        "attempts": evidence, "trials": trials,
        "counts": {
            "planned_trials": BUDGET["trials"], "attempted_trials": len(trials),
            "accepted_trials": sum(row["status"] == "accepted" for row in trials),
            "attempts": len(evidence),
            "failed_attempts": sum(row["outcome"] != "accepted" for row in evidence),
        },
    }


def validate_record(record, context):
    keys(record, "kind context_id context_sha256 environment review attempts", "reviewed record")
    require(record["kind"] == "measured", "A measured release requires measured records")
    require(record["context_sha256"] == context["sha256"], "Record must match the exact pinned comparison context")
    require(bool(record["attempts"]), "Reviewed record must contain at least one attempt")

    review = record["review"]
    keys(review, "decision_id evidence_id retained_sha256 ownership destination decision", "review")
    require(
        review["ownership"] == "operator-owned" and review["decision"] == "allow"
        and review["destination"] == "public-release",
        "A public-release allow decision for operator-owned evidence is required",
    )
    for field in ("decision_id", "evidence_id"):
        value = review[field]
        require(isinstance(value, str) and str(UUID(value)) == value, f"{field} must be a canonical UUID")

    environment = record["environment"]
    keys(environment, "hardware os backend runtime_binary_sha256 adapter_sha256", "environment")
    for digest in (review["retained_sha256"], environment["runtime_binary_sha256"], environment["adapter_sha256"]):
        require(isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest), "Expected lowercase SHA-256")
    require(
        all(plain_text(environment[field]) and re.fullmatch(r"[A-Za-z0-9 .(),+_-]{1,80}", environment[field])
            for field in ("hardware", "os"))
        and environment["backend"] in ("Metal", "CUDA"),
        "Supply a public hardware configuration, OS build and supported backend",
    )


def comparison(plan, records, demo):
    by_context = {}
    environment = None
    evidence_ids = set()
    for record in records:
        require(isinstance(record, dict), "Reviewed record must be an object")
        context_id = record.get("context_id")
        context = next((row for row in plan["contexts"] if row["id"] == context_id), None)
        require(context is not None, "Unknown comparison context")
        require(context_id not in by_context, "Submit at most one reviewed ledger per context")
        validate_record(record, context)
        require(environment is None or environment == record["environment"], "Runtime environments must match across contexts")
        environment = record["environment"]
        source_id = record["review"]["evidence_id"]
        require(source_id not in evidence_ids, "Evidence IDs must be unique")
        evidence_ids.add(source_id)
        by_context[context_id] = record

    rows = []
    for context in plan["contexts"]:
        record = by_context.get(context["id"], {})
        attempts = demo_attempts(context["id"]) if demo else record.get("attempts", [])
        rows.append({
            **context, **evaluate_attempts(attempts, context, demo),
            "review": record.get("review"),
        })
    document = {
        "schema_version": 1,
        "kind": "synthetic" if demo else "measured",
        "notice": (
            "Scripted synthetic outcomes and illustrative timings."
            if demo else "Only operator-owned, reviewed measurements appear here. Missing contexts have no approved observations."
        ),
        "conditions": {key: value for key, value in plan.items() if key != "contexts"},
        "environment": environment,
        "contexts": rows,
    }
    return {**document, "release_id": identity(document)}
