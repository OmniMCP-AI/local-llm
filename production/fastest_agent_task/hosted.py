"""Publish the separately pinned shared CI CPU comparison."""

import re
from uuid import NAMESPACE_URL, UUID, uuid5

from fastest_release.validation import keys

from .evidence import comparison, evaluate_attempts, require
from .harness import HERE, identity, fingerprint, plan


RUN_URL = r"https://github\.com/OmniMCP-AI/local-llm/actions/runs/[1-9][0-9]*/attempts/[1-9][0-9]*"
SHA256 = r"[a-f0-9]{64}"
BINARY_SHA256 = "ae6b914314ba75c4ee884a9234fdc7bb2dc82fbfe7c0fcc12b711dece53eb4af"
THREADS = 4
TRIAL_ORDER = (("bundle", 1), ("split", 1), ("split", 2), ("bundle", 2))
WARMUPS = ("bundle", "split")
LIMITATION = "Physical host load is unknown and timing can vary with shared infrastructure."


def hosted_plan():
    shared = plan()
    contexts = shared.pop("contexts")
    files = {
        **shared["harness"]["files"],
        **{name: fingerprint((HERE / name).read_bytes()) for name in ("hosted.py", "measure.py")},
    }
    shared.update(
        protocol_id="inventory-agent-comparison-shared-ci-cpu@1",
        harness={"id": "fastest_agent_task-shared-ci-cpu@1", "sha256": identity(files), "files": files},
        runtime={**shared["runtime"], "build": 5163, "binary_sha256": BINARY_SHA256},
        settings={**shared["settings"], "threads": THREADS, "gpu_layers": 0, "device": "none",
                  "split_mode": "layer", "kv_reset_timeout_seconds": 90},
        controls={
            **shared["controls"],
            "reset": "Allow up to 90 seconds for the prior generation to drain and the slot to confirm KV erase. "
                     "The reset completes before the next attempt clock starts.",
            "session": "Use one GitHub-hosted Ubuntu 24.04 x86_64 guest with four available vCPUs, "
                       "one CPU-only loaded model, one request at a time, and one unmeasured warmup per context. "
                       "Start each attempt with empty KV and a new session. " + LIMITATION,
        },
    )
    for context in contexts:
        del context["sha256"]
        context["sha256"] = identity({"conditions": shared, "context": context})
    return {**shared, "contexts": contexts}


def matches(value, pattern):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def evidence_id(locator, context_id):
    return str(uuid5(NAMESPACE_URL, f"{locator}#{context_id}"))


def validate_candidate(record, context, protocol):
    keys(record, "kind context_id context_sha256 environment attempts", "hosted candidate")
    require(
        record["kind"] == "measured" and record["context_id"] == context["id"]
        and record["context_sha256"] == context["sha256"],
        "Record must match the exact pinned shared CI CPU context",
    )
    environment = record["environment"]
    keys(environment, "hardware os backend runtime_binary_sha256 adapter_sha256 source", "hosted environment")
    source = environment["source"]
    keys(source, "run_url checkout_sha runner_image_version", "hosted source")
    require(
        matches(environment["hardware"], r"GitHub-hosted [A-Za-z0-9][A-Za-z0-9 ().+@_-]{3,149}, 4 vCPUs")
        and environment["os"] == "Ubuntu 24.04 x86_64" and environment["backend"] == "CPU"
        and environment["runtime_binary_sha256"] == BINARY_SHA256
        and environment["adapter_sha256"] == protocol["harness"]["files"]["measure.py"]
        and matches(source["run_url"], RUN_URL)
        and matches(source["checkout_sha"], r"[a-f0-9]{40}")
        and matches(source["runner_image_version"], r"[0-9]+(?:\.[0-9]+){1,4}"),
        "Invalid shared CI CPU environment",
    )
    attempts = record["attempts"]
    require(isinstance(attempts, list) and attempts, "Hosted record requires at least one attempt")
    validation_attempts = []
    for attempt in attempts:
        keys(attempt, "trial attempt wall_ns generated_tokens reasoning_tokens termination outcome answer tool_reads",
             "hosted attempt")
        validation = {key: value for key, value in attempt.items() if key != "outcome"}
        if attempt["outcome"] == "rubric_mismatch":
            # Replay a redacted final candidate as a failed attempt for trial order and budget checks.
            require(
                attempt["termination"] == "answered" and attempt["answer"] is None
                and type(attempt["generated_tokens"]) is int and attempt["generated_tokens"] > 0,
                "A rubric mismatch must be a redacted final answer",
            )
            validation["termination"] = "invalid_output"
        validation_attempts.append(validation)
    evaluated = evaluate_attempts(validation_attempts, context, demo=False)
    for attempt, evaluated_attempt in zip(attempts, evaluated["attempts"]):
        if attempt["outcome"] == "rubric_mismatch":
            evaluated_attempt.update(termination="answered", outcome="rubric_mismatch")
        require(
            evaluated_attempt["outcome"] == attempt["outcome"]
            and evaluated_attempt["accepted_output"] == attempt["answer"],
            "Only the rubric-accepted answer can appear in a hosted record",
        )
    return evaluated


def reviewed_hosted_comparison(records):
    protocol = hosted_plan()
    dataset = comparison(protocol, [], demo=False)
    seen_contexts = set()
    retained_sha256 = None
    for record in records:
        keys(record, "kind context_id context_sha256 environment review attempts", "reviewed hosted record")
        context = next((row for row in dataset["contexts"] if row["id"] == record["context_id"]), None)
        require(context is not None and context["id"] not in seen_contexts, "Invalid or duplicate hosted policy")
        seen_contexts.add(context["id"])
        review = record["review"]
        keys(review, "decision_id evidence_id retained_sha256 ownership destination decision", "review")
        require(
            review["ownership"] == "operator-owned" and review["destination"] == "public-release"
            and review["decision"] == "allow" and matches(review["retained_sha256"], SHA256),
            "A public-release allow decision with retained hosted evidence is required",
        )
        decision = review["decision_id"]
        require(isinstance(decision, str) and str(UUID(decision)) == decision, "decision_id must be a canonical UUID")
        require(retained_sha256 in (None, review["retained_sha256"]), "Hosted records must share one retained receipt")
        retained_sha256 = review["retained_sha256"]
        environment = record["environment"]
        require(dataset["environment"] in (None, environment), "Hosted environments must match across contexts")
        dataset["environment"] = environment
        candidate = {key: value for key, value in record.items() if key != "review"}
        evaluated = validate_candidate(candidate, context, protocol)
        require(review["evidence_id"] == evidence_id(environment["source"]["run_url"], context["id"]),
                "Evidence ID must match the run attempt and policy")
        context.update(**evaluated, review=review)
    dataset["notice"] = "Shared CI CPU tool-policy comparison. " + LIMITATION
    del dataset["release_id"]
    return {**dataset, "release_id": identity(dataset)}
