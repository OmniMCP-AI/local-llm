"""Verify and retain a private fixed-token text pilot capture."""

import json
from pathlib import Path, PurePath
from subprocess import TimeoutExpired

from fastest_pilot_bundle import digest, json_text
from fastest_release import ReleaseError, _sql_text
from fastest_release.validation import plain_text
from fastest_text.capture import (
    CUDA_MASK, classify_phase, parse_bench_row, parse_runtime_build, phase_argv,
)
from fastest_text.intake import require, require_digest

from .scaling_capture import (
    _check_digest, _directory, _has_receipt, _process, _read_json, _sealed_nonempty, _timestamp,
)


PLAN_PATH = Path(__file__).parents[1] / "fastest_text" / "plan.json"
PHASES = ("prefill", "decode")
FINISHED = ("complete", "incomplete")
UNAVAILABLE = ("blocked", "interrupted")
PHASE_FIELDS = ("outcome", "reason", "placement", "observed_progress", "attempts", "samples_ns")
MISSING_LATENCY = {
    key: {"status": "missing", "sample_count": 0}
    for key in ("ttft", "first_visible_answer")
}


def _runtime(packet, run, plan):
    receipt = None
    bench = None
    build_sha = run.get("build_evidence_sha256")
    binary_sha = run.get("binary_sha256")
    runtime = run.get("runtime_build")
    if build_sha is not None:
        _sealed_nonempty(packet / "build-evidence", build_sha)
    if binary_sha is not None:
        require(build_sha is not None, "Runtime binary requires prior build evidence.")
        require_digest(binary_sha, "binary_sha256")
    directory = _directory(packet / "runtime")
    if directory is not None and _has_receipt(directory):
        require(binary_sha is not None, "Runtime probe has no pinned binary digest.")
        record, receipt, raw, _, _ = _process(directory, "stdout.md")
        argv = record.get("argv")
        require(isinstance(argv, list) and len(argv) == 7 and plain_text(argv[0])
                and argv[1:] == ["-p", "0", "-n", "0", "-o", "md"], "Unexpected runtime probe invocation.")
        bench = argv[0]
        if runtime is not None:
            require(record["outcome"] == "exited" and record["exit_code"] == 0 and "stdout.md" in raw,
                    "Verified runtime lacks a successful build probe.")
            expected = parse_runtime_build(raw["stdout.md"].decode("utf-8"), plan["runtime"]["revision"])
            require(json_text(runtime) == json_text(expected), "Runtime build disagrees with the retained probe.")
    else:
        require(runtime is None, "Missing retained runtime build probe.")
    return receipt, bench


def _classify(record, raw, cell, phase, model, protocol, runtime):
    process = dict(record)
    if record["exit_code"] is not None:
        process["outcome"] = "exited"
    else:
        require(record["outcome"] in ("failed", "timeout", "interrupted", "oom"),
                "Phase outcome requires an observed process exit.")
        if record["outcome"] == "oom":
            process["outcome"] = "failed"
    return classify_phase(
        process, cell, phase, model, protocol, runtime, raw.get("stderr.log", b"").decode("utf-8", "replace"),
        parse_bench_row(raw.get("stdout.jsonl", b"")),
    )


