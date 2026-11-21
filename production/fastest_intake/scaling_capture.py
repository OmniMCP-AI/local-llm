"""Verify and retain a private single-to-multi-GPU capture for review."""

from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import PurePosixPath, PureWindowsPath
from subprocess import TimeoutExpired
from uuid import UUID

from fastest_pilot_bundle import digest, json_text
from fastest_pilot_capture import sha256_file
from fastest_release import ReleaseError, _sql_text
from fastest_release.capture_scaling import (
    ENVIRONMENT, INVENTORY, decode_argv, decode_result, decode_samples, inventory_devices, placement,
    validate_selected_devices,
)
from fastest_release.scaling import LOAD, PLAN, transport_matches_devices
from fastest_release.validation import keys, plain_text
from fastest_text.intake import require, require_digest


ROLES = ("baseline", "comparison")
FINISHED = ("complete", "incomplete")
TERMINAL = (*FINISHED, "failed", "interrupted")
PROTOCOL = {
    **PLAN["protocol"], "load": LOAD, "phases": {"decode": PLAN["protocol"]["phases"]["decode"]},
}


def _unique_fields(pairs):
    record = dict(pairs)
    require(len(record) == len(pairs), "Capture JSON has duplicate object fields.")
    return record


def _invalid_constant(value):
    raise ValueError(f"Invalid JSON constant {value}.")


def _decode_json(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_fields, parse_constant=_invalid_constant)


def _regular_file(path):
    require(not path.is_symlink() and path.is_file(), f"Missing or invalid evidence file: {path.name}.")
    return path


def _read_json(path):
    data = _regular_file(path).read_bytes()
    try:
        return _decode_json(data), sha256(data).hexdigest()
    except (ValueError, RecursionError) as error:
        raise ValueError(f"Malformed capture JSON: {path.name}.") from error


def _directory(path):
    require(not path.is_symlink(), f"Evidence directory cannot be a symlink: {path.name}.")
    if path.exists():
        require(path.is_dir(), f"Invalid evidence directory: {path.name}.")
        return path
    return None


def _has_receipt(directory):
    path = directory / "attempt.json"
    return path.exists() or path.is_symlink()


def _check_digest(path, expected, actual):
    require_digest(expected, path.name)
    require(expected == actual, f"SHA-256 mismatch: {path.parent.name}/{path.name}.")


def _sealed_nonempty(path, expected):
    actual = sha256_file(_regular_file(path))
    require(actual != sha256(b"").hexdigest(), f"Evidence file must be nonempty: {path.name}.")
    _check_digest(path, expected, actual)
    return actual


def _timestamp(value):
    require(isinstance(value, str) and "T" in value, "Expected an ISO timestamp in the process receipt.")
    stamp = datetime.fromisoformat(value)
    require(stamp.utcoffset() == timedelta(0), "Process receipt timestamps must be UTC.")
    return stamp


def _run_id(value):
    require(isinstance(value, str) and str(UUID(value)) == value, "Expected a canonical run UUID.")
    return value


def _process(directory, stdout_name):
    record, receipt_sha = _read_json(directory / "attempt.json")
    require(isinstance(record, dict), "Process receipt must be an object.")
    require(plain_text(record.get("outcome")) and "exit_code" in record, "Missing process outcome or exit code.")
    started = _timestamp(record.get("started_utc"))
    finished = None
    files = record.get("files", {})
    expected_files = {stdout_name, "stderr.log"}
    require(isinstance(files, dict) and files.keys() <= expected_files, "Invalid process output file list.")
    outcome, code = record["outcome"], record["exit_code"]
    if outcome == "running":
        require("finished_utc" not in record and code is None and not files, "Invalid running process receipt.")
    else:
        finished = _timestamp(record.get("finished_utc"))
        require(started <= finished, "Process finish precedes its start.")
        if code is not None or outcome in ("timeout", "interrupted"):
            require(files.keys() == expected_files, "Finalized process receipt must seal both output files.")
    require(code is None or type(code) is int and -(2**31) <= code < 2**31, "Invalid process exit code.")
    timeout = record.get("timeout_seconds")
    require(type(timeout) is int and timeout > 0, "Invalid process timeout.")
    raw = {}
    for name, expected in files.items():
        path = directory / name
        data = _regular_file(path).read_bytes()
        _check_digest(path, expected, sha256(data).hexdigest())
        raw[name] = data
    return record, receipt_sha, raw, started, finished


