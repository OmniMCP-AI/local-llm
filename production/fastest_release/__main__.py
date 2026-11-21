import argparse
import json
import os
import re
from pathlib import Path
import sys

from fastest_delivery.engagement_store import EngagementStore
from fastest_fit import FitEngineError
from fastest_goals import GoalService
from fastest_prices import PriceStore
from fastest_release_watch.postgres import PostgresStore
from fastest_text.latency_review import read_eligible_latency

from . import ReleaseError, ReleaseNotFound, ReleaseStore
from .http import CONTENT_TYPES, make_server
from .research import SEED_ROOT, import_seed, read_seed


def main(argv=None):
    parser = argparse.ArgumentParser(description="Publish and read a reviewed PostgreSQL benchmark release.")
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_DATABASE_URL"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="Install the release schema.")
    publish = commands.add_parser("publish", help="Publish a reviewed observation JSON file.")
    publish.add_argument("observation", type=Path)
    publish_agent_task = commands.add_parser("publish-agent-task", help="Publish a reviewed agent-task report in PostgreSQL.")
    publish_agent_task.add_argument("--record", type=Path, action="append", required=True)
    publish_agent_task.add_argument("--expires-at", help="Optional UTC expiry for the reviewed report.")
    read = commands.add_parser("read", help="Read the permitted release snapshot.")
    read.add_argument("release_id", nargs="?", default="current")
    artifact = commands.add_parser("artifact", help="Print a rights-filtered release artifact.")
    artifact.add_argument("release_id")
    artifact.add_argument("name", choices=CONTENT_TYPES)
    withdraw = commands.add_parser("withdraw", help="Quarantine an evidence ID across all releases.")
    withdraw.add_argument("evidence_id")
    withdraw.add_argument("reason")
    serve = commands.add_parser("serve", help="Serve the read-only release routes.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    serve.add_argument("--trusted-host", action="append", default=[], help="Allowed HTTP Host header, including its port if present.")
    serve.add_argument("--fit-engine", type=Path, help="Path to the pinned fit executable built by fastest_fit.")
    serve.add_argument("--profile-release", action="append", default=[], help="Include a reviewed observation release UUID in the profile comparison.")
    serve.add_argument("--profile-archive", action="append", default=[], metavar="UUID,UUID,...",
                       help="Keep a prior profile release available from its comma-separated observation release UUIDs.")
    serve.add_argument("--scaling-pair", nargs=2, default=(), metavar=("BASELINE", "COMPARISON"),
                       help="Compare one reviewed one-GPU release to one reviewed multi-GPU release.")
    serve.add_argument("--goal-cohort", type=Path, action="append", default=[],
                       help="Keep a reviewed goals cohort available. The last manifest becomes current.")
    serve.add_argument("--cost-scenario", type=Path, help="Read a reviewed cost scenario for the public evidence view.")
    tariffs = serve.add_mutually_exclusive_group()
    tariffs.add_argument("--cost-tariff-references", type=Path,
                         help="Show reviewed tariff references from a file in Costs.")
    tariffs.add_argument("--cost-tariff-references-pin",
                         help="Show the active tariff references for this exact PostgreSQL approval SHA-256.")
    serve.add_argument("--contributor-receipts", action="store_true",
                       help="Serve private contributor receipt links using the configured release reader.")
    serve.add_argument("--goal-rights", type=Path, help="Read this live rights file on each measured goal request.")
    serve.add_argument("--agent-task-release",
                       help="Use this pinned PostgreSQL agent-task report as the default and enable public API discovery.")
    serve.add_argument("--runtime-release-watch", action="store_true",
                       help="Serve retained runtime release histories from PostgreSQL.")
    watch_notes = serve.add_mutually_exclusive_group()
    watch_notes.add_argument("--runtime-release-watch-notes", type=Path,
                             help="Read reviewed runtime applicability JSON on each release watch request.")
    watch_notes.add_argument("--runtime-release-watch-notes-revision",
                             help="Read this pinned PostgreSQL applicability revision on each watch request.")
    serve.add_argument("--pilot-engagement-origin",
                       help="Enable private pilot engagement on this exact HTTPS origin.")
    serve.add_argument("--pilot-engagement-mode", choices=("live", "rehearsal"), default="live",
                       help="Use only engagement bindings in this mode.")
    research_import = commands.add_parser("research-import", help="Reconcile the private video research seed.")
    research_import.add_argument("--seed-dir", type=Path, default=SEED_ROOT)
    research_read = commands.add_parser("research-read", help="Read a private research manifest or its records.")
    research_read.add_argument("seed_id")
    research_read.add_argument("kind", nargs="?")
    research_read.add_argument("identifier", nargs="?")
    args = parser.parse_args(argv)

    fit_engine = args.fit_engine if args.command == "serve" else None
    if not args.database_url and args.command != "serve":
        parser.error("set FASTEST_DATABASE_URL or pass --database-url")
    store = ReleaseStore(args.database_url) if args.database_url else None
    if args.command == "serve":
        if args.runtime_release_watch and store is None:
            parser.error("--runtime-release-watch requires FASTEST_DATABASE_URL or --database-url")
        if args.runtime_release_watch_notes is not None and not args.runtime_release_watch:
            parser.error("--runtime-release-watch-notes requires --runtime-release-watch")
        if args.runtime_release_watch_notes_revision is not None and not args.runtime_release_watch:
            parser.error("--runtime-release-watch-notes-revision requires --runtime-release-watch")
    if args.command == "serve" and args.pilot_engagement_origin:
        service = os.environ.get("FASTEST_PILOT_ENGAGEMENT_DBSERVICE")
        key = os.environ.get("FASTEST_PILOT_ENGAGEMENT_SIGNING_KEY", "")
        if store is None or not service or not re.fullmatch(r"[a-f0-9]{64}", key):
            parser.error("pilot engagement requires a release reader, an engagement libpq service, and a 32-byte hex signing key")
    try:
        if args.command == "migrate":
            store.migrate()
        elif args.command == "publish":
            print(store.publish(json.loads(args.observation.read_text(encoding="utf-8"))))
        elif args.command == "publish-agent-task":
            records = [json.loads(path.read_text(encoding="utf-8")) for path in args.record]
            print(store.publish_agent_task(records, args.expires_at))
        elif args.command == "read":
            print(json.dumps(store.read(args.release_id), ensure_ascii=False, indent=2))
        elif args.command == "artifact":
            sys.stdout.write(store.artifact(args.release_id, args.name))
        elif args.command == "withdraw":
            store.withdraw(args.evidence_id, args.reason)
        elif args.command == "research-import":
            print(json.dumps(import_seed(store, args.seed_dir), ensure_ascii=False, indent=2))
        elif args.command == "research-read":
            print(json.dumps(read_seed(store, args.seed_id, args.kind, args.identifier), ensure_ascii=False, indent=2))
        elif args.command == "serve":
            runtime_watch = PostgresStore(args.database_url) if args.runtime_release_watch else None
            pilot_engagement = (
                EngagementStore(service), args.pilot_engagement_origin, args.pilot_engagement_mode, bytes.fromhex(key)
            ) if args.pilot_engagement_origin else None
            price_reader = PriceStore(args.database_url).read if args.database_url else None
            latency_reader = (lambda capture: read_eligible_latency(store, capture)) if store else None
            goal_history = [
                GoalService(manifest, price_reader=price_reader, rights_path=args.goal_rights, latency_reader=latency_reader)
                for manifest in args.goal_cohort
            ]
            with make_server(store, args.host, args.port, args.trusted_host, fit_engine=fit_engine,
                             profile_releases=args.profile_release,
                             profile_archives=[archive.split(",") for archive in args.profile_archive],
                             goals=goal_history[-1] if goal_history else None, goal_history=goal_history[:-1],
                             price_reader=price_reader, scaling_pair=args.scaling_pair, cost_scenario=args.cost_scenario,
                             contributor_receipts=args.contributor_receipts,
                             agent_task_release=args.agent_task_release,
                             cost_tariff_references=args.cost_tariff_references,
                             cost_tariff_references_pin=args.cost_tariff_references_pin, runtime_watch=runtime_watch,
                             runtime_watch_notes=args.runtime_release_watch_notes,
                             runtime_watch_notes_revision=args.runtime_release_watch_notes_revision,
                             pilot_engagement=pilot_engagement) as server:
                host, port = server.server_address
                print(f"Listening on {host}:{port}", file=sys.stderr, flush=True)
                server.serve_forever()
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, ReleaseError, ReleaseNotFound, FitEngineError) as error:
        parser.exit(1, f"{error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
