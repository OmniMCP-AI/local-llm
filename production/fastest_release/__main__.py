import argparse
import json
import os
from pathlib import Path
import sys

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
    research_import = commands.add_parser("research-import", help="Reconcile the private video research seed.")
    research_import.add_argument("--seed-dir", type=Path, default=SEED_ROOT)
    research_read = commands.add_parser("research-read", help="Read a private research manifest or its records.")
    research_read.add_argument("seed_id")
    research_read.add_argument("kind", nargs="?")
    research_read.add_argument("identifier", nargs="?")
    args = parser.parse_args(argv)

    if not args.database_url:
        parser.error("set FASTEST_DATABASE_URL or pass --database-url")
    store = ReleaseStore(args.database_url)
    try:
        if args.command == "migrate":
            store.migrate()
        elif args.command == "publish":
            print(store.publish(json.loads(args.observation.read_text(encoding="utf-8"))))
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
            with make_server(store, args.host, args.port, args.trusted_host) as server:
                host, port = server.server_address
                print(f"Listening on {host}:{port}", file=sys.stderr, flush=True)
                server.serve_forever()
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, ReleaseError, ReleaseNotFound) as error:
        parser.exit(1, f"{error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
