"""Record status for public benchmark requests and result corrections on GitHub."""

import argparse
from datetime import datetime
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
from subprocess import TimeoutExpired
import sys

from fastest_release import ReleaseError, ReleaseStore, _sql_text


REPOSITORY = "OmniMCP-AI/local-llm"
WEBHOOK_PATH = "/webhooks/github/issues"
MAX_BODY_BYTES = 1024 * 1024
REVISION_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
ISSUE_KINDS = (
    ("[Benchmark request]", "benchmark_request"),
    ("[Result correction]", "result_correction"),
)


def positive_bigint(value):
    return type(value) is int and 0 < value < 2**63


def record_issue(store, issue, action):
    if not isinstance(issue, dict):
        raise ValueError
    if "pull_request" in issue:
        return
    issue_id, number = issue.get("id"), issue.get("number")
    title, status, revision = issue.get("title"), issue.get("state"), issue.get("updated_at")
    if not positive_bigint(issue_id) or not positive_bigint(number):
        raise ValueError
    if not isinstance(title, str) or status not in ("open", "closed"):
        raise ValueError
    if not isinstance(revision, str) or not REVISION_PATTERN.fullmatch(revision):
        raise ValueError
    datetime.fromisoformat(revision)

    kind = next((kind for prefix, kind in ISSUE_KINDS if title == prefix or title.startswith(prefix + " ")), None)
    if action == "deleted":
        status = "deleted"
    repository = _sql_text(REPOSITORY)
    category = _sql_text(kind) if kind else "NULL"
    store._query(f"""
        INSERT INTO fastest_github_intake.issue AS current
            (repository, issue_id, issue_number, kind, status, revision)
        SELECT {repository}, {issue_id}, {number}, candidate.kind,
               {_sql_text(status)}, {_sql_text(revision)}::timestamptz
        FROM (SELECT coalesce({category}, (
            SELECT kind FROM fastest_github_intake.issue
            WHERE repository = {repository} AND issue_id = {issue_id}
        )) AS kind) AS candidate
        WHERE candidate.kind IS NOT NULL
        ON CONFLICT (repository, issue_id) DO UPDATE
        SET status = EXCLUDED.status, revision = greatest(current.revision, EXCLUDED.revision)
        WHERE current.status <> 'deleted'
          AND (EXCLUDED.status = 'deleted' OR EXCLUDED.revision > current.revision
               OR (EXCLUDED.revision = current.revision AND current.status = 'open' AND EXCLUDED.status = 'closed'));
    """)


def make_server(port, secret, store):
    class GitHubWebhook(BaseHTTPRequestHandler):
        timeout = 5

        def log_message(self, format, *args):
            pass

        def respond(self, status):
            self.send_response(status)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def do_POST(self):
            if self.path != WEBHOOK_PATH:
                return self.respond(404)

            lengths = self.headers.get_all("Content-Length", [])
            if self.headers.get("Transfer-Encoding") or len(lengths) != 1 or not re.fullmatch(r"[0-9]+", lengths[0]):
                return self.respond(400)
            if len(lengths[0]) > len(str(MAX_BODY_BYTES)) or int(lengths[0]) > MAX_BODY_BYTES:
                return self.respond(413)
            if self.headers.get_content_type() != "application/json":
                return self.respond(415)

            signatures = self.headers.get_all("X-Hub-Signature-256", [])
            if len(signatures) != 1 or not re.fullmatch(r"sha256=[a-f0-9]{64}", signatures[0]):
                return self.respond(401)
            length = int(lengths[0])
            raw = self.rfile.read(length)
            if len(raw) != length:
                return self.respond(400)
            expected = "sha256=" + hmac.digest(secret, raw, "sha256").hex()
            if not hmac.compare_digest(expected, signatures[0]):
                return self.respond(401)

            if self.headers.get_all("X-GitHub-Event") != ["issues"]:
                return self.respond(204)
            try:
                document = json.loads(raw.decode("utf-8"))
                if not isinstance(document, dict) or not isinstance(document.get("action"), str):
                    raise ValueError
                repo = document.get("repository")
                if (not isinstance(repo, dict) or repo.get("full_name") != REPOSITORY
                        or repo.get("private") is not False or repo.get("visibility", "public") != "public"):
                    return self.respond(403)
                action = document["action"]
                if action in ("opened", "edited", "closed", "reopened", "deleted"):
                    record_issue(store, document.get("issue"), action)
            except (ValueError, RecursionError):
                return self.respond(400)
            except (OSError, ReleaseError, TimeoutExpired):
                print("Could not store GitHub issue status.", file=sys.stderr)
                return self.respond(503)
            self.respond(204)

    return ThreadingHTTPServer(("127.0.0.1", port), GitHubWebhook)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("migrate")
    serve = subcommands.add_parser("serve")
    serve.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()
    database_url = os.environ.get("FASTEST_GITHUB_INTAKE_DATABASE_URL")
    if not database_url:
        parser.error("Set FASTEST_GITHUB_INTAKE_DATABASE_URL.")
    store = ReleaseStore(database_url)
    if args.command == "migrate":
        try:
            store._query(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
        except (OSError, ReleaseError, TimeoutExpired) as error:
            parser.exit(1, f"{error}\n")
        return

    secret = os.environ.get("FASTEST_GITHUB_WEBHOOK_SECRET")
    if not secret:
        parser.error("Set FASTEST_GITHUB_WEBHOOK_SECRET.")
    with make_server(args.port, secret.encode("utf-8"), store) as server:
        print(f"Listening on 127.0.0.1:{server.server_port}", file=sys.stderr)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