def _inventory(packet, capture, selected):
    directory = _directory(packet / "inventory")
    if directory is None or not _has_receipt(directory):
        require("os_driver" not in capture, "Capture is missing its sealed GPU inventory.")
        return selected, None, None
    record, receipt_sha, raw, _, finished = _process(directory, "stdout.csv")
    require(record.get("argv") == INVENTORY and record["timeout_seconds"] == 30, "Invalid GPU inventory invocation.")
    outcome, code = record["outcome"], record.get("exit_code")
    require(outcome in ("running", "exited", "failed", "timeout", "interrupted")
            and (outcome == "exited") == (code is not None), "Invalid GPU inventory outcome.")
    if "os_driver" in capture:
        require(outcome == "exited" and code == 0, "Capture is missing a successful GPU inventory.")
        selected = inventory_devices(raw["stdout.csv"].decode("utf-8"), selected)
        require(capture["os_driver"] == f"{capture['platform']} · NVIDIA {selected[0]['driver']}",
                "GPU inventory driver disagrees with capture.json.")
    evidence = {"receipt_sha256": receipt_sha, "files": record.get("files", {}), "outcome": outcome,
                "exit_code": code}
    return selected, evidence, finished


def _attempt(directory, role, devices, reference, boundary):
    record, receipt_sha, raw, started, finished = _process(directory, "stdout.jsonl")
    require(boundary is not None and started >= boundary, "Capture attempts must follow the inventory in sequence.")
    run_id = _run_id(record.get("run_id"))
    require(record.get("devices") == devices and record.get("role") == role
            and record.get("primary_device") == devices[0]["id"], f"{role} device placement disagrees with inventory.")
    split = "/".join(["1"] * len(devices))
    require(record.get("tensor_split") == split
            and record.get("strategy") == ("single-device" if role == "baseline" else "layer"),
            f"{role} must use the pinned layer split.")
    argv = record.get("argv")
    require(isinstance(argv, list) and len(argv) >= 3 and all(isinstance(arg, str) and "\x00" not in arg for arg in argv),
            f"Invalid {role} benchmark invocation.")
    bench, model = argv[0], argv[2]
    valid_paths = any(path(bench).is_absolute() and path(model).is_absolute()
                      and path(model).name == PLAN["artifact"]["shards"][0]["path"]
                      for path in (PurePosixPath, PureWindowsPath))
    require(valid_paths and "," not in model
            and argv == decode_argv(bench, model, PROTOCOL, split), f"{role} did not run the pinned decode invocation.")
    environment = record.get("environment")
    keys(environment, " ".join(ENVIRONMENT), "process environment")
    require(all(value is None or isinstance(value, str) and "\x00" not in value for value in environment.values())
            and environment["CUDA_VISIBLE_DEVICES"] == ",".join(gpu["uuid"] for gpu in devices)
            and environment["CUDA_DEVICE_ORDER"] == "PCI_BUS_ID", f"{role} CUDA environment disagrees with inventory.")

    stderr = raw.get("stderr.log", b"").decode("utf-8", errors="replace")
    recorded_placement = placement(stderr)
    try:
        runner_row = _decode_json(raw.get("stdout.jsonl", b""))
    except (ValueError, RecursionError):
        runner_row = None
    sample_error, samples = decode_samples(runner_row, record, PROTOCOL, model)
    outcome, code = record["outcome"], record.get("exit_code")
    if code is not None:
        actual, _, claimed_samples = decode_result({**record, "placement_mib": recorded_placement},
                                                   stderr, sample_error, samples)
        if outcome == "exited":
            require(reference is None, f"Capture references an unclassified {role} attempt.")
        else:
            claim = record.get("samples_ns")
            require(outcome == actual and isinstance(claim, list) and all(type(ns) is int for ns in claim)
                    and claim == claimed_samples and record.get("placement_mib") == recorded_placement,
                    f"{role} outcome, placement or timings disagree with runner output.")
    else:
        require(outcome in ("failed", "timeout", "interrupted", "running") and "samples_ns" not in record,
                f"{role} outcome disagrees with its process receipt.")
        if "placement_mib" in record:
            require(record["placement_mib"] == recorded_placement, f"{role} placement disagrees with runner output.")

    if reference is not None:
        require(reference == {"run_id": run_id, "outcome": outcome, "ledger": f"{role}/attempt.json"}
                and outcome in ("complete", "invalid-output", "oom", "failed", "timeout"),
                f"{role} outcome disagrees with capture.json.")
    if outcome == "exited" or outcome == "running" or (outcome == "complete" and reference is None):
        outcome = "unavailable"
    row = {
        "run_id": run_id, "role": role, "receipt_sha256": receipt_sha, "outcome": outcome,
        "started_at": started.isoformat(), "finished_at": finished.isoformat() if finished else None,
        "exit_code": code, "timeout_seconds": record["timeout_seconds"], "samples_ns": samples,
        "metadata": {"devices": devices, "tensor_split": split, "strategy": record["strategy"],
                     "placement_mib": recorded_placement, "files": record.get("files", {}),
                     "collector_outcome": record["outcome"]},
    }
    controls = bench, model, record["timeout_seconds"], {key: environment[key] for key in ENVIRONMENT[1:]}
    return row, controls, finished


