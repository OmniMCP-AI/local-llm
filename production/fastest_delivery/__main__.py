import argparse
import os
from pathlib import Path
from zipfile import BadZipFile

from fastest_release import ReleaseError, ReleaseNotFound, ReleaseStore

from . import shorts, x_post


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prepare and hand off approved editorial packages.")
    parser.add_argument("--channel", choices=("x", shorts.CHANNEL), default="x")
    commands = parser.add_subparsers(dest="command", required=True)
    draft = commands.add_parser("prepare", help="Build an upload-ready review package.")
    draft.add_argument("--draft", required=True, type=Path)
    draft.add_argument("--output-dir", required=True, type=Path)
    draft.add_argument("--font-file", type=Path, help="Font for a Shorts render or a Chinese shared CI CPU X chart.")
    draft.add_argument("--engagement-key", help="Use the supplied unique UUIDv4 for approved first-party pilot attribution.")
    approval = commands.add_parser("approve", help="Approve an exact package for one account and time window.")
    approval.add_argument("--package", required=True, type=Path)
    approval.add_argument("--approval-dir", required=True, type=Path)
    for flag in ("account", "payload-sha256", "window-start", "window-end", "approved-by", "rights-reference"):
        approval.add_argument(f"--{flag}", required=True)
    handoff = commands.add_parser("export", help="Recheck evidence and export the approved package.")
    handoff.add_argument("--package", required=True, type=Path)
    handoff.add_argument("--approval", required=True, type=Path)
    handoff.add_argument("--delivery-dir", required=True, type=Path)
    receipt = commands.add_parser("receipt", help="Record an operator-verified post URL for a handoff.")
    receipt.add_argument("--approval", required=True, type=Path)
    receipt.add_argument("--delivery-dir", required=True, type=Path)
    receipt.add_argument("--account", help="Observed YouTube channel ID for a Shorts receipt.")
    receipt.add_argument("--observed-engagement-url", help="Exact approved engagement link verified on this live post.")
    for flag in ("operator", "published-at", "url"):
        receipt.add_argument(f"--{flag}", required=True)
    corrections = commands.add_parser("corrections", help="Route withdrawn evidence for live YouTube Shorts.")
    corrections.add_argument("--delivery-dir", required=True, type=Path)
    for command in (draft, handoff, corrections):
        command.add_argument("--database-url", default=os.environ.get("FASTEST_EDITORIAL_DATABASE_URL"))
    args = parser.parse_args(argv)
    video = args.channel == shorts.CHANNEL
    if args.command in ("prepare", "export", "corrections") and not args.database_url:
        parser.error("set FASTEST_EDITORIAL_DATABASE_URL or pass --database-url")
    if args.command == "corrections" and not video:
        parser.error("corrections requires --channel youtube-shorts")
    if args.command == "receipt" and video and not args.account:
        parser.error("--account is required for a YouTube Shorts receipt")
    if args.command == "receipt" and args.account and not video:
        parser.error("--account requires --channel youtube-shorts")

    delivery = shorts if video else x_post
    try:
        if args.command == "prepare":
            path = delivery.prepare(ReleaseStore(args.database_url), args.draft, args.output_dir,
                                    font_file=args.font_file, engagement_key=args.engagement_key)
        elif args.command == "approve":
            path = delivery.approve(
                args.package, args.approval_dir, account=args.account, payload_sha256=args.payload_sha256,
                window_start=args.window_start, window_end=args.window_end, approved_by=args.approved_by,
                rights_reference=args.rights_reference,
            )
        elif args.command == "export":
            path = delivery.export(ReleaseStore(args.database_url), args.package, args.approval, args.delivery_dir)
        elif args.command == "corrections":
            for correction in shorts.corrections(ReleaseStore(args.database_url), args.delivery_dir):
                print(correction)
            return
        else:
            options = {"account": args.account} if video else {}
            path = delivery.record_receipt(
                args.approval, args.delivery_dir, url=args.url, published_at=args.published_at, operator=args.operator,
                observed_engagement_url=args.observed_engagement_url, **options,
            )
        print(path)
    except (OSError, ReleaseError, ReleaseNotFound, ValueError, KeyError, TypeError, BadZipFile) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
