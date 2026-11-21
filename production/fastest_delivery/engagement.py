"""Aggregate a retained first-party engagement export for the distribution pilot."""

from hashlib import sha256
import json
from uuid import UUID

from fastest_release.validation import plain_text

from .approval import instant


EVENTS = {
    "evidence_arrival": ("qualified_evidence_visits", "visit_id"),
    "comparison_result": ("completed_comparisons", "comparison_id"),
}
METRICS = tuple(metric for metric, _ in EVENTS.values())
EXPORT_FIELDS = {"schema_version", "mode", "start_date", "reference", "coverage", "events"}
EVENT_FIELDS = {"kind", "occurred_at", "receipt_id", "post_url"}


def _unique_object(pairs):
    record = dict(pairs)
    if len(record) != len(pairs):
        raise ValueError("engagement export has a duplicate JSON field")
    return record


def _object(record, fields, name):
    if not isinstance(record, dict) or record.keys() != fields:
        raise ValueError(f"{name} has missing or unexpected fields")


def _list(records, name):
    if not isinstance(records, list):
        raise ValueError(f"{name} must be an array")
    return records


def _receipt_days(coverage):
    return [{"date": day, "receipt_id": receipt_id} for day, receipt_id in sorted(coverage)]


def aggregate(path, days, timezone, mode, deliveries, drafts):
    """Return counts only for metrics with complete coverage of eligible receipts."""
    raw = path.read_bytes()
    export = json.loads(raw, object_pairs_hook=_unique_object)
    _object(export, EXPORT_FIELDS, "engagement export")
    if (
        type(export["schema_version"]) is not int or export["schema_version"] != 1
        or export["start_date"] != min(days) or export["mode"] not in ("live", "rehearsal")
        or (mode != "unreported" and export["mode"] != mode)
        or not plain_text(export["reference"])
    ):
        raise ValueError("engagement export requires version 1, the pilot start date, matching mode and a source reference")

    receipts = {
        entry["receipt"]["receipt_id"]: (
            entry["receipt"]["url"], instant(entry["receipt"]["published_at"]),
            drafts[entry["approval"]["story_revision"]]["story"]["evidence_destination"],
        )
        for entry in deliveries.values() if entry["status"] == "published"
    }
    expected = {
        (day, receipt_id) for receipt_id, (_, published, _) in receipts.items()
        for day in days if day >= published.astimezone(timezone).date().isoformat()
    }

    covered = {}
    _object(export["coverage"], set(METRICS), "engagement coverage")
    for metric, rows in export["coverage"].items():
        covered[metric] = set()
        for row in _list(rows, "engagement coverage rows"):
            _object(row, {"date", "receipt_id"}, "engagement coverage row")
            pair = (row["date"], row["receipt_id"])
            if pair not in expected:
                raise ValueError("engagement coverage must identify an eligible receipt and Shanghai date")
            covered[metric].add(pair)

    observed = {metric: {} for metric in METRICS}
    for event in _list(export["events"], "engagement events"):
        if not isinstance(event, dict) or event.get("kind") not in EVENTS:
            raise ValueError("engagement event must be an evidence arrival or a completed comparison result")
        kind = event["kind"]
        metric, id_field = EVENTS[kind]
        fields = EVENT_FIELDS | {id_field}
        if kind == "evidence_arrival":
            fields.add("evidence_destination")
        _object(event, fields, "engagement event")
        identifier = event[id_field]
        if not isinstance(identifier, str):
            raise ValueError(f"{id_field} must be a canonical random UUID")
        event_id = UUID(identifier)
        if event_id.version != 4 or str(event_id) != identifier:
            raise ValueError(f"{id_field} must be a canonical random UUID")
        receipt_id = event["receipt_id"]
        if receipt_id not in receipts or event["post_url"] != receipts[receipt_id][0]:
            raise ValueError("engagement event must match an exact published pilot receipt and post URL")
        _, published, destination = receipts[receipt_id]
        when = instant(event["occurred_at"])
        if when < published or when.astimezone(timezone).date().isoformat() not in days:
            raise ValueError("engagement event must occur in the Shanghai pilot dates after publication")
        if kind == "evidence_arrival" and event["evidence_destination"] != destination:
            raise ValueError("engagement event must reach the exact pinned evidence destination")
        entry = (receipt_id, when)
        if observed[metric].setdefault(event_id, entry) != entry:
            raise ValueError(f"engagement export has conflicting events for one {id_field}")

    reference = export["reference"]
    metrics = {}
    coverage = {}
    for metric in METRICS:
        missing = expected - covered[metric]
        count = len(observed[metric])
        metrics[metric] = {"count": count, "reference": reference} if expected and not missing else None
        coverage[metric] = {
            "covered_receipt_days": _receipt_days(covered[metric]),
            "missing_receipt_days": _receipt_days(missing),
            "observed_count": count,
        }
    return metrics, {
        "record": str(path), "sha256": sha256(raw).hexdigest(), "reference": reference,
        "mode": export["mode"], "coverage": coverage,
    }