def _transport(packet, status, attempts):
    directory = _directory(packet / "transport")
    if directory is None:
        return None
    require(status in FINISHED and "comparison" in attempts, "Transport requires a finished comparison attempt.")
    comparison = attempts["comparison"]
    receipt, receipt_sha = _read_json(directory / "receipt.json")
    keys(receipt, "status run_id attached_utc trace_filename files", "transport receipt")
    require(receipt["status"] == "supplied" and receipt["run_id"] == comparison["run_id"]
            and plain_text(receipt["trace_filename"]), "Transport receipt must be sealed for the captured comparison.")
    attached = _timestamp(receipt["attached_utc"])
    require(attached >= _timestamp(comparison["finished_at"]), "Transport receipt predates its comparison.")
    keys(receipt["files"], "trace links.json", "transport file digests")
    links_path = directory / "links.json"
    summary, links_sha = _read_json(links_path)
    _check_digest(links_path, receipt["files"]["links.json"], links_sha)
    keys(summary, "run_id links", "transport summary")
    require(summary["run_id"] == comparison["run_id"]
            and transport_matches_devices(summary["links"], [gpu["id"] for gpu in comparison["metadata"]["devices"]]),
            "Transport links must connect the captured comparison GPUs.")
    trace_sha = _sealed_nonempty(directory / "trace", receipt["files"]["trace"])
    return {"comparison_run_id": comparison["run_id"], "receipt_sha256": receipt_sha,
            "trace_sha256": trace_sha, "links_sha256": links_sha, "links": summary["links"],
            "attached_at": attached.isoformat()}


def _packet(packet):
    require(_directory(packet) is not None, "Expected a private scaling capture directory.")
    capture, capture_sha = _read_json(packet / "capture.json")
    require(isinstance(capture, dict) and type(capture.get("schema_version")) is int
            and capture["schema_version"] == 1 and capture.get("kind") == "private-capture",
            "Expected a version 1 private scaling capture.")
    status = capture.get("status")
    require(status in TERMINAL, "Capture must be finalized as complete, incomplete, failed or interrupted.")
    require(all(plain_text(capture.get(name)) for name in ("host_revision", "platform")),
            "Capture must identify its host revision and platform.")
    require_digest(capture.get("binary_sha256"), "binary_sha256")
    _sealed_nonempty(packet / "build-evidence", capture.get("build_evidence_sha256"))
    require(all(json_text(capture.get(key)) == json_text(value) for key, value in
                (("artifact", PLAN["artifact"]), ("runtime", PLAN["runtime"]), ("protocol", PROTOCOL))),
            "Capture does not match the pinned scaling artifact, runtime or protocol.")
    transport = capture.get("transport")
    keys(transport, "status reason attachment", "capture transport")
    require(capture.get("quality") == {"status": "unreviewed", "protocol": PLAN["rubric"]["id"]}
            and transport["status"] == "unknown" and plain_text(transport["reason"])
            and transport["attachment"] == "transport/receipt.json",
            "Collector manifest must report pending quality and unknown transport.")
    selected = validate_selected_devices(capture.get("selected_devices"))
    devices, inventory, boundary = _inventory(packet, capture, selected)

    references = capture.get("attempts")
    require(isinstance(references, dict) and set(references) == set(ROLES[:len(references)])
            and (status not in FINISHED or len(references) == len(ROLES)), "Invalid capture attempt list.")
    require(all(isinstance(reference, dict) for reference in references.values()), "Invalid capture attempt reference.")
    attempts, previous = {}, None
    for role in ROLES:
        directory = _directory(packet / role)
        if directory is None or not _has_receipt(directory):
            require(role not in references, f"Missing referenced {role} attempt.")
            continue
        require("os_driver" in capture and (role == "baseline" or "baseline" in references),
                f"Missing verified inventory or preceding attempt for {role}.")
        row, controls, boundary = _attempt(directory, role, devices[:1] if role == "baseline" else devices,
                                           references.get(role), boundary)
        require(previous is None or controls == previous, "Matched attempts must keep the same runtime controls.")
        attempts[role] = {**row, "capture_sha256": capture_sha}
        previous = controls
    if status in FINISHED:
        require((status == "complete") == all(row["outcome"] == "complete" for row in attempts.values()),
                "Capture status disagrees with its verified attempt outcomes.")
    require(len({row["run_id"] for row in attempts.values()}) == len(attempts), "Capture run IDs must be distinct.")

    evidence = {"inventory": inventory, "attempts": {role: row["receipt_sha256"] for role, row in attempts.items()}}
    run = {
        "capture_sha256": capture_sha, "evidence_sha256": digest(json_text(evidence)), "capture_status": status,
        "review_status": "held", "metadata": {
            **{key: capture[key] for key in ("host_revision", "platform", "binary_sha256", "build_evidence_sha256",
                                             "protocol", "artifact", "runtime", "quality")},
            "devices": devices, "inventory": inventory, "os_driver": capture.get("os_driver"),
        },
    }
    attachment = _transport(packet, status, attempts)
    return run, list(attempts.values()), attachment


