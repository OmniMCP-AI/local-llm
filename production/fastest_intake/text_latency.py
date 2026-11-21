"""Verify and retain a private native-stream text latency capture."""

import json
from pathlib import Path
from subprocess import TimeoutExpired

from fastest_agent_task.measure import server_command
from fastest_pilot_bundle import digest, json_text
from fastest_pilot_capture import sha256_file
from fastest_release import ReleaseError, _sql_text
from fastest_release.validation import plain_text
from fastest_text.capture import CUDA_MASK, PLACEMENTS, device_placement_matches, effective_placement
from fastest_text.intake import json_settings_match, require, require_digest
from fastest_text.latency import (
    BOUNDARIES, GENERATION_SETTINGS, PROTOCOL, SERVER_SETTINGS, framed_events, parse_server_version,
    read_completion, runtime_profile,
)

from .scaling_capture import _check_digest, _decode_json, _directory, _process, _read_json, _timestamp
from .text_capture import PLAN_PATH


FILES = {
    "attempt.sse", "warmup.sse", "build-evidence", "events.jsonl", "server.log", "request.json",
    "response.json", "template-request.json", "runtime/attempt.json", "runtime/stdout.txt", "runtime/stderr.log",
}
OUTCOMES = ("not-run", "complete", "incomplete", "failed", "timeout", "interrupted")


def verify_inventory(packet, declared):
    require(isinstance(declared, dict) and declared.keys() <= FILES, "Invalid latency packet inventory.")
    actual = set()
    for path in packet.rglob("*"):
        require(not path.is_symlink(), "Latency evidence cannot contain symbolic links.")
        name = path.relative_to(packet).as_posix()
        if name in ("latency.json", "runtime") and (path.is_file() if name == "latency.json" else path.is_dir()):
            continue
        require(path.is_file() and name in declared, "Unexpected or unsealed latency packet evidence.")
        _check_digest(path, declared[name], sha256_file(path))
        actual.add(name)
    require(actual == declared.keys(), "Missing latency packet evidence.")
    return actual


def verify_controls(packet, run, plan, cell, files):
    require({"request.json", "template-request.json", "server.log", "events.jsonl", "build-evidence"} <= files,
            "Started latency requests require sealed runtime and request evidence.")
    require(run["verified_shards"] == plan["artifact"]["shards"] and plain_text(run.get("host_revision"))
            and (packet / "build-evidence").stat().st_size > 0, "Started latency requests require a pinned host and build.")
    require_digest(run.get("binary_sha256"), "binary_sha256")
    environment = run.get("environment")
    require(isinstance(environment, dict) and environment.get("LC_ALL") == "C"
            and all(key == "LC_ALL" or key.startswith("CUDA_") for key in environment),
            "Unexpected latency runtime environment.")
    if cell["backend"] == "CUDA":
        mask = environment.get("CUDA_VISIBLE_DEVICES")
        require(isinstance(mask, str) and CUDA_MASK.fullmatch(mask), "Latency capture requires one CUDA device.")

    probe, _, logs, _, _ = _process(packet / "runtime", "stdout.txt")
    argv = probe.get("argv")
    require(probe["outcome"] == "exited" and probe["exit_code"] == 0 and probe["timeout_seconds"] == 10
            and isinstance(argv, list) and len(argv) == 2 and plain_text(argv[0]) and argv[1] == "--version",
            "Latency capture requires a successful retained runtime probe.")
    version = parse_server_version(
        [raw.decode("utf-8", "replace") for raw in logs.values()], plan["runtime"]["revision"],
    )
    require(version["number_reported"] == int(plan["runtime"]["tag"][1:])
            and json_settings_match(run.get("runtime_build"), version),
            "Latency runtime build differs from the pinned b5163 probe.")

    placement = effective_placement((packet / "server.log").read_text(encoding="utf-8", errors="replace"), [])
    require(json_text(run.get("placement")) == json_text(placement)
            and device_placement_matches(cell, SERVER_SETTINGS["context_tokens"], placement),
            "Latency accelerator placement or context differs from the pinned cell.")
    events = [_decode_json(line) for line in (packet / "events.jsonl").read_bytes().splitlines()]
    require(all(isinstance(event, dict) for event in events)
            and [event.get("event") for event in events] == ["server_started", "server_ready", "server_stopped"],
            "Latency evidence requires one ready server lifecycle.")
    command = events[0].get("command")
    pid = events[0].get("pid")
    require(type(pid) is int and pid > 0 and all(event.get("pid") == pid for event in events)
            and isinstance(command, list) and len(command) >= 7
            and all(plain_text(argument) for argument in command), "Invalid latency server invocation.")
    model, listener, cache = map(Path, (command[2], command[4], command[-1]))
    require(model.name == plan["artifact"]["shards"][0]["path"]
            and listener.name == "run.sock" and cache.parent == listener.parent
            and cache.name.startswith("slot-cache-")
            and command == server_command(argv[0], model, listener, PLACEMENTS[cell["id"]][0], SERVER_SETTINGS)
            + ["--slot-save-path", str(cache)], "Latency server invocation differs from the pinned controls.")

    template, _ = _read_json(packet / "template-request.json")
    request, _ = _read_json(packet / "request.json")
    require(template == {"messages": [{"role": "user", "content": plan["rubric"]["prompt"]}]},
            "Latency capture does not use the pinned Chinese task.")
    require(isinstance(request, dict) and isinstance(request.get("prompt"), str) and request["prompt"].strip()
            and json_settings_match({key: value for key, value in request.items() if key != "prompt"},
                                    GENERATION_SETTINGS), "Latency request differs from the pinned generation controls.")


