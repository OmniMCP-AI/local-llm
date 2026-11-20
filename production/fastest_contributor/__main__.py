import argparse
import json
import os
from pathlib import Path
import sys

from fastest_release import ReleaseError, ReleaseNotFound

from . import ContributorStore
from .validation import MAX_BYTES, json_object


def read_input(path):
    if path == "-":
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    else:
        with Path(path).open("rb") as source:
            raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("JSON input exceeds 64 KiB")
    return raw.decode("utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Receive and review a private contributor benchmark submission.")
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_DATABASE_URL"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="Install private contributor intake after the release schema has been installed.")
    submit = commands.add_parser("submit", help="Import one JSON submission and return its shareable receipt.")
    submit.add_argument("file", help="Submission JSON file or - for stdin")
    status = commands.add_parser("status", help="Print the shareable status for a receipt.")
    status.add_argument("receipt")
    inspect = commands.add_parser("inspect", help="Print one private submission version and editorial review.")
    inspect.add_argument("receipt")
    inspect.add_argument("version", type=int)
    review = commands.add_parser("review", help="Record an explicit editorial decision for an exact version.")
    review.add_argument("receipt")
    review.add_argument("version", type=int)
    review.add_argument("file", help="Editorial decision JSON file or - for stdin")
    args = parser.parse_args(argv)
    if not args.database_url:
        parser.error("set FASTEST_DATABASE_URL or pass --database-url")
    store = ContributorStore(args.database_url)
    try:
        if args.command == "migrate":
            store.migrate()
            return 0
        if args.command == "submit":
            output = store.submit(read_input(args.file))
        elif args.command == "status":
            output = store.status(args.receipt)
        elif args.command == "inspect":
            output = store.inspect(args.receipt, args.version)
        else:
            output = store.review(args.receipt, args.version, json_object(read_input(args.file)))
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except (OSError, ValueError, ReleaseError, ReleaseNotFound) as error:
        parser.exit(1, f"{error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
