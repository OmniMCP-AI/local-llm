"""Private latency capture over the pinned llama-server native completion stream."""

from contextlib import contextmanager
from http.client import HTTPException
import json
import os
import platform
import re
import shutil
import signal
from time import monotonic_ns

from fastest_agent_task.measure import LocalConnection, exchange, interrupt, local_server
from fastest_pilot_bundle import digest, json_text
from fastest_pilot_capture import record_process, save_json, sha256_file, utc_now
from fastest_release.validation import plain_text

from .capture import (
    CUDA_MASK, PLACEMENTS, device_placement_matches, effective_placement, pinned_commit, private_environment,
    verify_shards,
)


VERSION_FOOTER = re.compile(r"^version: (\d+) \(([0-9a-f]{7,40})\)$", re.MULTILINE)
SERVER_SETTINGS = {
    "context_tokens": 2048, "threads": 8, "gpu_layers": 99, "batch_tokens": 512, "parallel_requests": 1,
}
GENERATION_SETTINGS = {
    "cache_prompt": False, "id_slot": 0, "n_predict": 256, "return_tokens": True,
    "seed": 42, "stream": True, "temperature": 0, "top_k": 1,
}
BOUNDARIES = {
    "ttft": "Private client request start to receipt of the first generated token event.",
    "first_visible_answer": "Private client request start to the first complete stream frame with printable non-whitespace text.",
}


@contextmanager
def capture_signals():
    previous = {}
    try:
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM):
            previous[signum] = signal.signal(signum, interrupt)
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def check_server(output, binary, revision, env):
    directory = output / "runtime"
    probe = record_process(directory, {"argv": [str(binary), "--version"]}, "stdout.txt", 10, env)
    messages = [
        (directory / file).read_text(encoding="utf-8", errors="replace") for file in probe["files"]
    ]
    versions = VERSION_FOOTER.findall("\n".join(messages))
    if probe["exit_code"] != 0 or len(versions) != 1 or not pinned_commit(versions[0][1], revision):
        raise ValueError("llama-server version does not match the pinned b5163 revision.")
    number, commit = versions[0]
    return {"commit_reported": commit, "number_reported": int(number)}


def stream_events(response, raw):
    """Consume the b5163 data line and separator together before observing arrival."""
    if response.status != 200 or response.headers.get_content_type() != "text/event-stream":
        raw.write(response.read(65_536))
        raise ValueError(f"Expected a native completion stream. HTTP status: {response.status}.")
    for line in iter(lambda: response.readline(65_537), b""):
        raw.write(line)
        if line in (b"\n", b"\r\n") or line.startswith(b":"):
            continue
        if not line.startswith(b"data: ") or len(line) > 65_536:
            raise ValueError("Unexpected or oversized SSE event. See the private stream.")
        separator = response.readline(2)
        received = monotonic_ns()
        raw.write(separator)
        if separator not in (b"\n", b"\r\n"):
            raise ValueError("Incomplete SSE event. See the private stream.")
        yield json.loads(line[6:]), received


