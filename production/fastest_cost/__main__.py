"""Manage operator-reviewed tariff references for public display."""

import argparse
import os
from pathlib import Path
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, ReleaseStore

from .postgres import approve, withdraw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_DATABASE_URL"))
    commands = parser.add_subparsers(dest="command", required=True)
    publish = commands.add_parser("approve", help="Retain an explicit approval and print its immutable pin.")
    publish.add_argument("approval", type=Path)
    retire = commands.add_parser("withdraw", help="Withdraw an exact retained approval pin.")
    retire.add_argument("pin")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("Set FASTEST_DATABASE_URL or pass --database-url.")
    store = ReleaseStore(args.database_url)
    try:
        if args.command == "approve":
            print(approve(store, args.approval))
        else:
            withdraw(store, args.pin)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    except (ReleaseError, TimeoutExpired):
        parser.exit(1, "PostgreSQL tariff review failed. Check the connection, intake migration and operator permissions.\n")


if __name__ == "__main__":
    main()
