from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from threading import Thread
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4
from zipfile import ZipFile

from fastest_delivery import shorts, x_post
from fastest_delivery.pilot import TIMEZONE, audit
from fastest_editorial import generate_package
from fastest_editorial.__main__ import _record
from fastest_release import ReleaseNotFound
from test_goals import fixture_service
import test_release
from test_shorts_delivery import CHANNEL_ID, POST_URL, RELEASE_ID, PublicRelease


PRODUCTION = Path(__file__).resolve().parents[1]


class MissingReleaseStore:
    def read(self, release_id):
        raise ReleaseNotFound(release_id)


class DistributionPilotTest(unittest.TestCase):
    def setUp(self):
        sandbox = TemporaryDirectory(prefix="distribution-36-")
        self.addCleanup(lambda: self.assertFalse(Path(sandbox.name).exists()))
        self.root = Path(self.enterContext(sandbox))
        self.drafts = self.root / "editorial-drafts"

    def draft(self, day, store=None):
        draft = generate_package(
            store or MissingReleaseStore(), editorial_date=day, locale="en",
            public_origin="https://benchmark.example", release_id=RELEASE_ID if store else None,
        )
        return draft, _record(self.drafts, draft)

    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_delivery.pilot", "--start", "2026-11-21", *args],
            cwd=self.root, capture_output=True, text=True, timeout=10,
            env={"PYTHONPATH": str(PRODUCTION)},
        )

    def audit(self, *args):
        result = self.invoke(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def publish_x(self, *, engagement_key=None, now=None):
        now = now or datetime(2026, 11, 20, 16, 30, tzinfo=timezone.utc)
        store = PublicRelease()
        draft, draft_path = self.draft(now.astimezone(TIMEZONE).date(), store)
        options = {"engagement_key": engagement_key} if engagement_key else {}
        package = x_post.prepare(store, draft_path, self.root / "x-review", **options)
        approval = x_post.approve(
            package, self.root / "x-approvals", account="@benchmarklab", payload_sha256=package.name,
            window_start=(now - timedelta(minutes=30)).isoformat(), window_end=(now + timedelta(minutes=30)).isoformat(),
            approved_by="Fixture editor", rights_reference="Fixture rights review",
        )
        with patch.object(x_post, "datetime", wraps=datetime) as clock:
            clock.now.return_value = now
            directory = self.root / "x-deliveries"
            handoff = x_post.export(store, package, approval, directory)
            options = {}
            if engagement_key:
                engagement_url = f"https://benchmark.example/pilot/evidence/{RELEASE_ID}/{engagement_key}#citation"
                with ZipFile(handoff) as archive:
                    self.assertIn(engagement_url, archive.read("post.txt").decode().splitlines())
                with self.assertRaisesRegex(ValueError, "engagement link"):
                    x_post.record_receipt(
                        approval, directory, url="https://x.com/benchmarklab/status/123",
                        published_at=now.isoformat(), operator="Fixture operator",
                    )
                options["observed_engagement_url"] = engagement_url
            receipt_path = x_post.record_receipt(
                approval, directory, url="https://x.com/benchmarklab/status/123",
                published_at=now.isoformat(), operator="Fixture operator", **options,
            )
        return draft, json.loads(receipt_path.read_bytes())

    def test_tracked_post_requires_the_exact_approved_link_on_reconciliation(self):
        key = "e1d2b415-ee2e-4b52-bea0-f49df47aff08"
        draft, receipt = self.publish_x(engagement_key=key)
        self.assertEqual(receipt["engagement_url"], f"https://benchmark.example/pilot/evidence/{RELEASE_ID}/{key}#citation")
        self.assertTrue(draft["story"]["evidence_destination"].endswith("/benchmark.html#citation"))
        self.assertEqual(self.audit()["channels"]["x"]["published_in_window"], 1)

    def test_hosted_opt_in_evidence_and_comparison_export_to_audit(self):
        from fastest_delivery.engagement_capture import main as capture_command
        from fastest_delivery.engagement_store import EngagementStore
        from fastest_release.http import make_server

        postgres = test_release.ReleaseTest()
        self.addCleanup(postgres.doCleanups)
        postgres.setUp()
        service_file = self.root / "pg-service.conf"
        roles = {"pilot-fixture": None, "pilot-origin": "pilot_origin", "pilot-binder": "pilot_binder",
                 "pilot-auditor": "pilot_auditor"}
        service_file.write_text("".join(
            f"[{service}]\nhost={postgres.socket_path}\ndbname=postgres\n"
            + (f"user={role}\n" if role else "")
            for service, role in roles.items()
        ))
        self.enterContext(patch.dict(os.environ, {
            "PGSERVICEFILE": str(service_file), "FASTEST_PILOT_ENGAGEMENT_DBSERVICE": "pilot-fixture",
        }))
        now = datetime.now(timezone.utc)
        start = now.astimezone(TIMEZONE).date().isoformat()
        key = str(uuid4())
        draft, receipt = self.publish_x(engagement_key=key, now=now)
        export_path = self.root / "pg-engagement.json"
        approval = receipt["approval_id"]
        source_args = [start, "--mode", "rehearsal", "--draft-dir", str(self.drafts),
                       "--x-approvals", str(self.root / "x-approvals"),
                       "--x-deliveries", str(self.root / "x-deliveries")]
        capture_command(["migrate"])
        postgres.store._query("""
            CREATE ROLE pilot_origin LOGIN;
            CREATE ROLE pilot_binder LOGIN;
            CREATE ROLE pilot_auditor LOGIN;
            GRANT USAGE ON SCHEMA fastest_pilot_engagement TO pilot_origin, pilot_binder, pilot_auditor;
            GRANT SELECT ON fastest_pilot_engagement.available TO pilot_origin;
            GRANT EXECUTE ON FUNCTION fastest_pilot_engagement.arrive(uuid, text, uuid) TO pilot_origin;
            GRANT EXECUTE ON FUNCTION fastest_pilot_engagement.complete(uuid, text, uuid, uuid) TO pilot_origin;
            GRANT SELECT, INSERT, UPDATE (attribution_key) ON fastest_pilot_engagement.binding TO pilot_binder;
            GRANT SELECT ON fastest_pilot_engagement.binding, fastest_pilot_engagement.journey TO pilot_auditor;
        """)
        hosted = EngagementStore("pilot-origin")
        goals = self.enterContext(fixture_service())
        releases = PublicRelease()
        http = self.enterContext(make_server(
            releases, port=0, trusted_hosts=["benchmark.example"], goals=goals,
            pilot_engagement=(hosted, "https://benchmark.example", "rehearsal", bytes(32)),
        ))
        worker = Thread(target=http.serve_forever)
        worker.start()
        self.addCleanup(worker.join, 5)
        self.addCleanup(http.shutdown)
        path = urlsplit(receipt["engagement_url"]).path
        base = f"http://127.0.0.1:{http.server_port}"

        def request(path, values=None, *, origin="https://benchmark.example"):
            body = urlencode(values).encode() if values is not None else None
            headers = {"Host": "benchmark.example", "Origin": origin}
            with urlopen(Request(base + path, data=body, headers=headers), timeout=5) as response:
                self.assertIsNone(response.headers.get("Set-Cookie"))
                return response.read().decode()

        def export(*flags):
            with patch.dict(os.environ, {"FASTEST_PILOT_ENGAGEMENT_DBSERVICE": "pilot-auditor"}):
                capture_command(["export", "--start", *source_args, "--output", str(export_path), *flags])
            self.assertEqual(export_path.stat().st_mode & 0o777, 0o600)
            return json.loads(export_path.read_text())

        self.assertIn('id="citation"', request(path))
        self.assertNotIn("Share anonymous activity", request(path))
        with patch.dict(os.environ, {"FASTEST_PILOT_ENGAGEMENT_DBSERVICE": "pilot-binder"}):
            binding = ["bind", "--start", *source_args, "--receipt-id", receipt["receipt_id"]]
            capture_command(binding)
            capture_command(binding)
        page = request(path)
        self.assertIn('id="citation"', page)
        self.assertEqual(export()["events"], [])
        token = re.search(r'name="journey" value="([^"]+)"', page)[1]
        with self.assertRaises(HTTPError) as error:
            request(path, {"action": "compare", "journey": token, "decode": "20", "prefill": "10"})
        with error.exception as response:
            self.assertEqual(response.code, 409)
        consent = {"action": "opt-in", "journey": token}
        with self.assertRaises(HTTPError) as error:
            request(path, consent, origin="https://other.example")
        with error.exception as response:
            self.assertEqual(response.code, 403)
        self.assertIn("Compare setups", request(path, consent))
        self.assertIn("Compare setups", request(path, consent))
        self.assertEqual([event["kind"] for event in export()["events"]], ["evidence_arrival"])
        with self.assertRaises(HTTPError) as error:
            request(path, {"action": "compare", "journey": token, "decode": "invalid", "prefill": "10"})
        with error.exception as response:
            self.assertEqual(response.code, 400)
        selection = {"action": "compare", "journey": token, "decode": "20", "prefill": "10"}
        self.assertIn("Exact goal results", request(path, selection))
        self.assertIn("Exact goal results", request(path, selection))
        snapshot = export()
        self.assertEqual(snapshot, export())
        self.assertEqual(snapshot["coverage"], {"qualified_evidence_visits": [], "completed_comparisons": []})
        visit, comparison = snapshot["events"]
        self.assertEqual(visit["evidence_destination"], draft["story"]["evidence_destination"])
        self.assertEqual(comparison["kind"], "comparison_result")
        self.assertNotEqual(visit["visit_id"], comparison["comparison_id"])
        self.assertTrue(all(event["receipt_id"] == receipt["receipt_id"] and event["post_url"] == receipt["url"]
                            for event in snapshot["events"]))

        releases.snapshot["status"] = "withdrawn"
        del releases.snapshot["row"]
        for values in (None, consent, selection):
            with self.assertRaises(HTTPError) as error:
                request(path, values)
            with error.exception as response:
                self.assertEqual(response.code, 410)
        self.assertEqual(export(), snapshot)

        report = audit(date.fromisoformat(start), self.drafts, {
            "x": (self.root / "x-approvals", self.root / "x-deliveries"),
            "youtube-shorts": (self.root / "shorts-approvals", self.root / "shorts-deliveries"),
        }, engagement_export=export_path)
        self.assertEqual(report["metrics"], {"qualified_evidence_visits": None, "completed_comparisons": None})
        self.assertEqual([item["observed_count"] for item in report["engagement_evidence"]["coverage"].values()], [1, 1])

    def engagement_export(self):
        draft, receipt = self.publish_x()
        visit = {
            "kind": "evidence_arrival", "occurred_at": "2026-11-20T16:45:00Z",
            "receipt_id": receipt["receipt_id"], "post_url": receipt["url"],
            "visit_id": "e1d2b415-ee2e-4b52-bea0-f49df47aff08",
            "evidence_destination": draft["story"]["evidence_destination"],
        }
        receipt_days = [{"date": f"2026-11-{day}", "receipt_id": receipt["receipt_id"]} for day in range(21, 28)]
        return {
            "schema_version": 1, "mode": "rehearsal", "start_date": "2026-11-21",
            "reference": "Fixture first-party projection",
            "coverage": {
                "qualified_evidence_visits": list(receipt_days), "completed_comparisons": list(receipt_days),
            },
            "events": [visit],
        }

    def write_engagement(self, export):
        path = self.root / "engagement.json"
        path.write_text(json.dumps(export))
        return path

    def test_computes_metrics_from_first_party_observations_against_published_receipt(self):
        export = self.engagement_export()
        path = self.write_engagement(export)
        audit = self.audit("--engagement-export", path)

        self.assertEqual(audit["metrics"], {
            "qualified_evidence_visits": {"count": 1, "reference": "Fixture first-party projection"},
            "completed_comparisons": {"count": 0, "reference": "Fixture first-party projection"},
        })
        self.assertEqual(audit["engagement_evidence"]["record"], str(path))
        self.assertEqual(audit["engagement_evidence"]["sha256"], sha256(path.read_bytes()).hexdigest())
        self.assertNotIn(export["events"][0]["visit_id"], json.dumps(audit))

    def test_partial_coverage_leaves_total_unknown_with_observed_events_retained(self):
        export = self.engagement_export()
        missing = export["coverage"]["qualified_evidence_visits"].pop()
        audit = self.audit("--engagement-export", self.write_engagement(export))

        self.assertIsNone(audit["metrics"]["qualified_evidence_visits"])
        self.assertIn("metric_unreported:qualified_evidence_visits", audit["gaps"])
        coverage = audit["engagement_evidence"]["coverage"]["qualified_evidence_visits"]
        self.assertEqual(coverage["missing_receipt_days"], [missing])
        self.assertEqual(coverage["observed_count"], 1)
        self.assertEqual(audit["metrics"]["completed_comparisons"]["count"], 0)

    def test_empty_export_without_published_receipts_leaves_metrics_unknown(self):
        export = self.write_engagement({
            "schema_version": 1, "mode": "rehearsal", "start_date": "2026-11-21",
            "reference": "Fixture first-party projection",
            "coverage": {"qualified_evidence_visits": [], "completed_comparisons": []}, "events": [],
        })
        audit = self.audit("--engagement-export", export)
        self.assertEqual(audit["metrics"], {"qualified_evidence_visits": None, "completed_comparisons": None})

    def test_rejects_unverified_or_out_of_window_engagement_events(self):
        export = self.engagement_export()
        event, = export["events"]
        for changes, reason in (
            ({"receipt_id": "f" * 64}, "published pilot receipt"),
            ({"post_url": "https://x.com/benchmarklab/status/456"}, "published pilot receipt"),
            ({"evidence_destination": event["evidence_destination"].removesuffix("#citation")}, "pinned evidence"),
            ({"occurred_at": "2026-11-20T16:29:59Z"}, "after publication"),
            ({"occurred_at": "2026-11-27T16:00:00Z"}, "Shanghai pilot dates"),
            ({"occurred_at": "2026-11-21T00:45:00"}, "include a UTC offset"),
            ({"kind": "comparison_started"}, "completed comparison result"),
            ({"cookie_id": "private"}, "unexpected fields"),
        ):
            with self.subTest(changes=changes):
                export["events"] = [{**event, **changes}]
                result = self.invoke("--engagement-export", self.write_engagement(export))
                self.assertEqual(result.returncode, 1)
                self.assertIn(reason, result.stderr)

    def test_rejects_one_visit_with_conflicting_observations(self):
        export = self.engagement_export()
        visit, = export["events"]
        export["events"].append({**visit, "occurred_at": "2026-11-20T16:45:01Z"})
        result = self.invoke("--engagement-export", self.write_engagement(export))
        self.assertEqual(result.returncode, 1)
        self.assertIn("conflicting events", result.stderr)

    def test_rejects_rehearsal_export_for_live_audit(self):
        export = self.engagement_export()
        ledger = self.root / "ledger.json"
        ledger.write_text(json.dumps({"schema_version": 1, "mode": "live", "start_date": export["start_date"]}))
        result = self.invoke("--operator-log", ledger, "--engagement-export", self.write_engagement(export))
        self.assertEqual(result.returncode, 1)
        self.assertIn("matching mode", result.stderr)

    def test_rejects_ambiguous_json_coverage(self):
        export = self.engagement_export()
        path = self.write_engagement(export)
        path.write_text(path.read_text().replace('"coverage": {', '"coverage": {}, "coverage": {', 1))
        result = self.invoke("--engagement-export", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate JSON field", result.stderr)

    def test_reports_all_seven_editorial_days_and_gaps_without_inventing_observations(self):
        before, _ = self.draft(date(2026, 11, 20))
        included, _ = self.draft(date(2026, 11, 21))
        after, _ = self.draft(date(2026, 11, 28))
        audit = self.audit()

        self.assertEqual(audit["status"], "incomplete")
        self.assertEqual(audit["timezone"], "Asia/Shanghai")
        self.assertEqual([day["date"] for day in audit["days"]], [f"2026-11-{d}" for d in range(21, 28)])
        self.assertEqual([draft["draft_revision"] for day in audit["days"] for draft in day["drafts"]],
                         [included["draft_revision"]])
        self.assertEqual(audit["days"][0]["drafts"][0]["reason"], "no_current_release")
        self.assertEqual(audit["days"][0]["status"], "no_story")
        self.assertEqual(audit["days"][1]["status"], "missing")
        self.assertEqual(audit["metrics"], {"qualified_evidence_visits": None, "completed_comparisons": None})
        self.assertNotIn(before["draft_revision"], json.dumps(audit))
        self.assertNotIn(after["draft_revision"], json.dumps(audit))

    def test_rehearsal_reconciles_partial_failure_replay_and_withdrawal(self):
        now = datetime(2026, 11, 20, 16, 30, tzinfo=timezone.utc)
        store = PublicRelease()
        draft = generate_package(
            store, editorial_date=date(2026, 11, 21), locale="en",
            public_origin="https://benchmark.example", release_id=RELEASE_ID,
        )
        draft_path = _record(self.drafts, draft)
        x_deliveries = self.root / "x-deliveries"
        shorts_deliveries = self.root / "shorts-deliveries"
        x_package = x_post.prepare(store, draft_path, self.root / "x-review")
        shorts_package = shorts.prepare(store, draft_path, self.root / "shorts-review")
        review = {
            "window_start": "2026-11-20T16:00:00Z", "window_end": "2026-11-20T17:00:00Z",
            "approved_by": "Fixture editor", "rights_reference": "Fixture rights review",
        }
        x_approval = x_post.approve(
            x_package, self.root / "x-approvals", account="@benchmarklab", payload_sha256=x_package.name, **review,
        )
        expired_x_approval = x_post.approve(
            x_package, self.root / "x-approvals", account="@benchmarklab", payload_sha256=x_package.name,
            **{**review, "window_start": "2026-11-20T15:00:00Z", "window_end": "2026-11-20T16:00:00Z"},
        )
        shorts_approval = shorts.approve(
            shorts_package, self.root / "shorts-approvals", account=CHANNEL_ID,
            payload_sha256=shorts_package.name, **review,
        )
        queued_approval = shorts.approve(
            shorts_package, self.root / "shorts-approvals", account="UC" + "a" * 22,
            payload_sha256=shorts_package.name, **review,
        )
        receipt = {"published_at": now.isoformat(), "operator": "Fixture operator"}
        with patch.object(x_post, "datetime", wraps=datetime) as x_clock, patch.object(
            shorts, "datetime", wraps=datetime,
        ) as shorts_clock:
            x_clock.now.return_value = shorts_clock.now.return_value = now
            with self.assertRaisesRegex(ValueError, "outside the approved window"):
                x_post.export(store, x_package, expired_x_approval, x_deliveries)
            shorts.export(store, shorts_package, shorts_approval, shorts_deliveries)
            shorts_receipt = shorts.record_receipt(
                shorts_approval, shorts_deliveries, account=CHANNEL_ID, url=POST_URL, **receipt,
            )
            x_post.export(store, x_package, x_approval, x_deliveries)
            x_receipt = x_post.record_receipt(
                x_approval, x_deliveries, url="https://x.com/benchmarklab/status/123", **receipt,
            )
            self.assertEqual(x_post.export(store, x_package, x_approval, x_deliveries), x_receipt)
            store.snapshot["status"] = "withdrawn"
            del store.snapshot["row"]
            with self.assertRaisesRegex(ValueError, "withdrawn_release"):
                shorts.export(store, shorts_package, queued_approval, shorts_deliveries)
            correction, = shorts.corrections(store, shorts_deliveries)

        source = {"reference": "Fixture execution log", "occurred_at": now.isoformat()}
        ledger = {
            "schema_version": 1, "start_date": "2026-11-21", "mode": "rehearsal",
            "runs": [{"scheduled_at": now.isoformat(), "draft_revision": draft["draft_revision"],
                      "reference": "Fixture scheduler log"}],
            "exercises": [
                {**source, "kind": "partial_failure", "successful_approval_id": shorts_approval.stem,
                 "failed_channel": "x", "failure": "outside the approved window"},
                {**source, "kind": "replay", "approval_id": x_approval.stem,
                 "receipt_id": json.loads(x_receipt.read_bytes())["receipt_id"]},
                {**source, "kind": "withdrawal", "queued_approval_id": queued_approval.stem,
                 "correction_id": json.loads(correction.read_bytes())["correction_id"]},
            ],
        }
        for offset in range(1, 7):
            day = date(2026, 11, 21) + timedelta(days=offset)
            no_story, _ = self.draft(day)
            ledger["runs"].append({
                "scheduled_at": f"{day}T00:30:00+08:00", "draft_revision": no_story["draft_revision"],
                "reference": "Fixture scheduler log",
            })
        ledger["reviews"] = [
            {"approval_id": x_approval.stem, "minutes": 3, "reference": "Fixture review log"},
            {"approval_id": shorts_approval.stem, "minutes": 5, "reference": "Fixture review log"},
            {"draft_revision": no_story["draft_revision"], "minutes": 2, "reference": "Fixture review log"},
        ]
        ledger["metrics"] = {
            "qualified_evidence_visits": {"count": 7, "reference": "Fixture site query"},
            "completed_comparisons": {"count": 0, "reference": "Fixture site query"},
        }
        ledger["readiness"] = {
            channel: {"access": "unavailable", "readiness": "blocked", "reference": "Fixture channel review"}
            for channel in ("tiktok", "bilibili", "weibo", "wechat-official-account", "wechat-channels")
        }
        ledger["readiness"]["bilibili"].update(access="available", readiness="ready")
        ledger_path = self.root / "ledger.json"
        ledger_path.write_text(json.dumps(ledger))
        audit = self.audit("--operator-log", ledger_path)
        self.assertEqual(audit["status"], "incomplete")
        self.assertEqual(audit["mode"], "rehearsal")
        self.assertEqual(audit["days"][0]["scheduled_runs"], ledger["runs"][:1])
        self.assertEqual(audit["channels"]["x"]["published_in_window"], 1)
        self.assertEqual(audit["channels"]["youtube-shorts"]["published_in_window"], 1)
        self.assertEqual(audit["channels"]["youtube-shorts"]["corrections"], 1)
        outcomes = {entry["approval"]["approval_id"]: entry for entry in audit["days"][0]["deliveries"]}
        self.assertEqual(outcomes[expired_x_approval.stem]["status"], "superseded")
        self.assertEqual(outcomes[queued_approval.stem]["status"], "blocked_by_withdrawal")
        self.assertEqual(outcomes[shorts_approval.stem]["receipt"]["url"], POST_URL)
        self.assertEqual(outcomes[shorts_approval.stem]["correction"]["receipt_id"],
                         json.loads(shorts_receipt.read_bytes())["receipt_id"])
        self.assertEqual(audit["exercises"], ledger["exercises"])
        self.assertEqual(audit["gaps"], ["live_evidence_required"])
        self.assertEqual(audit["review_effort"]["recorded_minutes"], 10)
        self.assertEqual(audit["metrics"], ledger["metrics"])
        self.assertEqual(audit["expansion_candidates"], ["bilibili"])

        ledger["mode"] = "live"
        ledger_path.write_text(json.dumps(ledger))
        legacy = self.audit("--operator-log", ledger_path)
        self.assertEqual(legacy["status"], "incomplete")
        self.assertEqual(legacy["gaps"], ["engagement_evidence_unreported"])
        self.assertEqual(legacy["metrics"], ledger["metrics"])
        self.assertIsNone(legacy["engagement_evidence"])

        published = [json.loads(path.read_bytes()) for path in (x_receipt, shorts_receipt)]
        covered = [{"receipt_id": receipt["receipt_id"], "date": f"2026-11-{day}"}
                   for receipt in published for day in range(21, 28)]
        result_event = {
            "kind": "comparison_result", "occurred_at": "2026-11-27T23:59:59+08:00",
            "receipt_id": published[1]["receipt_id"], "post_url": POST_URL,
            "comparison_id": "564f807d-efec-4b27-b6ea-bea5bad55550",
        }
        engagement = self.write_engagement({
            "schema_version": 1, "mode": "live", "start_date": "2026-11-21",
            "reference": "Fixture first-party export",
            "coverage": {"qualified_evidence_visits": covered, "completed_comparisons": covered},
            "events": [result_event, {**result_event, "occurred_at": "2026-11-27T15:59:59Z"}],
        })
        complete = self.audit("--operator-log", ledger_path, "--engagement-export", engagement)
        self.assertEqual(complete["status"], "complete")
        self.assertEqual(complete["gaps"], [])
        self.assertEqual(complete["metrics"]["completed_comparisons"]["count"], 1)
        self.assertEqual(complete["metrics"]["qualified_evidence_visits"]["count"], 0)
        partial = json.loads(engagement.read_bytes())
        partial["coverage"]["completed_comparisons"].pop()
        incomplete = self.audit("--operator-log", ledger_path, "--engagement-export", self.write_engagement(partial))
        self.assertEqual(incomplete["gaps"], ["metric_unreported:completed_comparisons"])
        self.assertIsNone(incomplete["metrics"]["completed_comparisons"])

        ledger["metrics"]["completed_comparisons"]["count"] = True
        ledger_path.write_text(json.dumps(ledger))
        invalid = self.invoke("--operator-log", ledger_path)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("nonnegative integer", invalid.stderr)

        ledger["metrics"]["completed_comparisons"]["count"] = 0
        ledger_path.write_text(json.dumps(ledger))
        x_receipt.write_bytes(x_receipt.read_bytes().replace(b'Fixture operator', b'Somebody else'))
        tampered = self.invoke("--operator-log", ledger_path)
        self.assertEqual(tampered.returncode, 1)
        self.assertIn("failed receipt_id verification", tampered.stderr)
