from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
from datetime import date
from io import StringIO
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from uuid import uuid4

from fastest_editorial import generate_package
from fastest_release import ReleaseError, ReleaseNotFound, ReleaseStore
from test_public_api import api_client


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic-observation.json"


def submission():
    sample = json.loads(FIXTURE.read_text())
    return {
        "submission_id": str(uuid4()),
        "version": 1,
        "authorization": {
            "contributor_id": "fictional-private-contributor",
            "consent": True,
            "scope": "public-release",
            "reference": "fictional-private-grant",
        },
        "hardware": sample["hardware"],
        "artifact": sample["artifact"],
        "workload": sample["workload"],
        "metric": sample["metric"],
        "conditions": {
            "runtime_revision": "synthetic-build-v1",
            "runtime_sha256": sample["artifact"]["sha256"],
            "os_driver": "Synthetic host, driver 1.0",
            "settings": "One active simulated device, context 1152, batch 1",
        },
        "source": {
            "label": "Synthetic creator fixture",
            "locator": "https://benchmarks.example.org/reports/test.json#/decode",
            "revision": "fixture-v1",
            "sha256": sample["artifact"]["sha256"],
        },
    }


def decision(outcome="publish"):
    return {
        "decision_id": str(uuid4()),
        "editor_id": "fictional-private-editor",
        "outcome": outcome,
        "reason": "fictional-private-note",
        "authorization_reference": "fictional-private-reviewed-grant",
    }


def contributor_store(database):
    from fastest_contributor import ContributorStore
    return ContributorStore(database)


class ContributorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sandbox = tempfile.TemporaryDirectory(prefix="fastest-contributor-", dir="/tmp")
        cls.addClassCleanup(lambda: cls.assert_cleaned(sandbox.name))
        workspace = cls.enterClassContext(sandbox)
        cluster = Path(workspace, "db")
        subprocess.run(
            ["initdb", "-D", str(cluster), "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True, capture_output=True,
        )
        with Path(workspace, "postgres.log").open("w") as log:
            postgres = subprocess.Popen(
                ["postgres", "-D", str(cluster), "-k", workspace, "-c", "listen_addresses="],
                stdout=log, stderr=subprocess.STDOUT,
            )
        cls.addClassCleanup(cls.stop_postgres, postgres)
        cls.database = f"host={workspace} dbname=postgres"
        for _ in range(100):
            if subprocess.run(["pg_isready", "-d", cls.database], capture_output=True).returncode == 0:
                break
            if postgres.poll() is not None:
                raise RuntimeError(Path(workspace, "postgres.log").read_text())
            time.sleep(0.05)
        else:
            raise RuntimeError("PostgreSQL did not start")
        cls.public = ReleaseStore(cls.database)
        cls.public.migrate()

    @staticmethod
    def assert_cleaned(workspace):
        assert not Path(workspace).exists()

    @staticmethod
    def stop_postgres(postgres):
        if postgres.poll() is None:
            postgres.send_signal(signal.SIGINT)
            try:
                postgres.wait(timeout=10)
            except subprocess.TimeoutExpired:
                postgres.send_signal(signal.SIGQUIT)
                postgres.wait(timeout=10)
        assert postgres.returncode is not None

    def setUp(self):
        self.intake = contributor_store(self.database)
        self.intake.migrate()

    def test_receipt_and_public_history_are_idempotent_across_amendments(self):
        record = submission()
        raw = json.dumps(record, indent=2)
        with ThreadPoolExecutor(max_workers=2) as writers:
            first, replay = writers.map(self.intake.submit, [raw, raw])
        self.assertEqual(first, replay)
        receipt = first["receipt"]
        self.assertEqual(first["revisions"], [{"version": 1, "status": "pending_review", "issues": []}])
        self.assertEqual(contributor_store(self.database).inspect(receipt, 1)["submission"], raw)

        reviewed = decision()
        with ThreadPoolExecutor(max_workers=2) as writers:
            saved, repeated = writers.map(lambda _: self.intake.review(receipt, 1, reviewed), range(2))
        self.assertEqual(saved, repeated)
        initial = saved["revisions"][0]["release_id"]
        initial_page = self.public.artifact(initial, "benchmark.html")
        initial_row = self.public.read(initial)["row"]
        self.assertEqual(initial_row["kind"], "contributor")
        self.assertEqual(initial_row["metric"]["value"], "37.625")
        self.assertIn("Contributor-reported measurement", initial_page)
        self.assertIn("Excluded from controlled comparisons", initial_page)

        record["version"] = 2
        record["metric"]["value"] = "41.000000000001"
        record["source"]["revision"] = "fixture-v2"
        record["source"]["locator"] = "https://benchmarks.example.org/reports/amendment.json#/decode"
        amended = json.dumps(record)
        self.assertEqual(self.intake.submit(amended), self.intake.submit(amended))
        self.assertEqual(self.intake.status(receipt)["revisions"][-1]["status"], "pending_review")
        self.assertEqual(self.public.read_evidence(initial_row["evidence_id"])["release_id"], initial)

        amendment = decision()
        final = self.intake.review(receipt, 2, amendment)
        revised = final["revisions"][1]["release_id"]
        self.assertEqual(self.intake.review(receipt, 2, amendment), final)
        self.assertEqual(self.intake.submit(raw), final)
        self.assertEqual(self.intake.review(receipt, 1, reviewed), final)
        self.assertEqual(contributor_store(self.database).status(receipt), final)
        self.assertEqual([item["status"] for item in final["revisions"]], ["published", "published"])
        self.assertEqual(final["revisions"][1]["url"], f"/releases/{revised}/benchmark.html")
        active = self.public.read_evidence(initial_row["evidence_id"])
        self.assertEqual((active["release_id"], active["revision"]), (revised, 2))
        self.assertEqual(self.public.artifact(initial, "benchmark.html"), initial_page)
        self.assertEqual(self.public._query(
            f"SELECT count(*) FROM fastest_release.data_release WHERE evidence_id = '{initial_row['evidence_id']}'"
        ), "2")
        chart = json.loads(self.public.artifact(revised, "chart.json"))
        self.assertEqual(chart["rows"], json.loads(self.public.artifact(revised, "table.json"))["rows"])
        self.assertEqual(chart["rows"][0]["metric"]["value"], "41.000000000001")
        self.assertEqual(chart["rows"][0]["fields"]["comparison_eligibility"]["value"],
                         "Excluded from controlled comparisons. The measurement is contributor-reported.")
        markdown = self.public.artifact(revised, "benchmark.md")
        self.assertIn("Contributor-reported measurement", markdown)
        self.assertIn("Excluded from controlled comparisons", markdown)

        with api_client(self.public) as request:
            status, _, page = request(final["revisions"][1]["url"], decode=False)
            self.assertEqual(status, 200)
            self.assertIn("41.000000000001", page)
            status, _, evidence = request(f"/api/v1/evidence?evidence_id={initial_row['evidence_id']}")
            self.assertEqual(status, 200)
            self.assertEqual(evidence["kind"], "contributor")
            self.assertEqual(evidence["conditions"]["comparison_eligibility"]["value"],
                             chart["rows"][0]["fields"]["comparison_eligibility"]["value"])
            self.assertEqual(evidence["metric"]["value"], "41.000000000001")
        for private in (receipt, record["submission_id"], "fictional-private"):
            self.assertNotIn(private, page)
            self.assertNotIn(private, json.dumps(evidence))
            self.assertNotIn(private, json.dumps(chart))

    def test_ambiguous_records_stay_private_and_show_safe_review_outcomes(self):
        for group, field, invalid, issue in (
            ("hardware", "revision_id", "unresolved-machine", "invalid_observation"),
            ("artifact", "sha256", "unavailable", "invalid_observation"),
            ("workload", "id", "unknown", "ambiguous_identity"),
            ("metric", "unit", "tokens", "unregistered_metric"),
            ("conditions", "settings", "unknown", "invalid_conditions"),
            ("source", "locator", "https://benchmarks.example.org/test.json?secret=token#/value", "invalid_locator"),
            ("authorization", "scope", "internal", "public_scope_required"),
            ("authorization", "consent", "maybe", "consent_required"),
            ("authorization", "expires_at", "2000-01-01T00:00:00Z", "expired_authorization"),
        ):
            with self.subTest(group=group, field=field):
                record = submission()
                record[group][field] = invalid
                raw = json.dumps(record)
                result = self.intake.submit(raw)
                receipt = result["receipt"]
                self.assertEqual(result["revisions"][0]["status"], "quarantined")
                self.assertIn(issue, result["revisions"][0]["issues"])
                self.assertEqual(self.intake.inspect(receipt, 1)["submission"], raw)
                with self.assertRaisesRegex(ValueError, "Quarantined"):
                    self.intake.review(receipt, 1, decision())
                rejected = self.intake.review(receipt, 1, decision("reject"))
                self.assertEqual(rejected["revisions"][0]["status"], "rejected")
                self.assertNotIn("release_id", rejected["revisions"][0])
                self.assertNotIn("fictional-private", json.dumps(rejected))
                self.assertNotIn("secret=token", json.dumps(rejected))

    def test_self_review_changed_replay_and_out_of_order_approval_are_blocked(self):
        record = submission()
        raw = json.dumps(record)
        receipt = self.intake.submit(raw)["receipt"]
        with self.assertRaisesRegex(ValueError, "independent"):
            self.intake.review(receipt, 1, {**decision(), "editor_id": record["authorization"]["contributor_id"]})
        with self.assertRaisesRegex(ValueError, "independently reviewed authorization"):
            self.intake.review(receipt, 1, {**decision(), "authorization_reference": None})
        with self.assertRaises(ReleaseError):
            self.intake.submit(json.dumps({**record, "metric": {**record["metric"], "value": "42"}}))
        self.assertEqual(self.intake.inspect(receipt, 1)["submission"], raw)
        with self.assertRaises(ReleaseError):
            self.intake.submit(json.dumps({**record, "version": 2, "authorization": {
                **record["authorization"], "contributor_id": "unrelated-contributor",
            }}))
        self.intake.submit(json.dumps({**record, "version": 3}))
        self.intake.submit(json.dumps({**record, "version": 2}))
        with self.assertRaises(ReleaseError):
            self.intake.review(receipt, 2, decision())
        published = self.intake.review(receipt, 3, decision())
        self.assertEqual(published["revisions"][-1]["status"], "published")
        self.assertEqual(self.public.read(published["revisions"][-1]["release_id"])["revision"], 1)
        with self.assertRaises(ReleaseError):
            self.intake.review(receipt, 3, decision("reject"))

    def test_missing_or_malformed_amendment_owner_cannot_advance_an_owned_receipt(self):
        record = submission()
        receipt = self.intake.submit(json.dumps(record))["receipt"]
        authorization = {key: value for key, value in record["authorization"].items() if key != "contributor_id"}
        for invalid in (authorization, {**authorization, "contributor_id": []}):
            with self.subTest(authorization=invalid):
                with self.assertRaisesRegex(ReleaseError, "original contributor ID"):
                    self.intake.submit(json.dumps({**record, "version": 2, "authorization": invalid}))
        revisions = self.intake.review(receipt, 1, decision())["revisions"]
        self.assertEqual([(item["version"], item["status"]) for item in revisions], [(1, "published")])

    def test_publication_and_editor_decision_commit_together(self):
        record = submission()
        original_decision = decision()
        receipt = self.intake.submit(json.dumps(record))["receipt"]
        first = self.intake.review(receipt, 1, original_decision)["revisions"][0]["release_id"]
        self.intake.submit(json.dumps({**record, "version": 2}))
        with self.assertRaises(ReleaseError):
            self.intake.review(receipt, 2, original_decision)
        self.assertEqual(self.intake.status(receipt)["revisions"][-1]["status"], "pending_review")
        evidence_id = self.intake.inspect(receipt, 1)["evidence_id"]
        self.assertEqual(self.public.read_evidence(evidence_id)["release_id"], first)

        package = generate_package(self.public, release_id=first, editorial_date=date(2026, 11, 21),
                                   locale="en", public_origin="https://benchmarks.example.org")
        self.assertEqual(package["reason"], "contributor_release")

        self.public.withdraw(evidence_id, "Private rights withdrawal")
        status = self.intake.status(receipt)["revisions"][0]
        self.assertEqual(status["status"], "withdrawn")
        self.assertNotIn("Private rights withdrawal", json.dumps(status))
        self.assertNotIn("37.625", self.public.artifact(first, "benchmark.html"))

    def test_cli_exports_receipt_without_private_submission_or_review(self):
        record = submission()
        result = subprocess.run(
            [sys.executable, "-B", "-m", "fastest_contributor", "submit", "-"],
            input=json.dumps(record), encoding="utf-8", capture_output=True, check=True,
            env={**os.environ, "FASTEST_DATABASE_URL": self.database},
        )
        receipt = json.loads(result.stdout)
        status = subprocess.run(
            [sys.executable, "-B", "-m", "fastest_contributor", "status", receipt["receipt"]],
            encoding="utf-8", capture_output=True, check=True,
            env={**os.environ, "FASTEST_DATABASE_URL": self.database},
        )
        self.assertEqual(json.loads(status.stdout), receipt)
        self.assertNotIn("fictional-private", status.stdout)
        self.assertNotIn(record["submission_id"], status.stdout)

        ambiguous_decision = json.dumps(decision())[:-1] + ', "outcome": "reject"}'
        review = subprocess.run(
            [sys.executable, "-B", "-m", "fastest_contributor", "review", receipt["receipt"], "1", "-"],
            input=ambiguous_decision, encoding="utf-8", capture_output=True,
            env={**os.environ, "FASTEST_DATABASE_URL": self.database},
        )
        self.assertNotEqual(review.returncode, 0)
        self.assertIn("Duplicate JSON field", review.stderr)
        self.assertEqual(self.intake.status(receipt["receipt"]), receipt)

    def test_contributor_can_follow_private_receipt_through_review_and_withdrawal(self):
        record = submission()
        options = {"contributor_receipts": True}
        result = subprocess.run(
            [sys.executable, "-B", "-m", "fastest_contributor", "submit", "-"],
            input=json.dumps(record), encoding="utf-8", capture_output=True, check=True,
            env={**os.environ, "FASTEST_DATABASE_URL": self.database},
        )
        received = json.loads(result.stdout)
        receipt = received["receipt"]
        status_url = received["status_url"]
        self.assertEqual(status_url, f"/contributors/receipt?id={receipt}")

        self.public._query(
            "CREATE ROLE contributor_receipt_reader LOGIN; "
            "GRANT USAGE ON SCHEMA fastest_release TO contributor_receipt_reader; "
            "GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid) TO contributor_receipt_reader; "
            "GRANT EXECUTE ON FUNCTION fastest_release.read_contributor_receipt(uuid) TO contributor_receipt_reader;"
        )
        database = self.database + " user=contributor_receipt_reader"
        reader = ReleaseStore(database)
        self.assertEqual(reader.read_contributor_receipt(receipt), received["revisions"])
        with self.assertRaises(ReleaseError):
            contributor_store(database).inspect(receipt, 1)
        with self.assertRaises(ReleaseError):
            contributor_store(database).submit(json.dumps(submission()))
        evidence_id = self.intake.inspect(receipt, 1)["evidence_id"]

        log = StringIO()
        with redirect_stderr(log), api_client(reader) as request:
            self.assertEqual(request(status_url, decode=False)[0], 404)

        with redirect_stderr(log), api_client(reader, **options) as request:
            status, headers, page = request(status_url, decode=False)
            self.assertEqual(status, 200)
            self.assertEqual(headers.get_content_type(), "text/html")
            self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual(headers["X-Robots-Tag"], "noindex")
            self.assertEqual(headers["Referrer-Policy"], "no-referrer")
            self.assertIn("Pending review", page)
            self.assertNotIn("benchmarks.example.org", page)
            self.assertEqual(request(status_url, "HEAD", decode=False)[2], "")
            self.assertEqual(request(status_url, "POST", decode=False)[0], 501)
            for missing in ("", str(uuid4()), record["submission_id"], "invalid"):
                status, headers, page = request(f"/contributors/receipt?id={missing}", decode=False)
                self.assertEqual((status, page), (404, "Contributor receipt unavailable.\n"))
                self.assertEqual(headers["X-Robots-Tag"], "noindex")

            published = self.intake.review(receipt, 1, decision())["revisions"][0]
            self.assertEqual(reader.read_contributor_receipt(receipt), [
                {key: published[key] for key in ("version", "status", "issues", "url")},
            ])
            status, _, page = request(status_url, decode=False)
            self.assertEqual(status, 200)
            self.assertIn("Published", page)
            self.assertIn(f'href="{published["url"]}"', page)
            self.assertIn("Excluded from controlled comparisons", request(published["url"], decode=False)[2])

            amended = {**record, "version": 2, "metric": {**record["metric"], "unit": "tokens"}}
            self.intake.submit(json.dumps(amended))
            status, _, page = request(status_url, decode=False)
            self.assertEqual(status, 200)
            self.assertIn("Quarantined", page)
            self.assertIn("Unregistered metric", page)
            self.intake.review(receipt, 2, decision("reject"))
            self.public.withdraw(evidence_id, "Private rights withdrawal")
            status, _, page = request(status_url, decode=False)
            self.assertEqual(status, 200)
            self.assertIn("Rejected", page)
            self.assertIn("Withdrawn", page)
            self.assertEqual(request(published["url"], decode=False)[0], 410)
            for private in (receipt, record["submission_id"], evidence_id, "fictional-private",
                            "Private rights withdrawal", "benchmarks.example.org"):
                self.assertNotIn(private, page)
        self.assertNotIn(receipt, log.getvalue())

    def test_reader_role_cannot_read_the_private_intake(self):
        record = submission()
        receipt = self.intake.submit(json.dumps(record))["receipt"]
        reviewed = self.intake.review(receipt, 1, decision())
        release = reviewed["revisions"][0]["release_id"]
        self.public._query(
            "CREATE ROLE intake_test_reader LOGIN; "
            "GRANT USAGE ON SCHEMA fastest_release TO intake_test_reader; "
            "GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid) TO intake_test_reader;"
        )
        database = self.database + " user=intake_test_reader"
        reader = ReleaseStore(database)
        self.assertEqual(reader.read(release)["row"]["kind"], "contributor")
        with self.assertRaises(ReleaseError):
            reader.read_contributor_receipt(receipt)
        with self.assertRaises(ReleaseError):
            contributor_store(database).status(receipt)
        with self.assertRaises(ReleaseNotFound):
            self.intake.status(str(uuid4()))
