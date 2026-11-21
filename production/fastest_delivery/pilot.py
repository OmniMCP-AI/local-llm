"""Audit seven Asia/Shanghai editorial days from retained records."""

import argparse
from collections import defaultdict
from datetime import date, datetime, time, timedelta
import json
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from zoneinfo import ZoneInfo

from fastest_editorial import EDITORIAL_TIMEZONE
from fastest_release.validation import plain_text

from . import engagement, shorts, x_post
from .approval import decode_sealed, instant, json_bytes, read_sealed, require_window
from .engagement_link import verified_link
from .run_slot import postgres_scheduled_runs, scheduled_runs


TIMEZONE = ZoneInfo(EDITORIAL_TIMEZONE)
CHANNELS = {"x": x_post, "youtube-shorts": shorts}
METRICS = engagement.METRICS
EXERCISES = ("partial_failure", "replay", "withdrawal")
OUTSTANDING_CHANNELS = ("tiktok", "bilibili", "weibo", "wechat-official-account", "wechat-channels")


def load_days(start, draft_dir):
    days = {}
    for offset in range(7):
        day = (start + timedelta(days=offset)).isoformat()
        drafts = []
        for path in sorted((draft_dir / day).glob("*.json")):
            draft = read_sealed(path, "draft_revision")
            if (
                draft["schema_version"] != 1 or draft["editorial_date"] != day
                or draft["editorial_timezone"] != EDITORIAL_TIMEZONE
                or draft["draft_revision"] != path.stem or draft["outcome"] not in ("story", "no_story")
            ):
                raise ValueError(f"invalid retained draft: {path}")
            drafts.append({**draft, "record": str(path)})
        outcomes = {draft["outcome"] for draft in drafts}
        status = "story" if "story" in outcomes else "no_story" if outcomes else "missing"
        days[day] = {"date": day, "status": status, "drafts": drafts, "scheduled_runs": [], "deliveries": []}
    return days


def _load_handoff(path, adapter, entries, drafts, days):
    directory = path.parent
    receipt_path, correction_path = directory / "receipt.json", directory / "correction.json"
    if not path.exists():
        if receipt_path.exists() or correction_path.exists():
            raise ValueError(f"delivery record has no retained handoff: {directory}")
        return

    with ZipFile(path) as archive:
        embedded = decode_sealed(archive.read("approval.json"), "approval_id", str(path))
        package, files = adapter._load_package(archive.read)
    entry = entries.get(embedded["approval_id"])
    if entry is None or embedded != entry["approval"]:
        raise ValueError(f"handoff approval is absent from the approval ledger: {path}")
    draft = drafts[embedded["story_revision"]]
    if package["payload_sha256"] != embedded["payload_sha256"] or package["draft"] != draft:
        raise ValueError(f"handoff payload differs from the approved draft: {path}")
    for candidate in entries.values():
        candidate["status"] = "superseded"
    entry.update(status="awaiting_receipt", handoff=str(path))

    if not receipt_path.exists():
        if correction_path.exists():
            raise ValueError(f"correction has no retained receipt: {correction_path}")
        return
    receipt = read_sealed(receipt_path, "receipt_id")
    matching_fields = ("schema_version", "channel", "account", "approval_id", "delivery_id", "payload_sha256")
    if receipt["status"] != "published" or any(receipt[key] != embedded[key] for key in matching_fields):
        raise ValueError(f"receipt differs from its approval: {receipt_path}")
    verified_link(package, files[adapter.POST_COPY], receipt.get("engagement_url"))
    if adapter is shorts and (
        receipt["render_sha256"] != package["files"]["short.mp4"]
        or receipt["release_id"] != draft["release"]["release_id"]
        or receipt["claim_ids"] != [claim["claim_id"] for claim in draft["story"]["claims"]]
    ):
        raise ValueError(f"Shorts receipt differs from its approved evidence: {receipt_path}")
    when = instant(receipt["published_at"])
    require_window(embedded, when)
    status = "published" if when.astimezone(TIMEZONE).date().isoformat() in days else "published_outside_pilot"
    entry.update(status=status, receipt={**receipt, "record": str(receipt_path)})

    if correction_path.exists():
        correction = read_sealed(correction_path, "correction_id")
        receipt_fields = ("schema_version", "channel", "account", "delivery_id", "receipt_id", "release_id",
                          "claim_ids", "post_id", "url")
        if (
            adapter is not shorts or correction["status"] != "needs_correction"
            or correction["reason"] != "withdrawn_release"
            or any(correction[key] != receipt[key] for key in receipt_fields)
        ):
            raise ValueError(f"correction differs from its receipt: {correction_path}")
        entry["correction"] = {**correction, "record": str(correction_path)}


