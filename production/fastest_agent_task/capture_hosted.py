"""Capture and verify the unsigned shared CI CPU inventory comparison."""

import argparse
from functools import partial
import json
import os
from pathlib import Path
import re
import signal
import subprocess
from tempfile import TemporaryDirectory
import time
from zipfile import BadZipFile, ZipFile

from fastest_release.capture_cpu import ARCHIVE_SHA256, ARCHIVE_URL, read_text, runner_provenance, run_url
from fastest_release.validation import keys
from fastest_text.capture import effective_placement

from .evidence import attempt_outcome, require
from .hosted import BINARY_SHA256, THREADS, TRIAL_ORDER, WARMUPS, evidence_id, hosted_plan, validate_candidate
from .measure import digest, interrupt, run, write_json


RUNTIME_FILES = (
    "llama-server", "libllama.so", "libggml.so", "libggml-base.so", "libggml-cpu.so", "libggml-rpc.so",
    "libllava_shared.so", "libmtmd_shared.so",
)
OS = "Ubuntu 24.04 x86_64"
CANDIDATES = {name: f"{name}-candidate.json" for name in WARMUPS}


def input_urls():
    artifact = hosted_plan()["artifact"]
    root = f"https://huggingface.co/{artifact['repository']}/resolve/{artifact['revision']}"
    return [ARCHIVE_URL, *(f"{root}/{shard['path']}" for shard in artifact["shards"])]


def check_cpu_allocation(pid):
    affinity = os.sched_getaffinity(pid)
    require(len(affinity) == THREADS, "Expected four CPUs in the guest affinity set")
    cgroup = next((line[3:] for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines()
                   if line.startswith("0::")), None)
    require(cgroup is not None and cgroup.startswith("/"), "Expected the guest's cgroup v2 CPU controls")
    root = Path("/sys/fs/cgroup")
    group = root / cgroup.lstrip("/")
    require(group.is_dir(), "Guest CPU cgroup is not visible")
    for ancestor in (group, *group.parents):
        cpu_max = ancestor / "cpu.max"
        if cpu_max.is_file():
            quota, period = cpu_max.read_text().split()
            require(quota == "max" or int(quota) >= THREADS * int(period),
                    "Guest CPU quota is below the pinned four threads")
        if ancestor == root:
            break
    return affinity


def guest_load():
    def counters():
        values = Path("/proc/stat").read_text().splitlines()[0].split()
        require(values[0] == "cpu" and len(values) >= 9, "Guest CPU counters are unavailable")
        return [int(value) for value in values[1:9]]

    before = counters()
    time.sleep(1)
    after = counters()
    elapsed = [end - start for start, end in zip(before, after)]
    total = sum(elapsed)
    require(total > 0 and all(value >= 0 for value in elapsed), "Invalid guest CPU sample")
    return {"idle_percent": round(100 * elapsed[3] / total), "steal_percent": round(100 * elapsed[7] / total)}


def startup_diagnostics(logfile):
    if not logfile.is_file():
        return {"log_available": False}
    with logfile.open("rb") as file:
        log = file.read(256 * 1024).decode("utf-8", errors="replace")
    placement = effective_placement(log, [])
    buffers = {kind: sorted({safe_device(device) for device, values in placement["buffers_mib"].items() if kind in values})
               for kind in ("model", "kv", "compute")}
    thread_fields = re.search(r"system info: n_threads = (-?\d{1,5}), n_threads_batch = (-?\d{1,5}), "
                              r"total_threads = (\d{1,5})\b", log)
    return {
        "log_available": True, "buffers": buffers, "devices": sorted({safe_device(name) for name in placement["devices"]}),
        "offloaded_layers": placement["offloaded_layers"], "context_tokens": sorted(set(placement["context_tokens"])),
        "batch_tokens": sorted({int(value) for value in re.findall(r"\bn_batch\s+= (\d{1,7})\b", log)}),
        "slots": sorted({int(value) for value in re.findall(r"\bn_slots = (\d{1,7})\b", log)}),
        "threads": [int(value) for value in thread_fields.groups()] if thread_fields else [],
        "unix_socket": "setting address family to AF_UNIX" in log,
    }


def safe_device(name):
    return name if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,24}", name) else "other"


def check_server(affinity, pid, logfile):
    require(check_cpu_allocation(pid) == affinity, "llama-server affinity differs from the capture controller")
    actual = startup_diagnostics(logfile)
    require(actual["log_available"], "Missing private startup verification log")
    buffers = actual["buffers"]
    require(
        not actual["devices"] and all(offloaded == 0 for offloaded, _ in actual["offloaded_layers"])
        and buffers["model"] and set(buffers["model"]) <= {"CPU", "CPU_Mapped", "CPU_REPACK", "CPU_AARCH64"}
        and buffers["kv"] == buffers["compute"] == ["CPU"],
        "Runtime logs did not confirm CPU-only model, KV and compute buffers",
    )
    require(
        actual["context_tokens"] == [2048] and actual["batch_tokens"] == [512] and actual["slots"] == [1]
        and actual["threads"] == [THREADS] * 3 and actual["unix_socket"],
        "Runtime logs did not confirm pinned CPU threads, context, batch, slot and socket settings",
    )


