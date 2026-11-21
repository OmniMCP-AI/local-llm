from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from zipfile import ZipFile

from fastest_delivery.approval import json_bytes, seal
from fastest_release import ReleaseStore
from fastest_release.capture_cpu import candidate


PRODUCTION = Path(__file__).resolve().parents[1]


class XDeliveryTest(unittest.TestCase):
    def run(self, result=None):
        try:
            return super().run(result)
        finally:
            self.doCleanups()

    def setUp(self):
        sandbox = tempfile.TemporaryDirectory(prefix="delivery-34-", dir="/tmp")
        self.addCleanup(lambda: self.assertFalse(Path(sandbox.name).exists()))
        self.directory = Path(self.enterContext(sandbox)).resolve()
        cluster = self.directory / "db"
        subprocess.run(
            ["initdb", "-D", str(cluster), "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        with (self.directory / "postgres.log").open("w") as log:
            postgres = subprocess.Popen(
                ["postgres", "-D", str(cluster), "-k", str(self.directory), "-c", "listen_addresses="],
                stdout=log, stderr=subprocess.STDOUT,
            )
        self.addCleanup(self.stop_postgres, postgres)
        self.database_url = f"host={self.directory} dbname=postgres"
        for _ in range(100):
            if subprocess.run(["pg_isready", "-d", self.database_url], capture_output=True).returncode == 0:
                break
            if postgres.poll() is not None:
                self.fail((self.directory / "postgres.log").read_text())
            time.sleep(0.05)
        else:
            self.fail("Delivery test database did not start")
        self.store = ReleaseStore(self.database_url)
        self.store.migrate()
        self.observation = json.loads((PRODUCTION / "fixtures" / "synthetic-observation.json").read_bytes())
        self.observation["kind"] = "measured"
        self.observation["source"]["label"] = "Example benchmark lab"
        self.observation["metric"]["value"] = "37.625000000001"
        self.release_id = self.store.publish(self.observation)
        self.evidence_url = f"https://benchmark.example/releases/{self.release_id}/benchmark.html#citation"
        self.now = datetime.now(timezone.utc).replace(microsecond=0)

    @staticmethod
    def stop_postgres(postgres):
        if postgres.poll() is None:
            postgres.send_signal(signal.SIGINT)
            try:
                postgres.wait(timeout=10)
            except subprocess.TimeoutExpired:
                postgres.kill()
                postgres.wait(timeout=10)
        assert postgres.returncode is not None

    def invoke(self, *args, module="fastest_delivery"):
        return subprocess.run(
            [sys.executable, "-B", "-m", module, *map(str, args)],
            cwd=PRODUCTION, capture_output=True, text=True, timeout=10,
        )

    def output_path(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(result.stdout.strip())

    def draft(self, locale):
        return self.output_path(self.invoke(
            "--database-url", self.database_url, "--public-origin", "https://benchmark.example",
            "--output-dir", self.directory / "editorial", "--date", "2026-11-21", "--locale", locale,
            module="fastest_editorial",
        ))

    def prepare_result(self, locale="zh-CN", *options):
        return self.invoke(
            "prepare", "--draft", self.draft(locale), "--database-url", self.database_url,
            "--output-dir", self.directory / "review", *options,
        )

    def prepare(self, locale="zh-CN"):
        return self.output_path(self.prepare_result(locale))

    @staticmethod
    def metadata(package):
        return json.loads((package / "package.json").read_bytes())

    def approve(self, package, **changes):
        options = {
            "account": "@benchmarklab",
            "window-start": (self.now - timedelta(minutes=5)).isoformat(),
            "window-end": (self.now + timedelta(minutes=5)).isoformat(),
            "approved-by": "editor@example.test",
            "rights-reference": "X reuse decision RX-421",
            "payload-sha256": self.metadata(package)["payload_sha256"],
            **changes,
        }
        arguments = [item for key, value in options.items() for item in (f"--{key}", value)]
        return self.invoke(
            "approve", "--package", package, "--approval-dir", self.directory / "approvals", *arguments,
        )

    def export(self, package, approval):
        return self.invoke(
            "export", "--package", package, "--approval", approval, "--database-url", self.database_url,
            "--delivery-dir", self.directory / "deliveries",
        )

    def receipt(self, approval, url="https://x.com/benchmarklab/status/1234567890123456789"):
        return self.invoke(
            "receipt", "--approval", approval, "--delivery-dir", self.directory / "deliveries",
            "--operator", "operator@example.test", "--url", url, "--published-at", self.now.isoformat(),
        )

    def publish_shared_cpu(self, *, source_label=None):
        observation = candidate({
            "runner": {"cpu_model": "Test CPU", "architecture": "x86_64", "image_version": "test"},
            "run_url": "https://benchmark.example/test-cpu-attempt",
            "median_tokens_per_second": "37.624926513815",
            "samples_ns": [3_402_000_000] * 7,
        }, "a" * 64)
        observation["rights"] = self.observation["rights"]
        if source_label is not None:
            observation["source"]["label"] = source_label
        for field in observation["fields"].values():
            field["rights"] = "allow"
        return observation, self.store.publish(observation)

    def test_shared_cpu_x_package_keeps_scope_and_exact_pinned_claim(self):
        observation, release_id = self.publish_shared_cpu()
        package = self.prepare(locale="en")
        metadata = self.metadata(package)
        story = metadata["draft"]["story"]
        claim_id = f"{release_id}:{observation['evidence_id']}:llama-bench-decode@1"
        self.assertEqual(story["claims"], [{
            **observation["metric"], "claim_id": claim_id, "evidence_id": observation["evidence_id"],
        }])
        self.assertEqual(story["copy"]["claim_refs"], [claim_id])
        evidence_url = f"https://benchmark.example/releases/{release_id}/benchmark.html#citation"
        self.assertEqual(story["evidence_destination"], evidence_url)
        self.assertEqual(
            (package / "post.txt").read_text(encoding="utf-8"),
            "Median decode throughput: 37.624926513815 tok/s (7 measurements)\n"
            "Shared CI runner, 1 CPU thread\n"
            f"Source: GitHub Actions CPU baseline capture\n{evidence_url}\n",
        )
        alt = (package / "chart-alt.txt").read_text(encoding="utf-8")
        for phrase in ("37.624926513815 tok/s (7 measurements)", "Shared CI runner, 1 CPU thread",
                       "Source: GitHub Actions CPU baseline capture"):
            self.assertIn(phrase, alt)
        from PIL import Image

        with Image.open(package / "chart.png") as chart:
            qualifier = chart.crop((56, 244, 944, 284))
            self.assertGreater(len(qualifier.getcolors()), 1)
        self.assertEqual(metadata["draft"]["release"]["release_id"], release_id)
        for name, expected in metadata["files"].items():
            self.assertEqual(sha256((package / name).read_bytes()).hexdigest(), expected)
        self.assertEqual(package.name, metadata["payload_sha256"])
        self.assertEqual(self.prepare(locale="en"), package)
        approval = self.output_path(self.approve(package))
        with ZipFile(self.output_path(self.export(package, approval))) as archive:
            for name in metadata["files"]:
                self.assertEqual(archive.read(name), (package / name).read_bytes())

    def test_shared_cpu_x_length_counts_scope_and_full_weighted_attribution(self):
        # The ASCII scope and the fixed X URL weight leave 152 units for the label.
        self.publish_shared_cpu(source_label="A" * 151 + "一")
        result = self.prepare_result("en")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("280-character limit", result.stderr)
        self.assertFalse((self.directory / "review").exists())

    def test_shared_cpu_x_chinese_chart_requires_a_font(self):
        self.publish_shared_cpu()
        for locale in ("zh-CN", "zh-TW"):
            with self.subTest(locale=locale):
                result = self.prepare_result(locale)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("--font-file", result.stderr)
                self.assertFalse((self.directory / "review").exists())

    def test_approval_cannot_export_shared_cpu_copy_without_scope(self):
        self.publish_shared_cpu()
        package = self.prepare(locale="en")
        metadata = self.metadata(package)
        metadata.pop("payload_sha256")
        for name, phrase in (("post.txt", b"Shared CI runner, 1 CPU thread\n"),
                             ("chart-alt.txt", b"Shared CI runner, 1 CPU thread. ")):
            path = package / name
            body = path.read_bytes().replace(phrase, b"")
            path.write_bytes(body)
            metadata["files"][name] = sha256(body).hexdigest()
        (package / "package.json").write_bytes(json_bytes(seal(metadata, "payload_sha256")))
        approval = self.output_path(self.approve(package))
        result = self.export(package, approval)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approved text differs from the pinned public evidence", result.stderr)
        self.assertFalse((self.directory / "deliveries").exists())

    def test_prepares_x_copy_chart_and_attribution_from_the_pinned_release(self):
        package = self.prepare()
        metadata = self.metadata(package)
        source = metadata["draft"]["story"]["attribution"]
        self.assertEqual(source["label"], "Example benchmark lab")
        self.assertEqual(source["locator"], "production/fixtures/synthetic-observation.json#/metric")
        self.assertEqual(
            (package / "post.txt").read_text(encoding="utf-8"),
            f"解码吞吐量中位数：37.625000000001 tok/s（5 次测量）\n"
            f"来源：Example benchmark lab\n{self.evidence_url}\n",
        )
        self.assertIn("37.625000000001 tok/s", (package / "chart-alt.txt").read_text(encoding="utf-8"))
        from PIL import Image

        with Image.open(package / "chart.png") as chart:
            self.assertEqual(chart.format, "PNG")
            chart.verify()
        self.assertEqual(self.prepare(), package)

    def test_exports_only_the_editor_approved_package_and_destination(self):
        package = self.prepare()
        self.assertNotEqual(self.export(package, self.directory / "missing.json").returncode, 0)
        self.assertFalse((self.directory / "deliveries").exists())
        approval_path = self.output_path(self.approve(package))
        archive_path = self.output_path(self.export(package, approval_path))
        with ZipFile(archive_path) as archive:
            for name in ("post.txt", "chart.png", "chart-alt.txt", "package.json"):
                self.assertEqual(archive.read(name), (package / name).read_bytes())
            approval = json.loads(archive.read("approval.json"))
        self.assertEqual(approval["account"], "@benchmarklab")
        self.assertEqual(approval["window_start"], (self.now - timedelta(minutes=5)).isoformat())
        self.assertEqual(approval["window_end"], (self.now + timedelta(minutes=5)).isoformat())
        self.assertEqual(approval["payload_sha256"], self.metadata(package)["payload_sha256"])
        self.assertEqual(approval["rights_reference"], "X reuse decision RX-421")

    def test_retries_reconcile_to_one_export_and_one_operator_receipt(self):
        package = self.prepare()
        approval = self.output_path(self.approve(package))
        self.assertNotEqual(self.receipt(approval).returncode, 0)

        archive = self.output_path(self.export(package, approval))
        self.assertFalse((archive.parent / "receipt.json").exists())
        modified = archive.stat().st_mtime_ns
        time.sleep(2.1)  # A ZIP with current timestamps would differ on retry.
        with ThreadPoolExecutor(max_workers=2) as pool:
            exports = list(pool.map(lambda _: self.output_path(self.export(package, approval)), range(2)))
        self.assertEqual(exports, [archive, archive])
        self.assertEqual(archive.stat().st_mtime_ns, modified)
        self.assertEqual(list(archive.parent.iterdir()), [archive])

        wrong_account = self.receipt(approval, "https://x.com/other/status/1234567890123456789")
        self.assertNotEqual(wrong_account.returncode, 0)
        with ThreadPoolExecutor(max_workers=2) as pool:
            receipts = list(pool.map(lambda _: self.output_path(self.receipt(approval)), range(2)))
        self.assertEqual(receipts, [archive.parent / "receipt.json"] * 2)
        confirmed = json.loads(receipts[0].read_bytes())
        self.assertEqual(confirmed["status"], "published")
        self.assertEqual(confirmed["url"], "https://x.com/benchmarklab/status/1234567890123456789")
        self.assertEqual(confirmed["post_id"], "1234567890123456789")
        self.assertEqual(confirmed["operator"], "operator@example.test")
        self.assertNotEqual(self.receipt(approval, "https://x.com/benchmarklab/status/999").returncode, 0)
        self.assertEqual(self.output_path(self.export(package, approval)), receipts[0])

    def test_queued_and_previously_exported_packages_stop_on_withdrawal(self):
        observation, _ = self.publish_shared_cpu()
        package = self.prepare(locale="en")
        pending = self.output_path(self.approve(package))
        prior = self.output_path(self.approve(package, account="@second_lab"))
        prior_archive = self.output_path(self.export(package, prior))
        self.store.withdraw(observation["evidence_id"], "private withdrawal reason")

        for approval in (pending, prior):
            result = self.export(package, approval)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("withdrawn_release", result.stderr)
            self.assertNotIn("private withdrawal reason", result.stderr)
            self.assertEqual(result.stdout, "")
        self.assertEqual(list((self.directory / "deliveries").glob("*/*")), [prior_archive])

    def test_different_payload_and_out_of_window_export_are_rejected(self):
        package = self.prepare()
        expired = self.output_path(self.approve(
            package, **{"window-end": (self.now - timedelta(minutes=1)).isoformat()},
        ))
        result = self.export(package, expired)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the approved window", result.stderr)

        approval = self.output_path(self.approve(package))
        english_package = self.prepare(locale="en")
        result = self.export(english_package, approval)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approval does not cover this package", result.stderr)

        (package / "post.txt").write_text("Replacement text\n", encoding="utf-8")
        result = self.export(package, approval)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("package bytes differ", result.stderr)
        self.assertFalse((self.directory / "deliveries").exists())
