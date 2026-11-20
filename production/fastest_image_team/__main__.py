import argparse
import json
from pathlib import Path

from fastest_pilot_bundle import json_text, write_bundle

from . import calculate
from .render import render


def main():
    parser = argparse.ArgumentParser(description="Compare local, cloud and hybrid plans for one image team.")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="Write a new comparison directory.")
    build.add_argument("output", type=Path)
    inputs = build.add_mutually_exclusive_group()
    inputs.add_argument("--scenario", type=Path, help="A reviewed and publishable aggregate scenario JSON file.")
    inputs.add_argument("--illustrative", action="store_true", help="Use the explicitly fictional example.")
    args = parser.parse_args()
    path = Path(__file__).with_name("illustrative.json") if args.illustrative else args.scenario
    try:
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
