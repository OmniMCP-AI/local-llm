from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from fastest_release import capture_cpu
from fastest_release.validation import InvalidObservation, validate


PROVENANCE = {
    "repository": "OmniMCP-AI/local-llm",
    "run_id": "123456",
    "run_attempt": "2",
    "checkout_sha": "1234567890abcdef1234567890abcdef12345678",
    "runner_image": "ubuntu-24.04",
    "image_version": "20261120.1.0",
    "architecture": "x86_64",
    "cpu_model": "AMD EPYC 7763 64-Core Processor",
}
RUNNER = '''
import json
from pathlib import Path
import sys

expected = [
    "-m", "qwen2.5-0.5b-instruct-q4_k_m.gguf", "-p", "0", "-n", "128",
    "-t", "1", "-b", "128", "-ub", "128", "-ngl", "0",
    "-ctk", "f16", "-ctv", "f16", "-nkvo", "1", "-fa", "0",
    "-mmp", "1", "-sm", "layer", "-mg", "0",
    "-r", "7", "--progress", "-v", "-o", "jsonl",
]
if sys.argv[sys.argv.index("-sm") + 1] == "none":
    print("llama_model_load_from_file_impl: invalid value for main_gpu: 0 (available devices: 0)", file=sys.stderr)
    sys.exit(1)
assert sys.argv[1:] == expected, sys.argv
print("load_tensors: CPU_Mapped model buffer size = 468.00 MiB", file=sys.stderr)
print("llama_context: n_ctx = 128", file=sys.stderr)
print("llama_kv_cache: CPU KV buffer size = 3.00 MiB", file=sys.stderr)
print("llama_context: CPU compute buffer size = 50.00 MiB", file=sys.stderr)
print("llama-bench: benchmark 1/1: warmup generation run", file=sys.stderr)
for index in range(1, 8):
    print(f"llama-bench: benchmark 1/1: generation run {index}/7", file=sys.stderr)
print(json.dumps({
    "build_commit": "84a9bf2f", "build_number": 5163,
    "cpu_info": "AMD EPYC 7763 64-Core Processor", "backends": "RPC", "gpu_info": "",
    "model_filename": expected[1], "n_prompt": 0, "n_gen": 128,
    "n_threads": 1, "n_batch": 128, "n_ubatch": 128, "n_gpu_layers": 0,
    "type_k": "f16", "type_v": "f16", "no_kv_offload": True, "flash_attn": False,
    "use_mmap": True, "split_mode": "layer", "main_gpu": 0, "tensor_split": "0.00",
    "cpu_mask": "0x0", "cpu_strict": False, "poll": 50, "embeddings": False,
    "samples_ns": [4000000000, 1000000000, 8000000000, 2000000000, 6000000000, 5000000000, 3000000000],
}))
'''


class CPUBaselineTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.output = self.root / "packet"
        self.asset = self.root / "llama-b5163-bin-ubuntu-x64.zip"
        self.model = self.root / "qwen2.5-0.5b-instruct-q4_k_m.gguf"
        self.model.write_bytes(b"test GGUF")
        self.enterContext(patch("fastest_release.capture_cpu.runner_provenance", return_value=PROVENANCE))

    def fake_asset(self, script=RUNNER):
        with ZipFile(self.asset, "w") as zip_file:
            for name in capture_cpu.RUNTIME_FILES:
                content = f"#!{sys.executable}\n{script}" if name == "llama-bench" else name
                zip_file.writestr(f"build/bin/{name}", content)

    def run_cli(self, *args):
        errors = StringIO()
        with redirect_stderr(errors), redirect_stdout(StringIO()):
            code = capture_cpu.main([str(arg) for arg in args])
        return code, errors.getvalue()

    def capture(self, script=RUNNER, *, matching_asset=True, matching_model=True):
        self.fake_asset(script)
        digest = sha256(self.asset.read_bytes()).hexdigest() if matching_asset else capture_cpu.ARCHIVE_SHA256
        artifact = capture_cpu.ARTIFACT.copy()
        if matching_model:
            artifact["sha256"] = sha256(self.model.read_bytes()).hexdigest()
        binary_digest = sha256(f"#!{sys.executable}\n{script}".encode()).hexdigest()
        with patch.multiple(capture_cpu, ARCHIVE_SHA256=digest, BINARY_SHA256=binary_digest, ARTIFACT=artifact):
            result = self.run_cli("capture", self.asset, self.model, self.output)
            replay = self.run_cli("verify", self.output) if result[0] == 0 else None
        return result, replay

    def test_emits_replayable_unsigned_candidate_at_the_existing_release_boundary(self):
        self.assertEqual(self.capture(), ((0, ""), (0, "")))
        candidate = json.loads((self.output / "candidate.json").read_text())
        receipt = json.loads((self.output / "receipt.json").read_text())
        self.assertEqual(candidate["kind"], "measured")
        self.assertEqual(candidate["metric"], {
            "id": "llama-bench-decode", "version": 1, "value": "32", "unit": "tok/s",
            "statistic": "median", "sample_count": 7,
            "boundary": "llama-bench synchronized time for 128 single-token steps starting at empty KV.",
        })
        self.assertEqual(receipt["samples_ns"], [4_000_000_000, 1_000_000_000, 8_000_000_000,
                                                2_000_000_000, 6_000_000_000, 5_000_000_000, 3_000_000_000])
        self.assertEqual(candidate["source"]["locator"],
                         "https://github.com/OmniMCP-AI/local-llm/actions/runs/123456/attempts/2")
        self.assertEqual(candidate["source"]["revision"], sha256((self.output / "receipt.json").read_bytes()).hexdigest())
        self.assertIn("shared", candidate["hardware"]["name"].lower())
        self.assertIn("x86_64", candidate["hardware"]["configuration"])
        self.assertEqual(candidate["fields"]["wall_power"]["status"], "missing")
        self.assertNotIn("rights", candidate)
        with self.assertRaises(InvalidObservation):
            validate(candidate)
        self.assertEqual({path.name for path in self.output.iterdir()},
                         {"receipt.json", "candidate.json", "stdout.jsonl", "stderr.log"})
        self.assertNotIn(str(self.root), (self.output / "receipt.json").read_text())

    def test_archive_and_model_must_match_the_pins(self):
        for options, message in (
            ({"matching_asset": False}, "Runtime archive SHA-256"),
            ({"matching_model": False}, "GGUF SHA-256"),
        ):
            with self.subTest(options=options):
                result, replay = self.capture(**options)
                self.assertEqual(result[0], 1)
                self.assertIn(message, result[1])
                self.assertIsNone(replay)
                self.assertFalse(self.output.exists())

    def test_runtime_rejects_invalid_build_flags_placement_samples_and_exit(self):
        for script, message in (
            (RUNNER.replace('"84a9bf2f"', '"aaaaaaaa"'), "pinned llama.cpp build"),
            (RUNNER.replace('"n_threads": 1', '"n_threads": 2'), "pinned CPU invocation"),
            (RUNNER.replace("CPU KV buffer", "CUDA0 KV buffer"), "CPU-only buffer placement"),
            (RUNNER.replace("4000000000", "0"), "positive timed decode samples"),
            (RUNNER.replace("range(1, 8)", "range(1, 7)"), "positive timed decode samples"),
            (RUNNER + '\nprint("failed to decode", file=sys.stderr)\n', "logged an error"),
            (RUNNER + "\nsys.exit(1)\n", "Runner failed"),
        ):
            with self.subTest(message=message):
                result, replay = self.capture(script)
                self.assertEqual(result[0], 1)
                self.assertIn(message, result[1])
                self.assertIsNone(replay)
                self.assertFalse(self.output.exists())


    def test_failed_run_reports_bounded_stderr_with_work_path_redacted(self):
        aborted = (
            RUNNER + '\nprint("early log entry", file=sys.stderr)\n'
            'print("x" * 5000, file=sys.stderr)\n'
            'print(f"runtime could not load {Path.cwd()}/runtime/llama-bench", file=sys.stderr)\n'
            'sys.exit(1)\n'
        )
        result, replay = self.capture(aborted)
        self.assertEqual(result[0], 1)
        self.assertIn("Runner failed (exited, exit 1).", result[1])
        self.assertIn("runtime could not load <capture>/runtime/llama-bench", result[1])
        self.assertNotIn("early log entry", result[1])
        self.assertNotIn("fastest-cpu-", result[1])
        self.assertLess(len(result[1]), 4400)
        self.assertIsNone(replay)
        self.assertFalse(self.output.exists())

    def test_replay_detects_changes_to_timing_or_candidate(self):
        self.assertEqual(self.capture(), ((0, ""), (0, "")))
        baseline = self.output / "stdout.jsonl"
        document = self.output / "candidate.json"
        original = baseline.read_text()
        with patch.multiple(
            capture_cpu, ARCHIVE_SHA256=sha256(self.asset.read_bytes()).hexdigest(),
            BINARY_SHA256=sha256(f"#!{sys.executable}\n{RUNNER}".encode()).hexdigest(),
            ARTIFACT={**capture_cpu.ARTIFACT, "sha256": sha256(self.model.read_bytes()).hexdigest()},
        ):
            baseline.write_text(original.replace("4000000000", "7000000000"))
            self.assertEqual(self.run_cli("verify", self.output),
                             (1, "Receipt differs from the retained runner evidence.\n"))
            baseline.write_text(original)
            document.write_text(document.read_text().replace('"32"', '"33"'))
            self.assertEqual(self.run_cli("verify", self.output),
                             (1, "Candidate differs from the retained runner evidence.\n"))

    def test_artifact_pin_matches_the_catalog(self):
        catalog_path = Path(__file__).resolve().parents[2] / "opendesign/mockups/llm-observatory/catalog-identities.json"
        models = json.loads(catalog_path.read_text())
        artifacts = models["Qwen/Qwen2.5-0.5B-Instruct"]["artifacts"]
        self.assertIn(capture_cpu.ARTIFACT, [{field: artifact[field] for field in capture_cpu.ARTIFACT}
                                            for artifact in artifacts])


if __name__ == "__main__":
    unittest.main()
