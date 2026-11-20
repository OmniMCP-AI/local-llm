import argparse
import os
from pathlib import Path
from zipfile import BadZipFile

from fastest_release import ReleaseError, ReleaseNotFound, ReleaseStore

from .x_post import approve, export, prepare, record_receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prepare and hand off an approved X editorial post.")
    commands = parser.add_subparsers(dest="command", required=True)
    draft = commands.add_parser("prepare", help="Build a candidate post, upload-ready chart, and alt text.")
    draft.add_argument("--draft", required=True, type=Path)
    draft.add_argument("--output-dir", required=True, type=Path)
    approval = commands.add_parser("approve", help="Approve an exact package for one X handle and time window.")
    approval.add_argument("--package", required=True, type=Path)
    approval.add_argument("--approval-dir", required=True, type=Path)
    for flag in ("account", "payload-sha256", "window-start", "window-end", "approved-by", "rights-reference"):
        approval.add_argument(f"--{flag}", required=True)
    handoff = commands.add_parser("export", help="Recheck evidence and export the approved X package.")
    handoff.add_argument("--package", required=True, type=Path)
    handoff.add_argument("--approval", required=True, type=Path)
    handoff.add_argument("--delivery-dir", required=True, type=Path)
    receipt = commands.add_parser("receipt", help="Record an operator-verified X post URL for a handoff.")
    receipt.add_argument("--approval", required=True, type=Path)
    receipt.add_argument("--delivery-dir", required=True, type=Path)
    for flag in ("operator", "published-at", "url"):
        receipt.add_argument(f"--{flag}", required=True)
    for command in (draft, handoff):
        command.add_argument("--database-url", default=os.environ.get("FASTEST_EDITORIAL_DATABASE_URL"))
    args = parser.parse_args(argv)
    if args.command in ("prepare", "export") and not args.database_url:
        parser.error("set FASTEST_EDITORIAL_DATABASE_URL or pass --database-url")
    try:
        if args.command == "prepare":
            path = prepare(ReleaseStore(args.database_url), args.draft, args.output_dir)
        elif args.command == "approve":
            path = approve(
                args.package, args.approval_dir, account=args.account, payload_sha256=args.payload_sha256,
                window_start=args.window_start, window_end=args.window_end, approved_by=args.approved_by,
                rights_reference=args.rights_reference,
            )
        elif args.command == "export":
            path = export(ReleaseStore(args.database_url), args.package, args.approval, args.delivery_dir)
        else:
            path = record_receipt(
                args.approval, args.delivery_dir, url=args.url, published_at=args.published_at, operator=args.operator,
            )
        print(path)
    except (OSError, ReleaseError, ReleaseNotFound, ValueError, KeyError, TypeError, BadZipFile) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
