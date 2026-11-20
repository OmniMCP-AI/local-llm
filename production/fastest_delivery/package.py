"""Shared evidence validation and atomic writes for review packages."""

from datetime import date
import errno
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from fastest_editorial import generate_package


def verify_story(store, draft):
    if draft["outcome"] != "story":
        raise ValueError("draft contains no approved evidence story")
    citation = urlsplit(draft["story"]["evidence_destination"])
    release_id = draft["release"]["release_id"]
    checked = generate_package(
        store,
        editorial_date=date.fromisoformat(draft["editorial_date"]),
        locale=draft["locale"],
        public_origin=f"{citation.scheme}://{citation.netloc}",
        release_id=release_id,
    )
    if checked["outcome"] != "story":
        raise ValueError(f"evidence is ineligible: {checked['reason']}")
    if checked != draft:
        raise ValueError("draft differs from the pinned public evidence")
    chart = store.artifact(release_id, "chart.json")
    data = json.loads(chart)
    manifest = store.artifact(release_id, "manifest.json")
    manifest_data = json.loads(manifest)
    if data["status"] == "withdrawn" or manifest_data["status"] == "withdrawn":
        raise ValueError("evidence is ineligible: withdrawn_release")
    if (
        sha256(manifest.encode()).hexdigest() != draft["release"]["manifest_sha256"]
        or sha256(chart.encode()).hexdigest() != manifest_data["artifacts"]["chart.json"]
    ):
        raise ValueError("public chart differs from the pinned evidence manifest")
    return data["scale"]["maximum"]


def story_lineage(store, release_id):
    """Report whether this exact evidence has been withdrawn or replaced."""
    pinned = store.read(release_id)
    if pinned["status"] == "withdrawn":
        return "withdrawn_release", None
    current = store.read_evidence(pinned["row"]["evidence_id"])
    if current["status"] == "withdrawn":
        return "withdrawn_release", None
    if current["release_id"] != release_id:
        return "superseded_release", current["release_id"]
    return None, None


def require_current_story(store, draft):
    reason, _ = story_lineage(store, draft["release"]["release_id"])
    if reason:
        raise ValueError(f"evidence is ineligible: {reason}")


def retain_package(output_dir, payload_sha256, files):
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / payload_sha256
    with TemporaryDirectory(dir=output_dir, prefix=".review-") as staging:
        pending = Path(staging) / "package"
        pending.mkdir()
        for name, body in files.items():
            (pending / name).write_bytes(body)
        try:
            pending.rename(path)
        except OSError as error:
            if error.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                raise
            if any((path / name).read_bytes() != body for name, body in files.items()):
                raise ValueError(f"existing candidate differs from {path.name}") from None
    return path.resolve()
