"""Run the regional price publisher."""

import argparse
import json
import os
from pathlib import Path
from subprocess import TimeoutExpired
import sys

from . import PriceStore
from .artifacts import ARTIFACT_NAMES


def main(argv=None):
    parser = argparse.ArgumentParser(description="Publish and read dated regional price cohorts.")
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_DATABASE_URL"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="Install the prices schema.")
    ingest = commands.add_parser("ingest", help="Append a reviewed source and collection bundle.")
    ingest.add_argument("bundle", type=Path)
    publish = commands.add_parser("publish", help="Pin a dated release from the reviewed database rows.")
    publish.add_argument("cohort_id")
    publish.add_argument("start")
    publish.add_argument("as_of")
    artifact = commands.add_parser("artifact", help="Print a rights-filtered release artifact.")
    artifact.add_argument("release_id")
    artifact.add_argument("name", choices=ARTIFACT_NAMES)
    withdraw = commands.add_parser("withdraw", help="Withdraw source approval for a cohort.")
    withdraw.add_argument("cohort_id")
    withdraw.add_argument("reason")
    args = parser.parse_args(argv)

    if not args.database_url:
        parser.error("set FASTEST_DATABASE_URL or pass --database-url")
    store = PriceStore(args.database_url)
    try:
        if args.command == "migrate":
            store.migrate()
        elif args.command == "ingest":
            print(store.ingest(json.loads(args.bundle.read_text(encoding="utf-8"))))
        elif args.command == "publish":
            print(store.publish(args.cohort_id, args.start, args.as_of))
        elif args.command == "artifact":
            sys.stdout.write(store.artifact(args.release_id, args.name))
        else:
            store.withdraw(args.cohort_id, args.reason)
    except (OSError, TimeoutExpired, ValueError) as error:
        parser.exit(1, f"{error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
