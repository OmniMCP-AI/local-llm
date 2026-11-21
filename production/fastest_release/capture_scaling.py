"""Capture a private controlled CUDA decode pair on an authorized GPU host."""

import argparse
import csv
from decimal import Decimal
from io import StringIO
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastest_pilot_capture import BENCH_SETTING_FLAGS, record_process, save_json, sha256_file, utc_now
from fastest_text.intake import json_settings_match

from .scaling import DEVICE_ID, LOAD, PLAN, transport_matches_devices
from .validation import keys, plain_text


GPU_UUID = re.compile(r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")
INVENTORY = ["nvidia-smi", "--query-gpu=uuid,pci.bus_id,name,driver_version", "--format=csv,noheader"]
BUFFER = re.compile(r"\b(CUDA\d+)\s+(model|KV) buffer size =\s+([0-9]+\.[0-9]+) MiB")
DECODE_ERROR = re.compile(r"failed to decode|decode failed|could not find a kv slot|CUDA error:", re.IGNORECASE)
ENVIRONMENT = ("CUDA_VISIBLE_DEVICES", "CUDA_DEVICE_ORDER", "CUDA_MODULE_LOADING",
               "GGML_CUDA_DISABLE_PEER_COPY", "GGML_CUDA_ENABLE_UNIFIED_MEMORY",
               "GGML_BACKEND_PATH", "LD_LIBRARY_PATH", "LD_PRELOAD")


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_selected_devices(devices):
    if not isinstance(devices, list) or not 2 <= len(devices) <= 16:
        raise ValueError("Select 2 to 16 full physical CUDA GPU UUIDs in baseline-first order.")
    for device in devices:
        keys(device, "uuid slot", "each selected GPU")
        if not (plain_text(device["uuid"]) and GPU_UUID.fullmatch(device["uuid"]) and plain_text(device["slot"])):
            raise ValueError("Each GPU needs a full GPU UUID and a physical slot label.")
    uuids = {device["uuid"].lower() for device in devices}
    slots = {device["slot"] for device in devices}
    if not len(uuids) == len(slots) == len(devices):
        raise ValueError("GPU UUIDs and physical slot labels must be distinct.")
    return devices


def _devices(path):
    devices = validate_selected_devices(_read(path))
    mask = os.environ.get("CUDA_VISIBLE_DEVICES")
    if mask is not None and not {device["uuid"] for device in devices} <= set(mask.split(",")):
        raise ValueError("Selected UUIDs must be permitted by the existing CUDA_VISIBLE_DEVICES allocation.")
    return devices


def _inventory(output, selected):
    record = record_process(output / "inventory", {"argv": INVENTORY}, "stdout.csv", 30, dict(os.environ))
    if record["exit_code"] != 0:
        raise ValueError("nvidia-smi inventory failed. See inventory/attempt.json.")
    return inventory_devices((output / "inventory" / "stdout.csv").read_text(encoding="utf-8"), selected)


def inventory_devices(raw, selected):
    by_uuid = {}
    for row in csv.reader(StringIO(raw, newline=""), skipinitialspace=True):
        if len(row) != 4:
            raise ValueError("Unexpected nvidia-smi CSV row.")
        uuid, pci, card, driver = (value.strip() for value in row)
        pci = pci[4:] if len(pci) == 16 and pci.startswith("0000") else pci
        if uuid in by_uuid:
            raise ValueError("Repeated GPU UUID in nvidia-smi inventory.")
        by_uuid[uuid] = {"id": pci.lower(), "card": card, "driver": driver}
    devices = [{**gpu, **by_uuid.get(gpu["uuid"], {})} for gpu in selected]
    if not all(DEVICE_ID.fullmatch(gpu.get("id", "")) and plain_text(gpu["card"])
               and plain_text(gpu["driver"]) for gpu in devices):
        raise ValueError("Selected GPUs need valid nvidia-smi PCI, card and driver records.")
    if len({gpu["id"] for gpu in devices}) != len(devices) or len({gpu["driver"] for gpu in devices}) != 1:
        raise ValueError("Selected GPUs must be different physical PCI devices with the same NVIDIA driver.")
    return devices


def placement(stderr):
    placement = {}
    for device, kind, mib in BUFFER.findall(stderr):
        if Decimal(mib) > 0:
            placement.setdefault(device, {})[kind] = mib
    return placement


def decode_argv(bench, model, protocol, tensor_split):
    phase = protocol["phases"]["decode"]
    settings = protocol["settings"]
    reps = protocol["warm_samples_per_phase"]
    argv = [str(bench), "-m", str(model), "-p", str(phase["input_tokens"]), "-n", str(phase["output_tokens"])]
    for setting, flag in BENCH_SETTING_FLAGS.items():
        value = settings[setting]
        argv.extend((flag, str(int(value) if type(value) is bool else value)))
    argv.extend(("-ts", tensor_split, "-r", str(reps), "--progress", "-v", "-o", "jsonl"))
    return argv


def _decode_attempt(output, *, role, devices, bench, model, protocol, timeout):
    tensor_split = "/".join(["1"] * len(devices))
    argv = decode_argv(bench, model, protocol, tensor_split)
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": ",".join(gpu["uuid"] for gpu in devices),
           "CUDA_DEVICE_ORDER": "PCI_BUS_ID"}
    directory = output / role
    record = {
        "run_id": str(uuid4()), "argv": argv, "role": role, "devices": devices,
        "primary_device": devices[0]["id"], "strategy": "single-device" if role == "baseline" else "layer",
        "tensor_split": tensor_split,
        "treatment": ("Only the reference GPU is visible to CUDA." if role == "baseline"
                      else "All selected GPUs are visible to CUDA with equal layer-split weights."),
        "environment": {name: env.get(name) for name in ENVIRONMENT},
    }
    record_process(directory, record, "stdout.jsonl", timeout, env)
    stderr = (directory / "stderr.log").read_text(encoding="utf-8", errors="replace")
    record["placement_mib"] = placement(stderr)
    if record["outcome"] == "exited":
        try:
            row = _read(directory / "stdout.jsonl")
        except (ValueError, RecursionError):
            row = None
        sample_error, durations = decode_samples(row, record, protocol, model)
        outcome, reason, samples = decode_result(record, stderr, sample_error, durations)
        record.update(outcome=outcome, reason=reason, samples_ns=samples)
    save_json(directory / "attempt.json", record)
    return record


