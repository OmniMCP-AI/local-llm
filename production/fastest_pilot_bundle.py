"""Deterministic file bundle for the planned and measured pilots."""

from hashlib import sha256
import json


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def digest(text):
    return sha256(text.encode("utf-8")).hexdigest()


def bundle_manifest(release_id, files):
    return json_text({"id": release_id, "files": {name: digest(content) for name, content in files.items()}})


def write_bundle(target, release_id, files):
    target.mkdir()
    for name, content in files.items():
        (target / name).write_bytes(content.encode("utf-8"))
    (target / "manifest.json").write_bytes(bundle_manifest(release_id, files).encode("utf-8"))
