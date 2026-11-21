"""Import the pinned image pilot's private provenance and attempt ledger."""

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re

from fastest_image.intake import require, validate_attempts
from fastest_release import _sql_text


PLAN = Path(__file__).resolve().parents[1] / "fastest_image" / "plan.json"
FAILURE_REASON = re.compile(
    r"ComfyUI reported [A-Za-z_][A-Za-z0-9_.]{0,79}\."
    r"|ComfyUI interrupted the prompt\."
    r"|Client deadline elapsed\."
    r"|Capture error \([A-Za-z_][A-Za-z0-9_]{0,79}\)\."
)


def checked_json(packet, name, checksums):
    content = (packet / name).read_bytes()
    digest = sha256(content).hexdigest()
    require(checksums.get(name) == digest, f"{name} does not match SHA256SUMS")
    return json.loads(content), digest


def read_packet(packet):
    packet = packet.resolve(strict=True)
    manifest = (packet / "SHA256SUMS").read_bytes()
    checksums = {}
    for line in manifest.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line)
        require(match, "Invalid SHA256SUMS entry")
        digest, name = match.groups()
        require(name not in checksums, "Duplicate SHA256SUMS member")
        checksums[name] = digest
    provenance, provenance_sha256 = checked_json(packet, "provenance.json", checksums)
    attempts, ledger_sha256 = checked_json(packet, "run/attempts.json", checksums)
    plan_bytes = PLAN.read_bytes()
    plan = json.loads(plan_bytes)

    require(isinstance(provenance, dict), "Provenance must be a JSON object")
    start = provenance.get("start_utc")
    require(isinstance(start, str) and datetime.fromisoformat(start).utcoffset() is not None,
            "start_utc must specify a time zone")
    require(provenance.get("workflow_sha256") == plan["workflow"]["sha256"],
            "Provenance workflow does not match the pinned SHA-256")
    require(provenance.get("checkpoint") == plan["artifact"], "Provenance checkpoint does not match the pin")
    require(provenance.get("runtime") == plan["runtime"], "Provenance runtime does not match the pin")
    require(provenance.get("protocol") == plan["protocol"], "Provenance protocol does not match the pin")
    cell = next((cell for cell in plan["cells"] if cell["lock"]["sha256"] == provenance.get("lock_sha256")), None)
    hardware = provenance.get("hardware")
    require(cell and isinstance(hardware, str) and cell["name"] in hardware,
            "Provenance hardware and lock must match a pinned cell")

    require(isinstance(attempts, list), "Attempt ledger must be a JSON array")
    require(all(isinstance(attempt, dict) and attempt.get("review") is None for attempt in attempts),
            "Timing intake requires unreviewed attempts")
    validate_attempts(attempts, plan["protocol"], plan["rubric"])
    manifest_sha256 = sha256(manifest).hexdigest()
    rows = []
    for index, attempt in enumerate(attempts):
        output = attempt.get("output_sha256")
        failure = attempt.get("reason")
        if output is not None:
            require(checksums.get(f"run/sample-{index:02d}.png") == output,
                    "Attempt output digest does not match SHA256SUMS")
        else:
            require(FAILURE_REASON.fullmatch(failure), "Failure reason must be a capture status message")
        rows.append({
            "manifest_sha256": manifest_sha256, "attempt_index": index, "phase": attempt["phase"],
            "seed": attempt["seed"], "outcome": attempt["outcome"], "elapsed_ns": attempt["elapsed_ns"],
            "phase_end_ns": attempt["phase_end_ns"], "output_sha256": output, "failure_reason": failure,
        })

    run = {
        "manifest_sha256": manifest_sha256, "provenance_sha256": provenance_sha256, "ledger_sha256": ledger_sha256,
        "packet_locator": str(packet), "started_at": start, "cell_id": cell["id"],
        "plan_sha256": sha256(plan_bytes).hexdigest(), "protocol_id": plan["protocol"]["id"],
        "workflow_sha256": plan["workflow"]["sha256"], "artifact_sha256": plan["artifact"]["sha256"],
        "artifact_repository": plan["artifact"]["repository"], "artifact_revision": plan["artifact"]["revision"],
        "runtime_revision": plan["runtime"]["revision"], "lock_sha256": cell["lock"]["sha256"],
        "eligibility": "exploratory", "quality_status": "pending",
    }
    return run, rows


def ingest_image_pilot(store, packet):
    run, attempts = read_packet(packet)
    payload = _sql_text(json.dumps({"run": run, "attempts": attempts}, ensure_ascii=False, allow_nan=False))
    return json.loads(store._query(f"""
        BEGIN;
        CREATE TEMP TABLE image_pilot_payload (document jsonb NOT NULL) ON COMMIT DROP;
        INSERT INTO image_pilot_payload VALUES ({payload}::jsonb);
        INSERT INTO fastest_intake.image_pilot_run
        SELECT item.* FROM image_pilot_payload,
            jsonb_populate_record(NULL::fastest_intake.image_pilot_run, document->'run') AS item
        ON CONFLICT (manifest_sha256) DO NOTHING;
        INSERT INTO fastest_intake.image_pilot_attempt
        SELECT item.* FROM image_pilot_payload,
            jsonb_populate_recordset(NULL::fastest_intake.image_pilot_attempt, document->'attempts') AS item
        ON CONFLICT (manifest_sha256, attempt_index) DO NOTHING;
        SELECT json_build_object(
            'manifest_sha256', document #>> '{{run,manifest_sha256}}',
            'attempts', count(attempt.attempt_index),
            'successful', count(*) FILTER (WHERE attempt.outcome = 'success'),
            'failed', count(*) FILTER (WHERE attempt.outcome <> 'success')
        ) FROM image_pilot_payload
        LEFT JOIN fastest_intake.image_pilot_attempt AS attempt
            ON attempt.manifest_sha256 = document #>> '{{run,manifest_sha256}}'
        GROUP BY document;
        COMMIT;
    """))
