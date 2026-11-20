import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PRODUCTION = Path(__file__).resolve().parents[1]


class ImagePilotTest(unittest.TestCase):
    def build(self, target, *args):
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_image", "build", str(target), *args],
            cwd=PRODUCTION, capture_output=True, text=True, check=False,
        )

    def test_planned_release_links_exact_workflow_and_retains_both_access_blockers(self):
        with tempfile.TemporaryDirectory(prefix="fastest-image-test-") as directory:
            target = Path(directory) / "public"
            result = self.build(target)
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = json.loads((target / "image-pilot.json").read_text())
            manifest = json.loads((target / "manifest.json").read_text())
            self.assertEqual(dataset["evidence_kind"], "planned")
            self.assertEqual([cell["id"] for cell in dataset["cells"]], ["apple-m4", "rtx-4090"])
            self.assertEqual(dataset["workflow"]["sha256"], manifest["files"]["workflow.json"])
            for name, expected in manifest["files"].items():
                self.assertEqual(hashlib.sha256((target / name).read_bytes()).hexdigest(), expected)
            for extension in ("md", "html"):
                page = (target / f"image-pilot.{extension}").read_text()
                self.assertIn("./workflow.json", page)
                self.assertIn(manifest["files"]["image-pilot.json"], page)
                for cell in dataset["cells"]:
                    self.assertEqual(cell["status"], "blocked")
                    self.assertEqual(cell["attempts"], [])
                    self.assertEqual(cell["quality"]["accepted_count"], 0)
                    self.assertIn(cell["name"], page)
                    self.assertIn(cell["blocker"], page)
                    for metric in cell["metrics"].values():
                        self.assertIsNone(metric["value"])
                        self.assertEqual(metric["status"], "missing")

    def test_reviewed_demo_uses_elapsed_time_from_rejects_and_failures_in_accepted_rate(self):
        with tempfile.TemporaryDirectory(prefix="fastest-image-test-") as directory:
            target = Path(directory) / "public"
            result = self.build(target, "--demo", "--record", "fixtures/synthetic-image-pilot.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = json.loads((target / "image-pilot.json").read_text())
            self.assertEqual(dataset["evidence_kind"], "synthetic")
            cell, other = dataset["cells"]
            self.assertEqual(cell["status"], "complete")
            self.assertEqual(other["status"], "blocked")
            self.assertEqual(cell["metrics"]["median_completion"]["value"], "2")
            self.assertEqual(cell["metrics"]["median_completion"]["sample_count"], 3)
            self.assertEqual(cell["metrics"]["seconds_per_accepted_image"]["value"], "8")
            self.assertEqual(cell["metrics"]["seconds_per_accepted_image"]["sample_count"], 5)
            self.assertEqual(cell["quality"], {"output_count": 3, "review_count": 3, "accepted_count": 2})
            self.assertEqual(cell["attempts"][3]["outcome"], "oom")
            self.assertEqual(cell["attempts"][3]["phase_end_ns"], {"sampler": 100_000_000})
            for extension in ("md", "html"):
                page = (target / f"image-pilot.{extension}").read_text()
                self.assertIn("Synthetic demonstration", page)
                self.assertIn("8 s/image", page)
                self.assertIn("https://example.invalid/image-pilot/synthetic", page)
                self.assertIn("Synthetic accelerator memory failure.", page)
            self.assertIn("&lt;synthetic&gt;", (target / "image-pilot.html").read_text())

    def test_unreviewed_output_withholds_rate_without_dropping_timing(self):
        source = PRODUCTION / "fixtures/synthetic-image-pilot.json"
        record = json.loads(source.read_text())
        record["attempts"][2]["review"] = None
        with tempfile.TemporaryDirectory(prefix="fastest-image-test-") as directory:
            target = Path(directory) / "public"
            reviewed = Path(directory) / "reviewed.json"
            reviewed.write_text(json.dumps(record))
            result = self.build(target, "--demo", "--record", str(reviewed))
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = json.loads((target / "image-pilot.json").read_text())
            cell = dataset["cells"][0]
            self.assertEqual(cell["status"], "partial")
            self.assertEqual(cell["metrics"]["median_completion"]["value"], "2")
            self.assertIsNone(cell["metrics"]["seconds_per_accepted_image"]["value"])
            self.assertEqual(cell["quality"]["accepted_count"], 2)

    def test_workflow_drift_and_evidence_without_public_rights_fail_before_writing(self):
        source = PRODUCTION / "fixtures/synthetic-image-pilot.json"
        with tempfile.TemporaryDirectory(prefix="fastest-image-test-") as directory:
            target = Path(directory) / "public"
            reviewed = Path(directory) / "reviewed.json"
            for field, value, expected in [
                ("workflow_sha256", "fixture", "pinned SHA-256"),
                ("source", {"locator": "javascript:alert(1)", "revision": "fixture"}, "public HTTPS"),
                ("rights", {"decision_id": "fixture", "destination": "internal", "core": "deny", "basis": "Fixture"}, "allow decision"),
            ]:
                with self.subTest(field=field):
                    record = json.loads(source.read_text())
                    record[field] = value
                    reviewed.write_text(json.dumps(record))
                    result = self.build(target, "--demo", "--record", str(reviewed))
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(expected, result.stderr)
                    self.assertFalse(target.exists())
            result = self.build(target, "--record", str(source))
            self.assertEqual(result.returncode, 1)
            self.assertIn("measured records", result.stderr)
            self.assertFalse(target.exists())

    def test_rejects_skipped_seed_and_impossible_phase_timing(self):
        source = PRODUCTION / "fixtures/synthetic-image-pilot.json"
        with tempfile.TemporaryDirectory(prefix="fastest-image-test-") as directory:
            target = Path(directory) / "public"
            reviewed = Path(directory) / "reviewed.json"
            for mutation, expected in [
                ({"seed": 731002}, "seed order"),
                ({"phase_end_ns": {"sampler": 10, "decode": 8}}, "increasing integer offsets"),
            ]:
                with self.subTest(mutation=mutation):
                    record = json.loads(source.read_text())
                    record["attempts"][1].update(mutation)
                    reviewed.write_text(json.dumps(record))
                    result = self.build(target, "--demo", "--record", str(reviewed))
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(expected, result.stderr)
                    self.assertFalse(target.exists())
