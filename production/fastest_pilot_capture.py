"""Local process and provenance helpers for the pinned llama-bench captures."""

from datetime import datetime, timezone
from hashlib import file_digest
import subprocess

from fastest_pilot_bundle import json_text


BENCH_SETTING_FLAGS = {
    "n_threads": "-t", "n_batch": "-b", "n_ubatch": "-ub", "n_gpu_layers": "-ngl",
    "type_k": "-ctk", "type_v": "-ctv", "no_kv_offload": "-nkvo", "flash_attn": "-fa",
    "use_mmap": "-mmp", "split_mode": "-sm", "main_gpu": "-mg",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    with path.open("rb") as source:
        return file_digest(source, "sha256").hexdigest()


def save_json(path, record):
    staging = path.with_suffix(".next.json")
    staging.write_text(json_text(record), encoding="utf-8")
    staging.replace(path)


def record_process(directory, record, stdout_name, timeout, env):
    directory.mkdir()
    ledger = directory / "attempt.json"
    stdout, stderr = (directory / name for name in (stdout_name, "stderr.log"))
    record.update(started_utc=utc_now(), outcome="running", exit_code=None, timeout_seconds=timeout)
    save_json(ledger, record)
    try:
        with stdout.open("xb") as output, stderr.open("xb") as error_log:
            completed = subprocess.run(record["argv"], stdin=subprocess.DEVNULL, stdout=output, stderr=error_log,
                                       env=env, timeout=timeout, check=False)
        record["exit_code"] = completed.returncode
        record["outcome"] = "exited"
    except subprocess.TimeoutExpired:
        record.update(outcome="timeout", reason="Subprocess deadline elapsed.")
    except OSError as error:
        record.update(outcome="failed", reason=str(error))
    except KeyboardInterrupt:
        record.update(outcome="interrupted", reason="Operator interrupted the subprocess.")
        raise
    finally:
        record.update(finished_utc=utc_now(), files={path.name: sha256_file(path) for path in (stdout, stderr)
                                                 if path.is_file()})
        save_json(ledger, record)
    return record