def checked_attempt(packet, label, attempt, files):
    require(isinstance(attempt, dict) and attempt.get("status") in OUTCOMES, "Invalid latency request outcome.")
    file = f"{label}.sse"
    if attempt["status"] == "not-run":
        require(attempt == {"status": "not-run"} and file not in files, "Unexpected evidence for unstarted request.")
        return dict.fromkeys(BOUNDARIES), None

    cap = GENERATION_SETTINGS["n_predict"]
    reset = attempt.get("kv_reset")
    require(isinstance(reset, dict) and type(reset.get("id_slot")) is int and reset["id_slot"] == 0
            and type(reset.get("n_erased")) is int and reset["n_erased"] >= 0
            and type(attempt.get("expected_max_output_tokens")) is int and attempt["expected_max_output_tokens"] == cap,
            "Latency request must follow a slot reset and use the pinned output limit.")
    start, end = (attempt.get(f"{point}_monotonic_ns") for point in ("started", "finished"))
    require(type(end) is int and 0 < end < 2**63 and (start is None or type(start) is int and 0 < start <= end)
            and (start is not None) == (file in files), "Invalid latency request timing bounds.")
    observed = attempt.get("observed_ns")
    require(isinstance(observed, dict) and observed.keys() == BOUNDARIES.keys()
            and all(value is None or start is not None and type(value) is int and 0 < value <= end - start
                    for value in observed.values()), "Observed latency must fall within the request.")
    ttft, visible = (observed[key] for key in BOUNDARIES)
    require(ttft is None or visible is None or ttft <= visible, "Latency boundaries are out of sequence.")

    replay = {"status": "running", "started_monotonic_ns": 0, "expected_max_output_tokens": cap,
              "prompt_tokens": None, "output_tokens": None, "events": 0, "observed_ns": dict.fromkeys(BOUNDARIES)}
    answer = None
    if file in files:
        with (packet / file).open("rb") as stream:
            try:
                answer = read_completion(framed_events(stream, lambda _: None, lambda: 1), replay)
            except (ValueError, RecursionError):
                require(attempt["status"] in ("failed", "timeout", "interrupted"), "Invalid retained latency stream.")
            if replay["status"] == "complete":
                require(not stream.read(1), "Unexpected stream bytes after the terminal event.")
    require((attempt["status"] == "complete") == (replay["status"] == "complete")
            and all(type(attempt.get(key)) is type(replay[key]) and attempt.get(key) == replay[key]
                    for key in ("prompt_tokens", "output_tokens", "events"))
            and all((observed[key] is None) == (replay["observed_ns"][key] is None) for key in BOUNDARIES)
            and (attempt["prompt_tokens"] is None or attempt["prompt_tokens"] <= SERVER_SETTINGS["context_tokens"]),
            "Latency timings or token counts disagree with the native stream.")
    return observed, answer


