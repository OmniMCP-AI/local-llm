import argparse
from datetime import date, datetime
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from zoneinfo import ZoneInfo

from fastest_release import ReleaseError, ReleaseStore

from . import COPY, EDITORIAL_TIMEZONE, generate_package


def _record(output_dir, package):
    directory = output_dir / package["editorial_date"]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{package['draft_revision']}.json"
    body = (json.dumps(package, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with NamedTemporaryFile(dir=directory, prefix=".draft-") as pending:
        pending.write(body)
        pending.flush()
        os.fsync(pending.fileno())
        try:
            # Link the completed file without replacing an earlier successful replay.
            os.link(pending.name, path)
        except FileExistsError:
            if path.read_bytes() != body:
                raise ValueError(f"existing draft bytes do not match revision {path.stem}") from None
    return path.resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Record a reviewable editorial draft from a public release.")
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_EDITORIAL_DATABASE_URL"))
    parser.add_argument("--public-origin", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--date", type=date.fromisoformat, help="Editorial date (YYYY-MM-DD). Defaults to Shanghai today.")
    parser.add_argument("--locale", choices=COPY, default="en")
    parser.add_argument("--release", help="Read a pinned release ID. Defaults to the current release.")
    args = parser.parse_args(argv)
    if not args.database_url:
        parser.error("set FASTEST_EDITORIAL_DATABASE_URL or pass --database-url")

    try:
        package = generate_package(
            ReleaseStore(args.database_url),
            editorial_date=args.date or datetime.now(ZoneInfo(EDITORIAL_TIMEZONE)).date(),
            locale=args.locale,
            public_origin=args.public_origin,
            release_id=args.release,
        )
        print(_record(args.output_dir, package))
    except (OSError, ReleaseError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