def _load_deliveries(days, drafts, directories):
    deliveries = {}
    posts = set()
    for channel, adapter in CHANNELS.items():
        approval_dir, delivery_dir = directories[channel]
        grouped = defaultdict(dict)
        for path in sorted(approval_dir.glob("*.json")):
            approval = adapter._read_approval(path)
            draft = drafts.get(approval["story_revision"])
            if draft is None:
                continue
            approval_id = approval["approval_id"]
            if draft["outcome"] != "story" or approval_id != path.stem:
                raise ValueError(f"approval does not identify a retained story: {path}")
            entry = {"approval": approval, "record": str(path), "status": "approved"}
            deliveries[approval_id] = grouped[approval["delivery_id"]][approval_id] = entry
            days[draft["editorial_date"]]["deliveries"].append(entry)
        for delivery_id, entries in grouped.items():
            _load_handoff(delivery_dir / delivery_id / adapter.ARCHIVE, adapter, entries, drafts, days)
            for entry in entries.values():
                if "receipt" in entry:
                    post = (channel, entry["receipt"]["post_id"])
                    if post in posts:
                        raise ValueError(f"post reused across multiple approvals: {entry['receipt']['url']}")
                    posts.add(post)
    return deliveries


def _reference(record):
    if not plain_text(record.get("reference")):
        raise ValueError("operator records require an evidence reference")


def _record_runs(runs, days, drafts, *, canonical):
    slots = set()
    for run in runs:
        _reference(run)
        scheduled_at = instant(run["scheduled_at"])
        day = scheduled_at.astimezone(TIMEZONE).date().isoformat()
        if day not in days or scheduled_at in slots:
            raise ValueError("scheduled runs must have distinct slots in the pilot dates")
        slots.add(scheduled_at)
        if canonical and run["status"] == "pending":
            days[day]["scheduled_runs"].append(run)
            continue
        if ("draft_revision" in run) == ("error" in run):
            raise ValueError("a scheduled run requires either a retained draft revision or an error")
        if "draft_revision" in run:
            draft = drafts.get(run["draft_revision"])
            if draft is None or draft["editorial_date"] != day:
                raise ValueError("scheduled run requires its retained draft from the same editorial day")
            if canonical and run["status"] != draft["outcome"]:
                raise ValueError("scheduled run outcome differs from its retained draft")
        if "error" in run and not plain_text(run["error"]):
            raise ValueError("a failed run requires its observed error")
        if not canonical and days[day]["status"] == "missing":
            days[day]["status"] = "failed"
        days[day]["scheduled_runs"].append(run)
    if canonical:
        for day in days.values():
            observed = {run["status"] for run in day["scheduled_runs"]}
            day["status"] = next(
                (status for status in ("story", "no_story", "failed", "pending") if status in observed), "missing",
            )


def _record_exercises(exercises, deliveries, drafts, days):
    corrections = {entry["correction"]["correction_id"]: entry for entry in deliveries.values() if "correction" in entry}
    for exercise in exercises:
        _reference(exercise)
        when = instant(exercise["occurred_at"]).astimezone(TIMEZONE)
        if when.date().isoformat() not in days:
            raise ValueError("exercises must occur during the pilot dates")
        kind = exercise["kind"]
        if kind == "partial_failure":
            success = deliveries[exercise["successful_approval_id"]]
            if (success["status"] != "published" or exercise["failed_channel"] not in CHANNELS
                    or exercise["failed_channel"] == success["approval"]["channel"]
                    or not plain_text(exercise["failure"])):
                raise ValueError("partial failure requires another channel's observed failure and a published receipt")
        elif kind == "replay":
            entry = deliveries[exercise["approval_id"]]
            if entry["status"] != "published" or entry["receipt"]["receipt_id"] != exercise["receipt_id"]:
                raise ValueError("replay must identify the original published receipt")
        elif kind == "withdrawal":
            queued = deliveries[exercise["queued_approval_id"]]
            live = corrections[exercise["correction_id"]]
            queued_release = drafts[queued["approval"]["story_revision"]]["release"]["release_id"]
            if (queued["status"] not in ("approved", "awaiting_receipt", "blocked_by_withdrawal")
                    or live["status"] != "published" or queued_release != live["correction"]["release_id"]):
                raise ValueError("withdrawal requires a blocked approval and a live correction for the same release")
            queued["status"] = "blocked_by_withdrawal"
        else:
            raise ValueError(f"unknown exercise: {kind}")