def stream_attempt(output, listener, body, timeout, label, attempt):
    raw_path = output / f"{label}.sse"
    connection = LocalConnection(listener, timeout)
    attempt.update(
        status="running", expected_max_output_tokens=GENERATION_SETTINGS["n_predict"],
        prompt_tokens=None, output_tokens=None, events=0, observed_ns=dict.fromkeys(BOUNDARIES),
    )
    answer_parts = []
    previous = 0
    try:
        with raw_path.open("xb") as raw:
            attempt["started_monotonic_ns"] = monotonic_ns()
            signal.setitimer(signal.ITIMER_REAL, timeout)
            connection.request("POST", "/completion", body, {"Content-Type": "application/json"})
            with connection.getresponse() as response:
                for event, received in stream_events(response, raw):
                    if not isinstance(event, dict) or type(event.get("index")) is not int or event["index"] != 0:
                        raise ValueError("Unexpected completion index in the stream.")
                    final = event.get("stop")
                    # b5163 leaves the slot unset on partials and fills it on the terminal result.
                    slot = event.get("id_slot")
                    if type(slot) is not int or slot != (0 if final else -1):
                        raise ValueError("Unexpected slot in the native completion stream.")
                    count = event.get("tokens_predicted")
                    prompt_tokens = event.get("tokens_evaluated")
                    content = event.get("content")
                    if (type(final) is not bool or type(count) is not int or type(prompt_tokens) is not int
                            or not previous <= count <= attempt["expected_max_output_tokens"]
                            or prompt_tokens < 1 or attempt["prompt_tokens"] not in (None, prompt_tokens)
                            or not isinstance(content, str)):
                        raise ValueError("Unexpected generated token count, prompt length, or content in the stream.")
                    attempt["prompt_tokens"] = prompt_tokens
                    elapsed = received - attempt["started_monotonic_ns"]
                    if final:
                        if event.get("truncated") is not False or event.get("stop_type") not in ("eos", "word", "limit"):
                            raise ValueError("Completion ended outside the pinned request bounds.")
                        attempt.update(status="complete", output_tokens=count)
                        return "".join(answer_parts)
                    tokens = event.get("tokens")
                    if (count <= previous or not isinstance(tokens, list) or len(tokens) != 1
                            or type(tokens[0]) is not int or tokens[0] < 0):
                        raise ValueError("Expected an ordered native generated-token event.")
                    previous = count
                    attempt["events"] += 1
                    if count == 1:
                        attempt["observed_ns"]["ttft"] = elapsed
                    if (attempt["observed_ns"]["first_visible_answer"] is None
                            and any(character.isprintable() and not character.isspace() for character in content)):
                        attempt["observed_ns"]["first_visible_answer"] = elapsed
                    answer_parts.append(content)
                attempt.update(status="incomplete", reason="Stream ended before a complete terminal event.")
    except TimeoutError:
        attempt.update(status="timeout", reason="Streaming request exceeded its wall time limit.")
    except (OSError, HTTPException, ValueError, RecursionError) as error:
        attempt.update(status="failed", reason=str(error))
    except KeyboardInterrupt:
        attempt.update(status="interrupted", reason="Operator interrupted the streaming request.")
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        connection.close()
        attempt["finished_monotonic_ns"] = monotonic_ns()


