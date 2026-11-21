"""Capture the pinned text pilot on one operator-controlled machine."""

from decimal import Decimal
import json
import os
import platform
import re
import shutil

from fastest_pilot_capture import BENCH_SETTING_FLAGS, record_process, save_json, sha256_file, utc_now
from fastest_release.validation import plain_text
from fastest_text.intake import json_settings_match


CUDA_MASK = re.compile(r"(?:[0-9]+|GPU-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", re.IGNORECASE)
BUILD_FOOTER = re.compile(r"^build: ([0-9a-f]{7,40}) \((\d+)\)$", re.MULTILINE)
DEVICE = re.compile(r"\busing device (\S+) \(([^)]+)\) - \d+ MiB free")
BUFFER = re.compile(r"\b(\S+)\s+(model|KV|compute) buffer size =\s+([0-9]+\.[0-9]+) MiB")
LAYERS = re.compile(r"\boffloaded (\d+)/(\d+) layers to GPU")
CONTEXT = re.compile(r"\bn_ctx\s+= (\d+)")
OOM = re.compile(r"\bout of memory\b|\bCUDA_ERROR_OUT_OF_MEMORY\b|\bstd::bad_alloc\b", re.IGNORECASE)
RUNNER_ERROR = re.compile(
    r"failed to decode|decode failed|failed to find KV cache slot|CUDA error:|failed to allocate",
    re.IGNORECASE,
)
PLACEMENTS = {
    "apple-m4": ("Metal", ("Apple M4",), {"Metal", "Metal_Mapped"}),
    "rtx-4090": ("CUDA0", ("NVIDIA GeForce RTX 4090", "GeForce RTX 4090"), {"CUDA0"}),
}


def private_environment(env):
    return {
        key: value for key, value in env.items()
        if key.startswith(("CUDA_", "GGML_", "LD_", "DYLD_")) or key == "LC_ALL"
    }


def pinned_commit(reported, revision):
    return (
        isinstance(reported, str) and re.fullmatch(r"[0-9a-f]{7,40}", reported) is not None
        and revision.startswith(reported)
    )


def verify_runtime(output, bench, revision, env):
    path = output / "runtime"
    process = {"argv": [str(bench), "-p", "0", "-n", "0", "-o", "md"]}
    record_process(path, process, "stdout.md", 30, env)
    if process["exit_code"] != 0:
        raise ValueError("Runner build probe failed. See runtime/attempt.json.")
    return parse_runtime_build((path / "stdout.md").read_text(encoding="utf-8"), revision)


def parse_runtime_build(stdout, revision):
    builds = BUILD_FOOTER.findall(stdout)
    if len(builds) != 1 or not pinned_commit(builds[0][0], revision):
        raise ValueError("Runner build probe does not match the pinned b5163 revision.")
    commit, number = builds[0]
    return {"commit_reported": commit, "number_reported": int(number)}


def verify_shards(model_dir, artifact, verified_shards):
    for shard in artifact["shards"]:
        path = model_dir / shard["path"]
        if not path.is_file() or path.stat().st_size != shard["bytes"] or sha256_file(path) != shard["sha256"]:
            raise ValueError(f"GGUF shard differs from the pinned artifact: {path.name}")
        verified_shards.append(shard)


def effective_placement(stderr, backends):
    buffers = {}
    for device, kind, mib in BUFFER.findall(stderr):
        if Decimal(mib) > 0:
            buffers.setdefault(device, {}).setdefault(kind.lower(), []).append(mib)
    return {
        "registered_backends": backends,
        "devices": dict(DEVICE.findall(stderr)),
        "buffers_mib": buffers,
        "offloaded_layers": [[int(actual), int(total)] for actual, total in LAYERS.findall(stderr)],
        "context_tokens": [int(tokens) for tokens in CONTEXT.findall(stderr)],
    }


def device_placement_matches(cell, context_tokens, placement):
    device, gpu_names, gpu_buffers = PLACEMENTS[cell["id"]]
    devices = placement["devices"]
    buffers = placement["buffers_mib"]
    layers = placement["offloaded_layers"]
    return (
        set(devices) == {device} and devices[device] in gpu_names
        and any("model" in buffers.get(name, {}) for name in gpu_buffers)
        and {name for name, kinds in buffers.items() if "kv" in kinds} == {device}
        and len(layers) == 1 and layers[0][0] == layers[0][1] > 0
        and context_tokens in placement["context_tokens"]
    )


