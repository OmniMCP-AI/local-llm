"""Capture a private attempt ledger against a dedicated local ComfyUI process."""

import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
from time import monotonic_ns
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from websocket import WebSocketException, WebSocketTimeoutException, create_connection


def request(url, timeout, data=None):
    headers = {"Content-Type": "application/json"} if data is not None else {}
    with urlopen(Request(url, data=data, headers=headers), timeout=timeout) as response:
        return response.read()


def capture_attempt(socket, base, client_id, workflow, plan, seed, phase):
    protocol = plan["protocol"]
    workflow[plan["workflow"]["sampler_node"]]["inputs"]["noise_seed"] = seed
    endpoints = {item["node"]: item["id"] for item in protocol["phase_endpoints"]}
    phase_order = list(endpoints.values())
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    offsets = {}
    image = None
    start = monotonic_ns()
    deadline = start + protocol["timeout_s"] * 10**9

    def remaining():
        available = deadline - monotonic_ns()
        if available <= 0:
            raise TimeoutError
        return available / 10**9

    outcome, reason = "success", ""
    try:
        prompt_id = json.loads(request(base + "/prompt", remaining(), payload))["prompt_id"]
        while "complete" not in offsets:
            socket.settimeout(remaining())
            raw = socket.recv()
            elapsed = monotonic_ns() - start
            if not raw:
                raise ValueError("ComfyUI disconnected before completing the prompt.")
            if isinstance(raw, bytes):
                continue
            event = json.loads(raw)
            data = event.get("data", {})
            if data.get("prompt_id") != prompt_id:
                continue

            kind, node = event.get("type"), data.get("node")
            if kind == "execution_error":
                error_type = data.get("exception_type", "execution error")
                outcome = "oom" if str(error_type).endswith("OutOfMemoryError") else "failed"
                reason = f"ComfyUI reported {error_type}."
                break
            if kind == "execution_interrupted":
                outcome, reason = "interrupted", "ComfyUI interrupted the prompt."
                break
            if kind == "executing" and node in endpoints:
                endpoint = endpoints[node]
                if endpoint not in offsets:
                    if endpoint != phase_order[len(offsets)]:
                        raise ValueError("ComfyUI phase order differs from the pinned workflow.")
                    offsets[endpoint] = elapsed
            if kind == "executed" and node == plan["workflow"]["output_node"]:
                images = data.get("output", {}).get("images", [])
                if len(images) == 1:
                    image = images[0]

        if outcome == "success":
            if image is None:
                raise ValueError("ComfyUI did not report exactly one saved image.")
            image = request(base + "/view?" + urlencode(image), remaining())
            end = monotonic_ns()
            if end > deadline:
                raise TimeoutError
        else:
            end = monotonic_ns()
            image = None
    except (TimeoutError, WebSocketTimeoutException):
        outcome, reason, image = "timeout", "Client deadline elapsed.", None
        end = monotonic_ns()
    except (OSError, ValueError, KeyError, WebSocketException) as error:
        outcome, reason, image = "failed", f"Capture error ({type(error).__name__}).", None
        end = monotonic_ns()

    attempt = {
        "phase": phase, "seed": seed, "outcome": outcome,
        "elapsed_ns": end - start, "phase_end_ns": offsets,
    }
    if outcome == "success":
        attempt["output_sha256"] = sha256(image).hexdigest()
        if phase == "repeat":
            attempt["review"] = None
    else:
        attempt["reason"] = reason
    return attempt, image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory for the private attempts and PNGs.")
    parser.add_argument("--port", type=int, default=8188, help="Port of the dedicated loopback-only server.")
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    plan = json.loads((package / "plan.json").read_text(encoding="utf-8"))
    graph = (package / plan["workflow"]["path"]).read_bytes()
    if sha256(graph).hexdigest() != plan["workflow"]["sha256"]:
        parser.exit(1, "workflow does not match the pinned SHA-256\n")
    workflow = json.loads(graph)
    protocol = plan["protocol"]
    client_id = uuid4().hex
    host = f"127.0.0.1:{args.port}"
    attempts = []
    with closing(create_connection(f"ws://{host}/ws?clientId={client_id}", timeout=5)) as socket:
        args.output.mkdir()
        for index, seed in enumerate([protocol["warmup_seed"], *protocol["repeat_seeds"]]):
            phase = "repeat" if index else "warmup"
            attempt, image = capture_attempt(socket, f"http://{host}", client_id, workflow, plan, seed, phase)
            if image is not None:
                (args.output / f"sample-{index:02d}.png").write_bytes(image)
            attempts.append(attempt)
            staged = args.output / "attempts.next.json"
            staged.write_text(json.dumps(attempts, indent=2) + "\n", encoding="utf-8")
            staged.replace(args.output / "attempts.json")
            if attempt["outcome"] == "timeout" or (not index and attempt["outcome"] != "success"):
                parser.exit(1, f"Capture stopped after {phase} {seed}. Private attempts were saved.\n")


if __name__ == "__main__":
    main()
