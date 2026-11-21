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

from fastest_text.__main__ import PLAN_PATH, main


SERVER = r'''
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import socketserver
import sys
from time import sleep

if sys.argv[1:] == ["--version"]:
    print("version: 5163 (84a9bf2f)", file=sys.stderr)
    sys.exit(0)

args = sys.argv[1:]
for key, value in {"--device": "Metal", "--parallel": "1", "--split-mode": "none",
                   "--ctx-size": "2048", "--gpu-layers": "99"}.items():
    assert args[args.index(key) + 1] == value
assert "--jinja" in args
print("llama_model_load_from_file_impl: using device Metal (Apple M4) - 10240 MiB free", flush=True)
print("load_tensors: Metal_Mapped model buffer size = 3780.00 MiB", flush=True)
print("load_tensors: offloaded 29/29 layers to GPU", flush=True)
print("init: Metal KV buffer size = 10.00 MiB", flush=True)
print("llama_context: n_ctx = 2048", flush=True)
print(f"fixture PID: {os.getpid()}", flush=True)
completed = 0
erases = 0


class Handler(BaseHTTPRequestHandler):
    def send_json(self, value):
        raw = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        assert self.path == "/health"
        self.send_json({"status": "ok"})

    def do_POST(self):
        global completed, erases
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/apply-template":
            assert len(body["messages"]) == 1
            assert body["messages"][0]["role"] == "user" and "芽杯" in body["messages"][0]["content"]
            self.send_json({"prompt": "<resolved chat prompt>"})
            return
        if self.path == "/slots/0?action=erase":
            erases += 1
            self.send_json({"id_slot": 0, "n_erased": 3 if completed else 0})
            return
        assert self.path == "/completion" and erases == completed + 1
        assert body == {
            "cache_prompt": False, "id_slot": 0, "n_predict": 256, "prompt": "<resolved chat prompt>",
            "return_tokens": True, "seed": 42, "stream": True, "temperature": 0, "top_k": 1,
        }
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        def chunk(content, tokens, predicted, **extra):
            self.wfile.write(b"data: " + json.dumps({
                "index": 0, "content": content, "tokens": tokens, "stop": False,
                "id_slot": 0 if extra.get("stop") else -1,
                "tokens_predicted": predicted, "tokens_evaluated": 72, **extra,
            }, ensure_ascii=False).encode() + b"\n\n")
            self.wfile.flush()

        self.wfile.write(b": keepalive\n\n")
        mode = os.environ.get("FIXTURE_STREAM") if completed else None
        if mode != "buffered-first":
            chunk(" ", [468], 1)
            sleep(0.02)
        chunk("芽杯", [110], 2)
        if mode == "timeout":
            sleep(30)
        elif mode == "disconnected":
            return
        chunk("", [], 3, stop=True, stop_type="eos", truncated=False)
        completed += 1

    def address_string(self):
        return "fixture"


with socketserver.UnixStreamServer(args[args.index("--host") + 1], Handler) as server:
    server.serve_forever()
'''


class TextLatencyTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory(prefix="fastest-text-latency-", dir="/tmp")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.output = self.root / "private"
        self.server = self.root / "llama-server"
        self.server.write_text(f"#!{sys.executable}\n" + SERVER, encoding="utf-8")
        self.server.chmod(0o700)
        self.build_evidence = self.root / "build-evidence"
        self.build_evidence.write_text("Fixture runtime and linked-library provenance.\n", encoding="utf-8")
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        for index, shard in enumerate(plan["artifact"]["shards"]):
            raw = f"Fixture shard {index}".encode()
            (self.root / shard["path"]).write_bytes(raw)
            shard.update(bytes=len(raw), sha256=sha256(raw).hexdigest())
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        self.enterContext(patch("fastest_text.__main__.PLAN_PATH", plan_path))

    def capture(self, timeout=2, **env):
        stderr = StringIO()
        with redirect_stderr(stderr), patch.dict(os.environ, env):
            result = main([
                "capture-latency", str(self.output), "--cell", "apple-m4", "--server", str(self.server),
                "--model-dir", str(self.root), "--host-revision", "fixture-host",
                "--build-evidence", str(self.build_evidence), "--quiet-host", "--timeout", str(timeout),
            ])
        return result, stderr.getvalue()

    def read(self, name="latency.json"):
        return json.loads((self.output / name).read_text(encoding="utf-8"))

    def test_private_native_stream_times_first_token_before_first_printable_text(self):
        self.assertEqual(self.capture(), (0, ""))
        ledger = self.read()
        self.assertEqual(ledger["status"], "complete")
        self.assertEqual(ledger["runtime_build"]["commit_reported"], "84a9bf2f")
        self.assertEqual(ledger["binary_sha256"], sha256(self.server.read_bytes()).hexdigest())
        self.assertEqual(ledger["placement"]["devices"], {"Metal": "Apple M4"})
        self.assertEqual(ledger["warmup"]["status"], "complete")
        self.assertEqual(ledger["attempt"]["prompt_tokens"], 72)
        self.assertEqual(ledger["attempt"]["expected_max_output_tokens"], 256)
        ttft = ledger["metrics"]["ttft"]
        first_answer = ledger["metrics"]["first_visible_answer"]
        self.assertEqual(ttft["sample_count"], 1)
        self.assertEqual(first_answer["sample_count"], 1)
        self.assertGreater(ttft["samples_ns"][0], 0)
        self.assertGreater(first_answer["samples_ns"][0], ttft["samples_ns"][0])
        stream = (self.output / "attempt.sse").read_bytes()
        self.assertIn(b": keepalive\n\n", stream)
        self.assertEqual(ledger["files"]["attempt.sse"], sha256(stream).hexdigest())
        self.assertEqual(self.read("response.json")["choices"][0]["message"]["content"], " 芽杯")
        self.assertEqual(ledger["quality"]["status"], "unreviewed")
        self.assertNotIn("rights", ledger)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        self.assertFalse((self.output / "run.sock").exists())
        log = (self.output / "server.log").read_text(encoding="utf-8")
        pid = int(next(line.split(": ")[-1] for line in log.splitlines() if line.startswith("fixture PID: ")))
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)


    def test_buffered_ordinal_one_keeps_ttft_missing_and_records_visible_text(self):
        self.assertEqual(self.capture(FIXTURE_STREAM="buffered-first"), (0, ""))
        ledger = self.read()
        self.assertEqual(ledger["attempt"]["events"], 1)
        self.assertEqual(ledger["metrics"]["ttft"]["sample_count"], 0)
        self.assertIn("ordinal 1", ledger["metrics"]["ttft"]["reason"])
        self.assertEqual(ledger["metrics"]["first_visible_answer"]["sample_count"], 1)
        self.assertEqual(self.read("response.json")["choices"][0]["message"]["content"], "芽杯")

    def test_missing_terminal_event_retains_observed_times_without_a_sample(self):
        result, error = self.capture(FIXTURE_STREAM="disconnected")
        self.assertEqual(result, 1)
        self.assertIn("Private latency capture incomplete", error)
        ledger = self.read()
        self.assertEqual(ledger["status"], "incomplete")
        self.assertEqual(ledger["attempt"]["events"], 2)
        self.assertGreater(ledger["attempt"]["observed_ns"]["first_visible_answer"], 0)
        for metric in ledger["metrics"].values():
            self.assertEqual(metric["sample_count"], 0)
            self.assertIn("No completed", metric["reason"])
        self.assertFalse((self.output / "response.json").exists())

    def test_timeout_preserves_attempt_and_reaps_owned_listener(self):
        self.assertEqual(self.capture(timeout=1, FIXTURE_STREAM="timeout")[0], 1)
        ledger = self.read()
        self.assertEqual(ledger["attempt"]["status"], "timeout")
        self.assertEqual(ledger["metrics"]["ttft"]["sample_count"], 0)
        self.assertGreater(ledger["attempt"]["observed_ns"]["ttft"], 0)
        self.assertFalse((self.output / "run.sock").exists())
        self.assertFalse(any(self.output.glob("slot-cache-*")))
