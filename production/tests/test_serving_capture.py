"""Exercise the scheduled capture against a small HTTP fixture."""

import asyncio
from collections import Counter
from contextlib import asynccontextmanager
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastest_serving import capture


@asynccontextmanager
async def server():
    calls = []
    attempts = Counter()
    active = set()

    async def handle(reader, writer):
        active.add(asyncio.current_task())
        try:
            headers = (await reader.readuntil(b"\r\n\r\n")).decode().splitlines()
            _, path, _ = headers[0].split()
            size = int(next(line.split(":")[1] for line in headers if line.lower().startswith("content-length:")))
            request = json.loads(await reader.readexactly(size))
            calls.append((path, request))
            status = 200
            if path == "/completion":
                user = {1251: 1, 1502: 2, 1753: 3, 1004: 4}[request["prompt"][0]]
                attempts[user] += 1
                response = {"stop": True, "tokens": [42] * 128}
                if attempts[user] > 1:
                    if user == 2:
                        response["tokens"].pop()
                    if user == 3:
                        status, response = 503, {"error": "server fixture failure"}
                    if user == 4:
                        body = json.dumps(response).encode()
                        writer.write(f"HTTP/1.1 200 Test\r\nContent-Length: {len(body)}\r\n\r\n".encode() + body[:16])
                        await writer.drain()
                        await asyncio.sleep(0.12)
                        return
            else:
                slot = int(path.split("/")[-1].split("?")[0])
                response = {"id_slot": slot, "n_erased": 1024}

            body = json.dumps(response).encode()
            writer.write(f"HTTP/1.1 {status} Test\r\nContent-Length: {len(body)}\r\n\r\n".encode() + body)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            active.discard(asyncio.current_task())

    async with await asyncio.start_server(handle, "127.0.0.1", 0) as listener:
        try:
            yield listener.sockets[0].getsockname()[1], calls
        finally:
            if active:
                await asyncio.gather(*active)


class ServingCaptureTests(unittest.IsolatedAsyncioTestCase):
    async def test_scheduled_capture_retains_attempts_and_explicit_missing_meter(self):
        async with server() as (port, calls):
            with TemporaryDirectory(prefix="fastest-serving-capture-test-") as root:
                output = Path(root) / "private"
                with patch.multiple(capture, REQUESTS=2, INTERVAL_MS=110, WINDOW_MS=220, TIMEOUT_MS=70):
                    await capture.capture(output, "127.0.0.1", port, diagnostic_reason="Local fixture.")
                ledger = json.loads((output / "capture.json").read_text())
                trace = [json.loads(line) for line in (output / "trace.jsonl").read_text().splitlines()]
                self.assertEqual(json.loads((output / "response-01-3.bin").read_bytes()),
                                 {"error": "server fixture failure"})
                self.assertEqual((output / "response-01-4.bin").read_bytes(), b'{"stop": true, "')
                request = json.loads((output / "request-4.json").read_bytes())
                self.assertEqual(request["prompt"][995:998], [1999, 1000, 1001])
                self.assertEqual(request, next(request for path, request in reversed(calls)
                                               if path == "/completion" and request["prompt"][0] == 1004))
                self.assertEqual(output.stat().st_mode & 0o777, 0o700)

        self.assertEqual([path for path, _ in calls[:8]], ["/completion"] * 4 +
                         [f"/slots/{slot}?action=erase" for slot in range(4)])
        sent = [request for path, request in calls if path == "/completion"]
        self.assertEqual(len(sent), 12)
        self.assertEqual({tuple(request["prompt"][:3]) for request in sent}, {
            (1251, 1252, 1253), (1502, 1503, 1504), (1753, 1754, 1755), (1004, 1005, 1006),
        })
        for request in sent:
            self.assertEqual(len(request.pop("prompt")), 1024)
            self.assertEqual(request, {"n_predict": 128, "temperature": 0, "ignore_eos": True,
                                       "cache_prompt": False, "return_tokens": True, "stream": False})
        self.assertEqual(ledger["kind"], "diagnostic")
        self.assertEqual(ledger["duration_ms"], 220)
        self.assertEqual(ledger["power"]["status"], "missing")
        self.assertIn("AC input", ledger["power"]["reason"])
        self.assertEqual([(attempt["request"], attempt["user"], attempt["outcome"], attempt["output_tokens"])
                          for attempt in ledger["attempts"]], [
            (1, 1, "accepted", 128), (1, 2, "rejected", 127), (1, 3, "failed", 0), (1, 4, "timeout", 0),
            (2, 1, "accepted", 128), (2, 2, "rejected", 127), (2, 3, "failed", 0), (2, 4, "timeout", 0),
        ])
        self.assertEqual([event["scheduled_ms"] for event in trace if event["phase"] == "timed"], [0] * 4 + [110] * 4)
        self.assertEqual(sum(event["phase"] == "erase" for event in trace), 4)
