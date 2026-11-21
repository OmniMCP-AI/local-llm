"""Read the original sealed ambient-load Apple M4 text capture."""

from datetime import datetime
from hashlib import sha256
from pathlib import PurePosixPath
import re

from fastest_pilot_bundle import digest, json_text
from fastest_release.validation import plain_text
from fastest_text.capture import classify_phase, phase_argv, pinned_commit
from fastest_text.intake import require, require_digest

from .scaling_capture import _check_digest, _decode_json, _regular_file
from .text_capture import MISSING_LATENCY, PHASES, _attempt_rows


def _checksums(raw, *, allow_paths=False):
    entries = {}
    for line in raw.decode("utf-8").splitlines():
        checksum, separator, name = line.partition("  ")
        require_digest(checksum, "Legacy file checksum")
        require(separator and plain_text(name), "Invalid legacy checksum entry.")
        basename = PurePosixPath(name).name
        require((allow_paths or basename == name) and basename not in ("", "..") and basename not in entries,
                "Invalid or duplicate legacy checksum target.")
        entries[basename] = checksum
    return entries


def _phase_events(raw):
    events = {phase: [] for phase in PHASES}
    for line in raw.splitlines():
        event = _decode_json(line)
        require(isinstance(event, dict) and plain_text(event.get("name")), "Invalid legacy process event.")
        if event["name"] in events:
            events[event["name"]].append(event)
    require(all(len(items) == 2 for items in events.values()), "Legacy packet requires two ended benchmark phases.")
    return events


def _event_time(event):
    timestamp = event.get("timestamp")
    require(isinstance(timestamp, str) and "T" in timestamp, "Invalid legacy process timestamp.")
    stamp = datetime.fromisoformat(timestamp)
    require(stamp.utcoffset() is not None, "Legacy process timestamp requires a time zone.")
    return stamp


def _legacy_argv_matches(argv, phase, protocol):
    if not isinstance(argv, list) or not all(plain_text(value) for value in argv):
        return False
    expected = phase_argv("llama-bench", "model", phase, protocol)
    if len(argv) != len(expected) or argv[1:2] != expected[1:2] or argv[-4:] != expected[-4:]:
        return False
    return dict(zip(argv[3:-4:2], argv[4:-4:2])) == dict(zip(expected[3:-4:2], expected[4:-4:2]))


def read_ambient_m4_packet(packet, plan):
    manifest = _regular_file(packet / "sources.sha256").read_bytes()
    checksums = _checksums(manifest)
    capture_sha = sha256(manifest).hexdigest()

    def sealed(name):
        filename = packet / name
        data = _regular_file(filename).read_bytes()
        _check_digest(filename, checksums.get(name), sha256(data).hexdigest())
        return data

    release = _decode_json(sealed("llama-release.json"))
    runtime = plan["runtime"]
    require(isinstance(release, dict) and release.get("target_commitish") == runtime["revision"]
            and release.get("tag_name") == runtime["tag"], "Legacy release does not match the pinned llama.cpp build.")
    shards = plan["artifact"]["shards"]
    require(_checksums(sealed("model-sha256.txt")) == {s["path"]: s["sha256"] for s in shards},
            "Legacy packet does not match the pinned model shards.")
    binaries = _checksums(sealed("llama-binaries.sha256"), allow_paths=True)
    require("llama-bench" in binaries, "Legacy packet is missing the llama-bench binary digest.")
    events = _phase_events(sealed("run-events.jsonl"))
    cell = next(cell for cell in plan["cells"] if cell["id"] == "apple-m4")
    protocol = plan["protocol"]
    phases, attempts, identity, first, last = [], [], None, None, None
    for name in PHASES:
        start, exit_event = events[name]
        started, finished = _event_time(start), _event_time(exit_event)
        pid, revision = start.get("pid"), start.get("worktree_revision")
        require(start.get("event") == "start" and exit_event.get("event") == "exit"
                and type(pid) is int and pid > 0 and exit_event.get("pid") == pid
                and isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision)
                and exit_event.get("worktree_revision") == revision and started <= finished
                and (last is None or last <= started), "Legacy benchmark process events do not match.")
        code = exit_event.get("code")
        require(type(code) is int and -(2**31) <= code < 2**31, "Invalid legacy process exit status.")
        argv, phase = start.get("argv"), protocol["phases"][name]
        require(_legacy_argv_matches(argv, phase, protocol) and PurePosixPath(argv[0]).name == "llama-bench"
                and PurePosixPath(argv[2]).name == shards[0]["path"],
                "Legacy benchmark invocation does not match the pinned protocol.")
        stdout, stderr = f"{name}.jsonl", f"{name}.stderr"
        runner = _decode_json(sealed(stdout))
        require(isinstance(runner, dict) and pinned_commit(runner.get("build_commit"), runtime["revision"])
                and type(runner.get("build_number")) is int and runner["build_number"] > 0,
                "Legacy benchmark output does not match the pinned runtime revision.")
        build = {"commit_reported": runner["build_commit"], "number_reported": runner["build_number"]}
        controls = (revision, argv[0], argv[2], build)
        require(identity is None or identity == controls, "Legacy phases used different runner or model revisions.")
        outcome = classify_phase({"outcome": "exited", "exit_code": code}, cell, phase, argv[2], protocol, build,
                                 sealed(stderr).decode("utf-8", "replace"), runner)
        phases.append({
            "capture_sha256": capture_sha, "phase": name, "outcome": outcome["outcome"],
            "receipt_sha256": checksums["run-events.jsonl"], "placement": outcome["placement"],
            "files": {filename: checksums[filename] for filename in (stdout, stderr)},
        })
        attempts.extend(_attempt_rows(capture_sha, name, outcome))
        identity, first, last = controls, first or started, finished

    run = {
        "capture_sha256": capture_sha, "evidence_sha256": capture_sha, "packet_kind": "ambient-m4-legacy",
        "capture_status": "complete" if all(row["outcome"] == "complete" for row in phases) else "incomplete",
        "review_status": "held", "cell_id": cell["id"], "started_at": first.isoformat(), "finished_at": last.isoformat(),
        "metadata": {
            "artifact": plan["artifact"], "protocol": protocol, "runtime": runtime, "backend": cell["backend"],
            "binary_sha256": binaries["llama-bench"], "runtime_build": identity[3], "worktree_revision": identity[0],
            "artifact_checksum_manifest_sha256": checksums["model-sha256.txt"],
            "runtime_release_sha256": checksums["llama-release.json"],
            "runtime_checksum_manifest_sha256": checksums["llama-binaries.sha256"],
            "quiet_host_operator_attested": False, "load_condition": "ambient-desktop",
            "latency": MISSING_LATENCY,
            "quality": {"status": "unreviewed", "rubric_id": plan["rubric"]["id"]},
        },
    }
    return run, phases, attempts
