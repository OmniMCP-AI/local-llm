"""Import a private four-user client capture for review."""

from datetime import datetime
from hashlib import sha256
from ipaddress import ip_address
import json

from fastest_release import _sql_text
from fastest_serving import (
    INTERVAL_MS, OUTCOMES, OUTPUT_TOKENS, PROTOCOL, REQUESTS, START_TOLERANCE_MS, TIMEOUT_MS, USERS, WINDOW_MS,
    _validate_attempt, _wall_joules,
)
from fastest_serving.capture import ERASE_TIMEOUT_MS, NS_PER_MS, WARMUP_TIMEOUT_MS
from fastest_serving.meter import _read_json, _unique_fields
from fastest_text.intake import require


PLANNED = len(USERS) * REQUESTS
TERMINAL = ("complete", "partial", "failed", "interrupted")


def _timestamp(value, label):
    if value is None:
        return None
    try:
        stamp = datetime.fromisoformat(value)
        require(stamp.utcoffset() is not None, "missing time zone")
        return stamp.isoformat()
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be an ISO timestamp with a time zone.") from error


def _trace_response(event, timeout_ms):
    start, finish = event.get("started_ns"), event.get("finished_ns")
    require(type(start) is int and type(finish) is int and 0 <= start <= finish < 2**63,
            "invalid monotonic response timing")
    elapsed_ns = finish - start
    timeout = event.get("timeout", False)
    require(type(timeout) is bool and (timeout or elapsed_ns <= timeout_ms * NS_PER_MS),
            "response timing and timeout disagree")
    error, status = event.get("transport_error"), event.get("http_status")
    require(error is None or isinstance(error, str) and error, "invalid transport status")
    require(timeout or error or type(status) is int and 100 <= status < 600,
            "missing or invalid HTTP status")
    return elapsed_ns, timeout, error, status