def capture_latency(args, plan):
    cell = next(cell for cell in plan["cells"] if cell["id"] == args.cell)
    env = {key: value for key, value in os.environ.items() if not key.startswith(("LLAMA_", "GGML_", "DYLD_", "LD_"))}
    env["LC_ALL"] = "C"
    args.output.mkdir(mode=0o700)
    output = args.output.resolve()
    ledger = {
        "schema_version": 1, "kind": "private-latency-capture", "status": "starting",
        "protocol": "llama-server-native-zh-copy-latency@1", "cell_id": cell["id"], "platform": platform.platform(),
        "host_revision": args.host_revision, "quiet_host_operator_attested": args.quiet_host,
        "environment": private_environment(env),
        "runtime": {
            **plan["runtime"], "name": "llama.cpp llama-server",
            "source": f'https://github.com/ggml-org/llama.cpp/tree/{plan["runtime"]["revision"]}/examples/server',
        },
        "artifact": plan["artifact"], "verified_shards": [], "server_settings": SERVER_SETTINGS,
        "quality": {"status": "unreviewed", "rubric_id": plan["rubric"]["id"]},
        "started_utc": utc_now(), "warmup": {"status": "not-run"}, "attempt": {"status": "not-run"},
        "metrics": {key: {"status": "missing", "sample_count": 0, "samples_ns": [], "boundary": boundary,
                          "reason": "No completed measured streaming request."}
                    for key, boundary in BOUNDARIES.items()},
    }
    ledger_path = output / "latency.json"
    save_json(ledger_path, ledger)
    try:
        if not plain_text(args.host_revision) or args.timeout < 1:
            raise ValueError("Supply a stable physical host revision and a positive timeout.")
        if args.cell == "rtx-4090" and not CUDA_MASK.fullmatch(env.get("CUDA_VISIBLE_DEVICES", "")):
            raise ValueError("Select one allocated device in CUDA_VISIBLE_DEVICES before capturing the CUDA cell.")
        if not args.build_evidence.is_file() or args.build_evidence.stat().st_size == 0:
            raise ValueError("Supply a nonempty local runtime build evidence file.")
        shutil.copyfile(args.build_evidence, output / "build-evidence")
        binary = args.server.resolve()
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError("Supply an executable llama-server binary.")
        ledger["binary_sha256"] = sha256_file(binary)
        ledger["runtime_build"] = check_server(output, binary, plan["runtime"]["revision"], env)
        model_dir = args.model_dir.resolve()
        verify_shards(model_dir, plan["artifact"], ledger["verified_shards"])
        model = model_dir / plan["artifact"]["shards"][0]["path"]

        device = PLACEMENTS[args.cell][0]
        with local_server(output, binary, model, device, SERVER_SETTINGS, env) as listener:
            placement = effective_placement((output / "server.log").read_text(encoding="utf-8", errors="replace"), [])
            ledger["placement"] = placement
            if not device_placement_matches(cell, SERVER_SETTINGS["context_tokens"], placement):
                raise ValueError("Server device, model and KV placement, or context differs from the planned cell.")

            chat = {"messages": [{"role": "user", "content": plan["rubric"]["prompt"]}]}
            save_json(output / "template-request.json", chat)
            prompt = exchange(listener, "/apply-template", 5, chat).get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("The server did not resolve the embedded chat template.")
            body = json_text({"prompt": prompt, **GENERATION_SETTINGS}).encode("utf-8")
            (output / "request.json").write_bytes(body)
            ledger["status"] = "capturing"
            save_json(ledger_path, ledger)
            for label in ("warmup", "attempt"):
                attempt = ledger[label]
                erased = exchange(listener, "/slots/0?action=erase", 5, {})
                if (not isinstance(erased, dict) or type(erased.get("id_slot")) is not int or erased["id_slot"] != 0
                        or type(erased.get("n_erased")) is not int or erased["n_erased"] < 0):
                    raise ValueError("The server did not confirm a KV reset.")
                attempt["kv_reset"] = erased
                answer = stream_attempt(output, listener, body, args.timeout, label, attempt)
                save_json(ledger_path, ledger)
                if attempt["status"] != "complete":
                    ledger.update(status="incomplete", reason=attempt["reason"])
                    return False

        for key, metric in ledger["metrics"].items():
            observed = ledger["attempt"]["observed_ns"][key]
            if observed is not None:
                metric.update(status="measured", sample_count=1, samples_ns=[observed])
                metric.pop("reason")
            else:
                metric["reason"] = ("The stream did not emit generated token ordinal 1." if key == "ttft"
                                    else "The stream did not emit printable non-whitespace answer text.")
        if ledger["metrics"]["first_visible_answer"]["sample_count"]:
            save_json(output / "response.json", {"choices": [{"message": {"role": "assistant", "content": answer}}]})
            ledger["quality"]["output_sha256"] = digest(answer)
        ledger["status"] = "complete"
    except (HTTPException, OSError, RuntimeError, ValueError, KeyboardInterrupt) as error:
        ledger.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "blocked",
                      reason=str(error) or type(error).__name__)
        if isinstance(error, (HTTPException, RuntimeError)):
            raise ValueError(ledger["reason"]) from error
        raise
    finally:
        ledger["finished_utc"] = utc_now()
        ledger["files"] = {str(path.relative_to(output)): sha256_file(path)
                           for path in sorted(output.rglob("*")) if path.is_file() and path != ledger_path}
        save_json(ledger_path, ledger)
    return True
