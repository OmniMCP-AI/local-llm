"""Capture and replay one unsigned benchmark candidate on GitHub-hosted Linux."""

import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
from tempfile import TemporaryDirectory
from uuid import NAMESPACE_URL, uuid5
from zipfile import BadZipFile, ZipFile

from fastest_pilot_capture import BENCH_SETTING_FLAGS, record_process, save_json, sha256_file
from fastest_text.capture import OOM, RUNNER_ERROR, effective_placement, phase_progress, pinned_commit
from fastest_text.intake import json_settings_match, median_throughput, require


REPOSITORY = "OmniMCP-AI/local-llm"
RUNNER_IMAGE = "ubuntu-24.04"
RUNTIME_REVISION = "84a9bf2fc2875205f0806fbbfbb66dc67204094c"
RUNTIME_BUILD = 5163
ARCHIVE_URL = "https://github.com/ggml-org/llama.cpp/releases/download/b5163/llama-b5163-bin-ubuntu-x64.zip"
ARCHIVE_SHA256 = "9663781ea5cd79035fcecb1f3e00b8aabcf559a181984d96ce5cfdeef9d7c2b7"
BINARY_SHA256 = "3a8af6f994c61334f0b903aa7af5d24fa73bec2b051135272690920aa8766d50"
RUNTIME_FILES = ("llama-bench", "libllama.so", "libggml.so", "libggml-base.so", "libggml-cpu.so", "libggml-rpc.so")
ARTIFACT = {
    "repository": "Qwen/Qwen2.5-0.5B-Instruct-GGUF", "revision": "9217f5db79a29953eb74d5343926648285ec7e67",
    "path": "qwen2.5-0.5b-instruct-q4_k_m.gguf", "format": "GGUF", "quantization": "Q4_K_M",
    "sha256": "74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db",
}
MODEL_URL = "https://huggingface.co/{repository}/resolve/{revision}/{path}".format(**ARTIFACT)
TOKENS = 128
REPETITIONS = 7
SETTINGS = {
    "n_threads": 1, "n_batch": 128, "n_ubatch": 128, "n_gpu_layers": 0,
    "type_k": "f16", "type_v": "f16", "no_kv_offload": True, "flash_attn": False,
    # In b5163, split mode "none" requires an active GPU even with zero offloaded layers.
    "use_mmap": True, "split_mode": "layer", "main_gpu": 0,
}
LOG_NAMES = ("stdout.jsonl", "stderr.log")
FILE_LIMIT = 256 * 1024


def runner_provenance():
    require(
        (os.getenv("RUNNER_ENVIRONMENT"), os.getenv("ImageOS"), platform.system()) ==
        ("github-hosted", "ubuntu24", "Linux"),
        "Capture requires a GitHub-hosted Ubuntu 24.04 Linux runner.",
    )
    with Path("/proc/cpuinfo").open(encoding="utf-8") as cpuinfo:
        cpu_model = next((line.partition(":")[2].strip() for line in cpuinfo if line.startswith("model name")), "")
    return {
        "repository": os.getenv("GITHUB_REPOSITORY"), "run_id": os.getenv("GITHUB_RUN_ID"),
        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"), "checkout_sha": os.getenv("GITHUB_SHA"),
        "runner_image": RUNNER_IMAGE, "image_version": os.getenv("ImageVersion"),
        "architecture": platform.machine(), "cpu_model": cpu_model,
    }


def run_url(runner):
    require(isinstance(runner, dict) and set(runner) == {
        "repository", "run_id", "run_attempt", "checkout_sha", "runner_image", "image_version",
        "architecture", "cpu_model",
    }, "Invalid GitHub runner metadata.")
    patterns = {
        "run_id": r"[1-9][0-9]{0,19}", "run_attempt": r"[1-9][0-9]{0,9}", "checkout_sha": r"[0-9a-f]{40}",
        "image_version": r"[0-9]+(?:\.[0-9]+){1,4}", "cpu_model": r"[A-Za-z0-9][A-Za-z0-9 ().+@_-]{3,149}",
    }
    require(runner["repository"] == REPOSITORY and runner["runner_image"] == RUNNER_IMAGE and
            runner["architecture"] == "x86_64" and
            all(isinstance(runner[field], str) and re.fullmatch(pattern, runner[field])
                for field, pattern in patterns.items()), "Invalid GitHub runner metadata.")
    return f"https://github.com/{REPOSITORY}/actions/runs/{runner['run_id']}/attempts/{runner['run_attempt']}"