def decode_samples(row, record, protocol, model):
    if not isinstance(row, dict):
        return "Expected exactly one readable runner JSONL object.", []
    phase = protocol["phases"]["decode"]
    expected = {
        **protocol["settings"], "backends": "CUDA", "model_filename": str(model),
        "n_prompt": phase["input_tokens"], "n_gen": phase["output_tokens"],
        "tensor_split": "/".join(["1.00"] * len(record["devices"])),
    }
    commit = row.get("build_commit")
    if not (isinstance(commit, str) and len(commit) >= 7 and PLAN["runtime"]["revision"].startswith(commit)):
        return "Runner build commit does not match the pinned revision.", []
    if not json_settings_match({field: row.get(field) for field in expected}, expected):
        return "Runner row does not match the pinned CUDA decode invocation.", []
    samples = row.get("samples_ns")
    if not (isinstance(samples, list) and len(samples) == protocol["warm_samples_per_phase"]
            and all(type(value) is int and 0 < value < 2**63 for value in samples)):
        return "Runner row lacks the pinned 20 valid timed durations.", []
    return None, samples


def decode_result(record, stderr, sample_error, samples):
    if re.search(r"\bout of memory\b|\bCUDA_ERROR_OUT_OF_MEMORY\b", stderr, re.IGNORECASE):
        return "oom", "Runner reported out of memory. See stderr.log.", []
    if record["exit_code"] != 0 or DECODE_ERROR.search(stderr):
        return "failed", "Runner exited unsuccessfully or logged a decode error. See original output.", []
    if sample_error is not None:
        return "invalid-output", sample_error, []
    placement = record["placement_mib"]
    if placement.keys() != {f"CUDA{index}" for index in range(len(record["devices"]))} or any(
        buffers.keys() != {"model", "KV"} for buffers in placement.values()
    ):
        return "invalid-output", "Logs lack positive model and KV allocations for the requested CUDA devices.", samples
    return "complete", None, samples


