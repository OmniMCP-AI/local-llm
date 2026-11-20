"""Validate reviewed four-user serving evidence and derive comparable metrics."""

from collections import Counter
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import json
import re
from uuid import UUID

from fastest_release.validation import keys
from fastest_text.intake import require, require_digest, require_text


USERS = range(1, 5)
REQUESTS = 24
INTERVAL_MS = 6000
TIMEOUT_MS = 5000
WINDOW_MS = REQUESTS * INTERVAL_MS
START_TOLERANCE_MS = 100
MIN_P95 = 20
INPUT_TOKENS = 1024
OUTPUT_TOKENS = 128
WALL_BOUNDARY = "serving-host-ac-input"
OUTCOMES = ("accepted", "failed", "timeout", "rejected")
JOULES = re.compile(r"(?:0|[1-9][0-9]{0,14})(?:\.[0-9]{1,6})?")
METRICS = {
    "user_p95": {"label": "Worst user p95 response time", "unit": "ms", "direction": "lower", "default": "4000"},
    "capacity": {"label": "Aggregate accepted output", "unit": "tok/s", "direction": "higher", "default": "60"},
    "wall_energy": {"label": "Wall energy per accepted request", "unit": "J/request", "direction": "lower", "default": ""},
}
PROTOCOL = {
    "id": "four-user-fixed-token-serving@1", "users": len(USERS),
    "requests_per_user": REQUESTS, "arrival_interval_ms": INTERVAL_MS, "window_ms": WINDOW_MS,
    "start_tolerance_ms": START_TOLERANCE_MS, "timeout_ms": TIMEOUT_MS,
    "input_tokens": INPUT_TOKENS, "output_tokens": OUTPUT_TOKENS, "context_tokens_per_user": 2048,
    "min_accepted_per_user_for_p95": MIN_P95,
    "runtime": "llama.cpp llama-server",
    "runtime_args": "-np 4 -c 8192 -cb -t 8 -b 1024 -ub 512 -ngl 99 -ctk f16 -ctv f16",
    "endpoint": "POST /completion",
    "prompt": "1,024 token IDs with token i (zero-based) equal to 1000 + ((i + 251 × user) mod 1000).",
    "request_options": {
        "n_predict": OUTPUT_TOKENS, "temperature": 0, "ignore_eos": True, "cache_prompt": False,
        "return_tokens": True, "stream": False,
    },
    "warmup": "One untimed simultaneous request per user after model load. Clear KV before the timed window.",
    "cache": "No prefix reuse. Clear KV for each request. OS page cache is uncontrolled.",
    "acceptance": "The client received a valid complete response with exactly 128 output tokens by the 5 s deadline.",
    "latency_boundary": "Client send to complete response, including queue and transfer time. Nearest-rank p95 of accepted responses for each user.",
    "capacity_boundary": "Accepted output tokens divided by the full scheduled window, including idle gaps and unsuccessful requests.",
    "wall_boundary": "Cumulative whole-host AC input over the same window, across every server power feed. Includes idle gaps, failures and timeouts. Excludes client, network equipment and external cooling.",
}


def _wall_joules(power):
    require(isinstance(power, dict), "Power requires a measured wall meter or a missing reason.")
    if power.get("status") == "missing":
        keys(power, "status reason", "missing power")
        require_text(power["reason"], "power.reason")
        return None
    require(power.get("status") == "measured" and power.get("boundary") == WALL_BOUNDARY,
            "Power requires a whole-host wall meter or a missing reason.")
    keys(power, "status boundary meter start_ms end_ms start_joules end_joules", "measured power")
    require_text(power["meter"], "power.meter")
    require(type(power["start_ms"]) is int and type(power["end_ms"]) is int and
            (power["start_ms"], power["end_ms"]) == (0, WINDOW_MS), "Power requires the full wall-meter window.")
    start, end = power["start_joules"], power["end_joules"]
    require(all(isinstance(value, str) and JOULES.fullmatch(value) for value in (start, end)),
            "Wall meter readings must be nonnegative decimal joules.")
    with localcontext() as context:
        context.prec = 28
        total = Decimal(end) - Decimal(start)
    require(total > 0, "Wall meter reading must increase over the measurement window.")
    return total


def _validate_attempt(attempt, duration):
    require(isinstance(attempt, dict) and attempt.get("outcome") in OUTCOMES, "Invalid serving attempt outcome.")
    outcome = attempt["outcome"]
    keys(attempt, "user request started_ms outcome elapsed_ms output_tokens"
         + (" reason" if outcome != "accepted" else ""), "serving attempt")
    user, request = attempt["user"], attempt["request"]
    require(type(user) is int and user in USERS and type(request) is int and 1 <= request <= REQUESTS,
            "Serving attempt must identify a planned user and request.")
    start, elapsed, tokens = (attempt[field] for field in ("started_ms", "elapsed_ms", "output_tokens"))
    scheduled = (request - 1) * INTERVAL_MS
    require(type(start) is int and scheduled <= start <= scheduled + START_TOLERANCE_MS,
            "Serving request started outside its pinned arrival slot.")
    require(type(elapsed) is int and 0 < elapsed <= TIMEOUT_MS and start + elapsed <= duration,
            "Serving attempt must end within its client deadline and the captured window.")
    require(type(tokens) is int and 0 <= tokens < 2**31, "Invalid serving output token count.")
    if outcome == "accepted":
        require(tokens == OUTPUT_TOKENS, "Accepted work must have the pinned output length.")
    else:
        require_text(attempt["reason"], "attempt.reason")
        if outcome == "timeout":
            require(elapsed == TIMEOUT_MS, "Timeout must reach the client deadline.")
    return user, request


