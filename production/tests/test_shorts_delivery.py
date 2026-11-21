from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from fastest_delivery import shorts
from fastest_editorial import generate_package
from fastest_release.artifacts import build_artifacts


RELEASE_ID = "7b52433e-e6b7-4cf1-967b-293c1c85bc80"
CHANNEL_ID = "UCabcdefghijklmnopqrstuv"
POST_URL = "https://www.youtube.com/shorts/Abc_123-deF"
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic-observation.json"


class PublicRelease:
    def __init__(self):
        row = json.loads(FIXTURE.read_bytes())
        row["kind"] = "measured"
        row["metric"]["value"] = "37.625000000001"
        row["source"]["label"] = "Example benchmark lab"
        row["fields"] = {}
        self.snapshot = {
            "release_id": RELEASE_ID, "revision": 1, "status": "published",
            "schema_version": 1, "previous_release_id": None, "row": row,
        }

    def read(self, release_id):
        assert release_id == RELEASE_ID
        return self.snapshot

    def read_evidence(self, evidence_id):
        assert evidence_id == "c5258a75-75ec-465f-8cbc-1212b749fddd"
        return getattr(self, "latest", self.snapshot)

    def artifact(self, release_id, name):
        return build_artifacts(self.read(release_id))[name]


class ShortsDeliveryTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory(prefix="shorts-35-")))
        self.store = PublicRelease()
        self.now = datetime.now(timezone.utc)
        self.delivery_dir = self.directory / "deliveries"

    def draft(self, locale="en"):
        story = generate_package(
            self.store, editorial_date=date(2026, 11, 21), locale=locale,
            public_origin="https://benchmark.example", release_id=RELEASE_ID,
        )
        path = self.directory / f"{locale}.json"
        path.write_text(json.dumps(story), encoding="utf-8")
        return path

    def approve(self, package, **overrides):
        options = {
            "account": CHANNEL_ID,
            "payload_sha256": package.name,
            "window_start": (self.now - timedelta(minutes=2)).isoformat(),
            "window_end": (self.now + timedelta(minutes=2)).isoformat(),
            "approved_by": "editor@example.test",
            "rights_reference": "YouTube release clearance YT-421",
            **overrides,
        }
        return shorts.approve(package, self.directory / "approvals", **options)

    def test_render_has_vertical_video_timed_captions_and_exact_evidence(self):
        package = shorts.prepare(self.store, self.draft(), self.directory / "review")
        metadata = json.loads((package / "package.json").read_bytes())
        video = package / "short.mp4"
        stream, = json.loads(subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(video)],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout)["streams"]
        self.assertEqual((stream["codec_name"], stream["width"], stream["height"]), ("h264", 720, 1280))
        self.assertEqual(float(stream["duration"]), 15)
        self.assertEqual(metadata["files"]["short.mp4"], sha256(video.read_bytes()).hexdigest())
        self.assertEqual(metadata["channel"], "youtube-shorts")
        self.assertEqual(metadata["draft"]["locale"], "en")
        claim, = metadata["draft"]["story"]["claims"]
        self.assertEqual(claim["claim_id"], f"{RELEASE_ID}:c5258a75-75ec-465f-8cbc-1212b749fddd:decode-throughput@1")
        self.assertIn("37.625000000001 tok/s", (package / "captions.srt").read_text())
        self.assertIn("00:00:15,000", (package / "captions.srt").read_text())
        description = (package / "description.txt").read_text()
        self.assertIn("Example benchmark lab", description)
        self.assertIn(f"https://benchmark.example/releases/{RELEASE_ID}/benchmark.html#citation", description)

    def test_exact_approval_exports_one_immutable_handoff(self):
        package = shorts.prepare(self.store, self.draft(), self.directory / "review")
        with self.assertRaisesRegex(ValueError, "digest differs"):
            self.approve(package, payload_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "clearance|rights"):
            self.approve(package, rights_reference="")
        approval = self.approve(package)
        export = shorts.export(self.store, package, approval, self.delivery_dir)
        with ZipFile(export) as archive:
            self.assertEqual(archive.read("short.mp4"), (package / "short.mp4").read_bytes())
            reviewed = json.loads(archive.read("approval.json"))
        self.assertEqual(reviewed["account"], CHANNEL_ID)
        self.assertEqual(reviewed["channel"], "youtube-shorts")
        self.assertEqual(reviewed["rights_reference"], "YouTube release clearance YT-421")
        self.assertEqual(reviewed["payload_sha256"], package.name)
        self.assertEqual(shorts.export(self.store, package, approval, self.delivery_dir), export)

        video = package / "short.mp4"
        video.write_bytes(video.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "package bytes differ"):
            shorts.export(self.store, package, approval, self.delivery_dir)

    def test_receipt_reconciles_operator_confirmation_to_the_original_short(self):
        package = shorts.prepare(self.store, self.draft(), self.directory / "review")
        approval = self.approve(package)
        options = {
            "url": POST_URL, "account": CHANNEL_ID, "published_at": self.now.isoformat(),
            "operator": "operator@example.test",
        }
        with self.assertRaises(FileNotFoundError):
            shorts.record_receipt(approval, self.delivery_dir, **options)
        handoff = shorts.export(self.store, package, approval, self.delivery_dir)
        with self.assertRaisesRegex(ValueError, "approved channel"):
            shorts.record_receipt(approval, self.delivery_dir, **{**options, "account": "UC" + "a" * 22})
        receipt_path = shorts.record_receipt(approval, self.delivery_dir, **options)
        receipt = json.loads(receipt_path.read_bytes())
        self.assertEqual(receipt["account"], CHANNEL_ID)
        self.assertEqual(receipt["post_id"], "Abc_123-deF")
        self.assertEqual(receipt["url"], POST_URL)
        self.assertEqual(receipt["release_id"], RELEASE_ID)
        self.assertEqual(shorts.record_receipt(approval, self.delivery_dir, **options), receipt_path)
        with self.assertRaisesRegex(ValueError, "conflicting record"):
            shorts.record_receipt(approval, self.delivery_dir, **{**options, "url": POST_URL[:-1] + "G"})
        self.assertEqual(shorts.export(self.store, package, approval, self.delivery_dir), receipt_path)
        self.assertEqual(sorted(path.name for path in handoff.parent.iterdir()), ["receipt.json", "youtube-short.zip"])

    def test_tracked_short_requires_exact_reconciled_link(self):
        key = "7b52433e-e6b7-4cf1-967b-293c1c85bc81"
        link = f"https://benchmark.example/pilot/evidence/{RELEASE_ID}/{key}#citation"
        package = shorts.prepare(self.store, self.draft(), self.directory / "review", engagement_key=key)
        approval = self.approve(package)
        handoff = shorts.export(self.store, package, approval, self.delivery_dir)
        with ZipFile(handoff) as archive:
            self.assertIn(link, archive.read("description.txt").decode().splitlines())
        options = {"url": POST_URL, "account": CHANNEL_ID, "published_at": self.now.isoformat(),
                   "operator": "operator@example.test"}
        with self.assertRaisesRegex(ValueError, "engagement link"):
            shorts.record_receipt(approval, self.delivery_dir, **options, observed_engagement_url=link[:-1])
        receipt = shorts.record_receipt(approval, self.delivery_dir, **options, observed_engagement_url=link)
        self.assertEqual(json.loads(receipt.read_bytes())["engagement_url"], link)

    def test_withdrawal_holds_queued_exports_and_routes_the_recorded_short_once(self):
        package = shorts.prepare(self.store, self.draft(), self.directory / "review")
        queued = self.approve(package, account="UC" + "a" * 22)
        published = self.approve(package)
        shorts.export(self.store, package, published, self.delivery_dir)
        receipt = shorts.record_receipt(
            published, self.delivery_dir, account=CHANNEL_ID, url=POST_URL,
            published_at=self.now.isoformat(), operator="operator@example.test",
        )
        self.assertEqual(shorts.corrections(self.store, self.delivery_dir), [])
        self.store.snapshot["status"] = "withdrawn"
        del self.store.snapshot["row"]

        with self.assertRaisesRegex(ValueError, "withdrawn_release"):
            shorts.export(self.store, package, queued, self.delivery_dir)
        self.assertEqual(shorts.export(self.store, package, published, self.delivery_dir), receipt)
        correction_path, = shorts.corrections(self.store, self.delivery_dir)
        self.assertEqual(correction_path, receipt.with_name("correction.json"))
        task = json.loads(correction_path.read_bytes())
        self.assertEqual(task["status"], "needs_correction")
        self.assertEqual(task["reason"], "withdrawn_release")
        self.assertEqual(task["account"], CHANNEL_ID)
        self.assertEqual(task["url"], POST_URL)
        self.assertEqual(task["release_id"], RELEASE_ID)
        self.assertEqual(task["receipt_id"], json.loads(receipt.read_bytes())["receipt_id"])
        self.assertEqual(shorts.corrections(self.store, self.delivery_dir), [correction_path])

    def test_superseded_release_holds_new_exports_but_preserves_a_live_receipt(self):
        package = shorts.prepare(self.store, self.draft(), self.directory / "review")
        live = self.approve(package)
        queued = self.approve(package, account="UC" + "a" * 22)
        shorts.export(self.store, package, live, self.delivery_dir)
        receipt = shorts.record_receipt(
            live, self.delivery_dir, account=CHANNEL_ID, url=POST_URL,
            published_at=self.now.isoformat(), operator="operator@example.test",
        )
        self.store.latest = {**self.store.snapshot, "release_id": "e343f9c9-285b-420d-b181-7324f27046b8", "revision": 2}
        with self.assertRaisesRegex(ValueError, "superseded_release"):
            shorts.export(self.store, package, queued, self.delivery_dir)
        self.assertEqual(shorts.export(self.store, package, live, self.delivery_dir), receipt)
        task_path, = shorts.corrections(self.store, self.delivery_dir)
        task = json.loads(task_path.read_bytes())
        self.assertEqual(task["reason"], "superseded_release")
        self.assertEqual(task["replacement_release_id"], self.store.latest["release_id"])
        self.assertEqual(shorts.corrections(self.store, self.delivery_dir), [task_path])
