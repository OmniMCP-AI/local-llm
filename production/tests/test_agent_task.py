import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


PRODUCTION = Path(__file__).resolve().parents[1]


class AgentTaskTest(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_agent_task", *args],
            cwd=PRODUCTION, capture_output=True, text=True, check=False,
        )

    def test_only_pinned_fixture_reads_are_available(self):
        permitted = self.cli("tool", "split", "read_page", "a")
        self.assertEqual(permitted.returncode, 0, permitted.stderr)
        self.assertEqual(json.loads(permitted.stdout)["rows"][0]["units"], 8)
        for request in (
            ("bundle", "read_page", "a"),
            ("split", "read_page", "../task.json"),
            ("split", "read_page", "https://example.test/data"),
            ("split", "shell", "ls"),
        ):
            with self.subTest(request=request):
                denied = self.cli("tool", *request)
                self.assertEqual(denied.returncode, 2, denied.stderr)
                self.assertEqual(denied.stdout, "")

    def test_demo_publishes_each_context_attempt_and_exact_artifact(self):
        with TemporaryDirectory() as temporary:
            out = Path(temporary) / "release"
            result = self.cli("build", str(out), "--demo")
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = json.loads((out / "agent-task.json").read_text())
            self.assertEqual(dataset["kind"], "synthetic")
            bundle, split = dataset["contexts"]
            self.assertEqual([bundle["id"], split["id"]], ["bundle", "split"])
            self.assertEqual(bundle["counts"], {
                "planned_trials": 2, "attempted_trials": 2, "accepted_trials": 2,
                "attempts": 2, "failed_attempts": 0,
            })
            self.assertEqual(split["counts"]["accepted_trials"], 2)
            self.assertEqual(split["counts"]["failed_attempts"], 1)
            self.assertEqual([a["outcome"] for a in split["attempts"]], ["rubric_mismatch", "accepted", "accepted"])
            self.assertEqual(split["attempts"][1]["accepted_output"], {"open_units": 17})
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual(dataset["release_id"], manifest["release_id"])
            self.assertEqual(manifest["sha256"].get("task.json"), dataset["conditions"]["task"]["fixture_sha256"])
            for name, digest in manifest["sha256"].items():
                self.assertEqual(hashlib.sha256((out / name).read_bytes()).hexdigest(), digest)
            for name in ("agent-task.md", "agent-task.html"):
                rendered = (out / name).read_text()
                for term in ("synthetic", "rubric_mismatch", "open_units", dataset["release_id"]):
                    self.assertIn(term, rendered)

    def test_default_build_makes_missing_measurements_explicit(self):
        with TemporaryDirectory() as temporary:
            out = Path(temporary) / "release"
            result = self.cli("build", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = json.loads((out / "agent-task.json").read_text())
            self.assertEqual(dataset["kind"], "measured")
            self.assertEqual([context["status"] for context in dataset["contexts"]], ["missing", "missing"])
            self.assertTrue(all(context["attempts"] == [] for context in dataset["contexts"]))

    def test_owned_record_requires_review_and_pinned_policy(self):
        plan_result = self.cli("plan")
        self.assertEqual(plan_result.returncode, 0, plan_result.stderr)
        plan = json.loads(plan_result.stdout)
        context = plan["contexts"][0]
        record = {
            "kind": "measured",
            "context_id": context["id"],
            "context_sha256": context["sha256"],
            "environment": {
                "hardware": "Apple M4, 24 GiB",
                "os": "macOS 15.7",
                "backend": "Metal",
                "runtime_binary_sha256": "1" * 64,
                "adapter_sha256": "2" * 64,
            },
            "review": {
                "decision_id": "fb03a586-85a3-448f-8e67-0dc3cfde31dc",
                "evidence_id": "98233d0f-0fdd-4645-87dd-fe4fae4725da",
                "retained_sha256": "3" * 64,
                "ownership": "operator-owned",
                "destination": "public-release",
                "decision": "allow",
            },
            "attempts": [{
                "trial": 1, "attempt": 1, "wall_ns": 25_000, "generated_tokens": 16,
                "reasoning_tokens": 0, "termination": "answered", "answer": {"open_units": 17},
                "tool_reads": [{"tool": "read_bundle", "resource": "inventory"}],
            }],
        }
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            submitted = root / "owned.json"
            submitted.write_text(json.dumps(record))
            result = self.cli("build", str(root / "approved"), "--record", str(submitted))
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((root / "approved" / "agent-task.json").read_text())
            self.assertEqual(data["kind"], "measured")
            self.assertEqual(data["contexts"][0]["status"], "partial")
            self.assertEqual(data["contexts"][0]["attempts"][0]["wall_ns"], 25_000)
            self.assertEqual(data["contexts"][0]["counts"]["accepted_trials"], 1)
            self.assertEqual(data["contexts"][1]["status"], "missing")

            invalid_records = (
                {**record, "review": {**record["review"], "decision": "deny"}},
                {**record, "kind": "synthetic"},
                {**record, "context_sha256": "0" * 64},
                {**record, "attempts": [{**record["attempts"][0], "reasoning_tokens": 1}]},
                {**record, "attempts": [{**record["attempts"][0], "tool_reads": [
                    {"tool": "read_page", "resource": "a"},
                ]}]},
                {**record, "attempts": [{**record["attempts"][0], "attempt": 2}]},
                {**record, "attempts": [{**record["attempts"][0], "generated_tokens": 0}]},
                {**record, "attempts": [{
                    **record["attempts"][0], "answer": None, "termination": "timeout",
                }]},
                {**record, "attempts": [{**record["attempts"][0], "answer": {"private_text": "sample"}}]},
            )
            for i, invalid in enumerate(invalid_records):
                submitted.write_text(json.dumps(invalid))
                out = root / f"denied-{i}"
                result = self.cli("build", str(out), "--record", str(submitted))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse(out.exists())