def placement_matches(cell, phase, placement, gpu_info):
    device = PLACEMENTS[cell["id"]][0]
    return (
        cell["backend"] in placement["registered_backends"]
        and gpu_info == placement["devices"].get(device)
        and device_placement_matches(cell, phase["requested_context_tokens"], placement)
    )


def phase_progress(stderr, phase, total):
    stage = "prompt" if phase["input_tokens"] else "generation"
    progress = re.compile(rf"llama-bench: benchmark 1/1: {stage} run (\d+)/{total}")
    started, errors = [], {}
    current = None
    for line in stderr.splitlines():
        timed = progress.fullmatch(line)
        if timed:
            current = int(timed[1])
            started.append(current)
        elif "llama_perf_context_print:" in line:
            current = None
        elif OOM.search(line):
            errors[current] = "oom"
        elif RUNNER_ERROR.search(line):
            errors.setdefault(current, "failed")
    return started, errors


def parse_bench_row(stdout):
    try:
        row = json.loads(stdout.decode("utf-8"))
    except (ValueError, RecursionError):
        return {}
    return row if isinstance(row, dict) else {}


def classify_phase(record, cell, phase, model, protocol, runtime, stderr, row):
    backends = row.get("backends")
    placement = effective_placement(stderr, backends.split(",") if isinstance(backends, str) else [])
    total = protocol["warm_samples_per_phase"]
    started, errors = phase_progress(stderr, phase, total)
    ordinals = sorted({number for number in started if 1 <= number <= total})
    ordered = started == list(range(1, total + 1))
    samples = row.get("samples_ns")
    expected = {
        **protocol["settings"],
        "model_filename": str(model), "n_prompt": phase["input_tokens"], "n_gen": phase["output_tokens"],
        "tensor_split": "0.00", "build_commit": runtime["commit_reported"], "build_number": runtime["number_reported"],
    }

    outcome = record["outcome"]
    verified = False
    if "oom" in errors.values():
        outcome, reason = "oom", "Runner reported out of memory. See stderr.log."
    elif outcome != "exited":
        reason = record.get("reason", "Runner did not finish. See stderr.log.")
    elif record["exit_code"] != 0 or None in errors:
        outcome, reason = "failed", "Runner exited unsuccessfully or logged an unscoped runtime error. See stderr.log."
    elif not json_settings_match({field: row.get(field) for field in expected}, expected):
        outcome, reason = "invalid-output", "Runner JSONL does not match the verified build and pinned invocation."
    elif not placement_matches(cell, phase, placement, row.get("gpu_info")):
        outcome, reason = "invalid-output", "Runner device, model and KV placement, or context differs from the planned cell."
    elif (not ordered or not isinstance(samples, list) or len(samples) != total
          or not all(type(value) is int and 0 < value < 2**63 for value in samples)):
        outcome, reason = "incomplete", "Runner output lacks the full, ordered set of expected timed samples."
    else:
        verified = True
        outcome, reason = ("partial", "A timed repetition logged a runtime error. See stderr.log.") if errors else (
            "complete", None
        )

    attempts = []
    for number in ordinals:
        attempt = {"number": number}
        if number in errors:
            attempt.update(outcome=errors[number], reason="Runner logged an error during this repetition. See stderr.log.")
        elif verified:
            attempt.update(outcome="success", elapsed_ns=samples[number - 1])
        elif outcome in ("timeout", "interrupted") and started == ordinals and number == ordinals[-1]:
            attempt.update(outcome=outcome, reason="Capture ended after entering this repetition. Completion was unobserved.")
        else:
            attempt.update(outcome="unmeasured", reason=reason)
        attempts.append(attempt)
    return {
        "outcome": outcome, "reason": reason, "placement": placement, "observed_progress": started,
        "attempts": attempts,
        "samples_ns": [attempt["elapsed_ns"] for attempt in attempts if attempt["outcome"] == "success"],
    }


def finish_phase(directory, record, cell, phase, model, protocol, runtime):
    stderr_file = directory / "stderr.log"
    stderr = stderr_file.read_text(encoding="utf-8", errors="replace") if stderr_file.is_file() else ""
    try:
        row = parse_bench_row((directory / "stdout.jsonl").read_bytes())
    except FileNotFoundError:
        row = {}
    record.update(classify_phase(record, cell, phase, model, protocol, runtime, stderr, row))
    save_json(directory / "attempt.json", record)


