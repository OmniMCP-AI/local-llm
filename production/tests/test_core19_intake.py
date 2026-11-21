from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from fastest_intake.core19 import core19_bundle


MANIFEST = "8db507125de192b10b0930110efe9e014696fa30c274dc8e76c8337a84e23cf7"
SUITE = {"id": "core19", "version": "1.0.0", "manifest_hash": MANIFEST}
PROFILE = "a" * 64
DIRECTORY = f"strix-halo/example-{PROFILE}_results"
CHECKED_AT = "2026-11-21T13:00:00Z"


def publisher_documents():
    """A 19-task run with one first-attempt pass and one pass after a retry."""
    tasks = [{"id": f"task-{n}", "instruction": "exclude this text"} for n in range(19)]
    outcomes = [[True], [False, True]] + [[False]] * 17
    primary_results = [
        {"id": task["id"], "results": {"run": {"passed": any(outcome), "transcript": "omit"}}}
        for task, outcome in zip(tasks, outcomes)
    ]
    run_results = [
        {"taskId": task["id"], "passAt1": outcome[0], "passed": any(outcome), "completed": True,
         "attempts": [{"number": n, "passed": passed, "transcriptUrl": "omit"}
                      for n, passed in enumerate(outcome, 1)]}
        for task, outcome in zip(tasks, outcomes)
    ]
    index_run = {
        "id": "run", "profile_hash": PROFILE, "result_directory": DIRECTORY, "suite": SUITE,
        "total_tasks": 19, "passed_tasks": 2,
        "model": {"name": "Example publisher label", "endpoint_metadata": {"secret": "omit"}},
    }
    explorer_run = {
        "id": f"results/suites/core19-{MANIFEST}/{DIRECTORY}", "profileHash": PROFILE,
        "name": "Example publisher label", "modelId": "/private/endpoint/alias",
        "totalTasks": 19, "attemptedTasks": 19, "incomplete": False, "pendingRetries": 0,
        "passAt1": 1, "passedWithinAttempts": 2, "results": run_results,
        "engine": "Example engine", "backend": "rocm", "inferenceProfile": "temperature 0",
        "platform": {"id": "strix-halo", "name": "AMD Strix Halo"},
        "agent": {"name": "terminus-2", "version": "2.0.0", "endpoint": "omit"},
    }
    index = {"schema_version": 4, "suite": SUITE, "models": [index_run], "tasks": primary_results}
    explorer = {
        "schemaVersion": 2, "repository": "kyuz0/terminal-bench-mini",
        "benchmark": {"name": "Core-19", "suite": SUITE, "taskCount": 19, "tier": "full",
                      "official": False},
        "models": [explorer_run], "tasks": tasks,
    }
    return index, explorer


class Core19IntakeTest(unittest.TestCase):
    def test_import_prepares_distinct_pass_scores_with_private_provenance(self):
        bundle = core19_bundle(*publisher_documents(), CHECKED_AT)
        first, within = bundle["evaluations"]
        self.assertEqual((first["metric"], first["amount"]), ("tasks_passed_first_attempt", 1))
        self.assertEqual((within["metric"], within["amount"]), ("tasks_passed_within_attempts", 2))
        self.assertEqual(first["unit"], "reported_score")
        self.assertNotEqual(first["id"], within["id"])
        self.assertEqual(first["model"], "Example publisher label")
        self.assertIsNone(first["revision"])
        self.assertEqual(first["context"]["denominator"], 19)
        self.assertEqual(first["context"]["recorded_attempts"], 20)
        self.assertEqual(first["context"]["public_reuse"], "pending_review")
        self.assertEqual(first["context"]["agent"], {"name": "terminus-2", "version": "2.0.0"})
        self.assertEqual(first["context"]["inference_profile"], "temperature 0")
        self.assertIn("f28e1a024df97d40470a5e10a0147a56650b6457", first["locator"])
        self.assertTrue(first["locator"].endswith(f"{DIRECTORY}/summary.json"))
        self.assertNotIn("omit", repr(bundle))
        self.assertNotIn("/private/endpoint/alias", repr(bundle))

    def test_defers_publisher_incomplete_profile_with_all_tasks_attempted(self):
        index, explorer = publisher_documents()
        explorer["models"][0]["incomplete"] = True
        bundle = core19_bundle(index, explorer, CHECKED_AT)
        self.assertEqual(bundle["evaluations"], [])
        self.assertIn("Deferred 1 incomplete profiles.", bundle["sources"][0]["note"])

    def test_rejects_a_task_outcome_that_disagrees_with_the_suite_index(self):
        index, explorer = publisher_documents()
        index["tasks"][0]["results"]["run"]["passed"] = False
        with self.assertRaisesRegex(ValueError, "task pass outcomes disagree"):
            core19_bundle(index, explorer, CHECKED_AT)

    def test_cli_rejects_changed_file_before_database_access(self):
        with tempfile.TemporaryDirectory(prefix="core19-intake-test-") as source:
            Path(source, "index.json").write_text("{}", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", "-m", "fastest_intake", "--database-url",
                 "host=/tmp/core19-unavailable dbname=postgres", "ingest-core19", source,
                 "--checked-at", CHECKED_AT],
                cwd=Path(__file__).resolve().parents[1],
                check=False, capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("index.json does not match the pinned Core-19 snapshot", result.stderr)
