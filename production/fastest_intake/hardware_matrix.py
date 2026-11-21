"""Collect reviewed fields from one pinned, creator-reported hardware matrix."""

from decimal import Decimal
from hashlib import sha256
import json

REPOSITORY = "maluramichael/llm-benchmarks"
REVISION = "8340ac1d8dfaf8902f47ccf1d4ebbcf81703f21e"
SOURCE = f"https://github.com/{REPOSITORY}/blob/{REVISION}"
LICENSE = f"{SOURCE}/LICENSE"
INPUTS = {
    "2026-11-03-pc-gtx-1080-ti-11gb": "7f0c1eaea67166cb2f6c3a18bb6db683624057876e1cf12f94cf66ceb975f023",
    "2026-11-03-pc-radeon-rx-560-4gb": "a846a24486ebc64d176d22b6678d89d523184522edf953d86681fa52299c11fe",
    "2026-11-03-pc-rtx-3080-ti-12gb": "020243919518269813dea54f06e8afdf3a7e7da83bd0d5127577fc5c41f8c4de",
    "2026-11-03-pc-rtx-3090-24gb": "0f67076d9115bb5eee10c29145249dcf9aa253bdc6ba605dbc304a1fccf0e9fd",
    "2026-11-03-pc-rtx-4060-ti-8gb": "32b3deb0b1bda37bfe018293ba63cb978f9e686272eb764113754f8b7a16d7e3",
}
LATENCY = {"gen_tps": "tok/s", "prompt_tps": "tok/s", "ttft_s": "s"}
METRICS = {
    "speed": LATENCY,
    "memory": {"vram_used_mb": "MiB", "vram_baseline_mb": "MiB", "kv_buffer_mb": "MiB",
               "load_s": "s", **LATENCY},
    "concurrency": {"total_tps": "tok/s", "decode_tps_total": "tok/s",
                    "per_request_tps": "tok/s", "ttft_p50_s": "s"},
}
SETTINGS = ("ctx", "effective_ctx", "effective_parallel", "ctx_per_slot", "parallel",
            "serialized", "cache_contaminated", "prompt_tokens", "gen_tokens", "cached_tokens", "gpu_fraction")
LIMITS = ("Creator-reported benchmark on the named host. Weights are identified by publisher digest. "
          "Class labels do not resolve a model repository, tokenizer or model revision. "
          "No independent reproduction or wall-meter measurement is part of this import.")


def run_trials(run_id, result):
    if result["schema_version"] != 1 or result.get("legacy"):
        raise ValueError(f"Expected a structured hardware matrix run for {run_id}.")
    run, host = result["run"], result["system"]
    inventory = host["gpus"]
    if len(inventory) != 1:
        raise ValueError(f"Expected one reported GPU for {run_id}.")
    gpu = inventory[0]
    trials = []
    for key, test in result["tests"].items():
        engine_id, size, suite, step = key.split("/")
        chosen = (suite == "concurrency"
                  or (suite == "speed" and step == "warm")
                  or (suite == "memory" and step in {"ctx-8192", "ctx-32768"}))
        if not chosen:
            continue
        engine = result["engines"][engine_id]
        model = result["models"][f"{engine_id}/{size}"]
        raw = test.get("values", {})
        status = test["status"]
        context = {
            "class_label": size, "test_suite": suite, "variant": step, "source_status": status,
            "bench_version": run["bench_version"], "driver": gpu.get("driver"),
            "gpu_in_host": gpu["name"], "cpu": host.get("cpu"), "ram_gib": host.get("ram_gb"),
            "os": host.get("os"), "monitors_on_gpu": host.get("monitors_on_gpu"),
            **{field: raw[field] for field in SETTINGS if field in raw},
        }
        common = {
            "source": run_id, "locator": f"results.json · tests[{key}]",
            "observed_on": test.get("started_at", run["started_at"])[:10],
            "artifact_revision": model.get("digest"), "quantization": model.get("quant"),
            "runtime": {"llamacpp": "llama.cpp", "ollama": "Ollama"}[engine_id],
            "runtime_revision": test.get("meta", {}).get("engine_version") or engine.get("version"),
            "backend": engine.get("backend"),
            "context_tokens": raw.get("ctx") if suite == "memory" else raw.get("effective_ctx"),
            "context": {field: str(value) if isinstance(value, Decimal) else value
                        for field, value in context.items()},
            "qualification": LIMITS,
        }
        if status == "ok" and (raw.get("gpu_fraction") or 0) > 0:
            common.update(gpu_count=1, gpu_ids=[gpu["name"]])
        identity = f"{run_id}/{key}"
        if status != "ok":
            outcome = {"oom": "oom", "failed": "failed"}.get(status, "unknown")
            trials.append({**common, "id": identity, "outcome": outcome,
                           "qualification": f"Publisher status {status}. {LIMITS}"})
            continue
        for metric, unit in METRICS[suite].items():
            amount = raw.get(metric)
            if amount is None:
                continue
            if type(amount) not in (int, Decimal) or not Decimal(amount).is_finite() or amount < 0:
                raise ValueError(f"Invalid reported {metric} for {identity}.")
            repeats = raw.get("runs", [])
            summary = {}
            if suite == "speed" and repeats and all(row.get(metric) is not None for row in repeats):
                summary = {"statistic": "median", "sample_count": len(repeats)}
            if metric == "ttft_p50_s":
                summary = {"statistic": "p50"}
                if raw.get("requests"):
                    summary["sample_count"] = len(raw["requests"])
            trials.append({**common, "id": f"{identity}/{metric}", "outcome": "measured",
                           "metric": metric, "amount": str(amount), "unit": unit, **summary})
    return trials


def read_hardware_matrix(directory, checked_at):
    sources, trials = [], []
    for run_id, digest in INPUTS.items():
        content = (directory / f"{run_id}.json").read_bytes()
        if sha256(content).hexdigest() != digest:
            raise ValueError(f"{run_id}.json does not match the hardware matrix at {REVISION}.")
        trials.extend(run_trials(run_id, json.loads(content, parse_float=Decimal)))
        sources.append({
            "source": run_id, "url": f"{SOURCE}/runs/{run_id}/results.json", "status": "captured",
            "note": f"Michael Malura and contributors. Adapted to typed observations under CC BY 4.0. "
                    f"License: {LICENSE}. Input SHA-256: {digest}.",
        })
    return {
        "checked_at": checked_at,
        "note": f"Five structured single-GPU hardware matrix runs at {REVISION}. "
                "Legacy RTX 4090 and MacBook files have no typed tests.",
        "sources": sources, "prices": [], "evaluations": [], "inference_trials": trials,
    }