def phase_argv(bench, model, phase, protocol):
    argv = [str(bench), "-m", str(model), "-p", str(phase["input_tokens"]), "-n", str(phase["output_tokens"])]
    for setting, flag in BENCH_SETTING_FLAGS.items():
        value = protocol["settings"][setting]
        argv.extend((flag, str(int(value) if type(value) is bool else value)))
    argv.extend(("-r", str(protocol["warm_samples_per_phase"]), "--progress", "-v", "-o", "jsonl"))
    return argv


def capture_phase(output, key, cell, model, bench, protocol, runtime, env, timeout):
    phase = protocol["phases"][key]
    argv = phase_argv(bench, model, phase, protocol)
    directory = output / key
    record = {"phase": key, "argv": argv, "requested_context_tokens": phase["requested_context_tokens"]}
    try:
        record_process(directory, record, "stdout.jsonl", timeout, env)
    finally:
        if "outcome" in record:
            finish_phase(directory, record, cell, phase, model, protocol, runtime)
    return record


def capture(args, plan, missing_latency):
    cell = next(cell for cell in plan["cells"] if cell["id"] == args.cell)
    env = {**os.environ, "LC_ALL": "C"}
    args.output.mkdir(mode=0o700)
    path = args.output / "capture.json"
    ledger = {
        "schema_version": 1, "kind": "private-capture", "status": "starting",
        "cell_id": cell["id"], "host_revision": args.host_revision, "platform": platform.platform(),
        "quiet_host_operator_attested": args.quiet_host, "environment": private_environment(env),
        "runtime": plan["runtime"], "artifact": plan["artifact"], "verified_shards": [],
        "protocol": plan["protocol"], "quality": {"status": "unreviewed", "rubric_id": plan["rubric"]["id"]},
        "metrics": missing_latency, "started_utc": utc_now(),
        "phases": {key: {"outcome": "not-run", "sample_count": 0} for key in plan["protocol"]["phases"]},
    }
    save_json(path, ledger)
    try:
        if not plain_text(args.host_revision) or args.timeout < 1:
            raise ValueError("Supply a stable physical host revision and a positive timeout.")
        if args.cell == "rtx-4090" and not CUDA_MASK.fullmatch(env.get("CUDA_VISIBLE_DEVICES", "")):
            raise ValueError("Select one allocated device in CUDA_VISIBLE_DEVICES before capturing the CUDA cell.")
        if not args.build_evidence.is_file() or args.build_evidence.stat().st_size == 0:
            raise ValueError("Supply a nonempty local runtime build evidence file.")
        build_path = args.output / "build-evidence"
        shutil.copyfile(args.build_evidence, build_path)
        ledger["build_evidence_sha256"] = sha256_file(build_path)
        bench = args.bench.resolve()
        if not bench.is_file() or not os.access(bench, os.X_OK):
            raise ValueError("Supply an executable llama-bench binary.")
        ledger["binary_sha256"] = sha256_file(bench)
        ledger["runtime_build"] = verify_runtime(args.output, bench, plan["runtime"]["revision"], env)
        model_dir = args.model_dir.resolve()
        model = model_dir / plan["artifact"]["shards"][0]["path"]
        if any(character in str(model) for character in ',"\\\n\r'):
            raise ValueError("The pinned llama-bench cannot safely serialize this model path.")
        verify_shards(model_dir, plan["artifact"], ledger["verified_shards"])
        ledger["status"] = "capturing"
        save_json(path, ledger)
        for phase in ("prefill", "decode"):
            ledger["phases"][phase].update(outcome="running", ledger=f"{phase}/attempt.json")
            save_json(path, ledger)
            try:
                capture_phase(args.output, phase, cell, model, bench, plan["protocol"],
                              ledger["runtime_build"], env, args.timeout)
            finally:
                attempt = args.output / phase / "attempt.json"
                if attempt.is_file():
                    record = json.loads(attempt.read_text(encoding="utf-8"))
                    ledger["phases"][phase].update(
                        outcome=record["outcome"], sample_count=len(record.get("samples_ns", [])),
                        observed_attempt_count=len(record.get("attempts", [])), ledger_sha256=sha256_file(attempt),
                    )
                    save_json(path, ledger)
        ledger["status"] = (
            "complete" if all(phase["outcome"] == "complete" for phase in ledger["phases"].values()) else "incomplete"
        )
    except (OSError, ValueError, KeyboardInterrupt) as error:
        ledger.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "blocked",
                      reason=str(error) or type(error).__name__)
        raise
    finally:
        ledger["finished_utc"] = utc_now()
        save_json(path, ledger)
    return ledger["status"] == "complete"
