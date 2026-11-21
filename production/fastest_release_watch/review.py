from hashlib import sha256

from .feed import json_text


OPEN_STATUSES = {"suggested", "unresolved"}


def release_reference(release):
    return {key: release[key] for key in ("revision_id", "tag", "source_url", "first_seen_at", "status")}


def observation(release, note):
    return {
        "release": release_reference(release),
        "note_id": note["id"],
        "status": note["status"],
        "source_url": note["source_url"],
        "configuration": note["configuration"],
    }


def review_snapshot(report):
    positions = {}
    current = {}
    tracked = {}
    for position, release in enumerate(report["releases"]):
        revision = release["revision_id"]
        positions[revision] = position
        runtime_id = release["runtime_id"]
        prerelease = release["prerelease"]
        if release["status"] in {"current", "prerelease"}:
            current.setdefault((runtime_id, prerelease), release)
        for note in release["applicability"]:
            if "review_line" not in note:
                continue
            # A review may advance the runtime build. Every other condition stays exact.
            config = {key: value for key, value in note["configuration"].items() if key != "build_sha"}
            key = (runtime_id, prerelease, note["card_id"], note["review_line"], json_text(config))
            observations = tracked.setdefault(key, {})
            if revision in observations:
                raise ValueError("More than one applicability note for the same tracked line and revision")
            observations[revision] = observation(release, note)

    reviews = []
    sources = report["sources"]
    for key, observations in sorted(tracked.items()):
        runtime_id, prerelease, card_id, line, _ = key
        target = current.get((runtime_id, prerelease))
        if target is None:
            continue
        revision = target["revision_id"]
        # History is ordered newest first. An assessment of the target cannot establish its own prior.
        prior = next((record for seen, record in observations.items() if positions[seen] > positions[revision]), None)
        if prior is None:
            continue
        assessment = observations.get(revision)
        status = "review_due"
        if assessment and assessment["status"] not in OPEN_STATUSES:
            status = "unsupported" if assessment["status"] == "unsupported" else "assessed"
        source = sources[runtime_id]
        reviews.append({
            "review_id": sha256(json_text([key, revision]).encode("utf-8")).hexdigest(),
            "review_line": line,
            "runtime_id": runtime_id,
            "card_id": card_id,
            "target": release_reference(target),
            "prior": prior,
            "assessment": assessment,
            "status": status,
            "actionable": status == "review_due" and not source["stale"] and source["last_error"] is None,
        })
    return {"schema": "fastest.ai/runtime-release-review/v1", "sources": sources, "reviews": reviews}
