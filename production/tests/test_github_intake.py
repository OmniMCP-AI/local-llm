from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import hmac
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from fastest_release import ReleaseStore


PRODUCTION = Path(__file__).resolve().parents[1]
REPOSITORY = "OmniMCP-AI/local-llm"
SECRET = b"local-webhook-test-fixture"
URL = "/webhooks/github/issues"


def event(number=41, *, title="[Benchmark request] Run a café workload", action="opened",
          status="open", revision="2026-11-21T06:00:00Z"):
    return {
        "action": action,
        "repository": {"full_name": REPOSITORY, "private": False},
        "issue": {
            "id": 4000 + number, "number": number, "title": title, "state": status,
            "updated_at": revision, "body": "private-text https://private.example/receipt/fixture",
            "html_url": "https://arbitrary.example/should-never-be-copied",
            "user": {"login": "test-user-profile"},
        },
        "sender": {"login": "test-sender-profile"},
    }


class GitHubIntakeTest(unittest.TestCase):
    def run(self, result=None):
        try:
            return super().run(result)
        finally:
            self.doCleanups()

    def setUp(self):
        sandbox = tempfile.TemporaryDirectory(prefix="fastest-github-intake-", dir="/tmp")
        self.addCleanup(self.assert_removed, sandbox.name)
        workspace = Path(self.enterContext(sandbox))
        cluster = workspace / "db"
        subprocess.run(["initdb", "-D", str(cluster), "--auth=trust", "--encoding=UTF8", "--no-locale"],
                       check=True, capture_output=True, timeout=30)
        postgres_log = workspace / "postgres.log"
        with postgres_log.open("w") as log:
            postgres = subprocess.Popen(["postgres", "-D", str(cluster), "-k", str(workspace),
                                         "-c", "listen_addresses=", "-c", "log_statement=all"],
                                        stdout=log, stderr=subprocess.STDOUT)
        self.addCleanup(self.stop_process, postgres, signal.SIGINT)
        database = f"host={workspace} dbname=postgres"
        for _ in range(100):
            if subprocess.run(["pg_isready", "-d", database], capture_output=True, timeout=5).returncode == 0:
                break
            if postgres.poll() is not None:
                raise RuntimeError(postgres_log.read_text())
            time.sleep(0.05)
        else:
            raise RuntimeError("PostgreSQL did not start")

        self.database = ReleaseStore(database)
        env = {**os.environ, "FASTEST_GITHUB_INTAKE_DATABASE_URL": database,
               "FASTEST_GITHUB_WEBHOOK_SECRET": SECRET.decode()}
        args = [sys.executable, "-B", "-m", "fastest_github_intake"]
        subprocess.run([*args, "migrate"], check=True, cwd=PRODUCTION, env=env, timeout=15)
        self.database._query("""
            CREATE ROLE intake_webhook LOGIN;
            GRANT USAGE ON SCHEMA fastest_github_intake TO intake_webhook;
            GRANT SELECT, INSERT, UPDATE (status, revision)
                ON fastest_github_intake.issue TO intake_webhook;
        """)
        env["FASTEST_GITHUB_INTAKE_DATABASE_URL"] += " user=intake_webhook"
        server = subprocess.Popen([*args, "serve", "--port", "0"], cwd=PRODUCTION, env=env,
                                  stderr=subprocess.PIPE, text=True)
        self.addCleanup(server.stderr.close)
        self.addCleanup(self.assert_metadata_only_logs, server.stderr, postgres_log)
        self.addCleanup(self.stop_process, server, signal.SIGTERM)
        if not select.select([server.stderr], [], [], 10)[0]:
            raise RuntimeError("GitHub intake listener did not start")
        banner = server.stderr.readline().strip()
        match = re.fullmatch(r"Listening on 127\.0\.0\.1:([0-9]+)", banner)
        if not match:
            raise RuntimeError(banner)
        self.port = int(match[1])

    def assert_metadata_only_logs(self, listener_log, postgres_log):
        logs = listener_log.read() + postgres_log.read_text()
        for fixture in ("café workload", "private-text", "private.example", "arbitrary.example",
                        "test-user-profile", "test-sender-profile", SECRET.decode()):
            self.assertNotIn(fixture, logs)

    @staticmethod
    def stop_process(process, shutdown_signal):
        if process.poll() is None:
            process.send_signal(shutdown_signal)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        assert process.returncode is not None

    @staticmethod
    def assert_removed(path):
        assert not Path(path).exists()

    def deliver(self, document, event_type="issues", *, signature=None, headers=None, path=URL):
        raw = document if isinstance(document, bytes) else json.dumps(document, ensure_ascii=False, indent=2).encode()
        digest = hmac.new(SECRET, raw, sha256).hexdigest()
        request_headers = {"Content-Type": "application/json", "X-GitHub-Event": event_type,
                           "X-Hub-Signature-256": f"sha256={digest}" if signature is None else signature}
        request_headers.update(headers or {})
        client = HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            client.request("POST", path, raw, request_headers)
            response = client.getresponse()
            self.assertEqual(response.read(), b"")
            return response.status
        finally:
            client.close()

    def rows(self):
        return json.loads(self.database._query("""
            SET TIME ZONE 'UTC';
            SELECT coalesce(json_agg(issue ORDER BY issue_number), '[]')
            FROM fastest_github_intake.issue;
        """))

    def test_signed_forms_create_only_canonical_issue_metadata(self):
        self.assertEqual(self.deliver(event()), 204)
        self.assertEqual(self.deliver(event(42, title="[Result correction] Wrong number")), 204)
        self.assertEqual([row for row in self.rows() if row["issue_number"] in (41, 42)], [
            {"repository": REPOSITORY, "issue_id": 4041, "issue_number": 41, "kind": "benchmark_request",
             "status": "open", "revision": "2026-11-21T06:00:00+00:00",
             "url": f"https://github.com/{REPOSITORY}/issues/41"},
            {"repository": REPOSITORY, "issue_id": 4042, "issue_number": 42, "kind": "result_correction",
             "status": "open", "revision": "2026-11-21T06:00:00+00:00",
             "url": f"https://github.com/{REPOSITORY}/issues/42"},
        ])
        stats = PRODUCTION.parent / "opendesign/mockups/llm-observatory/catalog-stats.sql"
        counts = subprocess.run(["psql", "-XAtw", "-d", self.database.database_url, "-f", str(stats)],
                                check=True, capture_output=True, text=True, timeout=5)
        self.assertIn("fastest_github_intake.issue|2", counts.stdout.splitlines())

    def test_rejects_untrusted_or_oversized_deliveries(self):
        self.assertEqual(self.deliver(event(), signature=""), 401)
        self.assertEqual(self.deliver(event(), signature="sha256=" + "a" * 64), 401)
        signed = b'{"notice":"original"}'
        signature = "sha256=" + hmac.new(SECRET, signed, sha256).hexdigest()
        self.assertEqual(self.deliver(signed + b" ", signature=signature), 401)
        self.assertEqual(self.deliver(b"", headers={"Content-Length": "1048577"}), 413)
        self.assertEqual(self.deliver(b"", headers={"Transfer-Encoding": "chunked"}), 400)
        self.assertEqual(self.deliver(event(), headers={"Content-Type": "text/plain"}), 415)
        self.assertEqual(self.deliver(b'"not an object"'), 400)
        self.assertEqual(self.deliver(event(), path="/api/v1/feedback"), 404)
        wrong_repository = event()
        wrong_repository["repository"]["full_name"] += "-other"
        self.assertEqual(self.deliver(wrong_repository), 403)
        private_repository = event()
        private_repository["repository"]["private"] = True
        self.assertEqual(self.deliver(private_repository), 403)
        internal_repository = event()
        internal_repository["repository"]["visibility"] = "internal"
        self.assertEqual(self.deliver(internal_repository), 403)
        self.assertEqual(self.rows(), [])

    def test_ignores_ping_other_events_issues_and_pull_requests(self):
        self.assertEqual(self.deliver({"zen": "test"}, "ping"), 204)
        self.assertEqual(self.deliver(event(), "issue_comment"), 204)
        self.assertEqual(self.deliver(event(action="labeled")), 204)
        self.assertEqual(self.deliver(event(title="Regular maintenance")), 204)
        pull_request = event()
        pull_request["issue"]["pull_request"] = {"url": "https://api.github.com/example"}
        self.assertEqual(self.deliver(pull_request), 204)
        self.assertEqual(self.rows(), [])

    def test_duplicate_and_late_revisions_do_not_override_new_status(self):
        opened = event()
        closed = event(title="Changed title", action="closed", status="closed", revision="2026-11-21T06:01:00Z")
        self.assertEqual(self.deliver(opened), 204)
        with ThreadPoolExecutor(max_workers=3) as deliveries:
            self.assertEqual(list(deliveries.map(self.deliver, [closed, closed, opened])), [204, 204, 204])
        self.assertEqual([(row["status"], row["revision"], row["kind"]) for row in self.rows()],
                         [("closed", "2026-11-21T06:01:00+00:00", "benchmark_request")])

        reopened = event(title="Changed title", action="reopened", revision="2026-11-21T06:02:00Z")
        self.assertEqual(self.deliver(reopened), 204)
        self.assertEqual(self.deliver(closed), 204)
        self.assertEqual([(row["status"], row["revision"], row["kind"]) for row in self.rows()],
                         [("open", "2026-11-21T06:02:00+00:00", "benchmark_request")])

    def test_close_and_reopen_in_same_second_are_deterministic(self):
        reopened = event(action="reopened", revision="2026-11-21T06:01:00Z")
        closed = event(action="closed", status="closed", revision="2026-11-21T06:01:00Z")
        self.assertEqual(self.deliver(reopened), 204)
        self.assertEqual(self.deliver(closed), 204)
        self.assertEqual(self.deliver(reopened), 204)
        self.assertEqual([row["status"] for row in self.rows()], ["closed"])

    def test_deleted_issue_cannot_be_restored_by_a_delayed_delivery(self):
        opened = event()
        edited = event(action="edited", revision="2026-11-21T06:03:00Z")
        deleted = event(title="Changed title", action="deleted", revision="2026-11-21T06:01:00Z")
        self.assertEqual(self.deliver(opened), 204)
        self.assertEqual(self.deliver(edited), 204)
        self.assertEqual(self.deliver(deleted), 204)
        self.assertEqual(self.deliver(edited), 204)
        self.assertEqual([(row["status"], row["revision"]) for row in self.rows()],
                         [("deleted", "2026-11-21T06:03:00+00:00")])

    def test_database_failure_returns_retryable_status_without_acknowledging(self):
        self.database._query("ALTER TABLE fastest_github_intake.issue RENAME TO unavailable;")
        self.assertEqual(self.deliver(event()), 503)
        self.database._query("ALTER TABLE fastest_github_intake.unavailable RENAME TO issue;")
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.deliver(event()), 204)
        self.assertEqual([row["status"] for row in self.rows()], ["open"])
