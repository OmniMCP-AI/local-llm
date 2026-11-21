import argparse
import json
import os
from pathlib import Path

from fastest_pilot_bundle import json_text, write_bundle

from . import calculate, postgres
from .render import render


def main():
    parser = argparse.ArgumentParser(description="Compare local, cloud and hybrid plans for one image team.")
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_DATABASE_URL"),
                        help="Operator PostgreSQL connection for scenario storage.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="Create private PostgreSQL scenario storage.")
    ingest = commands.add_parser("ingest-approved", help="Retain an approved, consented aggregate scenario.")
    ingest.add_argument("scenario", type=Path)
    withdraw = commands.add_parser("withdraw", help="Disable future builds of an approved scenario pin.")
    withdraw.add_argument("pin")
    build = commands.add_parser("build", help="Write a new comparison directory.")
    build.add_argument("output", type=Path)
    inputs = build.add_mutually_exclusive_group()
    inputs.add_argument("--scenario", type=Path, help="A reviewed and publishable aggregate scenario JSON file.")
    inputs.add_argument("--illustrative", action="store_true", help="Use the explicitly fictional example.")
    inputs.add_argument("--scenario-pin", help="An exact PostgreSQL scenario SHA-256.")
    args = parser.parse_args()
    if (args.command != "build" or args.scenario_pin is not None) and not args.database_url:
        parser.error("Set FASTEST_DATABASE_URL or pass --database-url for PostgreSQL commands.")
    try:
        if args.command == "migrate":
            postgres.migrate(args.database_url)
            return
        if args.command == "ingest-approved":
            print(postgres.ingest_approved(args.database_url, args.scenario))
            return
        if args.command == "withdraw":
            postgres.withdraw(args.database_url, args.pin)
            return
        if args.scenario_pin is not None:
            data = postgres.read_scenario(args.database_url, args.scenario_pin)
        else:
            path = Path(__file__).with_name("illustrative.json") if args.illustrative else args.scenario
            data = json.loads(path.read_text(encoding="utf-8")) if path else None
            if path and (not isinstance(data, dict) or data.get("kind") != ("illustrative" if args.illustrative else "consented")):
                raise ValueError("Use --scenario for consented inputs or --illustrative for the fictional example.")
        result = calculate(data)
        markdown, html = render(result)
        write_bundle(args.output, result["revision"], {
            "image-team.json": json_text(result), "image-team.md": markdown, "image-team.html": html,
        })
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