def _observed_count(record, field):
    _reference(record)
    count = record[field]
    if type(count) is not int or count < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return count


def _review_effort(reviews, deliveries, drafts):
    published = {approval_id for approval_id, entry in deliveries.items() if entry["status"] == "published"}
    reviewed = set()
    total = None
    for review in reviews:
        minutes = _observed_count(review, "minutes")
        if ("approval_id" in review) == ("draft_revision" in review):
            raise ValueError("a review must identify its approval or draft revision")
        if "approval_id" in review:
            approval_id = review["approval_id"]
            if approval_id not in deliveries:
                raise ValueError(f"review references an unretained approval: {approval_id}")
            reviewed.add(approval_id)
        elif review["draft_revision"] not in drafts:
            raise ValueError("review references an unretained draft")
        total = (total or 0) + minutes
    return {"recorded_minutes": total, "reviews": reviews, "unreported_approvals": sorted(published - reviewed)}


def _metrics(records):
    if set(records) - set(METRICS):
        raise ValueError("operator log contains an unknown metric")
    for entry in records.values():
        _observed_count(entry, "count")
    return {name: records.get(name) for name in METRICS}


def _readiness(records):
    if set(records) - set(OUTSTANDING_CHANNELS):
        raise ValueError("operator log contains an unknown outstanding channel")
    for entry in records.values():
        _reference(entry)
        if (entry["access"] not in ("available", "unavailable", "unknown")
                or entry["readiness"] not in ("ready", "blocked", "unknown")):
            raise ValueError("invalid access or readiness assessment")
    return {channel: records.get(channel, {"access": "unknown", "readiness": "unknown", "reference": None})
            for channel in OUTSTANDING_CHANNELS}


def _gaps(mode, days, channels, exercises, effort, metrics, readiness, *, canonical):
    gaps = [] if mode == "live" else ["live_evidence_required"]
    gaps.extend(
        f"scheduled_run_unreported:{day['date']}" for day in days.values()
        if not day["scheduled_runs"] or (canonical and any(run["status"] == "pending" for run in day["scheduled_runs"]))
    )
    gaps.extend(f"publication_unreported:{channel}" for channel, totals in channels.items()
                if not totals["published_in_window"])
    demonstrated = {exercise["kind"] for exercise in exercises}
    gaps.extend(f"exercise_unreported:{kind}" for kind in EXERCISES if kind not in demonstrated)
    gaps.extend(f"review_effort_unreported:{approval_id}" for approval_id in effort["unreported_approvals"])
    gaps.extend(f"metric_unreported:{name}" for name, record in metrics.items() if record is None)
    gaps.extend(f"readiness_unreported:{channel}" for channel, record in readiness.items()
                if "unknown" in (record["access"], record["readiness"]))
    return gaps


def load_operator_log(path, start):
    if path is None:
        return {"mode": "unreported"}
    record = json.loads(path.read_bytes())
    if record["schema_version"] != 1 or record["start_date"] != start.isoformat():
        raise ValueError("operator log must specify schema version 1 and the pilot start date")
    if record["mode"] not in ("live", "rehearsal"):
        raise ValueError("operator log mode must be live or rehearsal")
    return record


def load_pilot_records(start, draft_dir, directories):
    days = load_days(start, draft_dir)
    drafts = {draft["draft_revision"]: {key: value for key, value in draft.items() if key != "record"}
              for day in days.values() for draft in day["drafts"]}
    deliveries = _load_deliveries(days, drafts, directories)
    return days, drafts, deliveries