def _phase(packet, name, reference, plan, cell, runtime, bench, capture_sha, capture_status):
    require(isinstance(reference, dict), f"Invalid {name} phase reference.")
    protocol = plan["protocol"]
    row = {"capture_sha256": capture_sha, "phase": name, "outcome": reference.get("outcome")}
    directory = _directory(packet / name)
    if reference == {"outcome": "not-run", "sample_count": 0}:
        require(directory is None or not _has_receipt(directory), f"Unexpected evidence for unstarted {name} phase.")
        return row, [], None
    require(runtime is not None and reference.get("ledger") == f"{name}/attempt.json",
            f"{name} phase requires a verified runtime and its fixed ledger path.")
    if reference.get("outcome") == "running" and "ledger_sha256" not in reference:
        require(reference == {"outcome": "running", "sample_count": 0, "ledger": f"{name}/attempt.json"}
                and (directory is None or not _has_receipt(directory)), f"Inconsistent unfinished {name} phase.")
        return {**row, "outcome": "unavailable"}, [], None
    require(directory is not None, f"Missing retained {name} phase ledger.")
    record, receipt, raw, _, finished = _process(directory, "stdout.jsonl")
    _check_digest(directory / "attempt.json", reference.get("ledger_sha256"), receipt)
    phase = protocol["phases"][name]
    argv = record.get("argv")
    require(isinstance(argv, list) and len(argv) > 3 and plain_text(argv[2]), f"Invalid {name} invocation.")
    model = argv[2]
    require(PurePath(model).name == plan["artifact"]["shards"][0]["path"]
            and argv == phase_argv(bench, model, phase, protocol)
            and record.get("phase") == name and record.get("requested_context_tokens") == phase["requested_context_tokens"],
            f"{name} invocation does not match the pinned protocol.")
    if not {"placement", "observed_progress", "attempts", "samples_ns"} & record.keys():
        expected = {"outcome": record["outcome"], "sample_count": 0, "observed_attempt_count": 0,
                    "ledger": f"{name}/attempt.json", "ledger_sha256": receipt}
        require(capture_status in UNAVAILABLE
                and record["outcome"] in ("running", "exited", "failed", "timeout", "interrupted")
                and json_text(reference) == json_text(expected), f"Inconsistent unfinished {name} phase.")
        return {**row, "outcome": "unavailable", "receipt_sha256": receipt, "files": record.get("files", {})}, [], model

    derived = _classify(record, raw, cell, phase, model, protocol, runtime)
    require(finished is not None and all(json_text(record.get(key)) == json_text(derived[key]) for key in PHASE_FIELDS),
            f"{name} outcome, placement, or timings disagree with retained runner output.")
    expected = {"outcome": derived["outcome"], "sample_count": len(derived["samples_ns"]),
                "observed_attempt_count": len(derived["attempts"]), "ledger": f"{name}/attempt.json",
                "ledger_sha256": receipt}
    require(json_text(reference) == json_text(expected), f"{name} phase summary disagrees with the retained ledger.")
    return {
        **row, "receipt_sha256": receipt, "placement": derived["placement"], "files": record["files"],
    }, _attempt_rows(capture_sha, name, derived), model


def _attempt_rows(capture_sha, phase, derived):
    return [
        {"capture_sha256": capture_sha, "phase": phase, "attempt_number": attempt["number"],
         "outcome": attempt["outcome"], "elapsed_ns": attempt.get("elapsed_ns")}
        for attempt in derived["attempts"]
    ]


def _packet(packet, plan):
    capture, capture_sha = _read_json(packet / "capture.json")
    require(isinstance(capture, dict) and type(capture.get("schema_version")) is int
            and capture["schema_version"] == 1 and capture.get("kind") == "private-capture",
            "Expected a version 1 private fixed-token capture.")
    status = capture.get("status")
    require(status in (*FINISHED, *UNAVAILABLE), "Text capture must have a finalized status.")
    require(_timestamp(capture.get("started_utc")) <= _timestamp(capture.get("finished_utc")),
            "Capture finish precedes its start.")
    require(all(json_text(capture.get(key)) == json_text(plan[key]) for key in ("artifact", "runtime", "protocol")),
            "Capture does not match the pinned text artifact, runtime or protocol.")
    cell = next((cell for cell in plan["cells"] if cell["id"] == capture.get("cell_id")), None)
    require(cell is not None and type(capture.get("quiet_host_operator_attested")) is bool
            and plain_text(capture.get("platform")), "Capture must identify a planned machine and host attestation.")
    require(capture.get("quality") == {"status": "unreviewed", "rubric_id": plan["rubric"]["id"]}
            and "rights" not in capture, "Fixed-token capture requires a private, unreviewed packet.")
    metrics = capture.get("metrics")
    require(isinstance(metrics, dict) and metrics.keys() == MISSING_LATENCY.keys()
            and all(isinstance(row, dict) and row.get("status") == "missing"
                    and type(row.get("sample_count")) is int and row["sample_count"] == 0
                    and row.get("value") is None for row in metrics.values()),
            "The fixed-token protocol has no client latency samples.")
    verified = capture.get("verified_shards")
    shards = plan["artifact"]["shards"]
    require(isinstance(verified, list) and json_text(verified) == json_text(shards[:len(verified)]),
            "Verified artifacts disagree with the pinned shard digests.")
    runtime_receipt, bench = _runtime(packet, capture, plan)
    runtime = capture.get("runtime_build")
    require(not verified or runtime is not None, "Shard verification requires a verified runtime.")
    references = capture.get("phases")
    require(isinstance(references, dict) and references.keys() == set(PHASES)
            and all(isinstance(ref, dict) for ref in references.values()), "Capture must account for both pinned phases.")
    environment = capture.get("environment")
    require(isinstance(environment, dict), "Capture is missing its private environment metadata.")
    if any(ref.get("outcome") != "not-run" for ref in references.values()):
        require(verified == shards and plain_text(capture.get("host_revision")),
                "Started phases require an identified host and both verified shards.")
        if cell["backend"] == "CUDA":
            mask = environment.get("CUDA_VISIBLE_DEVICES")
            require(isinstance(mask, str) and CUDA_MASK.fullmatch(mask), "CUDA capture requires a single-device mask.")

    phases, attempts, models = [], [], set()
    for name in PHASES:
        phase, observed, model = _phase(packet, name, references[name], plan, cell, runtime, bench, capture_sha, status)
        phases.append(phase)
        attempts.extend(observed)
        if model is not None:
            models.add(model)
    outcomes = [phase["outcome"] for phase in phases]
    require(len(models) <= 1 and (outcomes[1] == "not-run" or outcomes[0] not in ("not-run", "unavailable")),
            "Text phases must use the same verified artifact and run in order.")
    if status in FINISHED:
        require(not {"not-run", "unavailable", "interrupted"} & set(outcomes)
                and (status == "complete") == all(outcome == "complete" for outcome in outcomes),
                "Capture completion disagrees with the verified phase outcomes.")
    evidence = {"runtime": runtime_receipt, "phases": {row["phase"]: row.get("receipt_sha256") for row in phases}}
    run = {
        "capture_sha256": capture_sha, "evidence_sha256": digest(json_text(evidence)), "capture_status": status,
        "review_status": "held", "packet_kind": "fixed-token-v1", "cell_id": cell["id"],
        "started_at": capture["started_utc"], "finished_at": capture["finished_utc"],
        "metadata": {
            **{key: capture.get(key) for key in ("platform", "quiet_host_operator_attested", "runtime", "artifact",
                                                "protocol", "verified_shards", "binary_sha256",
                                                "build_evidence_sha256", "runtime_build", "quality")},
            "latency": MISSING_LATENCY,
            "backend": cell["backend"], "runtime_receipt_sha256": runtime_receipt,
            "host_revision": capture["host_revision"] if plain_text(capture.get("host_revision")) else None,
        },
    }
    return run, phases, attempts


