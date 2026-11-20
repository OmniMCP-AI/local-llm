from html import escape
from urllib.parse import urlencode


QUALIFICATIONS = {
    "missing_request_inputs": "Choose a machine and artifact, and enter your context and memory reservations.",
    "machine_fit_inputs_unavailable": "This profile lacks reviewed inputs for a reproducible fit estimate.",
    "artifact_quantization_unavailable": "The catalog does not identify this artifact's quantization.",
    "runtime_artifact_unavailable": "The fit engine has no supported estimate for this runtime and file format.",
    "reservation_exhausts_memory": "The reservations leave no available memory in one of the selected machine's pools.",
    "context_out_of_range": "The requested context exceeds the model catalog's limit.",
    "model_fit_inputs_unavailable": "The model metadata is outside the adapter's reviewed fit coverage.",
    "backend_incompatible": "The core reports that the selected backend does not support this model.",
    "core_selected_different_runtime": "The core selected another runtime.",
    "core_selected_different_quantization": "The core selected another quantization.",
    "core_reduced_context": "The core used a shorter context for its fit.",
    "cpu_cores_required_for_offload": "The model spills into system RAM. Enter the selected machine's CPU core count.",
}


def _options(rows, selected):
    return "".join(
        f'<option value="{escape(key)}"{" selected" if key == selected else ""}>{escape(label)}</option>'
        for key, label in rows
    )


def _summary(result, selection):
    if result is None:
        return ""
    estimate = result["estimate"]
    if estimate is not None:
        decode = estimate["decode_tokens_per_second"]
        decode_text = f"<p>Estimated decode {decode:.1f} tokens/s</p>" if decode is not None else ""
        if estimate["decode_qualification"] == "core_offload_context_cap":
            decode_text = "<p>Decode speed is unavailable at this context for CPU offload.</p>"
        details = (
            f'<p>{escape(estimate["fit_level"])} · {escape(estimate["run_mode"])} · '
            f'{escape(estimate["quantization"])}</p>'
            f'<p>Memory required {estimate["memory_required_gib"]:.2f} GiB, '
            f'available {estimate["memory_available_gib"]:.2f} GiB</p>'
            f'<p>Estimated usable context {estimate["usable_context_tokens"]:,} tokens</p>'
            f"{decode_text}"
        )
    else:
        details = f'<p>{escape(QUALIFICATIONS[result["qualification"]])}</p>'
        if "requested_artifact_memory_required_gib" in result:
            details += (
                f'<p>Selected artifact memory estimate {result["requested_artifact_memory_required_gib"]:.2f} GiB</p>'
                f'<p>Core suggestion {escape(result["engine_suggested_quantization"])} '
                f'with {escape(result["engine_selected_runtime"])}</p>'
            )
    sources = [
        ("Machine profile", result["machine"]["source"] if result["machine"] else None),
        ("Selected file", result["artifact"]["source"] if result["artifact"] else None),
        ("Runtime release", result["runtime"]["source"] if result["runtime"] else None),
        ("Memory bandwidth", result["sources"].get("memory_bandwidth")),
        ("Installed VRAM", result["sources"].get("installed_vram")),
        ("Model metadata", result["sources"]["model_metadata"]["url"]),
        ("Pinned fit implementation", result["engine"]["source"]),
    ]
    links = " · ".join(
        f'<a href="{escape(url)}">{label}</a>' for label, url in sources if url
    )
    query = escape(urlencode(selection))
    return (
        f'<section><h2>Fit result</h2>{details}'
        f'<p>Engine revision <code>{result["engine"]["revision"]}</code></p>'
        f'<p>{links}</p><p><a href="/fit.json?{query}">View assumptions and result JSON</a></p></section>'
    )


def render_fit(service, selection, result=None):
    machines = sorted(
        service.machines.values(),
        key=lambda row: (row["kind"] != "llmfit example preset", row["name"].casefold()),
    )
    artifacts = sorted(service.artifacts.items(), key=lambda pair: pair[1]["quantization"] != "Q8_0")
    machine_options = _options(
        ((row["id"], row["name"]) for row in machines), selection.get("machine", "llmfit-nvidia-rtx-4090")
    )
    artifact_options = _options(
        ((key, item["path"]) for key, item in artifacts), selection.get("artifact")
    )
    runtime_options = _options(((key, key) for key in service.runtimes), selection.get("runtime"))
    context = escape(selection.get("context", "4096"))
    ram = escape(selection.get("ram_reserved_gib", "8"))
    vram = escape(selection.get("vram_reserved_gib", "2"))
    cores = escape(selection.get("cpu_cores", ""))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Machine fit · fastest.ai</title>
<style>
body {{ font: 1rem/1.5 system-ui,sans-serif; max-width: 48rem; margin: 2rem auto; padding: 0 1rem; }}
label {{ display: block; margin: .8rem 0; }} input, select, button {{ font: inherit; }}
select {{ max-width: 100%; }} code {{ overflow-wrap: anywhere; }}
</style></head><body>
<nav><a href="/">fastest.ai</a></nav>
<main><h1>Estimate model fit</h1>
<p>Choose a machine and exact artifact. Results are llmfit estimates.</p>
<form action="/fit">
<label>Machine <select name="machine">{machine_options}</select></label>
<label>Artifact <select name="artifact">{artifact_options}</select></label>
<label>Runtime <select name="runtime">{runtime_options}</select></label>
<label>Context tokens <input name="context" type="number" min="1" value="{context}" required></label>
<label>Reserved RAM (GiB) <input name="ram_reserved_gib" type="number" min="0" step="any" value="{ram}" required></label>
<label>Reserved VRAM (GiB) <input name="vram_reserved_gib" type="number" min="0" step="any" value="{vram}" required></label>
<label>CPU cores for offload <input name="cpu_cores" type="number" min="1" value="{cores}"></label>
<button>Estimate fit</button></form>
{_summary(result, selection)}
</main></body></html>
"""
