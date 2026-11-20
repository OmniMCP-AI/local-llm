"""Run the controlled inventory task against a private llama.cpp server."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import file_digest
from http.client import HTTPConnection, HTTPException
import json
import os
import platform
from pathlib import Path
import re
import signal
import socket
import subprocess
import time
from uuid import uuid4

from .evidence import attempt_outcome, evaluate_attempts
from .harness import BUDGET, TASK, TASK_BYTES, plan, read_tool


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def unique_keys(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("Duplicate JSON key")
    return result


def run_attempt(complete, context, trial, number, settings):
    opening = TASK["prompt"] + "\nAllowed tool requests: " + compact(context["allowed_reads"])
    messages = [{"role": "user", "content": opening}]
    attempt = {
        "trial": trial, "attempt": number, "wall_ns": 1, "generated_tokens": 0,
        "reasoning_tokens": 0, "termination": "budget_exhausted", "answer": None,
        "tool_reads": [],
    }
    turns = []
    outcome = None
    started = time.monotonic_ns()
    deadline = started + BUDGET["wall_ns_per_attempt"]

    while attempt["generated_tokens"] < BUDGET["generated_tokens_per_attempt"]:
        request = {
            "model": "pinned-qwen", "messages": list(messages), "stream": False,
            "cache_prompt": False,
            **{key: settings[key] for key in ("temperature", "top_k", "seed")},
            "max_tokens": BUDGET["generated_tokens_per_attempt"] - attempt["generated_tokens"],
        }
        now = time.monotonic_ns()
        if now >= deadline:
            break
        turn = {"request": request, "started_monotonic_ns": now}
        turns.append(turn)
        try:
            response = complete(request, (deadline - now) / 1_000_000_000)
            turn["response"] = response
            count = response["usage"]["completion_tokens"]
            if type(count) is not int or not 0 <= count <= request["max_tokens"]:
                raise ValueError("Invalid completion token usage")
        except (OSError, HTTPException, ValueError, KeyError, TypeError) as error:
            turn["error"] = repr(error)
            attempt.update(termination="runtime_error", generated_tokens=None)
            break
        finally:
            turn["ended_monotonic_ns"] = time.monotonic_ns()

        attempt["generated_tokens"] += count
        try:
            choice = response["choices"][0]
            message = choice["message"]
            if choice["finish_reason"] == "length":
                break
            if message.get("reasoning_content"):
                raise ValueError("Unexpected separate reasoning")
            reply = json.loads(message["content"], object_pairs_hook=unique_keys)
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            attempt["termination"] = "invalid_output"
            break

        if isinstance(reply, dict) and set(reply) == {"tool", "resource"} and all(
            isinstance(value, str) for value in reply.values()
        ):
            if len(attempt["tool_reads"]) == BUDGET["tool_reads_per_attempt"]:
                break
            try:
                result = read_tool(context["id"], reply["tool"], reply["resource"])
            except ValueError:
                attempt["termination"] = "tool_denied"
                turn["denied_tool"] = reply
                break
            attempt["tool_reads"].append(reply)
            turn["tool_result"] = result
            messages.extend([
                {"role": "assistant", "content": message["content"]},
                {"role": "user", "content": compact(result)},
            ])
        else:
            attempt.update(termination="answered", answer=reply)
            try:
                outcome = attempt_outcome(attempt, context, demo=False)
            except ValueError:
                attempt.update(termination="invalid_output", answer=None)
            break

    ended = time.monotonic_ns()
    attempt["wall_ns"] = max(1, ended - started)
    if ended >= deadline:
        attempt.update(termination="timeout", answer=None)
        outcome = None
    return {
        "context_id": context["id"], "attempt": attempt, "outcome": outcome or attempt["termination"],
        "started_monotonic_ns": started, "ended_monotonic_ns": ended, "turns": turns,
    }


class LocalConnection(HTTPConnection):
    def __init__(self, path, timeout):
        super().__init__("localhost", timeout=timeout)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(self.path))


def interrupt(signum, _frame):
    if signum == signal.SIGALRM:
        raise TimeoutError("Local response exceeded its wall time limit")
    raise KeyboardInterrupt(f"received signal {signum}")


def exchange(path, endpoint, timeout, body=None):
    conn = LocalConnection(path, timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        if body is None:
            conn.request("GET", endpoint)
        else:
            conn.request("POST", endpoint, compact(body).encode(), {"Content-Type": "application/json"})
        response = conn.getresponse()
        raw = response.read()
        if response.status != 200:
            raise ValueError(f"llama.cpp response {response.status}: {raw!r}")
        return json.loads(raw)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        conn.close()


def digest(path):
    with path.open("rb") as source:
        return file_digest(source, "sha256").hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def event(directory, data):
    with (directory / "events.jsonl").open("a", encoding="utf-8") as log:
        log.write(compact({"utc": datetime.now(timezone.utc).isoformat(), **data}) + "\n")


@contextmanager
def local_server(directory, binary, model, device, settings, env):
    listener = directory / "run.sock"
    command = [
        str(binary), "--model", str(model), "--host", str(listener), "--device", device,
        "--split-mode", "none", "--no-webui", "--jinja", "--no-warmup",
        "--alias", "pinned-qwen", "--cache-reuse", "0", "--reasoning-format", "none",
        "--ctx-size", str(settings["context_tokens"]), "--threads", str(settings["threads"]),
        "--gpu-layers", str(settings["gpu_layers"]), "--batch-size", str(settings["batch_tokens"]),
        "--parallel", str(settings["parallel_requests"]),
    ]

    with (directory / "server.log").open("wb") as output:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, env=env)
        try:
            event(directory, {"event": "server_started", "pid": child.pid, "command": command})
            for _ in range(120):
                if child.poll() is not None:
                    raise RuntimeError("llama.cpp stopped before readiness. Inspect server.log in the private packet.")
                try:
                    if exchange(listener, "/health", 1).get("status") == "ok":
                        break
                except (OSError, HTTPException, ValueError):
                    pass
                time.sleep(0.5)
            else:
                raise RuntimeError("llama.cpp never became ready")
            event(directory, {"event": "server_ready", "pid": child.pid})
            yield listener
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            listener.unlink(missing_ok=True)
            event(directory, {"event": "server_stopped", "pid": child.pid, "returncode": child.returncode})


def capture_host(path):
    commands = [["uname", "-a"]]
    if platform.system() == "Darwin":
        commands += [
            ["sw_vers"],
            ["sysctl", "hw.model", "hw.memsize", "hw.logicalcpu", "vm.swapusage"],
            ["top", "-l", "2", "-s", "1", "-n", "0"],
            ["system_profiler", "SPDisplaysDataType", "-json"],
        ]
    else:
        commands.append(["uptime"])
    with path.open("wb") as output:
        output.write((datetime.now(timezone.utc).isoformat() + "\n").encode())
        output.flush()
        for command in commands:
            subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=20, check=False)


def run(directory, binary, model, hardware, os_build, backend, device):
    protocol = plan()
    directory.mkdir(mode=0o700)
    write_json(directory / "plan.json", protocol)
    (directory / "task.json").write_bytes(TASK_BYTES)
    adapter = Path(__file__).read_bytes()
    (directory / "measure.py").write_bytes(adapter)

    env = {key: value for key, value in os.environ.items() if not key.startswith(("LLAMA_", "GGML_", "DYLD_", "LD_"))}
    version = subprocess.check_output([binary, "--version"], stderr=subprocess.STDOUT, text=True, timeout=10, env=env)
    (directory / "runtime-version.txt").write_text(version, encoding="utf-8")
    revision = protocol["runtime"]["revision"]
    version_commit = re.search(r"^version: [0-9]+ \(([0-9a-f]{7,40})\)", version, re.MULTILINE)
    if not version_commit or not revision.startswith(version_commit[1]):
        raise ValueError("llama-server revision does not match the plan")

    shards = protocol["artifact"]["shards"]
    if model.name != shards[0]["path"]:
        raise ValueError("Supply the first pinned GGUF shard; keep its companion alongside it")
    for shard in shards:
        path = model.with_name(shard["path"])
        if path.stat().st_size != shard["bytes"] or digest(path) != shard["sha256"]:
            raise ValueError(f"{path.name} does not match the pinned artifact")

    build = {"llama-server": digest(binary)}
    for pattern in ("*.dylib", "*.so*", "*.metal"):
        build.update({path.name: digest(path) for path in sorted(binary.parent.glob(pattern)) if path.is_file()})
    write_json(directory / "runtime-files.json", build)
    environment = {
        "hardware": hardware, "os": os_build, "backend": backend,
        "runtime_binary_sha256": build["llama-server"], "adapter_sha256": digest(directory / "measure.py"),
    }
    write_json(directory / "environment.json", environment)

    contexts = {context["id"]: context for context in protocol["contexts"]}
    records = {
        name: {"kind": "measured", "context_id": name, "context_sha256": context["sha256"],
               "environment": environment, "attempts": []}
        for name, context in contexts.items()
    }

    capture_host(directory / "host-before.txt")
    with local_server(directory, binary, model, device, protocol["settings"], env) as listener:
        def complete(body, timeout):
            return exchange(listener, "/v1/chat/completions", timeout, body)

        def attempt(name, trial, number, warmup=False):
            raw = run_attempt(complete, contexts[name], trial, number, protocol["settings"])
            event(directory, {"event": "attempt", "warmup": warmup, **raw})
            return raw

        for name in contexts:
            attempt(name, 1, 1, warmup=True)

        for name, trial in (("bundle", 1), ("split", 1), ("split", 2), ("bundle", 2)):
            record = records[name]
            for number in range(1, BUDGET["retries_per_trial"] + 2):
                raw = attempt(name, trial, number)
                record["attempts"].append(raw["attempt"])
                evaluate_attempts(record["attempts"], contexts[name], demo=False)
                write_json(directory / f"{name}-draft.json", record)
                if raw["outcome"] == "accepted":
                    break

    capture_host(directory / "host-after.txt")
    write_review_packet(directory, contexts)


def write_review_packet(directory, contexts):
    manifest = {path.name: digest(path) for path in sorted(directory.iterdir()) if path.is_file()}
    manifest_path = directory / "retained-sha256.json"
    write_json(manifest_path, manifest)
    write_json(directory / "review-pending.json", {
        "status": "pending_operator_review",
        "retained_sha256": digest(manifest_path),
        "contexts": {
            name: {"evidence_id": str(uuid4()), "context_sha256": context["sha256"], "draft": f"{name}-draft.json"}
            for name, context in contexts.items()
        },
    })


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path, help="Short, new path inside your private evidence directory")
    cli.add_argument("llama_server", type=Path)
    cli.add_argument("first_gguf", type=Path)
    cli.add_argument("--hardware", required=True)
    cli.add_argument("--os", required=True, help="Operating system version and build")
    cli.add_argument("--backend", choices=("Metal", "CUDA"), required=True)
    cli.add_argument("--device", required=True, help="One device from llama-server --list-devices")
    args = cli.parse_args()
    os.umask(0o077)
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM):
        signal.signal(signum, interrupt)
    try:
        run(args.directory.resolve(), args.llama_server.resolve(), args.first_gguf.resolve(),
            args.hardware, args.os, args.backend, args.device)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        cli.exit(1, f"{error}\n")
    except KeyboardInterrupt:
        cli.exit(130, "Measurement interrupted. The private evidence recorded so far was kept.\n")


if __name__ == "__main__":
    main()