def measure_sequences(private, protocol):
    contexts = {context["id"]: context for context in protocol["contexts"]}
    events = [json.loads(line) for line in (private / "events.jsonl").read_text().splitlines()]
    require([event["event"] for event in events[:2]] == ["server_started", "server_ready"]
            and events[-1]["event"] == "server_stopped", "The single server lifecycle was not captured")
    exchanges = events[2:-1]
    require(len(exchanges) % 2 == 0, "Expected a KV reset for every attempt")
    warmups, measured = [], []
    drafts = {name: [] for name in contexts}
    for reset, event in zip(exchanges[::2], exchanges[1::2]):
        name = event["context_id"]
        attempt = event["attempt"]
        trial, number = attempt["trial"], attempt["attempt"]
        warmup = event["warmup"]
        require(
            reset["event"] == "kv_reset" and event["event"] == "attempt"
            and (reset["context_id"], reset["trial"], reset["attempt"], reset["warmup"])
                == (name, trial, number, warmup)
            and reset["response"]["id_slot"] == 0 and type(reset["response"]["n_erased"]) is int
            and reset["response"]["n_erased"] >= 0
            and reset["completed_monotonic_ns"] <= event["started_monotonic_ns"]
            and event["ended_monotonic_ns"] - event["started_monotonic_ns"] == attempt["wall_ns"],
            "Captured reset, attempt identity or elapsed time does not replay",
        )
        outcome = attempt_outcome(attempt, contexts[name], demo=False)
        require(outcome == event["outcome"], "Recorded attempt differs from rubric evaluation")
        if warmup:
            require(not measured and trial == number == 1, "Warmup is outside its pinned place")
            warmups.append(name)
        else:
            measured.append([name, trial, number])
            drafts[name].append({
                **attempt, "outcome": outcome, "answer": attempt["answer"] if outcome == "accepted" else None,
            })
    require(tuple(warmups) == WARMUPS, "Expected exactly one warmup per policy")
    return drafts, warmups, measured


def evidence_ids(locator):
    return {name: evidence_id(locator, name) for name in WARMUPS}


def report_progress(data):
    print("Hosted capture", json.dumps(data, sort_keys=True), flush=True)


def capture(archive, models, directory):
    runner = runner_provenance()
    locator = run_url(runner)
    checkout = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, timeout=10).strip()
    require(checkout == runner["checkout_sha"], "Checked-out revision differs from the Actions run")
    require(archive.is_file(), "Missing pinned runtime asset: runtime.zip")
    require(digest(archive) == ARCHIVE_SHA256, "Runtime archive differs from the pinned official asset")
    protocol = hosted_plan()
    settings = protocol["settings"]
    for shard in protocol["artifact"]["shards"]:
        require((models / shard["path"]).is_file(), f"Missing pinned model shard: {shard['path']}")
    environment = {
        "hardware": f"GitHub-hosted {runner['cpu_model']}, {THREADS} vCPUs", "os": OS, "backend": "CPU",
        "runtime_binary_sha256": BINARY_SHA256, "adapter_sha256": protocol["harness"]["files"]["measure.py"],
        "source": {
            "run_url": locator, "checkout_sha": checkout, "runner_image_version": runner["image_version"],
        },
    }

    with TemporaryDirectory(prefix="agt-", dir="/tmp") as temporary:
        work = Path(temporary)
        runtime = work / "bin"
        runtime.mkdir()
        with ZipFile(archive) as source:
            for name in RUNTIME_FILES:
                entry = f"build/bin/{name}"
                require(entry in source.namelist(), f"Missing runtime archive member: {name}")
                (runtime / name).write_bytes(source.read(entry))
        binary = runtime / "llama-server"
        require(digest(binary) == BINARY_SHA256, "Extracted llama-server differs from the pinned official binary")
        binary.chmod(0o700)
        private = work / "private"
        model = (models / protocol["artifact"]["shards"][0]["path"]).resolve()
        affinity = check_cpu_allocation(os.getpid())
        before = guest_load()
        try:
            run(private, binary, model, environment["hardware"], OS, "CPU", settings["device"],
                protocol=protocol, check_server=partial(check_server, affinity), report_progress=report_progress,
                runtime_environment={"LC_ALL": "C", "LD_LIBRARY_PATH": str(runtime), "OMP_NUM_THREADS": str(THREADS)})
        except (ValueError, RuntimeError, subprocess.SubprocessError):
            print("Parsed startup diagnostics", json.dumps(startup_diagnostics(private / "server.log"), sort_keys=True))
            raise
        after = guest_load()
        require(affinity == check_cpu_allocation(os.getpid()), "Guest affinity changed during capture")
        attempts, warmups, order = measure_sequences(private, protocol)

        directory.mkdir(mode=0o700)
        files = {}
        for context in protocol["contexts"]:
            name = context["id"]
            candidate = {
                "kind": "measured", "context_id": name, "context_sha256": context["sha256"],
                "environment": environment, "attempts": attempts[name],
            }
            candidate_path = directory / CANDIDATES[name]
            write_json(candidate_path, candidate)
            files[candidate_path.name] = digest(candidate_path)
        write_json(directory / "receipt.json", {
            "schema_version": 1, "protocol_id": protocol["protocol_id"],
            "source": environment["source"], "artifact": protocol["artifact"],
            "runtime": {**protocol["runtime"], "archive_url": ARCHIVE_URL, "archive_sha256": ARCHIVE_SHA256},
            "controls": {
                "guest_before": before, "guest_after": after, "cpu_affinity_vcpus": len(affinity),
                "cpu_quota_allows_vcpus": THREADS, "cpu_only": True, "warmups": warmups,
                "attempts_with_kv_reset": order,
            },
            "files": files, "evidence_ids": evidence_ids(locator),
        })
        verify(directory)