def invocation():
    argv = ["./runtime/llama-bench", "-m", ARTIFACT["path"], "-p", "0", "-n", str(TOKENS)]
    for setting, flag in BENCH_SETTING_FLAGS.items():
        value = SETTINGS[setting]
        argv.extend((flag, str(int(value) if type(value) is bool else value)))
    return [*argv, "-r", str(REPETITIONS), "--progress", "-v", "-o", "jsonl"]


def read_text(path):
    require(path.is_file() and 0 < path.stat().st_size <= FILE_LIMIT, f"Missing or oversized {path.name}.")
    return path.read_text(encoding="utf-8")


def build_receipt(directory, runner):
    locator = run_url(runner)
    stdout, stderr = (read_text(directory / name) for name in LOG_NAMES)
    row = json.loads(stdout)
    require(isinstance(row, dict) and pinned_commit(row.get("build_commit"), RUNTIME_REVISION) and
            type(row.get("build_number")) is int and row["build_number"] == RUNTIME_BUILD,
            "Runner output does not match the pinned llama.cpp build.")
    expected = {
        **SETTINGS, "n_prompt": 0, "n_gen": TOKENS, "model_filename": ARTIFACT["path"],
        "tensor_split": "0.00", "cpu_mask": "0x0", "cpu_strict": False, "poll": 50, "embeddings": False,
        "gpu_info": "", "cpu_info": runner["cpu_model"], "backends": "RPC",
    }
    require(json_settings_match({field: row.get(field) for field in expected}, expected),
            "Runner output does not match the pinned CPU invocation.")
    require(not OOM.search(stderr) and not RUNNER_ERROR.search(stderr), "Runner logged an error during decode.")
    placement = effective_placement(stderr, ["RPC"])
    buffer_devices = {kind: {device for device, sizes in placement["buffers_mib"].items() if kind in sizes}
                      for kind in ("model", "kv", "compute")}
    # The official CPU asset registers an unused RPC backend with zero devices.
    require(not placement["devices"] and all(actual == 0 for actual, _ in placement["offloaded_layers"]) and
            buffer_devices["model"] and buffer_devices["model"] <= {"CPU", "CPU_Mapped", "CPU_REPACK"} and
            buffer_devices["kv"] == {"CPU"} and buffer_devices["compute"] == {"CPU"} and
            placement["context_tokens"] == [TOKENS], "Runner logs do not confirm CPU-only buffer placement.")
    started, _ = phase_progress(stderr, {"input_tokens": 0}, REPETITIONS)
    samples = row.get("samples_ns")
    require(stderr.splitlines().count("llama-bench: benchmark 1/1: warmup generation run") == 1 and
            started == list(range(1, REPETITIONS + 1)) and isinstance(samples, list) and
            len(samples) == REPETITIONS and all(type(sample) is int and 0 < sample < 2**63 for sample in samples),
            "Runner output lacks the full set of positive timed decode samples.")
    median = Decimal(median_throughput(samples, TOKENS)).quantize(Decimal("0.000000000001")).normalize()
    return {
        "schema_version": 1, "runner": runner, "run_url": locator, "argv": invocation(),
        "runtime": {
            "revision": RUNTIME_REVISION, "build_reported": row["build_commit"], "build_number": RUNTIME_BUILD,
            "archive_url": ARCHIVE_URL, "archive_sha256": ARCHIVE_SHA256, "binary_sha256": BINARY_SHA256,
        },
        "artifact": {**ARTIFACT, "url": MODEL_URL},
        "samples_ns": samples, "median_tokens_per_second": format(median, "f"),
        "files": {name: sha256_file(directory / name) for name in LOG_NAMES},
    }


