import argparse
from functools import partial
import os
from pathlib import Path
import sqlite3
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, ReleaseStore

from . import feed, store
from .applicability import apply_notes
from .postgres import PostgresStore, WatchStorageError
from .render import render
from .retest import evidence_origin
from .review import review_snapshot


def main():
    parser = argparse.ArgumentParser(description="Watch official runtime release feeds")
    storage = parser.add_mutually_exclusive_group(required=True)
    storage.add_argument("--db", type=Path, help="Local SQLite history file")
    storage.add_argument("--postgres", action="store_true", help="PostgreSQL history using FASTEST_DATABASE_URL")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="Initialize PostgreSQL watcher storage")
    refresh = commands.add_parser("refresh")
    refresh.add_argument("--source", choices=(*feed.SOURCES, "all"), default=feed.RUNTIME,
                         help="Choose a runtime feed or all live feeds (default: llama.cpp)")
    refresh.add_argument("--fixture", type=Path)
    refresh.add_argument("--observed-at", help="UTC observation time for fixture replay")
    report = commands.add_parser("report")
    report.add_argument("--as-of", default=feed.utc_now(), help="UTC time for the freshness check")
    report.add_argument("--notes", type=Path, help="Authored applicability JSON")
    report.add_argument("--format", choices=("json", "html", "markdown"), default="json")
    report.add_argument("--evidence-origin", type=evidence_origin, help="HTTPS origin for approved benchmark links")
    review = commands.add_parser("review", help="Show exact tracked configurations due for release review")
    review.add_argument("--notes", type=Path, required=True, help="Authored applicability JSON")
    review.add_argument("--as-of", default=feed.utc_now(), help="UTC time for the freshness check")
    args = parser.parse_args()

    try:
        database_url = os.environ.get("FASTEST_DATABASE_URL")
        if args.postgres and not database_url:
            raise ValueError("Set FASTEST_DATABASE_URL for PostgreSQL watcher storage")
        postgres = PostgresStore(database_url) if args.postgres else None

        if args.command == "migrate":
            if postgres is None:
                parser.error("migrate requires --postgres")
            postgres.migrate()
        elif args.command in ("report", "review"):
            feed.timestamp(args.as_of)
            read_release = ReleaseStore(database_url).read if database_url else None
            history = postgres.snapshot(args.as_of) if postgres else store.snapshot(args.db, args.as_of)
            if args.command == "review":
                reviewed = apply_notes(history, args.notes, read_release, include_review_lines=True)
                print(render(review_snapshot(reviewed), "json"))
            else:
                report = apply_notes(history, args.notes, read_release, args.evidence_origin or "")
                print(render(report, args.format))
        else:
            record = postgres.record if postgres else partial(store.record, args.db)
            if bool(args.fixture) != bool(args.observed_at):
                raise ValueError("--fixture and --observed-at must be supplied together")
            if args.fixture and args.source == "all":
                raise ValueError("Fixture replay requires one source")
            mode = "fixture" if args.fixture else "live"
            token = os.environ.get("FASTEST_RELEASE_WATCH_GITHUB_TOKEN")
            runtime_ids = feed.SOURCES if args.source == "all" else (args.source,)
            failures = []
            for runtime_id in runtime_ids:
                observed_at = args.observed_at or feed.utc_now()
                feed.timestamp(observed_at)
                try:
                    if args.fixture:
                        with args.fixture.open("rb") as fixture:
                            body = fixture.read(feed.MAX_BYTES + 1)
                    else:
                        body = feed.fetch(token, runtime_id=runtime_id)
                    releases = feed.decode(body, runtime_id=runtime_id)
                except (OSError, ValueError) as error:
                    message = "Could not read the fixture" if isinstance(error, OSError) else str(error)
                    record(mode, observed_at, error=message, runtime_id=runtime_id)
                    failures.append(f"{runtime_id}: {message}")
                else:
                    record(mode, observed_at, releases, runtime_id=runtime_id)
            if failures:
                raise ValueError("\n".join(failures))
    except (ReleaseError, TimeoutExpired):
        parser.exit(1, "Release watch: Could not read the approved benchmark release\n")
    except (OSError, ValueError, sqlite3.Error, WatchStorageError) as error:
        parser.exit(1, f"Release watch: {error}\n")


if __name__ == "__main__":
    main()
