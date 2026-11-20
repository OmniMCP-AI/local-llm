"""Read-only estimates for selected catalog configurations."""

from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
from subprocess import PIPE, SubprocessError, run

from fastest_release.research import UPSTREAM_COMMIT


CATALOG = Path(__file__).resolve().parents[2] / "opendesign/mockups/llm-observatory"
UPSTREAM = "https://github.com/AlexsJones/llmfit"
MODEL_DATA = "llmfit-core/data/hf_models.json"
MODEL_DATA_SHA256 = "298dbdf36913e1071e62dd07033b0bdf2672a208d71838d2e96d1f464fbd723a"
RTX_PROFILE = "llmfit-nvidia-rtx-4090"
RTX_VRAM_GIB = 24
RTX_SOURCE = "https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/"
PUBLIC_FIELDS = {"machine", "artifact", "runtime", "context", "ram_reserved_gib", "vram_reserved_gib", "cpu_cores"}
REQUIRED_FIELDS = PUBLIC_FIELDS - {"cpu_cores"}


class FitEngineError(RuntimeError):
    pass


def upstream_url(path):
    return f"{UPSTREAM}/blob/{UPSTREAM_COMMIT}/{path}"


def _load(name):
    return json.loads((CATALOG / name).read_bytes())


def _number(value, name, *, integer=False):
    try:
        number = int(value) if integer else float(value)
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f"Invalid {name}.") from None
    if number < int(integer) or number > 2**32 - 1 or not isfinite(number):
        raise ValueError(f"Invalid {name}.")
    return number or 0.0


class FitService:
    def __init__(self, engine):
        self.engine = Path(engine).resolve()
        if self._run(["--revision"]).strip() != UPSTREAM_COMMIT:
            raise FitEngineError("Fit executable does not match the pinned engine revision.")

        hardware = _load("catalog-hardware-sources.json")["upstream"]
        if hardware["commit"] != UPSTREAM_COMMIT:
            raise FitEngineError("Hardware catalog and fit engine pins disagree.")
        self.presets = {row["id"]: row for row in hardware["presets"]}
        self.machines = {
            row["id"]: {"id": row["id"], "name": row["name"], "source": row["source"], "kind": "research profile"}
            for row in _load("catalog-hardware.json")["machines"]
        }
        self.machines.update({
            key: {
                "id": key,
                "name": row["name"],
                "source": upstream_url(row["path"]),
                "source_sha256": row["sha256"],
                "kind": "llmfit example preset",
            }
            for key, row in self.presets.items()
        })
        self.artifacts = {
            item["sha256"]: {
                **item,
                "model": model,
                "source": f"https://huggingface.co/{item['repository']}/blob/{item['revision']}/{item['path']}",
            }
            for model, row in _load("catalog-identities.json").items()
            for item in row.get("artifacts", [])
        }
        self.runtimes = {
            row["id"]: {
                "id": row["id"],
                "tag": row["tag"],
                "source": f"{row['source']}/releases/tag/{row['tag']}",
                "backend_source": row["backendSource"],
            }
            for row in _load("catalog-runtimes.json")
        }

    def _run(self, args=(), payload=None):
        try:
            return run(
                [self.engine, *args],
                input=json.dumps(payload, allow_nan=False) if payload is not None else "",
                stdout=PIPE,
                stderr=PIPE,
                check=True,
                text=True,
                timeout=5,
            ).stdout
        except (OSError, SubprocessError) as error:
            raise FitEngineError("Pinned fit engine unavailable.") from error

    def estimate(self, selection):
        if selection.keys() - PUBLIC_FIELDS:
            raise ValueError("Unknown fit parameter.")
        try:
            machine = self.machines[selection["machine"]] if selection.get("machine") else None
            artifact = self.artifacts[selection["artifact"]] if selection.get("artifact") else None
            runtime = self.runtimes[selection["runtime"]] if selection.get("runtime") else None
        except KeyError:
            raise ValueError("Unknown machine, artifact or runtime.") from None
        assumptions = {}
        for public_name, result_name in (
            ("context", "context_tokens"),
            ("ram_reserved_gib", "ram_reserved_gib"),
            ("vram_reserved_gib", "vram_reserved_gib"),
            ("cpu_cores", "cpu_cores"),
        ):
            value = selection.get(public_name)
            assumptions[result_name] = (
                _number(value, public_name, integer=public_name in {"context", "cpu_cores"})
                if value else None
            )

        inputs = {
            "kind": "fit_estimate",
            "engine": {
                "name": "llmfit-core",
                "revision": UPSTREAM_COMMIT,
                "adapter": "fastest-fit/v1",
                "source": upstream_url("llmfit-core/src/fit.rs"),
                "license": upstream_url("LICENSE"),
            },
            "machine": machine,
            "artifact": artifact,
            "runtime": runtime,
            "assumptions": assumptions,
            "sources": {
                "model_metadata": {"url": upstream_url(MODEL_DATA), "sha256": MODEL_DATA_SHA256},
            },
        }
        native = {"status": "insufficient_input", "estimate": None}
        missing = sorted(field for field in REQUIRED_FIELDS if not selection.get(field))
        if missing:
            native.update(qualification="missing_request_inputs", missing=missing)
        elif machine["id"] != RTX_PROFILE:
            native.update(qualification="machine_fit_inputs_unavailable")
        elif artifact["quantization"] is None:
            native.update(qualification="artifact_quantization_unavailable")
        elif runtime["id"] != "llama.cpp" or artifact["format"] != "GGUF":
            native.update(status="unsupported", qualification="runtime_artifact_unavailable")
        elif assumptions["ram_reserved_gib"] >= self.presets[RTX_PROFILE]["memoryGb"] or (
            assumptions["vram_reserved_gib"] >= RTX_VRAM_GIB
        ):
            native.update(qualification="reservation_exhausts_memory")
        else:
            inputs["sources"]["memory_bandwidth"] = machine["source"]
            inputs["sources"]["installed_vram"] = RTX_SOURCE
            try:
                native = json.loads(self._run(payload={
                    "machine": machine["id"],
                    "model": artifact["model"],
                    "quantization": artifact["quantization"],
                    "runtime": runtime["id"],
                    "vram_capacity_gib": RTX_VRAM_GIB,
                    **assumptions,
                }))
            except json.JSONDecodeError as error:
                raise FitEngineError("Invalid response from the pinned fit engine.") from error

        identity = {**inputs, "calculation": native.get("calculation")}
        packed = json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return {"id": sha256(packed.encode()).hexdigest(), **inputs, **native}