def audit(start, draft_dir, directories, operator_log=None, run_dir=None, engagement_export=None, *,
          slot_db_service=None):
    operator = load_operator_log(operator_log, start)
    canonical = slot_db_service is not None
    if canonical:
        if run_dir is not None or operator.get("runs"):
            raise ValueError("PostgreSQL slot history requires a single scheduler evidence source")
        first = datetime.combine(start, time.min, TIMEZONE)
        end = first + timedelta(days=7)
        runs, mode = postgres_scheduled_runs(slot_db_service, first, end, draft_dir)
    else:
        runs, mode = scheduled_runs(run_dir, ((start + timedelta(days=offset)).isoformat() for offset in range(7)))
    if mode and operator_log is not None and mode != operator["mode"]:
        raise ValueError("pilot operator log and scheduler records use different modes")
    days, drafts, deliveries = load_pilot_records(start, draft_dir, directories)
    _record_runs([*runs, *operator.get("runs", [])], days, drafts, canonical=canonical)
    exercises = operator.get("exercises", [])
    _record_exercises(exercises, deliveries, drafts, days)
    channels = {}
    for channel in CHANNELS:
        entries = [entry for entry in deliveries.values() if entry["approval"]["channel"] == channel]
        channels[channel] = {
            "approvals": len(entries),
            "published_in_window": sum(entry["status"] == "published" for entry in entries),
            "corrections": sum("correction" in entry for entry in entries),
            "delivery_outcomes": {
                status: sum(entry["status"] == status for entry in entries)
                for status in ("approved", "awaiting_receipt", "blocked_by_withdrawal", "superseded",
                               "published", "published_outside_pilot")
            },
        }
    effort = _review_effort(operator.get("reviews", []), deliveries, drafts)
    metrics = _metrics(operator.get("metrics", {}))
    readiness = _readiness(operator.get("readiness", {}))
    mode = mode or operator["mode"]
    engagement_evidence = None
    if engagement_export is not None:
        metrics, engagement_evidence = engagement.aggregate(engagement_export, days, TIMEZONE, mode, deliveries, drafts)
    gaps = _gaps(mode, days, channels, exercises, effort, metrics, readiness, canonical=canonical)
    if mode == "live" and engagement_evidence is None:
        gaps.append("engagement_evidence_unreported")
    return {
        "schema_version": 1,
        "status": "incomplete" if gaps else "complete",
        "gaps": gaps,
        "mode": mode,
        "timezone": EDITORIAL_TIMEZONE,
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=6)).isoformat(),
        "days": list(days.values()),
        "channels": channels,
        "exercises": exercises,
        "review_effort": effort,
        "metrics": metrics,
        "engagement_evidence": engagement_evidence,
        "outstanding_channels": readiness,
        "expansion_candidates": [channel for channel, record in readiness.items()
                                 if record["access"] == "available" and record["readiness"] == "ready"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, type=date.fromisoformat, help="First pilot date (YYYY-MM-DD).")
    for key in ("draft-dir", "x-approvals", "x-deliveries", "shorts-approvals", "shorts-deliveries", "operator-log",
                "engagement-export"):
        defaults = {"draft-dir": Path("editorial-drafts"), "operator-log": None, "engagement-export": None}
        parser.add_argument(f"--{key}", type=Path, default=defaults.get(key, Path(key)))
    retention = parser.add_mutually_exclusive_group()
    retention.add_argument("--run-dir", type=Path)
    retention.add_argument("--slot-db-service", help="Private libpq service name for PostgreSQL slot history.")
    args = parser.parse_args(argv)
    try:
        result = audit(args.start, args.draft_dir, {
            "x": (args.x_approvals, args.x_deliveries),
            "youtube-shorts": (args.shorts_approvals, args.shorts_deliveries),
        }, args.operator_log, args.run_dir, args.engagement_export, slot_db_service=args.slot_db_service)
    except (AttributeError, BadZipFile, OSError, KeyError, TypeError, ValueError, OverflowError) as error:
        parser.exit(1, f"invalid pilot evidence: {error}\n")
    print(json_bytes(result).decode(), end="")


if __name__ == "__main__":
    main()
