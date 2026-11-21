"""Bind reconciled pilot posts and export consented first-party engagement."""

import argparse
from datetime import date
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from zipfile import BadZipFile

from fastest_release.validation import plain_text

from .approval import instant, json_bytes
from .engagement import METRICS
from .engagement_link import LINK_PATH
from .engagement_store import EngagementStorageError, EngagementStore
from .pilot import TIMEZONE, load_pilot_records


SOURCE = "production/fastest_delivery/engagement-export.sql"


def _bindings(start, mode, drafts, deliveries):
    result = {}
    for entry in deliveries.values():
        if entry["status"] != "published" or "engagement_url" not in entry["receipt"]:
            continue
        receipt = entry["receipt"]
        draft = drafts[entry["approval"]["story_revision"]]
        _, key = LINK_PATH.fullmatch(urlsplit(receipt["engagement_url"]).path).groups()
        result[receipt["receipt_id"]] = {
            "attribution_key": key, "mode": mode, "start_date": start,
            "release_id": draft["release"]["release_id"], "manifest_sha256": draft["release"]["manifest_sha256"],
            "evidence_destination": draft["story"]["evidence_destination"],
            "receipt_id": receipt["receipt_id"], "post_url": receipt["url"], "published_at": receipt["published_at"],
        }
    return result


def _coverage(evidence, days, bindings, closed_before):
    if evidence is None:
        return SOURCE, {metric: [] for metric in METRICS}
    supplied = json.loads(evidence.read_bytes())
    if (
        not isinstance(supplied, dict) or supplied.keys() != set(METRICS) | {"reference"}
        or not plain_text(supplied["reference"])
    ):
        raise ValueError("coverage evidence requires both metrics and an independent source reference")
    for metric in METRICS:
        rows = supplied[metric]
        if not isinstance(rows, list):
            raise ValueError("coverage evidence must list verified receipt-days")
        for row in rows:
            if (
                not isinstance(row, dict) or row.keys() != {"date", "receipt_id"}
                or row["receipt_id"] not in bindings or row["date"] not in days
                or not bindings[row["receipt_id"]] <= row["date"] < closed_before
            ):
                raise ValueError("coverage evidence must identify a bound pilot receipt and an eligible date")
    reference = f"{SOURCE} with coverage evidence {supplied.pop('reference')}"
    return reference, supplied


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="Install the private PostgreSQL engagement schema.")
    bind = commands.add_parser("bind", help="Associate an exact tracked link with a reconciled receipt.")
    bind.add_argument("--receipt-id", required=True)
    export = commands.add_parser("export", help="Write the private JSON export consumed by the pilot audit.")
    export.add_argument("--output", required=True, type=Path)
    export.add_argument("--coverage-evidence", type=Path, help="Optional independently verified receipt-day coverage.")
    for command in (bind, export):
        command.add_argument("--start", required=True, type=date.fromisoformat)
        command.add_argument("--mode", required=True, choices=("live", "rehearsal"))
        for key in ("draft-dir", "x-approvals", "x-deliveries", "shorts-approvals", "shorts-deliveries"):
            command.add_argument(f"--{key}", type=Path, default=Path("editorial-drafts" if key == "draft-dir" else key))
    args = parser.parse_args(argv)
    service = os.environ.get("FASTEST_PILOT_ENGAGEMENT_DBSERVICE")
    if not service:
        parser.error("set FASTEST_PILOT_ENGAGEMENT_DBSERVICE to a configured libpq service")
    try:
        store = EngagementStore(service)
        if args.command == "migrate":
            store.migrate()
            return
        start = args.start.isoformat()
        days, drafts, deliveries = load_pilot_records(args.start, args.draft_dir, {
            "x": (args.x_approvals, args.x_deliveries),
            "youtube-shorts": (args.shorts_approvals, args.shorts_deliveries),
        })
        bindings = _bindings(start, args.mode, drafts, deliveries)
        if args.command == "bind":
            record = bindings.get(args.receipt_id)
            if record is None:
                raise ValueError("binding requires a reconciled pilot receipt with an exact approved engagement link")
            store.bind(record)
            return
        projection = store.export(start, args.mode)
        verified_dates = {}
        for record in projection["bindings"]:
            receipt_id = record["receipt_id"]
            expected = bindings.get(receipt_id)
            published = instant(record["published_at"])
            record["published_at"] = published.isoformat()
            if expected != record:
                raise ValueError("PostgreSQL attribution differs from the retained pilot receipt and evidence")
            verified_dates[receipt_id] = published.astimezone(TIMEZONE).date().isoformat()
        reference, coverage = _coverage(args.coverage_evidence, days, verified_dates, projection["closed_before_date"])
        result = {
            "schema_version": 1, "mode": args.mode, "start_date": start, "reference": reference,
            "coverage": coverage, "events": projection["events"],
        }
        with TemporaryDirectory(dir=args.output.parent, prefix=".engagement-") as staging:
            pending = Path(staging) / "export.json"
            descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as output:
                output.write(json_bytes(result))
            pending.replace(args.output)
    except (AttributeError, BadZipFile, EngagementStorageError, KeyError, OSError, TypeError, ValueError) as error:
        parser.exit(1, f"pilot engagement: {error}\n")


if __name__ == "__main__":
    main()
