"""Prepare private model evaluations from one publisher-pinned Core-19 snapshot."""

from hashlib import sha256
import json


REPOSITORY = "kyuz0/terminal-bench-mini"
COMMIT = "f28e1a024df97d40470a5e10a0147a56650b6457"
MANIFEST = "8db507125de192b10b0930110efe9e014696fa30c274dc8e76c8337a84e23cf7"
SUITE_PATH = f"results/suites/core19-{MANIFEST}"
SOURCE_URL = f"https://github.com/{REPOSITORY}/blob/{COMMIT}"
INDEX_URL = f"{SOURCE_URL}/{SUITE_PATH}/index.json"
EXPLORER_URL = f"{SOURCE_URL}/docs/data.json"
SOURCE = "terminal-bench-local-core19"
DENOMINATOR = 19
INPUTS = (
    ("index.json", "a4faa469cb7ceb5f33f4638746bd5c5bd94e9a4bce1d0a3fe966ac771a30178d"),
    ("data.json", "d408bd77cea2c5513564a074d48c8938b94fda401d715c3ef91ed18939dec8aa"),
)
RUN_FIELDS = {
    "exported_at": "exportedAt",
    "engine": "engine",
    "engine_version": "engineVersion",
    "backend": "backend",
    "backend_version": "backendVersion",
    "quantization": "quant",
    "inference_profile": "inferenceProfile",
    "run_tag": "tag",
    "context_tokens": "contextLength",
    "harbor_version": "harborVersion",
    "terminal_bench_version": "terminalBenchVersion",
    "terminal_bench_revision": "terminalBenchRevision",
}
AGENT_FIELDS = ("name", "version", "context_length", "context_summarization", "summarization_free_tokens")


def read_core19(source, checked_at):
    documents = []
    for filename, digest in INPUTS:
        content = (source / filename).read_bytes()
        if sha256(content).hexdigest() != digest:
            raise ValueError(f"{filename} does not match the pinned Core-19 snapshot at {COMMIT}.")
        documents.append(json.loads(content))
    return core19_bundle(*documents, checked_at)


def _by_key(rows, key):
    indexed = {row[key]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"Duplicate Core-19 {key}.")
    return indexed


def _pass_counts(index_tasks, index_run, results):
    primary = {task_id: task["results"][index_run["id"]] for task_id, task in index_tasks.items()
               if index_run["id"] in task["results"]}
    if primary.keys() != results.keys() or len(primary) != DENOMINATOR:
        raise ValueError("Core-19 run does not have the same 19 task results in both sources.")
    first = within = recorded_attempts = 0
    for task_id, result in results.items():
        attempts = result["attempts"]
        if not attempts or [attempt["number"] for attempt in attempts] != list(range(1, len(attempts) + 1)):
            raise ValueError("Core-19 task results have missing or unordered attempts.")
        first_pass = attempts[0]["passed"]
        within_pass = any(attempt["passed"] for attempt in attempts)
        if (first_pass != result["passAt1"] or within_pass != result["passed"]
                or within_pass != primary[task_id]["passed"]):
            raise ValueError("Core-19 task pass outcomes disagree.")
        first += first_pass
        within += within_pass
        recorded_attempts += len(attempts)
    return first, within, recorded_attempts


def core19_bundle(index, explorer, checked_at):
    """Reconcile the publisher's two views and retain only factual run-level observations."""
    suite = index["suite"]
    benchmark = explorer["benchmark"]
    if (index["schema_version"] != 4 or explorer["schemaVersion"] != 2
            or explorer["repository"] != REPOSITORY or benchmark["tier"] != "full"
            or benchmark["official"] is not False or benchmark["taskCount"] != DENOMINATOR
            or suite != benchmark["suite"] or suite["id"] != "core19" or suite["version"] != "1.0.0"
            or suite["manifest_hash"] != MANIFEST):
        raise ValueError("Expected the publisher's full Core-19 1.0.0 suite in both sources.")

    index_tasks = _by_key(index["tasks"], "id")
    if index_tasks.keys() != _by_key(explorer["tasks"], "id").keys() or len(index_tasks) != DENOMINATOR:
        raise ValueError("Core-19 suite task lists disagree.")
    primary_runs = _by_key(index["models"], "profile_hash")
    explorer_runs = _by_key(explorer["models"], "profileHash")
    if primary_runs.keys() != explorer_runs.keys():
        raise ValueError("Core-19 run profiles disagree.")

    evaluations = []
    incomplete = 0
    for profile, run in explorer_runs.items():
        primary = primary_runs[profile]
        result_path = f"{SUITE_PATH}/{primary['result_directory']}"
        if (run["id"] != result_path or primary["suite"] != suite
                or run["name"] != primary["model"]["name"]):
            raise ValueError("Core-19 run identity disagrees between sources.")
        if run["incomplete"]:
            incomplete += 1
            continue
        if (run["totalTasks"] != DENOMINATOR or run["attemptedTasks"] != DENOMINATOR
                or primary["total_tasks"] != DENOMINATOR or run["pendingRetries"] != 0):
            raise ValueError("Publisher-complete Core-19 runs must have 19 attempted tasks and no pending retries.")

        results = _by_key(run["results"], "taskId")
        first, within, attempts = _pass_counts(index_tasks, primary, results)
        if (first != run["passAt1"] or within != run["passedWithinAttempts"]
                or within != primary["passed_tasks"]):
            raise ValueError("Core-19 pass counts disagree with the source-reported totals.")

        context = {
            "producer": "Donato Capitella (kyuz0)",
            "suite_manifest_sha256": MANIFEST,
            "explorer_schema_version": explorer["schemaVersion"],
            "explorer_source": EXPLORER_URL,
            "profile_sha256": profile,
            "denominator": DENOMINATOR,
            "attempted_tasks": run["attemptedTasks"],
            "recorded_attempts": attempts,
            "task_results_not_marked_complete": sum(not result["completed"] for result in results.values()),
            "platform": {key: run["platform"][key] for key in ("id", "name")},
            "agent": {key: run["agent"][key] for key in AGENT_FIELDS if run["agent"].get(key) is not None},
            "model_identity_scope": "publisher_label",
            "public_reuse": "pending_review",
            **{field: run[key] for field, key in RUN_FIELDS.items() if run.get(key) is not None},
        }
        for metric, amount in (("tasks_passed_first_attempt", first), ("tasks_passed_within_attempts", within)):
            evaluations.append({
                "id": f"core19-{profile}-{metric}",
                "source": SOURCE,
                "locator": f"{SOURCE_URL}/{result_path}/summary.json",
                "model": run["name"],
                "revision": None,
                "benchmark": benchmark["name"],
                "benchmark_version": suite["version"],
                "metric": metric,
                "amount": amount,
                "unit": "reported_score",
                "evidence_class": "publisher_reported",
                "context": context,
            })

    note = (f"Core-19 full suite at {COMMIT}. Verified {len(explorer_runs) - incomplete} of "
            f"{len(explorer_runs)} publisher run profiles against the suite index. "
            f"Deferred {incomplete} incomplete profiles. Public reuse pending review.")
    return {
        "checked_at": checked_at,
        "note": note,
        "sources": [{"source": SOURCE, "url": INDEX_URL, "status": "captured", "note": note}],
        "prices": [],
        "evaluations": evaluations,
    }
