from contextlib import redirect_stderr
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastest_release.capture_scaling import main
from fastest_release.scaling import PLAN


FIRST = "GPU-00000000-1111-2222-3333-444444444444"
SECOND = "GPU-55555555-6666-7777-8888-999999999999"
BENCH = '''
import json
import os
import sys

args = sys.argv[1:]
expected = {
    "-p": "0", "-n": "128", "-b": "1024", "-ub": "512", "-t": "8", "-ngl": "99",
    "-ctk": "f16", "-ctv": "f16", "-nkvo": "0", "-fa": "0", "-mmp": "1",
    "-sm": "layer", "-mg": "0", "-r": "20", "-o": "jsonl",
}
for option, value in expected.items():
    assert args[args.index(option) + 1] == value, (option, args)
assert "--progress" in args and "-v" in args
assert "--device" not in args
visible = os.environ["CUDA_VISIBLE_DEVICES"].split(",")
assert visible in ([%r], [%r, %r]), visible
split = "1" if len(visible) == 1 else "1/1"
assert args[args.index("-ts") + 1] == split
assert os.environ["CUDA_DEVICE_ORDER"] == "PCI_BUS_ID"
for index in range(len(visible)):
    print(f"load_tensors: CUDA{index} model buffer size = 100.00 MiB", file=sys.stderr)
    print(f"llama_kv_cache_unified: CUDA{index} KV buffer size = 10.00 MiB", file=sys.stderr)
print(json.dumps({
    "build_commit": "84a9bf2f", "backends": "CUDA",
    "model_filename": args[args.index("-m") + 1], "n_prompt": 0, "n_gen": 128,
    "n_threads": 8, "n_batch": 1024, "n_ubatch": 512, "n_gpu_layers": 99,
    "type_k": "f16", "type_v": "f16", "no_kv_offload": False, "flash_attn": False,
    "use_mmap": True, "split_mode": "layer", "main_gpu": 0,
    "tensor_split": "1.00" if len(visible) == 1 else "1.00/1.00",
    "samples_ns": list(range(100, 120)),
}))
''' % (FIRST, FIRST, SECOND)


class ScalingCaptureTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.output = self.root / "pair"
        self.bench = self.root / "llama-bench"
        self.executable(self.bench, BENCH)
        self.executable(self.root / "nvidia-smi", f"""
print({FIRST!r} + ", 00000000:01:00.0, First card, 570.10")
print({SECOND!r} + ", 00000000:02:00.0, Second card, 570.10")
""")
        self.devices = self.root / "devices.json"
        self.devices.write_text(json.dumps([
            {"uuid": FIRST, "slot": "PCIEX16_1"}, {"uuid": SECOND, "slot": "PCIEX16_2"},
        ]))
        self.build_evidence = self.root / "build.txt"
        self.build_evidence.write_text("Synthetic test build evidence.\n")
        shards = []
        for index, shard in enumerate(PLAN["artifact"]["shards"]):
            payload = f"Shard fixture {index}".encode()
            (self.root / shard["path"]).write_bytes(payload)
            shards.append({**shard, "bytes": len(payload), "sha256": sha256(payload).hexdigest()})
        self.enterContext(patch.dict(PLAN["artifact"], {"shards": shards}))
        self.enterContext(patch.dict(os.environ, {
            "PATH": f"{self.root}{os.pathsep}{os.environ['PATH']}",
            "CUDA_VISIBLE_DEVICES": f"{FIRST},{SECOND}",
        }))

    def executable(self, path, body):
        path.write_text(f"#!{sys.executable}\n" + body, encoding="utf-8")
        path.chmod(0o700)

    def capture(self):
        return main([
            "capture", str(self.output), "--bench", str(self.bench), "--model-dir", str(self.root),
            "--devices", str(self.devices), "--host-revision", "fixture-rev-1",
            "--build-evidence", str(self.build_evidence),
        ])

    def read(self, path):
        return json.loads((self.output / path).read_text(encoding="utf-8"))

    def test_captures_both_pinned_decode_invocations_with_private_provenance(self):
        self.assertEqual(self.capture(), 0)
        capture = self.read("capture.json")
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        self.assertEqual(capture["kind"], "private-capture")
        self.assertEqual(capture["host_revision"], "fixture-rev-1")
        self.assertEqual(capture["binary_sha256"], sha256(self.bench.read_bytes()).hexdigest())
        self.assertEqual(capture["transport"]["status"], "unknown")
        self.assertEqual(capture["quality"]["status"], "unreviewed")

        one = self.read("baseline/attempt.json")
        many = self.read("comparison/attempt.json")
        self.assertNotEqual(one["run_id"], many["run_id"])
        self.assertLessEqual(one["finished_utc"], many["started_utc"])
        for attempt, role, ids in ((one, "baseline", ["0000:01:00.0"]),
                                   (many, "comparison", ["0000:01:00.0", "0000:02:00.0"])):
            with self.subTest(role=role):
                self.assertEqual(attempt["outcome"], "complete")
                self.assertEqual(attempt["exit_code"], 0)
                self.assertEqual(attempt["samples_ns"], list(range(100, 120)))
                self.assertEqual([device["id"] for device in attempt["devices"]], ids)
                for filename in ("stdout.jsonl", "stderr.log"):
                    self.assertEqual(attempt["files"][filename],
                                     sha256((self.output / role / filename).read_bytes()).hexdigest())

    def test_retains_both_attempts_when_baseline_is_oom_and_comparison_logs_a_decode_failure(self):
        bench = BENCH.replace("for index in range(len(visible)):", '''
if len(visible) == 1:
    print("cudaMalloc failed: out of memory", file=sys.stderr)
    sys.exit(1)
print("llama_decode: failed to decode, ret = -1", file=sys.stderr)
for index in range(len(visible)):
''')
        self.executable(self.bench, bench)
        with redirect_stderr(StringIO()):
            self.assertEqual(self.capture(), 1)
        self.assertEqual(self.read("capture.json")["status"], "incomplete")
        self.assertEqual(self.read("baseline/attempt.json")["outcome"], "oom")
        comparison = self.read("comparison/attempt.json")
        self.assertEqual(comparison["outcome"], "failed")
        self.assertEqual(comparison["exit_code"], 0)
        raw = (self.output / "comparison/stdout.jsonl").read_bytes()
        self.assertEqual(json.loads(raw)["samples_ns"], list(range(100, 120)))
        self.assertEqual(comparison["files"]["stdout.jsonl"], sha256(raw).hexdigest())

    def test_makes_no_attempt_when_the_companion_shard_digest_differs(self):
        shard = self.root / PLAN["artifact"]["shards"][1]["path"]
        shard.write_bytes(b"x" * shard.stat().st_size)
        error = StringIO()
        with redirect_stderr(error):
            self.assertEqual(self.capture(), 1)
        self.assertIn("GGUF shard differs from the pinned artifact", error.getvalue())
        self.assertFalse(self.output.exists())

    def test_attaches_a_trace_to_the_comparison_without_rewriting_the_capture(self):
        self.assertEqual(self.capture(), 0)
        manifest = (self.output / "capture.json").read_bytes()
        run_id = self.read("comparison/attempt.json")["run_id"]
        trace, links = self.root / "source-trace.bin", self.root / "links.json"
        trace.write_bytes(b"Trace fixture\x00\n")
        link = {
            "from": "0000:01:00.0", "to": "0000:02:00.0", "path": "host-staged",
            "interconnect": "PCIe", "direction": "one-way", "payload_bytes": 8192,
            "scope": "Timed decode; GPU to host to GPU", "method": "Trace fixture",
            "rated": {"generation": 4, "width": 16, "rate": None},
            "negotiated": {"generation": 4, "width": 8, "rate": None}, "bandwidth_gb_s": None,
        }
        links.write_text(json.dumps({"run_id": run_id, "links": [{**link, "to": "0000:03:00.0"}]}))
        argv = ["attach-transport", str(self.output), "--trace", str(trace), "--links", str(links)]
        with redirect_stderr(StringIO()):
            self.assertEqual(main(argv), 1)
        self.assertFalse((self.output / "transport").exists())

        links.write_text(json.dumps({"run_id": run_id, "links": [link]}))
        self.assertEqual(main(argv), 0)
        receipt = self.read("transport/receipt.json")
        self.assertEqual(receipt["run_id"], run_id)
        self.assertEqual(receipt["status"], "supplied")
        self.assertEqual((self.output / "transport/trace").read_bytes(), trace.read_bytes())
        self.assertEqual(receipt["files"]["trace"], sha256(trace.read_bytes()).hexdigest())
        self.assertEqual(self.read("transport/links.json")["links"], [link])
        self.assertEqual((self.output / "capture.json").read_bytes(), manifest)
        with redirect_stderr(StringIO()):
            self.assertEqual(main(argv), 1)
