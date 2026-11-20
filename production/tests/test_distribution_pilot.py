from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastest_delivery import shorts, x_post
from fastest_editorial import generate_package
from fastest_editorial.__main__ import _record
from fastest_release import ReleaseNotFound
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
            public_origin="https://benchmark.example",
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
        complete = self.audit("--operator-log", ledger_path)
        self.assertEqual(complete["status"], "complete")
        self.assertEqual(complete["gaps"], [])

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