def _trace_attempt(event, timeout_ms):
    elapsed_ns, timeout, error, status = _trace_response(event, timeout_ms)
    outcome, tokens = event.get("outcome"), event.get("output_tokens")
    elapsed_ms = timeout_ms if timeout else max(1, (elapsed_ns + NS_PER_MS - 1) // NS_PER_MS)
    require(type(event.get("elapsed_ms")) is int and elapsed_ms == event["elapsed_ms"],
            "recorded latency disagrees with monotonic response timing")
    require(outcome in OUTCOMES and type(tokens) is int and 0 <= tokens < 2**31,
            "invalid response outcome or output token count")
    if timeout:
        require(outcome == "timeout" and tokens == 0, "timed-out response cannot contain accepted work")
    elif error or not 200 <= status < 300:
        require(outcome == "failed" and tokens == 0, "failed response cannot contain accepted work")
    else:
        require(outcome == "rejected" or outcome == "accepted" and tokens == OUTPUT_TOKENS,
                "successful HTTP response has an inconsistent serving outcome")
    return elapsed_ns


def _trace_rows(data, ledger, expected, capture_sha):
    warmup, erasures, timed = {}, {}, {}
    window_start = ledger.get("window_started_ns")
    duration = ledger["duration_ms"]
    for line_number, line in enumerate(data.splitlines(), 1):
        try:
            event = json.loads(line.decode("utf-8"), object_pairs_hook=_unique_fields)
            require(isinstance(event, dict), "expected one JSON event per line")
            phase = event.get("phase")
            if phase == "warmup":
                user = event.get("user")
                require(not erasures and not timed and type(user) is int and user in USERS and user not in warmup,
                        "unexpected or repeated warmup user")
                _trace_attempt(event, WARMUP_TIMEOUT_MS)
                warmup[user] = event["outcome"] == "accepted"
                continue

            require(phase in ("erase", "timed"), "unknown capture phase")
            require(len(warmup) == len(USERS) and all(warmup.values()),
                    "capture advanced before all warmup responses were accepted")
            if phase == "erase":
                slot = event.get("slot")
                require(not timed and all(erasures.values()) and type(slot) is int and
                        slot == len(erasures) and slot < len(USERS), "unexpected or repeated KV erasure")
                _, timeout, error, status = _trace_response(event, ERASE_TIMEOUT_MS)
                erasures[slot] = not timeout and error is None and status == 200
                continue

            require(window_start is not None and len(erasures) == len(USERS) and all(erasures.values()),
                    "timed request has no started window or successful KV erasure responses")
            user, request = event.get("user"), event.get("request")
            require(type(user) is int and user in USERS and type(request) is int and 1 <= request <= REQUESTS,
                    "invalid planned user or request")
            key = (user, request)
            require(key not in timed, "duplicate timed request")
            require(request == len(timed) // len(USERS) + 1,
                    "timed requests are out of schedule order or a previous slot is missing")
            scheduled = (request - 1) * INTERVAL_MS
            started_ns = event.get("started_ns")
            require(type(event.get("scheduled_ms")) is int and scheduled == event["scheduled_ms"] and
                    type(started_ns) is int and window_start + scheduled * NS_PER_MS <= started_ns < 2**63,
                    "timed request disagrees with its scheduled arrival")
            offset_ns = started_ns - window_start
            if duration < WINDOW_MS:
                require(offset_ns < (duration + 1) * NS_PER_MS, "timed request starts after the captured duration")
            outcome = event.get("outcome")
            row = {"capture_sha256": capture_sha, "user_slot": user, "request_number": request,
                   "scheduled_ms": scheduled, "started_ms": offset_ns // NS_PER_MS, "outcome": outcome}
            outside_slot = offset_ns > (scheduled + START_TOLERANCE_MS) * NS_PER_MS
            if outcome == "unrecorded":
                require(outside_slot and key not in expected and
                        not {"finished_ns", "elapsed_ms", "output_tokens"} & event.keys(),
                        "unrecorded request conflicts with the arrival tolerance or capture ledger")
            else:
                attempt = expected.get(key)
                require(attempt is not None and all(type(event.get(field)) is type(value) and event[field] == value
                                                    for field, value in attempt.items()),
                        "timed request disagrees with the capture ledger")
                require(not outside_slot and row["started_ms"] == attempt["started_ms"],
                        "timed request start disagrees with its pinned slot or monotonic offset")
                elapsed_ns = _trace_attempt(event, TIMEOUT_MS)
                require(duration == WINDOW_MS or offset_ns + elapsed_ns < (duration + 1) * NS_PER_MS,
                        "timed response ends after the captured duration")
                row.update(elapsed_ms=attempt["elapsed_ms"], observed_elapsed_ns=elapsed_ns,
                           output_tokens=attempt["output_tokens"])
            timed[key] = row
        except ValueError as error:
            raise ValueError(f"trace.jsonl line {line_number}: {error}.") from error

    require(expected.keys() <= timed.keys(), "trace.jsonl is missing a timed request in capture.json.")
    if window_start is not None:
        require(len(erasures) == len(USERS) and all(erasures.values()),
                "trace.jsonl is missing successful KV erasure responses before the started window.")
    status = ledger["status"]
    if status in ("complete", "partial"):
        require(len(timed) == PLANNED, "trace.jsonl does not account for every slot in the finished window.")
        require((status == "complete") == (len(expected) == PLANNED),
                "Capture completion status disagrees with the recorded request count.")
    return list(timed.values())


def _read_packet(packet):
    ledger, capture_sha = _read_json(packet / "capture.json")
    require(isinstance(ledger, dict), "capture.json must be a JSON object.")
    require(ledger.get("protocol") == PROTOCOL["id"], "capture.json must match the pinned serving protocol.")
    kind, reason = ledger.get("kind"), ledger.get("diagnostic_reason")
    require((kind == "diagnostic" and isinstance(reason, str) and reason.strip()) or
            (kind == "private-capture" and "diagnostic_reason" in ledger and reason is None),
            "Capture kind must be explicit and agree with its diagnostic reason.")
    server = ledger.get("server")
    require(isinstance(server, dict) and isinstance(server.get("ip"), str)
            and type(server.get("port")) is int and 1 <= server["port"] <= 65535,
            "capture.json must identify a numeric server address and port.")
    try:
        address = ip_address(server["ip"])
    except ValueError as error:
        raise ValueError("capture.json has an invalid server IP address.") from error
    endpoint = getattr(address, "ipv4_mapped", None) or address
    require(not endpoint.is_loopback or kind == "diagnostic", "Loopback captures require the diagnostic kind.")

    status, duration = ledger.get("status"), ledger.get("duration_ms")
    require(status in TERMINAL, "capture.json must be finalized as complete, partial, failed or interrupted.")
    require(type(duration) is int and 0 <= duration <= WINDOW_MS, "Invalid serving capture duration.")
    start = ledger.get("window_started_ns")
    end = ledger.get("window_ended_ns")
    started_at = _timestamp(ledger.get("window_started_utc"), "window_started_utc")
    finished_at = _timestamp(ledger.get("capture_finished_utc"), "capture_finished_utc")
    if start is None:
        require(duration == 0 and started_at is None and end is None, "Capture duration lacks a started window.")
    else:
        require(type(start) is int and 0 <= start < 2**63 and started_at and finished_at,
                "A started window requires valid monotonic and UTC timing.")
    if status in ("complete", "partial") or end is not None:
        require(start is not None and duration == WINDOW_MS and type(end) is int
                and end == start + WINDOW_MS * NS_PER_MS and end < 2**63,
                "A finished serving window must match the pinned duration and monotonic bounds.")

    power = ledger.get("power")
    require(isinstance(power, dict) and power.get("status") == "missing",
            "A raw serving ledger must report missing power. Meter evidence requires separate review.")
    _wall_joules(power)
    attempts = ledger.get("attempts")
    require(isinstance(attempts, list) and len(attempts) <= PLANNED, "Invalid timed attempt count in capture.json.")
    expected = {_validate_attempt(attempt, WINDOW_MS): attempt for attempt in attempts}
    require(len(expected) == len(attempts), "Duplicate timed request in capture.json.")

    trace = (packet / "trace.jsonl").read_bytes()
    rows = _trace_rows(trace, ledger, expected, capture_sha)
    return {
        "capture_sha256": capture_sha, "trace_sha256": sha256(trace).hexdigest(),
        "protocol_id": PROTOCOL["id"], "kind": kind, "capture_status": status, "duration_ms": duration,
        "window_started_at": started_at, "capture_finished_at": finished_at,
        "review_status": "held", "separate_host_status": "unverified", "power_status": "missing",
    }, rows


def ingest_serving_capture(store, packet):
    run, attempts = _read_packet(packet)
    payload = _sql_text(json.dumps({"run": run, "attempts": attempts}, allow_nan=False))
    return json.loads(store._query(f"""
        BEGIN;
        CREATE TEMP TABLE serving_capture_payload (document jsonb NOT NULL) ON COMMIT DROP;
        INSERT INTO serving_capture_payload VALUES ({payload}::jsonb);
        INSERT INTO fastest_intake.serving_capture_run
        SELECT item.* FROM serving_capture_payload,
            jsonb_populate_record(NULL::fastest_intake.serving_capture_run, document->'run') AS item
        ON CONFLICT (capture_sha256) DO NOTHING;
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM fastest_intake.serving_capture_run AS run, serving_capture_payload
                WHERE run.capture_sha256 = document #>> '{{run,capture_sha256}}'
                  AND run.trace_sha256 = document #>> '{{run,trace_sha256}}'
            ) THEN
                RAISE EXCEPTION 'This capture.json was already imported with a different trace.jsonl SHA-256.';
            END IF;
        END $$;
        INSERT INTO fastest_intake.serving_capture_attempt
        SELECT item.* FROM serving_capture_payload,
            jsonb_populate_recordset(NULL::fastest_intake.serving_capture_attempt, document->'attempts') AS item
        ON CONFLICT (capture_sha256, user_slot, request_number) DO NOTHING;
        SELECT json_build_object(
            'capture_sha256', run.capture_sha256, 'trace_sha256', run.trace_sha256,
            'kind', run.kind, 'capture_status', run.capture_status, 'review_status', run.review_status,
            'separate_host_status', run.separate_host_status, 'power_status', run.power_status,
            'planned', {PLANNED}, 'attempted', count(attempt.elapsed_ms),
            'unrecorded', {PLANNED} - count(attempt.elapsed_ms),
            'accepted', count(*) FILTER (WHERE attempt.outcome = 'accepted'),
            'accepted_output_tokens', coalesce(sum(attempt.output_tokens) FILTER (WHERE attempt.outcome = 'accepted'), 0)
        ) FROM serving_capture_payload
        JOIN fastest_intake.serving_capture_run AS run
            ON run.capture_sha256 = document #>> '{{run,capture_sha256}}'
        LEFT JOIN fastest_intake.serving_capture_attempt AS attempt USING (capture_sha256)
        GROUP BY run.capture_sha256;
        COMMIT;
    """))
