from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from fastest_image_team import calculate


PRODUCTION = Path(__file__).resolve().parents[1]
EXAMPLE = PRODUCTION / "fastest_image_team" / "illustrative.json"


def example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


class ImageTeamTest(unittest.TestCase):
    def test_default_bundle_abstains_without_consented_team_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "comparison"
            completed = subprocess.run(
                [sys.executable, "-B", "-m", "fastest_image_team", "build", str(output)],
                cwd=PRODUCTION, capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((output / "image-team.json").read_text())
            self.assertEqual(result["estimate_kind"], "unavailable")
            self.assertIsNone(result["inputs"])
            self.assertEqual(set(result["plans"]), {"local", "cloud", "hybrid"})
            for plan in result["plans"].values():
                self.assertEqual(plan["status"], "unknown")
                self.assertIsNone(plan["peak_accepted_by_deadline"])
            for payback in result["payback"].values():
                self.assertEqual(payback["status"], "unknown_inputs")
                self.assertIsNone(payback["months"])
            for suffix in ("md", "html"):
                report = (output / f"image-team.{suffix}").read_text()
                self.assertIn("No consented team scenario is available", report)
                self.assertIn(result["revision"], report)

    def test_example_compares_peaks_and_cash_across_all_three_plans(self):
        result = calculate(example())
        local, cloud, hybrid = (result["plans"][plan] for plan in ("local", "cloud", "hybrid"))
        self.assertEqual(result["estimate_kind"], "illustrative")
        for plan in (local, cloud, hybrid):
            self.assertEqual(plan["status"], "feasible")
            self.assertEqual(plan["peak_accepted_by_deadline"], 120)
        self.assertEqual(local["lanes"]["local"]["peak_waiting_attempts"], 150)
        self.assertEqual(local["lanes"]["local"]["monthly_capacity_accepted"], 3840)
        self.assertEqual(local["lanes"]["local"]["monthly_rejected"], 250)
        self.assertEqual(local["peak_completion_hours"], "1.320833")
        self.assertEqual(local["monthly_labor_hours"], "14.583333")
        self.assertEqual(local["cost"]["monthly_cash"], "45")
        self.assertEqual(local["cost"]["monthly_loaded_labor"], "729.166667")
        self.assertEqual(cloud["cost"]["monthly_cash"], "265")
        self.assertEqual(hybrid["lanes"]["local"]["peak_accepted_target"], 60)
        self.assertEqual(hybrid["lanes"]["cloud"]["peak_accepted_target"], 60)
        self.assertEqual(result["payback"]["local"]["months"], "6")
        self.assertFalse(result["payback"]["local"]["supports_payback_claim"])
        self.assertEqual(result["payback"]["hybrid"]["status"], "beyond_horizon")
        self.assertEqual(len(result["sensitivity"]), 8)
        self.assertTrue(all(not row["payback"]["local"]["supports_payback_claim"] for row in result["sensitivity"]))

    def test_blocked_comparisons_withhold_payback_in_each_sensitivity_case(self):
        scenario = example()
        scenario["plans"]["local"]["lanes"]["local"]["service"]["quality"] = "unknown"
        scenario["plans"]["hybrid"]["lanes"]["cloud"]["service"]["scope"]["workflow"]["rubric_revision"] = "other"
        result = calculate(scenario)
        for case in (result, *result["sensitivity"]):
            self.assertEqual(case["plans"]["local"]["reasons"], ["local.quality_unknown"])
            self.assertEqual(case["plans"]["hybrid"]["reasons"], ["cloud.workflow_or_workload_scope_mismatch"])
            for payback in case["payback"].values():
                self.assertEqual(payback["status"], "unknown_inputs")
                self.assertIsNone(payback["months"])

        scenario["workload"]["deadline_hours"] = "0.5"
        result = calculate(scenario)
        self.assertIn("peak_deadline_unmet", result["plans"]["cloud"]["reasons"])
        self.assertEqual(result["plans"]["cloud"]["peak_accepted_by_deadline"], 0)
        self.assertIsNone(result["plans"]["cloud"]["cost"])
        self.assertEqual(result["payback"]["local"]["status"], "infeasible_service")
        self.assertIsNone(result["payback"]["local"]["months"])

    def test_consent_and_evidence_are_required_for_supported_payback(self):
        scenario = example()
        scenario["workload"]["public_aggregate_allowed"] = False
        with self.assertRaisesRegex(ValueError, "consent"):
            calculate(scenario)

        def as_reviewed(value):
            if isinstance(value, dict):
                return {key: "reviewed" if item == "fictional" else as_reviewed(item) for key, item in value.items()}
            return value

        scenario["workload"]["public_aggregate_allowed"] = True
        scenario["kind"] = "consented"
        with self.assertRaisesRegex(ValueError, "must be reviewed"):
            calculate(scenario)

        scenario = as_reviewed(scenario)
        result = calculate(scenario)
        self.assertTrue(result["payback"]["local"]["supports_payback_claim"])
        self.assertEqual(result["payback"]["local"]["monthly_cash_savings"], "220")
        scenario["plans"]["cloud"]["lanes"]["cloud"]["cost"] = None
        result = calculate(scenario)
        self.assertEqual(result["plans"]["cloud"]["status"], "feasible")
        self.assertEqual(result["payback"]["local"]["status"], "unknown_inputs")
        self.assertFalse(result["payback"]["local"]["supports_payback_claim"])

    def test_exact_deadline_and_zero_yield_are_service_outcomes(self):
        scenario = example()
        scenario["workload"].update(monthly_accepted=1, peak_accepted=1, deadline_hours="0.01")
        plan = scenario["plans"]["local"]
        plan["labor"]["peak_reviewers"] = 1
        scope = plan["lanes"]["local"]["service"]["scope"]
        scope.update(concurrency=1, wave_seconds="30", accepted_yield="1", peak_queue_hours="0.001",
                     review_minutes_per_attempt="0.04")
        result = calculate(scenario)["plans"]["local"]
        self.assertEqual(result["status"], "feasible")
        self.assertEqual(result["peak_accepted_by_deadline"], 1)

        scope["review_minutes_per_attempt"] = "0.040000001"
        result = calculate(scenario)["plans"]["local"]
        self.assertEqual(result["status"], "infeasible")
        self.assertEqual(result["peak_accepted_by_deadline"], 0)

        scope["accepted_yield"] = "0"
        result = calculate(scenario)
        self.assertIn("local.accepted_yield_zero", result["plans"]["local"]["reasons"])
        self.assertIsNone(result["payback"]["local"]["months"])

    def test_missing_monthly_capacity_blocks_peak_delivery_and_cash_payback(self):
        scenario = example()
        scenario["plans"]["local"]["lanes"]["local"]["service"]["scope"]["monthly_compute_hours"] = "0"
        scenario["plans"]["hybrid"]["labor"]["monthly_hours"] = "0"
        result = calculate(scenario)
        self.assertIn("local.monthly_compute_capacity_unmet", result["plans"]["local"]["reasons"])
        self.assertIn("monthly_labor_capacity_unmet", result["plans"]["hybrid"]["reasons"])
        for plan in ("local", "hybrid"):
            self.assertEqual(result["plans"][plan]["peak_accepted_by_deadline"], 0)
            self.assertIsNone(result["payback"][plan]["months"])

    def test_publish_example_with_one_revision_and_file_digests(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "comparison"
            result = subprocess.run(
                [sys.executable, "-B", "-m", "fastest_image_team", "build", str(output), "--illustrative"],
                cwd=PRODUCTION, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            comparison = json.loads((output / "image-team.json").read_text())
            self.assertEqual(manifest["id"], comparison["revision"])
            self.assertEqual(comparison, calculate(example()))
            self.assertEqual(set(manifest["files"]), {"image-team.json", "image-team.md", "image-team.html"})
            for name, digest in manifest["files"].items():
                self.assertEqual(sha256((output / name).read_bytes()).hexdigest(), digest)
            for suffix in ("md", "html"):
                report = (output / f"image-team.{suffix}").read_text()
                for value in ("Fictional example", "729.166667", "Sensitivity", comparison["revision"]):
                    self.assertIn(value, report)