def verify(directory):
    require({path.name for path in directory.iterdir()} == {"receipt.json", *CANDIDATES.values()},
            "Packet must contain only the scoped receipt and two unsigned candidates")
    receipt = json.loads(read_text(directory / "receipt.json"))
    protocol = hosted_plan()
    keys(receipt, "schema_version protocol_id source artifact runtime controls files evidence_ids", "hosted receipt")
    require(
        receipt["schema_version"] == 1 and receipt["protocol_id"] == protocol["protocol_id"]
        and receipt["artifact"] == protocol["artifact"]
        and receipt["runtime"] == {**protocol["runtime"], "archive_url": ARCHIVE_URL, "archive_sha256": ARCHIVE_SHA256},
        "Receipt does not match the pinned workload and runtime",
    )
    keys(receipt["files"], " ".join(CANDIDATES.values()), "receipt files")
    environment = None
    attempts = {}
    for context in protocol["contexts"]:
        name = context["id"]
        path = directory / CANDIDATES[name]
        contents = read_text(path)
        require(digest(path) == receipt["files"][path.name], "Candidate digest differs from the receipt")
        record = json.loads(contents)
        result = validate_candidate(record, context, protocol)
        require(result["status"] == "complete", "Capture must cover both trials for each policy")
        require(environment in (None, record["environment"]), "Candidate environments must match")
        environment = record["environment"]
        attempts[name] = result["attempts"]
    require(receipt["source"] == environment["source"] and
            receipt["evidence_ids"] == evidence_ids(environment["source"]["run_url"]), "Receipt provenance differs")
    controls = receipt["controls"]
    keys(controls, "guest_before guest_after cpu_affinity_vcpus cpu_quota_allows_vcpus cpu_only warmups "
                   "attempts_with_kv_reset", "receipt controls")
    for field in ("guest_before", "guest_after"):
        sample = controls[field]
        keys(sample, "idle_percent steal_percent", "guest CPU sample")
        require(all(type(value) is int and 0 <= value <= 100 for value in sample.values())
                and sum(sample.values()) <= 100, "Invalid guest CPU utilization")
    require(
        controls["cpu_affinity_vcpus"] == controls["cpu_quota_allows_vcpus"] == THREADS
        and controls["cpu_only"] is True and controls["warmups"] == list(WARMUPS)
        and controls["attempts_with_kv_reset"] == [
            [name, trial, row["attempt"]] for name, trial in TRIAL_ORDER
            for row in attempts[name] if row["trial"] == trial
        ],
        "Receipt does not confirm the pinned guest controls and reset order",
    )
    return receipt


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    commands.add_parser("urls")
    collect = commands.add_parser("capture")
    collect.add_argument("archive", type=Path)
    collect.add_argument("models", type=Path)
    collect.add_argument("directory", type=Path)
    replay = commands.add_parser("verify")
    replay.add_argument("directory", type=Path)
    args = cli.parse_args()
    try:
        if args.command == "plan":
            print(json.dumps(hosted_plan(), indent=2))
        elif args.command == "urls":
            print(*input_urls(), sep="\n")
        elif args.command == "capture":
            os.umask(0o077)
            for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM):
                signal.signal(signum, interrupt)
            capture(args.archive, args.models, args.directory)
        else:
            verify(args.directory)
    except (ValueError, RuntimeError) as error:
        cli.exit(1, f"{error}\n")
    except (BadZipFile, KeyError, OSError, subprocess.SubprocessError) as error:
        cli.exit(1, f"Hosted capture or verification failed ({type(error).__name__}).\n")
    except KeyboardInterrupt:
        cli.exit(130, "Hosted capture interrupted.\n")


if __name__ == "__main__":
    main()