def ingest_scaling_capture(store, packet):
    run, attempts, transport = _packet(packet)
    payload = _sql_text(json_text({"run": run, "attempts": attempts, "transport": transport}))
    try:
        return json.loads(store._query(f"""
            BEGIN;
            CREATE TEMP TABLE scaling_capture_payload (document jsonb NOT NULL) ON COMMIT DROP;
            INSERT INTO scaling_capture_payload VALUES ({payload}::jsonb);
            INSERT INTO fastest_intake.scaling_capture_run
            SELECT item.* FROM scaling_capture_payload,
                jsonb_populate_record(NULL::fastest_intake.scaling_capture_run, document->'run') AS item
            ON CONFLICT (capture_sha256) DO NOTHING;
            INSERT INTO fastest_intake.scaling_capture_attempt
            SELECT item.* FROM scaling_capture_payload,
                jsonb_populate_recordset(NULL::fastest_intake.scaling_capture_attempt, document->'attempts') AS item
            ON CONFLICT (capture_sha256, role) DO NOTHING;
            INSERT INTO fastest_intake.scaling_capture_transport
            SELECT item.* FROM scaling_capture_payload,
                jsonb_populate_record(NULL::fastest_intake.scaling_capture_transport,
                    nullif(document->'transport', 'null'::jsonb)) AS item
            WHERE document->'transport' <> 'null'::jsonb
            ON CONFLICT (comparison_run_id) DO NOTHING;
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT FROM fastest_intake.scaling_capture_run AS run, scaling_capture_payload
                    WHERE run.capture_sha256 = document #>> '{{run,capture_sha256}}'
                      AND run.evidence_sha256 = document #>> '{{run,evidence_sha256}}'
                ) OR EXISTS (
                    SELECT FROM scaling_capture_payload
                    JOIN fastest_intake.scaling_capture_transport AS transport
                      ON transport.comparison_run_id = (document #>> '{{transport,comparison_run_id}}')::uuid
                    WHERE transport.receipt_sha256 <> document #>> '{{transport,receipt_sha256}}'
                ) THEN
                    RAISE EXCEPTION 'Scaling capture evidence differs from its previous import.';
                END IF;
            END $$;
            SELECT json_build_object(
                'capture_sha256', run.capture_sha256, 'capture_status', run.capture_status,
                'review_status', run.review_status,
                'transport_status', CASE WHEN transport.receipt_sha256 IS NULL THEN 'unknown' ELSE 'supplied' END,
                'transport_receipt_sha256', transport.receipt_sha256
            ) FROM scaling_capture_payload
            JOIN fastest_intake.scaling_capture_run AS run ON run.capture_sha256 = document #>> '{{run,capture_sha256}}'
            LEFT JOIN fastest_intake.scaling_capture_attempt AS cmp
                ON cmp.capture_sha256 = run.capture_sha256 AND cmp.role = 'comparison'
            LEFT JOIN fastest_intake.scaling_capture_transport AS transport ON transport.comparison_run_id = cmp.run_id;
            COMMIT;
        """))
    except (ReleaseError, OSError, TimeoutExpired):
        raise ValueError("Could not store scaling capture. Check the intake migration, permissions, and any prior "
                         "import for conflicting evidence.") from None
