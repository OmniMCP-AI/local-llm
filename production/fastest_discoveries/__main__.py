import argparse
import json
from pathlib import Path
import sqlite3

from . import store


def main():
    parser = argparse.ArgumentParser(description="Review opt-in research discoveries")
    parser.add_argument("--db", required=True, type=Path, help="Private SQLite discovery history")
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser("submit", help="Record one verified opt-in submission")
    submit.add_argument("submission", type=Path)
    review = commands.add_parser("review", help="Record an immutable editorial choice")
    review.add_argument("source_url")
    review.add_argument("choice", choices=("approve", "withhold"))
    review.add_argument("--reviewer", required=True)
    review.add_argument("--reason", required=True)
    withdraw = commands.add_parser("withdraw", help="Record deletion or revoked permission")
    withdraw.add_argument("source_url")
    withdraw.add_argument("--reason", required=True, choices=store.WITHDRAWAL_REASONS)
    commands.add_parser("queue", help="Show the private editorial queue")
    commands.add_parser("public", help="Export approved links and withholding reasons")
    args = parser.parse_args()

    try:
        if args.command == "submit":
            with args.submission.open("rb") as submission:
                body = submission.read(store.MAX_SUBMISSION_BYTES + 1)
            result = store.submit(args.db, body)
        elif args.command == "review":
            result = store.review(args.db, args.source_url, args.choice, args.reviewer, args.reason)
        elif args.command == "withdraw":
            result = store.withdraw(args.db, args.source_url, args.reason)
        else:
            result = store.report(args.db, public=args.command == "public")
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Discoveries: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