def read_packet(packet, plan):
    require(_directory(packet) is not None, "Expected a private text latency capture directory.")
    run, capture_sha = _read_json(packet / "latency.json")
    require(isinstance(run, dict) and type(run.get("schema_version")) is int and run["schema_version"] == 1
            and run.get("kind") == "private-latency-capture" and run.get("protocol") == PROTOCOL
            and "rights" not in run, "Expected a version 1 private text latency capture.")
    status = run.get("status")
    require(status in ("complete", "incomplete", "blocked", "interrupted")
            and _timestamp(run.get("started_utc")) <= _timestamp(run.get("finished_utc")),
            "Latency capture must be finalized with ordered UTC timestamps.")
    cell = next((cell for cell in plan["cells"] if cell["id"] == run.get("cell_id")), None)
    quiet = run.get("quiet_host_operator_attested")
    require(cell is not None and type(quiet) is bool and plain_text(run.get("platform"))
            and json_text(run.get("artifact")) == json_text(plan["artifact"])
            and json_text(run.get("runtime")) == json_text(runtime_profile(plan))
            and json_settings_match(run.get("server_settings"), SERVER_SETTINGS),
            "Latency capture differs from the pinned artifact, runtime or cell conditions.")
    shards = run.get("verified_shards")
    require(isinstance(shards, list) and json_text(shards) == json_text(plan["artifact"]["shards"][:len(shards)]),
            "Verified latency shards differ from the pinned artifact.")

    files = verify_inventory(packet, run.get("files"))
    warmup, attempt = run.get("warmup"), run.get("attempt")
    for request in (warmup, attempt):
        require(isinstance(request, dict) and request.get("status") in OUTCOMES, "Invalid latency request outcome.")
    if warmup["status"] != "not-run":
        verify_controls(packet, run, plan, cell, files)
    checked_attempt(packet, "warmup", warmup, files)
    observed, answer = checked_attempt(packet, "attempt", attempt, files)
    if attempt["status"] != "not-run":
        require(warmup["status"] == "complete"
                and warmup["finished_monotonic_ns"] <= (attempt.get("started_monotonic_ns")
                                                      or attempt["finished_monotonic_ns"]),
                "Timed latency request must follow a completed warmup.")
    require((status == "complete") == (attempt["status"] == "complete")
            and (status != "incomplete" or any(request["status"] in ("incomplete", "failed", "timeout")
                                               for request in (warmup, attempt))),
            "Latency capture outcome disagrees with its requests.")

    metrics = run.get("metrics")
    require(isinstance(metrics, dict) and metrics.keys() == BOUNDARIES.keys(), "Missing latency boundary metrics.")
    for key, boundary in BOUNDARIES.items():
        samples = [observed[key]] if status == "complete" and observed[key] is not None else []
        metric = metrics[key]
        require(isinstance(metric, dict) and metric.get("boundary") == boundary
                and metric.get("status") == ("measured" if samples else "missing")
                and type(metric.get("sample_count")) is int and metric["sample_count"] == len(samples)
                and json_text(metric.get("samples_ns")) == json_text(samples),
                "Latency sample summary disagrees with the validated attempt.")

    quality = {"status": "unreviewed", "rubric_id": plan["rubric"]["id"]}
    if status == "complete" and observed["first_visible_answer"] is not None:
        response, _ = _read_json(packet / "response.json")
        require(response == {"choices": [{"message": {"role": "assistant", "content": answer}}]},
                "Retained response disagrees with the native stream.")
        quality["output_sha256"] = digest(answer)
    else:
        require("response.json" not in files, "Unexpected retained response without a complete visible answer.")
    require(run.get("quality") == quality, "Latency packet must remain private and unreviewed.")

    return {
        "capture_sha256": capture_sha, "cell_id": cell["id"], "capture_status": status,
        "started_at": run["started_utc"], "finished_at": run["finished_utc"], "protocol": PROTOCOL,
        "quiet_host": quiet, "warmup_status": warmup["status"], "attempt_status": attempt["status"],
        "prompt_tokens": attempt.get("prompt_tokens"), "output_tokens": attempt.get("output_tokens"),
        "token_events": attempt.get("events", 0), "ttft_ns": observed["ttft"],
        "first_visible_answer_ns": observed["first_visible_answer"],
        "binary_sha256": run.get("binary_sha256") if warmup["status"] != "not-run" else None,
    }


def ingest_text_latency(store, packet):
    run = read_packet(packet, json.loads(PLAN_PATH.read_bytes()))
    payload = _sql_text(json_text(run))
    try:
        return json.loads(store._query(f"""
            BEGIN;
            INSERT INTO fastest_intake.text_latency_run
            SELECT item.* FROM jsonb_populate_record(NULL::fastest_intake.text_latency_run, {payload}::jsonb) AS item
            ON CONFLICT (capture_sha256) DO NOTHING;
            SELECT json_build_object(
                'capture_sha256', capture_sha256, 'capture_status', capture_status, 'cell_id', cell_id,
                'review_status', 'held', 'warmup_status', warmup_status, 'attempt_status', attempt_status,
                'eligible_samples', CASE WHEN capture_status = 'complete' AND quiet_host
                    THEN num_nonnulls(ttft_ns, first_visible_answer_ns) ELSE 0 END
            ) FROM fastest_intake.text_latency_run WHERE capture_sha256 = '{run["capture_sha256"]}';
            COMMIT;
        """))
    except (ReleaseError, OSError, TimeoutExpired):
        raise ValueError("Could not store text latency capture. Check the intake migration and permissions.") from None