def candidate(receipt, receipt_sha256):
    runner = receipt["runner"]
    cpu = runner["cpu_model"]
    arch = runner["architecture"]
    return {
        "kind": "measured", "evidence_id": str(uuid5(NAMESPACE_URL, receipt["run_url"])),
        "hardware": {
            "revision_id": str(uuid5(NAMESPACE_URL, f"{REPOSITORY}/{RUNNER_IMAGE}/{arch}/{cpu}")),
            "revision": 1, "name": f"GitHub-hosted shared CI runner ({cpu})",
            "configuration": f"{arch}, Ubuntu 24.04. One CPU thread. Shared host.",
        },
        "artifact": {**ARTIFACT, "artifact_id": str(uuid5(NAMESPACE_URL, MODEL_URL))},
        "workload": {
            "id": "llama-bench-shared-ci-cpu-decode", "version": 1,
            "description": "Single CPU thread, synthetic tokens, zero prompt tokens and 128 decode steps. "
                           "Seven timed repetitions following a one-token warmup on a shared CI runner.",
        },
        "metric": {
            "id": "llama-bench-decode", "version": 1, "value": receipt["median_tokens_per_second"], "unit": "tok/s",
            "statistic": "median", "sample_count": len(receipt["samples_ns"]),
            "boundary": "llama-bench synchronized time for 128 single-token steps starting at empty KV.",
        },
        "source": {
            "label": "GitHub Actions CPU baseline capture", "locator": receipt["run_url"], "revision": receipt_sha256,
        },
        "fields": {
            "backend": {"status": "known", "value": "CPU"},
            "runtime_revision": {"status": "known", "value": RUNTIME_REVISION},
            "runner_image_version": {"status": "known", "value": runner["image_version"]},
            "comparison_eligibility": {"status": "known", "value": "Standalone shared CI CPU baseline. "
                                       "Excluded from the quiet-host 7B text pilot."},
            "physical_host_revision": {"status": "missing", "reason": "Physical host identity is unavailable on CI."},
            "wall_power": {"status": "missing", "reason": "The GitHub-hosted runner has no wall power meter."},
        },
    }



def report_stderr(path, work):
    if not path.is_file():
        return
    with path.open("rb") as log:
        limit = 4096
        log.seek(max(0, path.stat().st_size - limit))
        tail = log.read(limit).decode("utf-8", errors="replace").replace(str(work), "<capture>")
    for line in tail.splitlines()[-16:]:
        if line:
            printable = "".join(character if character.isprintable() else "?" for character in line)
            print(f"llama-bench stderr | {printable}", file=sys.stderr)


def capture(archive, model, output):
    runner = runner_provenance()
    run_url(runner)
    require(sha256_file(archive) == ARCHIVE_SHA256, "Runtime archive SHA-256 does not match the official asset.")
    require(sha256_file(model) == ARTIFACT["sha256"], "GGUF SHA-256 does not match the catalog artifact.")
    with TemporaryDirectory(prefix="fastest-cpu-") as temporary:
        work = Path(temporary).resolve()
        runtime = work / "runtime"
        runtime.mkdir()
        with ZipFile(archive) as source:
            for name in RUNTIME_FILES:
                (runtime / name).write_bytes(source.read(f"build/bin/{name}"))
        bench = runtime / "llama-bench"
        require(sha256_file(bench) == BINARY_SHA256, "Extracted runner binary does not match the pinned asset.")
        bench.chmod(0o700)
        (work / ARTIFACT["path"]).symlink_to(model.resolve(strict=True))
        attempt_path = work / "attempt"
        attempt = record_process(attempt_path, {"argv": invocation()}, LOG_NAMES[0], 180,
                                 {"LC_ALL": "C", "LD_LIBRARY_PATH": "./runtime", "OMP_NUM_THREADS": "1"}, cwd=work)
        try:
            require(attempt["exit_code"] == 0, f"Runner failed ({attempt['outcome']}, exit {attempt['exit_code']}).")
            receipt = build_receipt(attempt_path, runner)
        except (OSError, ValueError):
            report_stderr(attempt_path / LOG_NAMES[1], work)
            raise
        output.mkdir(mode=0o700)
        for name in LOG_NAMES:
            shutil.copyfile(attempt_path / name, output / name)
        save_json(output / "receipt.json", receipt)
        save_json(output / "candidate.json", candidate(receipt, sha256_file(output / "receipt.json")))


def verify(directory):
    receipt_path = directory / "receipt.json"
    receipt = json.loads(read_text(receipt_path))
    require(isinstance(receipt, dict) and receipt == build_receipt(directory, receipt.get("runner")),
            "Receipt differs from the retained runner evidence.")
    observation = json.loads(read_text(directory / "candidate.json"))
    require(observation == candidate(receipt, sha256_file(receipt_path)),
            "Candidate differs from the retained runner evidence.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("capture")
    collect.add_argument("archive", type=Path)
    collect.add_argument("model", type=Path)
    collect.add_argument("directory", type=Path)
    replay = commands.add_parser("verify")
    replay.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            capture(args.archive, args.model, args.directory)
        else:
            verify(args.directory)
    except (BadZipFile, KeyError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
