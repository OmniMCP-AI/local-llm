import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PRODUCTION = Path(__file__).resolve().parents[1]


class TextPilotTest(unittest.TestCase):
    def build(self, target, *args):
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_text", "build", str(target), *args],
            cwd=PRODUCTION,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_blocked_release_shows_both_planned_cells_without_values(self):
        with tempfile.TemporaryDirectory(prefix="fastest-text-test-") as temporary:
            target = Path(temporary) / "public"
            result = self.build(target)
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = json.loads((target / "text-pilot.json").read_text())
            self.assertEqual(dataset["evidence_kind"], "planned")
            self.assertEqual(len(dataset["cells"]), 2)

            markdown = (target / "text-pilot.md").read_text()
            html = (target / "text-pilot.html").read_text()
            for cell in dataset["cells"]:
                self.assertEqual(cell["status"], "blocked")
                self.assertEqual(cell["attempts"], [])
                self.assertEqual(cell["quality"]["review_count"], 0)
                self.assertIn(cell["name"], markdown)
                self.assertIn(cell["name"], html)
                self.assertTrue(cell["blocker"])
                for metric in cell["metrics"].values():
                    self.assertEqual(metric["status"], "missing")
                    self.assertEqual(metric["sample_count"], 0)
                    self.assertIsNone(metric["value"])
            self.assertIn("事实保真", markdown)
            self.assertIn("事实保真", html)

            manifest = json.loads((target / "manifest.json").read_text())
            data_hash = hashlib.sha256((target / "text-pilot.json").read_bytes()).hexdigest()
            self.assertEqual(manifest["files"]["text-pilot.json"], data_hash)
            self.assertIn(data_hash, markdown)
            self.assertIn(data_hash, html)

    def test_synthetic_record_retains_failure_and_counts_actual_phase_and_quality_samples(self):
        with tempfile.TemporaryDirectory(prefix="fastest-text-test-") as temporary:
            target = Path(temporary) / "public"
            result = self.build(target, "--demo", "--record", "fixtures/synthetic-text-pilot.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = json.loads((target / "text-pilot.json").read_text())
            self.assertEqual(dataset["evidence_kind"], "synthetic")
            cell, other = dataset["cells"]
            self.assertEqual(other["status"], "blocked")
            self.assertEqual(cell["status"], "partial")
            self.assertEqual(cell["metrics"]["prefill"]["value"], "768")
            self.assertEqual(cell["metrics"]["prefill"]["sample_count"], 2)
            for key in ("decode", "ttft", "first_visible_answer"):
                self.assertIsNone(cell["metrics"][key]["value"])
                self.assertEqual(cell["metrics"][key]["sample_count"], 0)
            self.assertEqual(cell["attempts"][-1]["outcome"], "oom")
            self.assertEqual(cell["quality"]["review_count"], 2)
            self.assertEqual(cell["quality"]["output_count"], 1)
            self.assertEqual(cell["quality"]["accepted_count"], 0)
            self.assertEqual(cell["quality"]["disagreement_count"], 1)
            for extension in ("md", "html"):
                page = (target / f"text-pilot.{extension}").read_text()
                self.assertIn("Synthetic demonstration", page)
                self.assertIn("768 tok/s", page)
                self.assertIn("oom", page)
                self.assertIn("Synthetic reviewer disagreement", page)
            self.assertIn("&lt;simulated&gt;", (target / "text-pilot.html").read_text())

    def test_build_rejects_wrong_protocol_or_rights_before_writing(self):
        fixture = PRODUCTION / "fixtures/synthetic-text-pilot.json"
        with tempfile.TemporaryDirectory(prefix="fastest-text-test-") as temporary:
            target = Path(temporary) / "public"
            path = Path(temporary) / "record.json"
            for mutation, expected in [
                ({"runtime_revision": "unpinned"}, "pinned revision"),
                ({"artifact_sha256": ["other-model"]}, "both pinned GGUF"),
                ({"protocol": "different-cache@1"}, "pinned protocol"),
                ({"rights": {"decision_id": "draft", "destination": "internal", "core": "deny", "basis": "Draft"}}, "allow decision"),
            ]:
                with self.subTest(mutation=mutation):
                    record = json.loads(fixture.read_text())
                    record.update(mutation)
                    path.write_text(json.dumps(record), encoding="utf-8")
                    result = self.build(target, "--demo", "--record", str(path))
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(expected, result.stderr)
                    self.assertFalse(target.exists())

    def test_demo_requires_explicit_selection(self):
        with tempfile.TemporaryDirectory(prefix="fastest-text-test-") as temporary:
            target = Path(temporary) / "public"
            result = self.build(target, "--record", "fixtures/synthetic-text-pilot.json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("measured records", result.stderr)
            self.assertFalse(target.exists())