def _validate(record, cells, artifact, runtime):
    keys(record, "kind cell_id protocol artifact_sha256 runtime_revision runtime_build source rights privacy "
         "duration_ms attempts power", "serving record")
    require(record["kind"] == "measured", "Serving intake requires measured records.")
    require(record["protocol"] == PROTOCOL["id"], "Serving record must match the pinned protocol.")
    require(record["artifact_sha256"] == [shard["sha256"] for shard in artifact["shards"]],
            "Serving record must match the pinned GGUF shards.")
    require(record["runtime_revision"] == runtime["revision"], "Serving runtime must match the pinned revision.")
    cell = record["cell_id"]
    require(isinstance(cell, str) and cell in cells, "Serving record must match a planned setup.")
    build = record["runtime_build"]
    keys(build, "backend binary_sha256 configuration", "serving runtime build")
    require(build["backend"] == cells[cell]["backend"], "Serving runtime backend must match the planned setup.")
    require_digest(build["binary_sha256"], "runtime_build.binary_sha256")
    require_text(build["configuration"], "runtime_build.configuration")
    source = record["source"]
    keys(source, "locator revision", "serving source")
    require_text(source["locator"], "source.locator")
    require_text(source["revision"], "source.revision")
    rights = record["rights"]
    keys(rights, "decision_id destination core basis", "serving rights")
    require(rights["destination"] == "public-release" and rights["core"] == "allow",
            "Serving record requires a public-release allow decision.")
    require_text(rights["basis"], "rights.basis")
    require_text(rights["decision_id"], "rights.decision_id")
    require(str(UUID(rights["decision_id"])) == rights["decision_id"], "Serving rights require a canonical UUID.")
    require(record["privacy"] in ("local-only", "external"), "Invalid serving execution privacy.")
    duration, attempts = record["duration_ms"], record["attempts"]
    require(type(duration) is int and 0 < duration <= WINDOW_MS, "Serving record needs a valid captured duration.")
    require(isinstance(attempts, list) and len(attempts) <= len(USERS) * REQUESTS, "Invalid serving attempt count.")
    identifiers = {_validate_attempt(attempt, duration) for attempt in attempts}
    require(len(identifiers) == len(attempts), "Duplicate serving request.")
    total = _wall_joules(record["power"])
    require(total is None or duration == WINDOW_MS, "Power window extends beyond the captured serving window.")
    return cell, total


def _ratio(numerator, denominator):
    with localcontext() as context:
        context.prec = 40
        value = (Decimal(numerator) / denominator).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        return format(value.normalize(), "f")


def _metric(value, reason, count):
    return {"value": value, "status": "available" if value is not None else "missing",
            "reason": reason, "sample_count": count}


def summarize(record=None, wall_joules=None):
    attempts = record["attempts"] if record else []
    counts = Counter(attempt["outcome"] for attempt in attempts)
    planned = len(USERS) * REQUESTS
    accepted = counts["accepted"]
    full = len(attempts) == planned and record["duration_ms"] == WINDOW_MS
    missing_run = "No reviewed serving run was supplied."
    incomplete = "The reviewed run does not cover the full scheduled serving window and all planned requests."
    users = []
    for user in USERS:
        elapsed = sorted(attempt["elapsed_ms"] for attempt in attempts
                         if attempt["user"] == user and attempt["outcome"] == "accepted")
        p95 = elapsed[(95 * len(elapsed) + 99) // 100 - 1] if full and len(elapsed) >= MIN_P95 else None
        users.append({"user": user, "accepted": len(elapsed), "p95_ms": p95})

    user_p95 = max(user["p95_ms"] for user in users) if all(user["p95_ms"] is not None for user in users) else None
    run_gap = None if full else incomplete if record else missing_run
    latency_gap = (f"p95 requires at least {MIN_P95} accepted responses for every user."
                   if user_p95 is None else None)
    power = record["power"] if record else {"status": "missing", "reason": "No wall meter measurement was supplied."}
    power_gap = power.get("reason") or run_gap
    if power_gap is None and accepted == 0:
        power_gap = "The run produced zero accepted responses."
    metrics = {
        "user_p95": _metric(str(user_p95) if user_p95 is not None else None, run_gap or latency_gap, accepted),
        "capacity": _metric(_ratio(accepted * OUTPUT_TOKENS * 1000, WINDOW_MS) if full else None, run_gap, accepted),
        "wall_energy": _metric(_ratio(wall_joules, accepted) if power_gap is None else None, power_gap, accepted),
    }
    return {
        "status": ("measured" if accepted else "failed") if full else "partial" if record else "unmeasured",
        "reason": run_gap, "metrics": metrics, "users": users, "attempts": attempts,
        "counts": {"planned": planned, "attempted": len(attempts), "unrecorded": planned - len(attempts),
                   **{outcome: counts[outcome] for outcome in OUTCOMES}},
        "accepted_output_tokens": accepted * OUTPUT_TOKENS,
        "captured_duration_ms": record["duration_ms"] if record else None,
        "power": power, "wall_joules": format(wall_joules, "f") if wall_joules is not None else None,
        **({field: record[field] for field in ("source", "runtime_build", "privacy", "rights")} if record else {}),
    }


def load_records(paths, text):
    cells = {cell["id"]: cell for cell in text["cells"]}
    serving = {}
    for path in paths:
        record = json.loads(path.read_text(encoding="utf-8"))
        cell, total = _validate(record, cells, text["artifact"], text["runtime"])
        require(cell not in serving, "Duplicate reviewed serving record for one setup.")
        serving[cell] = summarize(record, total)
    return {cell: serving.get(cell) or summarize() for cell in cells}
