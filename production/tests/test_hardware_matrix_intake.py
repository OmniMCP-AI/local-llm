import json
import unittest
from decimal import Decimal

from fastest_intake.hardware_matrix import run_trials


class HardwareMatrixIntakeTest(unittest.TestCase):
    def test_warm_medians_and_fit_exclusions_keep_their_scope(self):
        digest = "sha256:" + "d" * 64
        trace = {
            "schema_version": 1,
            "run": {"bench_version": "1.1.0", "started_at": "2026-11-03T10:55:29Z"},
            "system": {"cpu": "Example CPU", "ram_gb": Decimal("127.9"),
                       "gpus": [{"name": "Example GPU", "driver": "1"}]},
            "engines": {"llamacpp": {"version": "b123", "backend": None}},
            "models": {"llamacpp/S": {"digest": digest, "quant": "Q4_K_M"}},
            "tests": {
                "llamacpp/S/speed/warm": {
                    "status": "ok",
                    "values": {"ttft_s": Decimal("0.021000"), "gen_tokens": 256, "cached_tokens": 0,
                               "runs": [{"ttft_s": ".020"}, {"ttft_s": ".021"}, {"ttft_s": ".022"}]},
                },
                "llamacpp/S/concurrency/p8": {"status": "does_not_fit"},
                "llamacpp/S/memory/ctx-32768": {
                    "status": "ok",
                    "values": {"vram_used_mb": 3000, "ctx": 32768, "gpu_fraction": Decimal("0.8"), "ttft_s": Decimal("0.5")},
                },
                "llamacpp/S/speed/cold": {"status": "ok", "values": {"ttft_s": 9}},
            },
        }
        warm, exclusion, memory, latency = run_trials("sample", trace)
        self.assertEqual((warm["metric"], warm["amount"], warm["statistic"], warm["sample_count"]),
                         ("ttft_s", "0.021000", "median", 3))
        self.assertEqual(warm["artifact_revision"], digest)
        self.assertIsNone(warm["backend"])
        self.assertIsNone(warm.get("model"))
        self.assertEqual(exclusion["outcome"], "unknown")
        self.assertEqual(exclusion["context"]["source_status"], "does_not_fit")
        self.assertNotIn("amount", exclusion)
        self.assertNotIn("gpu_count", exclusion)
        self.assertNotIn("gpu_count", warm)
        self.assertEqual(warm["context"]["gpu_in_host"], "Example GPU")
        self.assertEqual(memory["gpu_count"], 1)
        self.assertEqual(json.loads(json.dumps(memory))["context"]["ram_gib"], "127.9")
        self.assertEqual((memory["metric"], memory["unit"], memory["context_tokens"]),
                         ("vram_used_mb", "MiB", 32768))
        self.assertNotIn("statistic", latency)
