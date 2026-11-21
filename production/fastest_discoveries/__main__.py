import argparse
import json
import os
from pathlib import Path
import sqlite3

from . import postgres, store


def main():
    parser = argparse.ArgumentParser(description="Review private research discoveries")
    parser.add_argument("--db", type=Path, help="Use an explicit legacy SQLite discovery history")
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser("submit", help="Record one verified opt-in submission")
    submit.add_argument("submission", type=Path)
    youtube = commands.add_parser("intake-youtube-metadata", help="Queue the reviewed YouTube metadata snapshot")
    youtube.add_argument("sample", type=Path)
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
    commands.add_parser("migrate", help="Install the PostgreSQL discovery schema")
    legacy = commands.add_parser("import-sqlite", help="Copy a private legacy SQLite history to PostgreSQL")
    legacy.add_argument("history", type=Path)
    args = parser.parse_args()

    if args.db is not None and args.command in ("migrate", "import-sqlite", "intake-youtube-metadata"):
        parser.error(f"{args.command} requires a PostgreSQL connection")
    storage = store if args.db is not None else postgres
    database = args.db if args.db is not None else os.environ.get("FASTEST_DISCOVERIES_DATABASE_URL")
    if not database:
        parser.error("Set FASTEST_DISCOVERIES_DATABASE_URL.")

    try:
        if args.command == "submit":
            with args.submission.open("rb") as submission:
                body = submission.read(store.MAX_SUBMISSION_BYTES + 1)
            result = storage.submit(database, body)
        elif args.command == "intake-youtube-metadata":
            result = postgres.intake_youtube_metadata(database, args.sample)
        elif args.command == "review":
            result = storage.review(database, args.source_url, args.choice, args.reviewer, args.reason)
        elif args.command == "withdraw":
            result = storage.withdraw(database, args.source_url, args.reason)
        elif args.command == "migrate":
            result = postgres.migrate(database)
        elif args.command == "import-sqlite":
            result = postgres.import_sqlite(database, args.history)
        else:
            result = storage.report(database, public=args.command == "public")
    except (OSError, ValueError, sqlite3.Error, postgres.DiscoveryStorageError) as error:
        parser.exit(1, f"Discoveries: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
