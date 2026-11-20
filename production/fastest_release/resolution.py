"""Publish a reviewed benchmark correction or withdraw its exact public artifacts."""
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from uuid import UUID

from . import ReleaseError, ReleaseStore, _sql_text
from .artifacts import build_artifacts
from .validation import plain_text, validate


def _artifact_hashes(snapshots):
    return {
        f"/releases/{snapshot['release_id']}/{name}": sha256(body.encode("utf-8")).hexdigest()
        for snapshot in snapshots
        for name, body in build_artifacts(snapshot).items()
    }


def resolve_benchmark(store, request):
    action = request.get("action")
    if action not in {"correct", "withdraw"} or not plain_text(request.get("sourceLocator")):
        raise ValueError("Specify a reviewed benchmark resolution and source locator")
    decision = {
        "action": action,
        "evidenceId": str(UUID(request["evidenceId"])),
        "previousRelease": str(UUID(request["previousRelease"])),
        "sourceLocator": request["sourceLocator"],
    }
    if action == "correct":
        correction = request.get("correction")
        validate(correction)
        decision["correction"] = correction
    payload = _sql_text(json.dumps(decision, ensure_ascii=False))
    result = json.loads(store._query(f"SELECT fastest_release.resolve_benchmark({payload}::jsonb);"))
    before = _artifact_hashes(result["before"])
    after = _artifact_hashes(result["after"])
    return {
        "release": result["release"],
        "changes": [
            {"path": path, "before": before.get(path), "after": after.get(path)}
            for path in sorted(before.keys() | after.keys())
            if before.get(path) != after.get(path)
        ],
    }


def main():
    try:
        database = os.environ.get("FASTEST_DATABASE_URL")
        if not database or len(sys.argv) != 2:
            raise ValueError("Set FASTEST_DATABASE_URL and supply a reviewed benchmark resolution JSON file")
        request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(json.dumps(resolve_benchmark(ReleaseStore(database), request)))
    except (KeyError, OSError, ValueError, ReleaseError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