def _capture(args):
    if not plain_text(args.host_revision) or args.timeout < 1:
        raise ValueError("Supply a stable physical host revision and a positive timeout.")
    if not args.build_evidence.is_file() or args.build_evidence.stat().st_size == 0:
        raise ValueError("Supply a nonempty build evidence file.")
    devices = _devices(args.devices)
    model_dir = args.model_dir.resolve()
    artifact = PLAN["artifact"]
    model = model_dir / artifact["shards"][0]["path"]
    if "," in str(model):
        raise ValueError("The pinned llama-bench treats commas in model paths as argument separators.")
    for shard in artifact["shards"]:
        path = model_dir / shard["path"]
        if path.stat().st_size != shard["bytes"] or sha256_file(path) != shard["sha256"]:
            raise ValueError(f"GGUF shard differs from the pinned artifact: {path.name}")
    bench = args.bench.resolve()
    binary_sha256 = sha256_file(bench)
    args.output.mkdir(mode=0o700)
    build_evidence = args.output / "build-evidence"
    shutil.copyfile(args.build_evidence, build_evidence)
    protocol = PLAN["protocol"]
    ledger = {
        "schema_version": 1, "kind": "private-capture", "status": "starting", "host_revision": args.host_revision,
        "platform": platform.platform(), "binary_sha256": binary_sha256,
        "build_evidence_sha256": sha256_file(build_evidence), "artifact": artifact, "runtime": PLAN["runtime"],
        "protocol": {**protocol, "load": LOAD, "phases": {"decode": protocol["phases"]["decode"]}},
        "quality": {"status": "unreviewed", "protocol": PLAN["rubric"]["id"]},
        "transport": {"status": "unknown", "reason": "No independent comparison trace supplied at capture.",
                      "attachment": "transport/receipt.json"},
        "selected_devices": devices, "attempts": {},
    }
    capture_path = args.output / "capture.json"
    save_json(capture_path, ledger)
    try:
        devices = _inventory(args.output, devices)
        ledger.update(os_driver=f"{ledger['platform']} · NVIDIA {devices[0]['driver']}", status="capturing")
        save_json(capture_path, ledger)
        for role, selection in (("baseline", devices[:1]), ("comparison", devices)):
            attempt = _decode_attempt(args.output, role=role, devices=selection, bench=bench, model=model,
                                      protocol=protocol, timeout=args.timeout)
            ledger["attempts"][role] = {"run_id": attempt["run_id"], "outcome": attempt["outcome"],
                                        "ledger": f"{role}/attempt.json"}
            save_json(capture_path, ledger)
        ledger["status"] = ("complete" if all(run["outcome"] == "complete" for run in ledger["attempts"].values())
                            else "incomplete")
    except (OSError, ValueError, KeyboardInterrupt) as error:
        ledger.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                      reason=str(error) or type(error).__name__)
        raise
    finally:
        save_json(capture_path, ledger)
    return ledger["status"] == "complete"


def _attach_transport(args):
    capture = _read(args.output / "capture.json")
    if not (isinstance(capture, dict) and capture.get("kind") == "private-capture"
            and capture.get("status") in ("complete", "incomplete")):
        raise ValueError("Attach transport to a finished private scaling capture.")
    comparison = _read(args.output / "comparison" / "attempt.json")
    links_bytes = args.links.read_bytes()
    summary = json.loads(links_bytes)
    keys(summary, "run_id links", "transport summary")
    if summary["run_id"] != comparison["run_id"]:
        raise ValueError("Transport run_id must match the captured comparison.")
    if not transport_matches_devices(summary["links"], [gpu["id"] for gpu in comparison["devices"]]):
        raise ValueError("Transport must document connected direct-peer or host-staged paths among the comparison GPUs.")
    if not args.trace.is_file() or args.trace.stat().st_size == 0:
        raise ValueError("Supply the nonempty original trace as a file.")
    destination = args.output / "transport"
    if destination.exists():
        raise ValueError("The capture already has a transport attachment.")
    with TemporaryDirectory(dir=args.output) as tmp:
        staging = Path(tmp) / "transport"
        staging.mkdir(mode=0o700)
        (staging / "links.json").write_bytes(links_bytes)
        shutil.copyfile(args.trace, staging / "trace")
        save_json(staging / "receipt.json", {
            "status": "supplied", "run_id": comparison["run_id"], "attached_utc": utc_now(),
            "trace_filename": args.trace.name,
            "files": {name: sha256_file(staging / name) for name in ("trace", "links.json")},
        })
        staging.rename(destination)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="Execute both decode attempts sequentially.")
    capture.add_argument("output", type=Path, help="New private evidence directory.")
    capture.add_argument("--bench", type=Path, required=True, help="Pinned CUDA llama-bench executable.")
    capture.add_argument("--model-dir", type=Path, required=True, help="Directory with both pinned GGUF shards.")
    capture.add_argument("--devices", type=Path, required=True, help="Ordered JSON list of GPU UUIDs and slots.")
    capture.add_argument("--host-revision", required=True, help="Operator's stable physical host revision identifier.")
    capture.add_argument("--build-evidence", type=Path, required=True, help="Local file with the build provenance.")
    capture.add_argument("--timeout", type=int, default=900, help="Maximum seconds per decode invocation.")
    attach = commands.add_parser("attach-transport", help="Retain a comparison trace and validate its summary.")
    attach.add_argument("output", type=Path, help="Completed private evidence directory.")
    attach.add_argument("--trace", type=Path, required=True, help="Independently recorded original trace.")
    attach.add_argument("--links", type=Path, required=True, help="JSON summary with the comparison run ID and links.")
    args = parser.parse_args(argv)
    try:
        if args.command == "attach-transport":
            _attach_transport(args)
            return 0
        if _capture(args):
            return 0
        print(f"Pair incomplete. Private evidence retained in {args.output}.", file=sys.stderr)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
    except KeyboardInterrupt:
        print(f"Capture interrupted. Check private evidence in {args.output}.", file=sys.stderr)
        return 130
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
