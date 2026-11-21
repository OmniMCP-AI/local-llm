from contextlib import redirect_stderr
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastest_text.__main__ import PLAN_PATH, main


BENCH = '''
import json
import os
import sys

args = sys.argv[1:]
if args == ["-p", "0", "-n", "0", "-o", "md"]:
    print("| model | size | params | backend |")
    print()
    print("build: " + os.environ.get("FIXTURE_COMMIT", "84a9bf2f") + " (5163)")
    sys.exit(0)

phase = "prefill" if args[args.index("-n") + 1] == "0" else "decode"
expected = {
    "-p": "1024" if phase == "prefill" else "0",
    "-n": "0" if phase == "prefill" else "128",
    "-b": "1024", "-ub": "512", "-t": "8", "-ngl": "99",
    "-ctk": "f16", "-ctv": "f16", "-nkvo": "0", "-fa": "0", "-mmp": "1",
    "-sm": "layer", "-mg": "0", "-r": "20", "-o": "jsonl",
}
for option, value in expected.items():
    assert args[args.index(option) + 1] == value, (option, args)
assert "--progress" in args and "-v" in args
if phase == "decode":
    from pathlib import Path
    assert Path(os.environ["FIXTURE_CAPTURE"], "prefill", "attempt.json").is_file()
backend = os.environ.get("FIXTURE_BACKEND", "Metal")
if backend == "CUDA":
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "0"
    device, gpu, model = "CUDA0", "NVIDIA GeForce RTX 4090", "CUDA0"
else:
    device, gpu, model = "Metal", "Apple M4", "Metal_Mapped"
print(f"llama_model_load_from_file_impl: using device {device} ({gpu}) - 10240 MiB free", file=sys.stderr)
print(f"load_tensors: {model} model buffer size = 3780.00 MiB", file=sys.stderr)
print("load_tensors: CPU_Mapped model buffer size = 300.00 MiB", file=sys.stderr)
print("load_tensors: offloaded 29/29 layers to GPU", file=sys.stderr)
kv = "CPU" if phase == "decode" and os.environ.get("FIXTURE_FALLBACK") else device
print(f"init: {kv} KV buffer size = 10.00 MiB", file=sys.stderr)
print(f"llama_context: n_ctx = {expected['-p'] if phase == 'prefill' else expected['-n']}", file=sys.stderr)
work = "prompt" if phase == "prefill" else "generation"
print(f"llama-bench: benchmark 1/1: warmup {work} run", file=sys.stderr)
for index in range(1, 21):
    print(f"llama-bench: benchmark 1/1: {work} run {index}/20", file=sys.stderr, flush=True)
    if phase == "decode" and index == 3 and os.environ.get("FIXTURE_FAILURE") == "timeout":
        print(f"fixture-pid: {os.getpid()}", file=sys.stderr, flush=True)
        from time import sleep
        sleep(30)
    if phase == "decode" and index == 3 and os.environ.get("FIXTURE_FAILURE") == "oom":
        print("CUDA error: out of memory", file=sys.stderr)
        sys.exit(1)
    if phase == "decode" and index == 3 and os.environ.get("FIXTURE_FAILURE") == "decode":
        print("llama_decode: failed to decode, ret = 1", file=sys.stderr)
print(json.dumps({
    "build_commit": "84a9bf2f", "build_number": 5163,
    "backends": backend + (",BLAS" if backend == "Metal" else ""), "gpu_info": gpu,
    "model_filename": args[args.index("-m") + 1],
    "n_prompt": int(expected["-p"]), "n_gen": int(expected["-n"]),
    "n_threads": 8, "n_batch": 1024, "n_ubatch": 512, "n_gpu_layers": 99,
    "type_k": "f16", "type_v": "f16", "no_kv_offload": False, "flash_attn": False,
    "use_mmap": True, "split_mode": "layer", "main_gpu": 0, "tensor_split": "0.00",
    "samples_ns": list(range(100, 120)),
}))
'''


class TextCaptureTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.output = self.root / "private"
        self.bench = self.root / "llama-bench"
        self.bench.write_text(f"#!{sys.executable}\n" + BENCH, encoding="utf-8")
        self.bench.chmod(0o700)
        self.build_evidence = self.root / "build-evidence"
        self.build_evidence.write_text("Fixture binary and linked-library provenance.\n", encoding="utf-8")
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        self.shard_paths = []
        for index, shard in enumerate(plan["artifact"]["shards"]):
            payload = f"Fixture shard {index}".encode()
            path = self.root / shard["path"]
            path.write_bytes(payload)
            self.shard_paths.append(path)
            shard.update(bytes=len(payload), sha256=sha256(payload).hexdigest())
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        self.enterContext(patch("fastest_text.__main__.PLAN_PATH", plan_path))
        self.enterContext(patch.dict(os.environ, {"FIXTURE_CAPTURE": str(self.output)}))

    def capture(self, cell="apple-m4", **env):
        stderr = StringIO()
        with redirect_stderr(stderr), patch.dict(os.environ, env):
            result = main([
                "capture", str(self.output), "--cell", cell, "--bench", str(self.bench),
                "--model-dir", str(self.root), "--host-revision", "fixture-host",
                "--build-evidence", str(self.build_evidence), "--quiet-host", "--timeout", "1",
            ])
        return result, stderr.getvalue()

    def read(self, name="capture.json"):
        return json.loads((self.output / name).read_text(encoding="utf-8"))

    def test_retains_both_pinned_phases_and_actual_metal_placement(self):
        self.assertEqual(self.capture(), (0, ""))
        capture = self.read()
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        self.assertEqual(capture["kind"], "private-capture")
        self.assertEqual(capture["status"], "complete")
        self.assertEqual(capture["binary_sha256"], sha256(self.bench.read_bytes()).hexdigest())
        self.assertEqual(capture["build_evidence_sha256"], sha256(self.build_evidence.read_bytes()).hexdigest())
        self.assertEqual(capture["runtime_build"]["commit_reported"], "84a9bf2f")
        self.assertEqual(capture["metrics"]["ttft"]["status"], "missing")
        self.assertEqual(capture["metrics"]["first_visible_answer"]["sample_count"], 0)
        self.assertNotIn("rights", capture)
        for phase in ("prefill", "decode"):
            with self.subTest(phase=phase):
                attempt = self.read(f"{phase}/attempt.json")
                self.assertEqual(attempt["outcome"], "complete")
                self.assertEqual(attempt["placement"]["devices"], {"Metal": "Apple M4"})
                self.assertEqual(attempt["placement"]["buffers_mib"]["Metal_Mapped"]["model"], ["3780.00"])
                self.assertEqual(attempt["placement"]["buffers_mib"]["Metal"]["kv"], ["10.00"])
                self.assertEqual(attempt["attempts"][0], {"number": 1, "outcome": "success", "elapsed_ns": 100})
                self.assertEqual(len(attempt["attempts"]), 20)
                self.assertEqual(
                    attempt["files"]["stdout.jsonl"],
                    sha256((self.output / phase / "stdout.jsonl").read_bytes()).hexdigest(),
                )


    def test_cuda_requires_single_visible_device_and_matches_rtx_4090(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0,1"}):
            result, error = self.capture("rtx-4090")
        self.assertEqual(result, 1)
        self.assertIn("CUDA_VISIBLE_DEVICES", error)
        self.assertEqual(self.read()["status"], "blocked")
        self.assertFalse((self.output / "runtime").exists())

        self.output = self.root / "private-cuda"
        with patch.dict(os.environ, {"FIXTURE_CAPTURE": str(self.output)}):
            self.assertEqual(self.capture("rtx-4090", CUDA_VISIBLE_DEVICES="0", FIXTURE_BACKEND="CUDA"), (0, ""))
        self.assertEqual(self.read("decode/attempt.json")["placement"]["devices"], {"CUDA0": "NVIDIA GeForce RTX 4090"})

    def test_second_shard_with_wrong_hash_stops_before_benchmark(self):
        self.shard_paths[1].write_bytes(b"Fixture shard X")
        result, error = self.capture()
        self.assertEqual(result, 1)
        self.assertIn(self.shard_paths[1].name, error)
        self.assertEqual(self.read()["status"], "blocked")
        self.assertEqual(len(self.read()["verified_shards"]), 1)
        self.assertFalse((self.output / "prefill").exists())

    def test_wrong_runner_commit_stops_before_benchmark(self):
        result, error = self.capture(FIXTURE_COMMIT="0000000")
        self.assertEqual(result, 1)
        self.assertIn("pinned b5163 revision", error)
        self.assertEqual(self.read()["verified_shards"], [])
        self.assertFalse((self.output / "prefill").exists())

    def test_cpu_fallback_retains_raw_result_without_measurements(self):
        self.assertEqual(self.capture(FIXTURE_FALLBACK="1")[0], 1)
        capture = self.read()
        self.assertEqual(capture["phases"]["prefill"]["sample_count"], 20)
        self.assertEqual(capture["phases"]["decode"]["sample_count"], 0)
        phase = self.read("decode/attempt.json")
        self.assertEqual(phase["outcome"], "invalid-output")
        self.assertEqual(phase["placement"]["buffers_mib"]["CPU"]["kv"], ["10.00"])
        self.assertEqual(len(self.read("decode/stdout.jsonl")["samples_ns"]), 20)
        self.assertTrue(all(attempt["outcome"] == "unmeasured" for attempt in phase["attempts"]))

    def test_timeout_keeps_observed_progress_and_reaps_owned_process(self):
        self.assertEqual(self.capture(FIXTURE_FAILURE="timeout")[0], 1)
        phase = self.read("decode/attempt.json")
        self.assertEqual(phase["outcome"], "timeout")
        self.assertEqual(phase["observed_progress"], [1, 2, 3])
        self.assertEqual(phase["samples_ns"], [])
        self.assertEqual(phase["attempts"][-1]["outcome"], "timeout")
        log = (self.output / "decode" / "stderr.log").read_text(encoding="utf-8")
        pid = int(re.search(r"fixture-pid: (\d+)", log).group(1))
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_oom_retains_the_identifiable_failed_attempt(self):
        self.assertEqual(self.capture(FIXTURE_FAILURE="oom")[0], 1)
        phase = self.read("decode/attempt.json")
        self.assertEqual(phase["outcome"], "oom")
        self.assertEqual([attempt["outcome"] for attempt in phase["attempts"]], ["unmeasured", "unmeasured", "oom"])
        self.assertEqual(phase["samples_ns"], [])

    def test_pinned_runner_can_emit_timings_for_a_failed_sample(self):
        self.assertEqual(self.capture(FIXTURE_FAILURE="decode")[0], 1)
        phase = self.read("decode/attempt.json")
        self.assertEqual(phase["outcome"], "partial")
        self.assertEqual(self.read()["phases"]["decode"]["sample_count"], 19)
        self.assertEqual(phase["attempts"][2]["outcome"], "failed")
        self.assertEqual(phase["attempts"][3]["elapsed_ns"], 103)
        self.assertNotIn(102, phase["samples_ns"])


    def test_blind_quality_packet_keeps_raw_source_only_in_private_mapping(self):
        answer = "芽杯日用杯\n容量350毫升，售价79元。杯盖可拆洗。"
        raw_response = self.root / "operator-m4-private-completion.json"
        raw_response.write_text(json.dumps({
            "model": "private-model-location",
            "choices": [{"message": {"role": "assistant", "content": answer}}],
        }), encoding="utf-8")
        result = main(["review-packet", str(self.output), "--response", str(raw_response)])
        self.assertEqual(result, 0)
        packet = self.read("review-packet.json")
        provenance = self.read("private-map.json")
        output = packet["outputs"][0]
        self.assertEqual(output["answer"], answer)
        self.assertEqual(output["rating"]["output_sha256"], sha256(answer.encode("utf-8")).hexdigest())
        self.assertEqual(set(output["rating"]["scores"]), {"facts", "instructions", "brand", "leakage", "editability"})
        self.assertEqual(provenance["outputs"][output["rating"]["output_id"]]["response_path"], str(raw_response))
        self.assertNotIn("operator-m4", json.dumps(packet))
        self.assertNotIn("private-model-location", json.dumps(packet))
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)


if __name__ == "__main__":
    unittest.main()
