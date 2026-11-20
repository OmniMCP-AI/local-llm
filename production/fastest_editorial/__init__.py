"""Evidence-linked editorial drafts from reviewed benchmark releases."""

from hashlib import sha256
import json
from urllib.parse import urlsplit

from fastest_release import ReleaseNotFound


EDITORIAL_TIMEZONE = "Asia/Shanghai"
COPY = {
    "en": (
        {"evergreen": "How fast did this configuration decode?", "correction": "Revised decode throughput benchmark"},
        "Across {samples} measurements, this setup reached a median decode throughput of {value} {unit}.",
    ),
    "zh-CN": (
        {"evergreen": "这套配置的解码吞吐量是多少？", "correction": "解码吞吐量基准测试已修订"},
        "该配置经 {samples} 次测量，解码吞吐量的中位数为 {value} {unit}。",
    ),
    "zh-TW": (
        {"evergreen": "這套配置的解碼吞吐量是多少？", "correction": "解碼吞吐量基準測試已修訂"},
        "該配置經 {samples} 次測量，解碼吞吐量的中位數為 {value} {unit}。",
    ),
}


def _public_origin(value):
    parts = urlsplit(value)
    if (
        parts.scheme != "https" or not parts.hostname or parts.username is not None
        or parts.path not in ("", "/") or any(character in value for character in ("?", "#", "\\"))
        or any(character.isspace() or not character.isprintable() for character in value)
    ):
        raise ValueError("public origin must be an HTTPS origin without credentials or a path")
    # Accessing the parsed port rejects malformed or out-of-range values.
    if parts.port == 0:
        raise ValueError("public origin port must be between 1 and 65535")
    return f"https://{parts.netloc}"


def _verified_release(store, snapshot):
    release_id = snapshot["release_id"]
    table = store.artifact(release_id, "table.json")
    manifest = store.artifact(release_id, "manifest.json")
    table_digest = sha256(table.encode("utf-8")).hexdigest()
    expected = {key: value for key, value in snapshot.items() if key != "row"}
    table_data = json.loads(table)
    manifest_data = json.loads(manifest)
    if any(
        data.get("release_id") == release_id and data.get("status") == "withdrawn"
        for data in (table_data, manifest_data)
    ):
        return None
    rows = table_data.pop("rows")
    artifacts = manifest_data.pop("artifacts")
    if (
        table_data != expected or manifest_data != expected
        or artifacts.get("table.json") != table_digest
        or rows != [snapshot["row"]]
    ):
        raise ValueError("release row, public table and manifest failed verification")
    return {
        "table_sha256": table_digest,
        "manifest_sha256": sha256(manifest.encode("utf-8")).hexdigest(),
    }


def _select_story(store, release_id, origin, copy):
    try:
        snapshot = store.read(release_id)
    except ReleaseNotFound:
        if release_id not in (None, "current"):
            return {
                "outcome": "no_story",
                "reason": "release_not_found",
                "release": None,
                "requested_release_id": release_id,
            }
        return {"outcome": "no_story", "reason": "no_current_release", "release": None}

    release = {key: snapshot[key] for key in ("release_id", "revision")}
    if snapshot["status"] == "withdrawn":
        return {"outcome": "no_story", "reason": "withdrawn_release", "release": release}

    if snapshot["status"] != "published":
        raise ValueError("release does not have a recognized publication status")
    row = snapshot["row"]
    rights = row["rights"]
    if rights["core"] != "allow" or rights["destination"] != "public-release":
        raise ValueError("release does not have public evidence rights")

    if row["kind"] == "synthetic":
        return {"outcome": "no_story", "reason": "synthetic_release", "release": release}

    metric = row["metric"]
    if (metric["id"], metric["version"], metric["statistic"], metric["unit"]) != (
        "decode-throughput", 1, "median", "tok/s"
    ):
        return {"outcome": "no_story", "reason": "unsupported_metric", "release": release}

    hashes = _verified_release(store, snapshot)
    if hashes is None:
        return {"outcome": "no_story", "reason": "withdrawn_release", "release": release}

    claim_id = f"{release['release_id']}:{row['evidence_id']}:{metric['id']}@{metric['version']}"
    base_url = f"{origin}/releases/{release['release_id']}"

    # The release revision belongs to this evidence ID. The global release
    # pointer might previously have pointed to a different observation.
    kind = "correction" if release["revision"] > 1 else "evergreen"
    headlines, body = copy
    return {
        "outcome": "story",
        "release": {**release, **hashes},
        "story": {
            "kind": kind,
            "evidence_destination": f"{base_url}/benchmark.html#citation",
            "claims": [{**metric, "claim_id": claim_id, "evidence_id": row["evidence_id"]}],
            "benchmark_conditions": {
                "hardware": row["hardware"],
                "artifact": row["artifact"],
                "workload": row["workload"],
            },
            "attribution": row["source"],
            "rights": rights,
            "media": [],
            "copy": {
                "headline": headlines[kind],
                "body": body.format(value=metric["value"], unit=metric["unit"], samples=metric["sample_count"]),
                "claim_refs": [claim_id],
            },
        },
    }


def generate_package(store, *, editorial_date, locale, public_origin, release_id=None):
    """Build the daily decision and its immutable review revision using the public release interface."""
    outcome = _select_story(store, release_id, _public_origin(public_origin), COPY[locale])
    package = {
        "schema_version": 1,
        "editorial_date": editorial_date.isoformat(),
        "editorial_timezone": EDITORIAL_TIMEZONE,
        "locale": locale,
        **outcome,
    }
    canonical = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**package, "draft_revision": sha256(canonical).hexdigest()}
