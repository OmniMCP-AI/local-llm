"""Retain private calibrated AC-input evidence for a complete serving capture."""

import argparse
from decimal import Decimal
from hashlib import sha256
from ipaddress import ip_address
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

from fastest_release.validation import keys
from fastest_serving import (JOULES, METER_CLOCK_SOURCE, PROTOCOL, REQUESTS, USERS, WALL_BOUNDARY, WINDOW_MS,
                             _validate_attempt, _wall_joules)
from fastest_text.intake import require, require_text


NS_PER_MS = 1_000_000


def _unique_fields(pairs):
    record = {}
    for field, value in pairs:
        require(field not in record, f"Duplicate JSON field {field!r}.")
        record[field] = value
    return record


def _read_json(path):
    data = path.read_bytes()
    try:
        return json.loads(data, object_pairs_hook=_unique_fields), sha256(data).hexdigest()
    except ValueError as error:
        raise ValueError(f"Invalid JSON in {path.name}: {error}") from error


def _is_uuid(value):
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except ValueError:
        return False


def _capture_window(capture):
    require(isinstance(capture, dict), "The serving capture must be a JSON object.")
    require(capture.get("kind") == "private-capture" and capture.get("diagnostic_reason") is None,
            "Meter intake requires a non-diagnostic serving capture.")
    require(capture.get("protocol") == PROTOCOL["id"], "The serving capture must match the pinned protocol.")
    duration, attempts = capture.get("duration_ms"), capture.get("attempts")
    require(capture.get("status") == "complete" and type(duration) is int and duration == WINDOW_MS
            and isinstance(attempts, list) and len(attempts) == len(USERS) * REQUESTS,
            "Meter intake requires a complete serving capture with all scheduled attempts.")
    require(len({_validate_attempt(attempt, duration) for attempt in attempts}) == len(attempts),
            "Duplicate serving request in the capture.")

    window = capture.get("meter_window")
    keys(window, "capture_id start_ns end_ns clock", "announced meter window")
    require(_is_uuid(window["capture_id"]), "The capture has an invalid meter window ID.")
    start, end = window["start_ns"], window["end_ns"]
    captured_start, captured_end = capture.get("window_started_ns"), capture.get("window_ended_ns")
    require(all(type(ns) is int for ns in (start, end, captured_start, captured_end))
            and start > 0 and end - start == WINDOW_MS * NS_PER_MS
            and (start, end) == (captured_start, captured_end),
            "The announced meter bounds must match the captured monotonic window.")
    clock = window["clock"]
    keys(clock, "source boot_id time_namespace", "capture clock")
    require(clock["source"] == METER_CLOCK_SOURCE and _is_uuid(clock["boot_id"])
            and type(clock["time_namespace"]) is int and clock["time_namespace"] > 0,
            "The capture must identify a Linux monotonic clock, boot and time namespace.")
    return window


def _meter_power(meter, window, server):
    keys(meter, "schema_version capture_id clock alignment meter_id calibration_ref raw_log_ref boundary "
         "server_ip feeds unit samples", "meter log")
    require(type(meter["schema_version"]) is int and meter["schema_version"] == 1,
            "Expected meter log schema version 1.")
    require(meter["capture_id"] == window["capture_id"], "The meter log belongs to another capture.")
    clock = meter["clock"]
    require(isinstance(clock, dict) and type(clock.get("time_namespace")) is int and clock == window["clock"]
            and meter["alignment"] == "latched-on-client-monotonic-clock",
            "Meter samples require a recorded latch on the same client monotonic clock, boot and time namespace.")
    for field in ("meter_id", "calibration_ref", "raw_log_ref", "server_ip"):
        require_text(meter[field], f"meter.{field}")
    server_ip = server.get("ip") if isinstance(server, dict) else None
    require(isinstance(server_ip, str) and ip_address(meter["server_ip"]) == ip_address(server_ip),
            "Meter evidence must cover the captured serving host.")
    require(meter["boundary"] == WALL_BOUNDARY and meter["unit"] == "J",
            "Expected cumulative joules at the serving host AC input.")
    feeds = meter["feeds"]
    require(isinstance(feeds, list) and feeds, "Meter evidence must identify the covered serving host feeds.")
    for feed in feeds:
        require_text(feed, "meter feed")
    require(len(set(feeds)) == len(feeds), "Meter feed identifiers must be distinct.")

    samples = meter["samples"]
    require(isinstance(samples, list) and len(samples) >= 2,
            "Meter evidence requires recorded samples at both capture boundaries.")
    last_ns, last_joules = window["start_ns"] - 1, Decimal(0)
    epoch = None
    for sample in samples:
        keys(sample, "sampled_ns joules counter_epoch", "cumulative meter sample")
        stamp, reading = sample["sampled_ns"], sample["joules"]
        require(type(stamp) is int and last_ns < stamp <= window["end_ns"],
                "Meter samples must be ordered and inside the captured monotonic window.")
        require(isinstance(reading, str) and JOULES.fullmatch(reading),
                "Wall meter readings must be nonnegative decimal joules.")
        require_text(sample["counter_epoch"], "meter counter epoch")
        if epoch is None:
            epoch = sample["counter_epoch"]
        joules = Decimal(reading)
        require(sample["counter_epoch"] == epoch and joules >= last_joules,
                "The cumulative AC meter counter reset, wrapped or decreased during the capture.")
        last_ns, last_joules = stamp, joules
    require((samples[0]["sampled_ns"], last_ns) == (window["start_ns"], window["end_ns"]),
            "The first and last meter samples must match the exact captured monotonic boundaries.")

    power = {"status": "measured", "boundary": WALL_BOUNDARY, "meter": meter["meter_id"],
             "start_ms": 0, "end_ms": WINDOW_MS, "start_joules": samples[0]["joules"],
             "end_joules": samples[-1]["joules"]}
    _wall_joules(power)
    return power


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="Original private serving capture directory.")
    parser.add_argument("meter_log", type=Path, help="Recorder evidence JSON in the serving meter format.")
    parser.add_argument("output", type=Path, help="New private JSON receipt path.")
    args = parser.parse_args()
    try:
        capture, capture_sha256 = _read_json(args.capture / "capture.json")
        window = _capture_window(capture)
        meter, meter_sha256 = _read_json(args.meter_log)
        power = _meter_power(meter, window, capture.get("server"))
        receipt = {"schema_version": 1, "capture_sha256": capture_sha256, "meter_log_sha256": meter_sha256,
                   "meter_log": meter, "power": power}
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent, prefix=".serving-meter-") as file:
            json.dump(receipt, file, indent=2)
            file.write("\n")
            file.flush()
            os.link(file.name, args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Meter evidence rejected: {error}\n")


if __name__ == "__main__":
    main()
