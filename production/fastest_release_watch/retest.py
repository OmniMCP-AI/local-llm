import json
from urllib.parse import urlsplit
from uuid import UUID

from fastest_release import ReleaseNotFound

from .feed import RUNTIME


def approved_links(read_release, note, pair, origin):
    if not isinstance(pair, dict) or set(pair) != {"baseline_release_id", "tuned_release_id"}:
        raise ValueError("A retest needs baseline and tuned release IDs")
    baseline_id, tuned_id = (release_id(pair[key]) for key in ("baseline_release_id", "tuned_release_id"))
    baseline, tuned = (measured_row(read_release, identifier) for identifier in (baseline_id, tuned_id))
    config = note["configuration"]
    expected = {
        "card_id": note["card_id"],
        "configuration_id": config["id"],
        "os_version": config["os"],
        "driver_version": config["driver"],
        "backend": config["backend"],
        "runtime_id": RUNTIME,
        "runtime_build": config["build_sha"],
    }
    for row in (baseline, tuned):
        if any(known(row, key) != value for key, value in expected.items()):
            raise ValueError("Retest conditions must match the authored configuration and be matched across runs")
    metric = ("id", "version", "unit", "statistic", "boundary")
    artifact = tuned["artifact"]
    model = f"{artifact['repository']}@{artifact['revision']}/{artifact['path']}"
    tuned_flags = flags(tuned)
    if (
        baseline["evidence_id"] == tuned["evidence_id"]
        or any(baseline[key] != tuned[key] for key in ("hardware", "artifact", "workload"))
        or any(baseline["metric"][key] != tuned["metric"][key] for key in metric)
        or tuned["workload"]["id"] != config["workload_id"]
        or tuned["workload"]["version"] != config["workload_version"]
        or config["model_artifact"] != model
        or tuned_flags != config["flags"]
        or flags(baseline) == tuned_flags
    ):
        raise ValueError("Retest requires distinct observations with matched hardware, model, workload and metric")
    return {
        "baseline_url": f"{origin}/releases/{baseline_id}/benchmark.html",
        "tuned_url": f"{origin}/releases/{tuned_id}/benchmark.html",
    }


def release_id(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError("Retest release IDs must be canonical UUIDs")
    return value


def measured_row(read_release, identifier):
    try:
        release = read_release(identifier)
    except ReleaseNotFound as error:
        raise ValueError("Retest must cite a published measured release") from error
    if release["status"] != "published" or release["row"]["kind"] != "measured":
        raise ValueError("Retest must cite a published measured release")
    return release["row"]


def known(row, key):
    field = row["fields"].get(key, {})
    return field.get("value") if field.get("status") == "known" else None


def flags(row):
    raw = known(row, "runtime_flags")
    parsed = json.loads(raw) if raw is not None else None
    if not isinstance(parsed, list) or any(not isinstance(flag, str) for flag in parsed):
        raise ValueError("Retest requires public runtime flags as a JSON list of arguments")
    return parsed


def evidence_origin(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
        or parsed.path not in ("", "/") or parsed.query or parsed.fragment
        or any(character.isspace() for character in value) or "\\" in value
    ):
        raise ValueError("Evidence origin must be an HTTPS origin")
    return f"https://{parsed.netloc}"
