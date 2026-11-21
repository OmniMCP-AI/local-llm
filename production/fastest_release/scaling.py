"""Rights-checked, controlled single-to-multi-GPU decode comparisons."""

from decimal import Decimal, localcontext
from fractions import Fraction
from html import escape
import json
import re

from fastest_text.intake import json_settings_match

from .profiles import (EXCLUSIONS, RUN_ID, TEXT_PLAN, accessible_table, exclusion_reason,
                       html_page, metric_definitions, public_field)
from .validation import plain_text


ROUTE = "/topology/scaling"
METADATA_FIELD = "gpu_scaling_v1"
PLAN = json.loads(TEXT_PLAN.read_text(encoding="utf-8"))
PLAN["protocol"]["id"] = "llama-bench-solo-gpu-scaling@1"
LOAD = "One foreground sequence on an otherwise idle host."
SETTINGS = {key: value for key, value in PLAN["protocol"]["settings"].items()
            if key not in {"split_mode", "main_gpu"}}
DECODE = "llama-bench-decode"
METRICS = {DECODE: metric_definitions(PLAN)[DECODE]}
DEVICE_ID = re.compile(r"[0-9a-f]{4}:[0-9a-f]{2}:[0-1][0-9a-f]\.[0-7]")
DIGEST = re.compile(r"[0-9a-f]{64}")
DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,19})(?:\.[0-9]{1,12})?")
MESSAGES = {
    **EXCLUSIONS,
    "unpinned": "No reviewed 1→N GPU pair is pinned.",
    "metadata": "A run lacks readable, approved scaling metadata.",
    "host_mismatch": "The runs use different physical host revisions.",
    "runtime_mismatch": "The runs do not use the same pinned runtime, binary, OS and driver.",
    "quality_mismatch": "Both runs require an accepted quality result under the pinned task rubric.",
    "load_mismatch": "The runs do not match the pinned solo load and fixed runtime settings.",
    "devices": "The baseline needs one active physical GPU shared with the comparison, which needs at least two.",
    "strategy": "A run lacks a declared split strategy, primary device or placement treatment.",
    "path_unavailable": "A documented direct-peer or host-staged path with endpoints, direction, payload and scope is missing for the active GPUs.",
    "same_run": "The baseline and comparison must be distinct runs.",
    "nonpositive": "Both decode throughputs must be positive.",
}
for side, description in (("baseline", "one-GPU baseline"), ("comparison", "multi-GPU comparison")):
    MESSAGES.update({
        f"{side}_withdrawn": f"The pinned {description} was withdrawn.",
        f"{side}_unavailable": f"The pinned {description} release is unavailable.",
        f"{side}_oom": f"The {description} ran out of memory.",
        f"{side}_failed": f"The {description} did not complete successfully.",
    })


def _shape(record, fields):
    return isinstance(record, dict) and record.keys() == set(fields.split())


def _metadata(row):
    try:
        data = json.loads(public_field(row, METADATA_FIELD) or "")
    except (ValueError, RecursionError):
        return None
    if _shape(data, "outcome binary_sha256 os_driver quality load settings devices primary_device strategy treatment transports"):
        return data
    return None


def _devices(data):
    devices = data["devices"]
    if not isinstance(devices, list) or not all(
        _shape(device, "id slot card placement")
        and all(plain_text(value) for value in device.values())
        and DEVICE_ID.fullmatch(device["id"])
        for device in devices
    ):
        return {}
    by_id = {device["id"]: device for device in devices}
    return by_id if len(by_id) == len({device["slot"] for device in devices}) == len(devices) else {}


def _link_properties(record):
    return record is None or (
        _shape(record, "generation width rate")
        and all(record[key] is None or (type(record[key]) is int and record[key] > 0)
                for key in ("generation", "width"))
        and (record["rate"] is None or plain_text(record["rate"]))
    )


def _positive_decimal(value):
    return isinstance(value, str) and DECIMAL.fullmatch(value) is not None and Decimal(value) > 0


def transport_matches_devices(network, devices):
    """Check documented transfer paths connect the active PCI devices."""
    if not isinstance(network, list) or not network:
        return False
    adjacent = {device: set() for device in devices}
    for link in network:
        if not (_shape(link, "from to path interconnect direction payload_bytes scope method rated negotiated bandwidth_gb_s")
                and all(plain_text(link[key]) for key in ("from", "to", "interconnect", "scope", "method"))
                and link["from"] in devices and link["to"] in devices and link["from"] != link["to"]
                and link["path"] in ("direct-peer", "host-staged") and link["direction"] in ("one-way", "bidirectional")
                and type(link["payload_bytes"]) is int and link["payload_bytes"] > 0
                and all(_link_properties(link[key]) for key in ("rated", "negotiated"))
                and (link["bandwidth_gb_s"] is None or _positive_decimal(link["bandwidth_gb_s"]))):
            return False
        adjacent[link["from"]].add(link["to"])
        adjacent[link["to"]].add(link["from"])
    visited = set()
    pending = [next(iter(devices))]
    while pending:
        device = pending.pop()
        if device not in visited:
            visited.add(device)
            pending.extend(adjacent[device] - visited)
    return visited == adjacent.keys()