def ingest_text_capture(store, packet, *, ambient_m4=False):
    require(_directory(packet) is not None, "Expected a private text capture directory.")
    plan = json.loads(PLAN_PATH.read_bytes())
    if ambient_m4:
        from .text_ambient_m4 import read_ambient_m4_packet

        run, phases, attempts = read_ambient_m4_packet(packet, plan)
    else:
        run, phases, attempts = _packet(packet, plan)
    payload = _sql_text(json_text({"run": run, "phases": phases, "attempts": attempts}))
    try:
        return json.loads(store._query(f"""
            BEGIN;
            CREATE TEMP TABLE text_capture_payload (document jsonb NOT NULL) ON COMMIT DROP;
            INSERT INTO text_capture_payload VALUES ({payload}::jsonb);
            INSERT INTO fastest_intake.text_capture_run
            SELECT item.* FROM text_capture_payload,
                jsonb_populate_record(NULL::fastest_intake.text_capture_run, document->'run') AS item
            ON CONFLICT (capture_sha256) DO NOTHING;
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT FROM fastest_intake.text_capture_run AS run, text_capture_payload
                    WHERE run.capture_sha256 = document #>> '{{run,capture_sha256}}'
                      AND run.evidence_sha256 = document #>> '{{run,evidence_sha256}}'
                ) THEN
                    RAISE EXCEPTION 'Text capture evidence differs from its previous import.';
                END IF;
            END $$;
            INSERT INTO fastest_intake.text_capture_phase
            SELECT item.* FROM text_capture_payload,
                jsonb_populate_recordset(NULL::fastest_intake.text_capture_phase, document->'phases') AS item
            ON CONFLICT (capture_sha256, phase) DO NOTHING;
            INSERT INTO fastest_intake.text_capture_attempt
            SELECT item.* FROM text_capture_payload,
                jsonb_populate_recordset(NULL::fastest_intake.text_capture_attempt, document->'attempts') AS item
            ON CONFLICT (capture_sha256, phase, attempt_number) DO NOTHING;
            SELECT json_build_object(
                'capture_sha256', run.capture_sha256, 'evidence_sha256', run.evidence_sha256,
                'capture_status', run.capture_status,
                'review_status', run.review_status, 'packet_kind', run.packet_kind, 'cell_id', run.cell_id,
                'observed_attempts', count(attempt.attempt_number),
                'timing_samples', count(attempt.elapsed_ns)
            ) FROM text_capture_payload
            JOIN fastest_intake.text_capture_run AS run ON run.capture_sha256 = document #>> '{{run,capture_sha256}}'
            LEFT JOIN fastest_intake.text_capture_attempt AS attempt USING (capture_sha256)
            GROUP BY run.capture_sha256;
            COMMIT;
        """))
    except (ReleaseError, OSError, TimeoutExpired):
        raise ValueError("Could not store text capture. Check the intake migration, permissions, and any prior "
                         "import for conflicting evidence.") from None
