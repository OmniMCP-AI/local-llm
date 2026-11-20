import argparse
import os
from pathlib import Path
import sqlite3
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, ReleaseStore

from . import feed, store
from .applicability import apply_notes
from .render import render
from .retest import evidence_origin


def main():
    parser = argparse.ArgumentParser(description="Watch the official llama.cpp release feed")
    parser.add_argument("--db", type=Path, required=True, help="Local SQLite history file")
    commands = parser.add_subparsers(dest="command", required=True)
    refresh = commands.add_parser("refresh")
    refresh.add_argument("--fixture", type=Path)
    refresh.add_argument("--observed-at", help="UTC observation time for fixture replay")
    report = commands.add_parser("report")
    report.add_argument("--as-of", default=feed.utc_now(), help="UTC time for the freshness check")
    report.add_argument("--notes", type=Path, help="Authored applicability JSON")
    report.add_argument("--format", choices=("json", "html", "markdown"), default="json")
    report.add_argument("--evidence-origin", type=evidence_origin, help="HTTPS origin for approved benchmark links")
    args = parser.parse_args()

    try:
        if args.command == "report":
            feed.timestamp(args.as_of)
            database_url = os.environ.get("FASTEST_DATABASE_URL")
            read_release = ReleaseStore(database_url).read if database_url else None
            report = apply_notes(store.snapshot(args.db, args.as_of), args.notes, read_release, args.evidence_origin or "")
            print(render(report, args.format))
        else:
            if bool(args.fixture) != bool(args.observed_at):
                raise ValueError("--fixture and --observed-at must be supplied together")
            observed_at = args.observed_at or feed.utc_now()
            feed.timestamp(observed_at)
            mode = "fixture" if args.fixture else "live"
            try:
                if args.fixture:
                    with args.fixture.open("rb") as fixture:
                        body = fixture.read(feed.MAX_BYTES + 1)
                else:
                    body = feed.fetch(os.environ.get("FASTEST_RELEASE_WATCH_GITHUB_TOKEN"))
                releases = feed.decode(body)
            except (OSError, ValueError) as error:
                message = "Could not read the fixture" if isinstance(error, OSError) else str(error)
                store.record(args.db, mode, observed_at, error=message)
                raise
            store.record(args.db, mode, observed_at, releases)
    except (ReleaseError, TimeoutExpired):
        parser.exit(1, "Release watch: Could not read the approved benchmark release\n")
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Release watch: {error}\n")


if __name__ == "__main__":
    main()