def _ratio(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _run(snapshot, metadata):
    row = snapshot["row"]
    release_id = snapshot["release_id"]
    return {
        "release_id": release_id, "url": f"/releases/{release_id}/benchmark.html",
        "run_id": public_field(row, "run_id"), "devices": metadata["devices"],
        "active_count": len(metadata["devices"]), "primary_device": metadata["primary_device"],
        "strategy": metadata["strategy"], "treatment": metadata["treatment"],
        "transports": metadata["transports"],
        "metric": row["metric"],
    }


def scaling_report(store, pair):
    """Read both pinned snapshots together. Only eligible rows enter a ratio."""
    url = f"{ROUTE}/{'/'.join(pair)}" if pair else ROUTE
    report = {
        "schema_version": 1, "status": "unavailable", "url": url,
        "baseline": None, "comparison": None, "conditions": None, "speedup": None, "efficiency": None,
    }

    def excluded(reason):
        status = "unavailable" if not pair else "excluded"
        return {**report, "status": status, "reason": reason, "message": MESSAGES[reason]}

    if not pair:
        return excluded("unpinned")

    by_id = {snapshot["release_id"]: snapshot for snapshot in store.read_many(pair)}
    snapshots = [(side, by_id.get(release_id, {})) for side, release_id in zip(("baseline", "comparison"), pair)]
    for status in ("withdrawn", "unavailable"):
        for side, snapshot in snapshots:
            if snapshot.get("status", "unavailable") == status:
                return excluded(f"{side}_{status}")

    records = []
    for side, snapshot in snapshots:
        row = snapshot["row"]
        reason = exclusion_reason(PLAN, {"backend": "CUDA"}, row, METRICS)
        if reason and reason not in ("metric_mismatch", "insufficient_samples"):
            return excluded(reason)
        metadata = _metadata(row)
        if metadata is None:
            return excluded("metadata")
        if metadata["outcome"] != "success":
            return excluded(f"{side}_oom" if metadata["outcome"] == "oom" else f"{side}_failed")
        if reason:
            return excluded(reason)
        records.append((snapshot, row, metadata))

    (baseline_snapshot, baseline, one), (comparison_snapshot, comparison, many) = records
    if baseline["evidence_id"] == comparison["evidence_id"] or public_field(baseline, "run_id") == public_field(comparison, "run_id"):
        return excluded("same_run")
    host = baseline["hardware"]
    if host != comparison["hardware"]:
        return excluded("host_mismatch")
    if baseline["artifact"] != comparison["artifact"]:
        return excluded("artifact_mismatch")
    if not (isinstance(one["binary_sha256"], str) and DIGEST.fullmatch(one["binary_sha256"])
            and plain_text(one["os_driver"])
            and all(one[key] == many[key] for key in ("binary_sha256", "os_driver"))):
        return excluded("runtime_mismatch")
    for metadata in (one, many):
        quality = metadata["quality"]
        if not (_shape(quality, "protocol accepted") and quality["protocol"] == PLAN["rubric"]["id"]
                and quality["accepted"] is True):
            return excluded("quality_mismatch")
        if metadata["load"] != LOAD or not json_settings_match(metadata["settings"], SETTINGS):
            return excluded("load_mismatch")

    primary, parallel = _devices(one), _devices(many)
    if len(primary) != 1 or len(parallel) < 2 or not primary.keys() <= parallel.keys() or any(
        primary[device][key] != parallel[device][key] for device in primary for key in ("slot", "card")
    ):
        return excluded("devices")
    for metadata, devices, strategies in ((one, primary, ("single-device",)), (many, parallel, ("layer", "row"))):
        if not (metadata["strategy"] in strategies and plain_text(metadata["treatment"])
                and plain_text(metadata["primary_device"]) and metadata["primary_device"] in devices):
            return excluded("strategy")
    if one["transports"] != [] or not transport_matches_devices(many["transports"], parallel):
        return excluded("path_unavailable")

    values = [row["metric"]["value"] for row in (baseline, comparison)]
    if not all(_positive_decimal(value) for value in values):
        return excluded("nonpositive")
    value_one, value_many = map(Fraction, values)
    speedup = value_many / value_one
    return {
        **report, "status": "measured", "reason": None, "message": None,
        "baseline": _run(baseline_snapshot, one), "comparison": _run(comparison_snapshot, many),
        "conditions": {
            "host": host, "artifact": baseline["artifact"], "companion_sha256": PLAN["artifact"]["shards"][1]["sha256"],
            "tokenizer": PLAN["artifact"]["tokenizer"], "protocol": PLAN["protocol"]["id"],
            "phase": PLAN["protocol"]["phases"]["decode"], "warmup": PLAN["protocol"]["warmup"],
            "cache": PLAN["protocol"]["cache"], "load": LOAD, "quality_protocol": PLAN["rubric"]["id"],
            "quality_task": PLAN["rubric"]["task_id"], "runtime_revision": PLAN["runtime"]["revision"],
            "backend": "CUDA", "binary_sha256": one["binary_sha256"], "os_driver": one["os_driver"],
            "settings": SETTINGS,
        },
        "speedup": _ratio(speedup), "efficiency": _ratio(speedup / len(parallel)),
    }


def _display_ratio(ratio, percentage=False):
    numerator, denominator = (int(ratio[key]) for key in ("numerator", "denominator"))
    with localcontext() as context:
        context.prec = 40
        value = (Decimal(numerator) * (100 if percentage else 1)) / denominator
        rounded = f"{value:.4f}".rstrip("0").rstrip(".")
    unit = "%" if percentage else "×"
    return f"{rounded}{unit} (exact ratio {numerator}/{denominator})"


def _table(caption, columns, rows):
    return accessible_table(caption, columns, [
        "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>" for row in rows
    ])


def _link_label(link):
    if link is None:
        return "Unknown"
    return " · ".join((
        f"PCIe Gen {link['generation']}" if link["generation"] is not None else "Generation unknown",
        f"×{link['width']}" if link["width"] is not None else "Width unknown",
        link["rate"] or "Rate unknown",
    ))


def render_scaling(report):
    title = "Single-to-multi-GPU scaling"
    body = (f"<header><h1>{title}</h1><p><a href=\"{report['url']}.json\">Read JSON</a>"
            ' · <a href="https://fastest.ai/wiki/gpu-topology/">Explore GPU topology</a></p></header>')
    if report["status"] != "measured":
        return html_page(title, body + f'<p role="status">{escape(report["message"])}</p>')

    baseline, comparison = (report[key] for key in ("baseline", "comparison"))
    body += (
        f"<section><h2>1→{comparison['active_count']} active GPUs</h2>"
        f"<p>Speedup {_display_ratio(report['speedup'])} · "
        f"Efficiency {_display_ratio(report['efficiency'], percentage=True)}</p>"
        "<p>Speedup divides multi-GPU throughput by one-GPU throughput. "
        "Efficiency divides speedup by the number of active GPUs.</p><ul>"
    )
    for label, run in (("Baseline", baseline), ("Comparison", comparison)):
        metric = run["metric"]
        body += (f'<li><a href="{run["url"]}">{label} benchmark</a> · {escape(metric["value"])} tok/s'
                 f' · {metric["sample_count"]} samples · {escape(run["strategy"])} · {escape(run["treatment"])}</li>')
    body += "</ul>" + _table(
        "Active physical GPUs and placement", ("Run", "Physical slot", "PCI device", "Card", "Placement"), (
            (label, device["slot"], device["id"], device["card"],
             device["placement"] + (" · Primary" if device["id"] == run["primary_device"] else ""))
            for label, run in (("Baseline", baseline), ("Comparison", comparison)) for device in run["devices"]
        )
    ) + "</section>"
    body += "<section><h2>Observed transport</h2>" + _table(
        "Multi-GPU transfer paths", ("Endpoints", "Path", "Direction", "Payload (bytes)", "Scope and method",
                                    "Rated link properties", "Negotiated link properties", "Measured GB/s"), (
            (f"{link['from']} → {link['to']}" if link["direction"] == "one-way" else f"{link['from']} ↔ {link['to']}",
             link["path"] + " · " + link["interconnect"], link["direction"], link["payload_bytes"],
             link["scope"] + " · " + link["method"], _link_label(link["rated"]), _link_label(link["negotiated"]),
             link["bandwidth_gb_s"] or "Unknown")
            for link in comparison["transports"]
        )
    ) + "</section>"
    conditions = report["conditions"]
    body += "<section><h2>Matched conditions</h2>" + _table(
        "Pinned experiment controls", ("Control", "Value"), (
            ("Physical host", f"{conditions['host']['name']} · {conditions['host']['revision_id']} revision {conditions['host']['revision']}"),
            ("Artifact", f"{conditions['artifact']['repository']} · {conditions['artifact']['revision']} · "
                         f"{conditions['artifact']['quantization']}"),
            ("Shard SHA-256", conditions["artifact"]["sha256"] + " · " + conditions["companion_sha256"]),
            ("Tokenizer", conditions["tokenizer"]),
            ("Protocol and boundary", conditions["protocol"] + " · " + conditions["phase"]["boundary"]),
            ("Warmup", conditions["warmup"]),
            ("Cache", conditions["cache"]),
            ("Load", conditions["load"]),
            ("Quality", conditions["quality_protocol"] + " · " + conditions["quality_task"] + " · accepted on both runs"),
            ("Runtime", conditions["runtime_revision"] + " · " + conditions["backend"] + " · " + conditions["os_driver"]),
            ("Runtime binary SHA-256", conditions["binary_sha256"]),
        )
    ) + "</section>"
    return html_page(title, body)
