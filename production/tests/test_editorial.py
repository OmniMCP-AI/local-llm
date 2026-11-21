from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from fastest_release import ReleaseStore
from fastest_release.capture_cpu import candidate


PRODUCTION = Path(__file__).resolve().parents[1]
FIXTURE = PRODUCTION / "fixtures" / "synthetic-observation.json"


class EditorialTest(unittest.TestCase):
    def run(self, result=None):
        try:
            return super().run(result)
        finally:
            self.doCleanups()

    def setUp(self):
        sandbox = tempfile.TemporaryDirectory(prefix="editorial-33-", dir="/tmp")
        self.addCleanup(lambda: self.assertFalse(Path(sandbox.name).exists()))
        directory = Path(self.enterContext(sandbox))
        cluster = directory / "db"
        subprocess.run(
            ["initdb", "-D", str(cluster), "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True,
            capture_output=True,
            text=True,
        )
        with (directory / "postgres.log").open("w") as log:
            postgres = subprocess.Popen(
                ["postgres", "-D", str(cluster), "-k", str(directory), "-c", "listen_addresses="],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        self.addCleanup(self.stop_postgres, postgres)
        self.database_url = f"host={directory} dbname=postgres"
        for _ in range(100):
            if subprocess.run(["pg_isready", "-d", self.database_url], capture_output=True).returncode == 0:
                break
            if postgres.poll() is not None:
                self.fail((directory / "postgres.log").read_text())
            time.sleep(0.05)
        else:
            self.fail("Editorial test database did not start")
        self.store = ReleaseStore(self.database_url)
        self.store.migrate()
        self.sql("""
            CREATE ROLE editorial_reader LOGIN;
            GRANT USAGE ON SCHEMA fastest_release TO editorial_reader;
            GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid) TO editorial_reader;
        """)
        self.output = directory / "drafts"
        self.observation = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.observation["kind"] = "measured"
        self.observation["metric"]["value"] = "37.625000000001"

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

    def sql(self, statement):
        subprocess.run(
            ["psql", "-XqAtw", "-v", "ON_ERROR_STOP=1", "-d", self.database_url],
            input=statement,
            text=True,
            capture_output=True,
            check=True,
        )

    def invoke(self, *options):
        return subprocess.run(
            [
                sys.executable, "-B", "-m", "fastest_editorial",
                "--database-url", f"{self.database_url} user=editorial_reader",
                "--public-origin", "https://benchmark.example",
                "--date", "2026-11-21",
                "--output-dir", str(self.output),
                *options,
            ],
            cwd=PRODUCTION,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def draft(self, *options):
        result = self.invoke(*options)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = Path(result.stdout.strip())
        return record, json.loads(record.read_bytes())

    def run_slot(self, *options, entrypoint=("-m", "fastest_delivery.run_slot")):
        return subprocess.run(
            [
                sys.executable, "-B", *entrypoint,
                "--database-url", f"{self.database_url} user=editorial_reader",
                "--public-origin", "https://benchmark.example",
                "--scheduled-at", "2026-11-20T16:30:00Z",
                "--mode", "rehearsal",
                "--draft-dir", str(self.output),
                "--run-dir", str(self.output.parent / "scheduler"),
                *options,
            ],
            cwd=PRODUCTION, capture_output=True, text=True, timeout=10,
        )

    def slot_audit(self, *options):
        result = subprocess.run(
            [
                sys.executable, "-B", "-m", "fastest_delivery.pilot",
                "--start", "2026-11-21", "--draft-dir", str(self.output),
                "--run-dir", str(self.output.parent / "scheduler"),
                *options,
            ],
            cwd=PRODUCTION, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_scheduled_no_story_is_replayed_from_the_original_slot(self):
        result = self.run_slot()
        self.assertEqual(result.returncode, 0, result.stderr)
        (draft,) = (self.output / "2026-11-21").glob("*.json")
        original = json.loads(draft.read_bytes())
        self.assertEqual(original["reason"], "no_current_release")

        self.store.publish(self.observation)
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(
                lambda _: self.run_slot("--scheduled-at", "2026-11-21T00:30:00+08:00"), range(2),
            ))
        for replay in results:
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertEqual(replay.stdout, result.stdout)
        self.assertEqual(list(draft.parent.iterdir()), [draft])

        operator_log = self.output.parent / "operator-log.json"
        operator_log.write_text(json.dumps({
            "schema_version": 1,
            "start_date": "2026-11-21",
            "mode": "rehearsal",
            "reviews": [{
                "draft_revision": original["draft_revision"], "minutes": 2, "reference": "Fixture review log",
            }],
        }))
        audit = self.slot_audit("--operator-log", str(operator_log))
        self.assertEqual(audit["mode"], "rehearsal")
        self.assertEqual(audit["review_effort"]["recorded_minutes"], 2)
        day = audit["days"][0]
        self.assertEqual(day["status"], "no_story")
        (slot,) = day["scheduled_runs"]
        self.assertEqual(slot["scheduled_at"], "2026-11-21T00:30:00+08:00")
        self.assertEqual(slot["draft_revision"], original["draft_revision"])
        self.assertEqual(len(slot["attempts"]), 1)
        self.assertTrue(Path(slot["reference"]).is_file())
        self.assertIn("scheduled_run_unreported:2026-11-22", audit["gaps"])

    def test_scheduled_database_failure_is_reported_and_can_retry_once(self):
        invalid_connection = (
            "--database-url", f"{self.database_url} user=missing_runner password=slot-secret",
        )
        failed = self.run_slot(*invalid_connection)
        self.assertEqual(failed.returncode, 1, failed.stderr)
        self.assertNotIn("slot-secret", failed.stderr)
        day = self.slot_audit()["days"][0]
        self.assertEqual(day["status"], "failed")
        (slot,) = day["scheduled_runs"]
        self.assertEqual(slot["error"], "release database read failed")
        self.assertEqual(len(slot["attempts"]), 1)
        self.assertNotIn("slot-secret", Path(slot["reference"]).read_text())

        recovered = self.run_slot()
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        day = self.slot_audit()["days"][0]
        self.assertEqual(day["status"], "no_story")
        (slot,) = day["scheduled_runs"]
        self.assertNotIn("error", slot)
        self.assertEqual(slot["attempts"][0]["error"], "release database read failed")
        self.assertEqual(slot["draft_revision"], day["drafts"][0]["draft_revision"])
        self.assertEqual(len(slot["attempts"]), 2)

        another_slot = ("--scheduled-at", "2026-11-22T00:30:00+08:00")
        for _ in range(2):
            self.assertEqual(self.run_slot(*another_slot, *invalid_connection).returncode, 1)
        self.assertEqual(self.run_slot(*another_slot).returncode, 1)
        (exhausted,) = self.slot_audit()["days"][1]["scheduled_runs"]
        self.assertEqual(exhausted["error"], "release database read failed")
        self.assertEqual(len(exhausted["attempts"]), 2)

    def test_scheduled_retry_recovers_the_selected_draft_after_storage_failure(self):
        release_id = self.store.publish(self.observation)
        blocked = self.output / "2026-11-21"
        self.output.mkdir()
        blocked.touch()

        failed = self.run_slot()
        self.assertEqual(failed.returncode, 1, failed.stderr)
        (slot,) = self.slot_audit()["days"][0]["scheduled_runs"]
        self.assertEqual(slot["error"], "editorial draft could not be retained")

        self.store.withdraw(self.observation["evidence_id"], "fixture withdrawal")
        blocked.unlink()
        recovered = self.run_slot()
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        day = self.slot_audit()["days"][0]
        self.assertEqual(day["status"], "story")
        (slot,) = day["scheduled_runs"]
        (draft,) = day["drafts"]
        self.assertEqual(slot["attempts"][0]["error"], "editorial draft could not be retained")
        self.assertEqual(slot["draft_revision"], draft["draft_revision"])
        self.assertEqual(draft["release"]["release_id"], release_id)
        self.assertEqual(draft["story"]["claims"][0]["value"], "37.625000000001")

    def test_interrupted_outcome_write_reconciles_the_retained_draft(self):
        crash_before_commit = """
import json
import os
from pathlib import Path
import sys

from fastest_delivery.run_slot import main


def stop_before_outcome(event, args):
    if event == "os.rename":
        source, destination, *_ = args
        if Path(destination).suffix == ".json" and "draft_revision" in json.loads(Path(source).read_bytes()):
            os._exit(99)


sys.addaudithook(stop_before_outcome)
main(sys.argv[1:])
"""
        interrupted = self.run_slot(entrypoint=("-c", crash_before_commit))
        self.assertEqual(interrupted.returncode, 99, interrupted.stderr)
        (draft,) = (self.output / "2026-11-21").glob("*.json")
        self.assertIn("scheduled_run_unreported:2026-11-21", self.slot_audit()["gaps"])

        self.store.publish(self.observation)
        recovered = self.run_slot()
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        (slot,) = self.slot_audit()["days"][0]["scheduled_runs"]
        self.assertEqual(slot["draft_revision"], draft.stem)
        self.assertEqual(len(slot["attempts"]), 1)
        self.assertTrue(slot["attempts"][0]["reconciled_at"])

    def test_new_live_slot_cannot_be_backdated(self):
        result = self.run_slot("--mode", "live", "--scheduled-at", "2020-01-01T00:30:00+08:00")
        self.assertEqual(result.returncode, 1)
        self.assertIn("today's Asia/Shanghai editorial date", result.stderr)
        self.assertFalse(list((self.output.parent / "scheduler").rglob("*.json")))

    def test_draft_pins_verified_numeric_claim_and_attribution(self):
        release_id = self.store.publish(self.observation)
        path, package = self.draft("--locale", "zh-CN")
        self.assertEqual(package["outcome"], "story")
        self.assertEqual(package["editorial_date"], "2026-11-21")
        self.assertEqual(package["editorial_timezone"], "Asia/Shanghai")
        self.assertEqual(package["locale"], "zh-CN")
        self.assertEqual(package["release"]["release_id"], release_id)
        self.assertEqual(package["release"]["revision"], 1)
        table = self.store.artifact(release_id, "table.json")
        self.assertEqual(package["release"]["table_sha256"], sha256(table.encode()).hexdigest())

        story = package["story"]
        claim, = story["claims"]
        self.assertEqual(claim["value"], "37.625000000001")
        self.assertEqual(claim["unit"], "tok/s")
        self.assertEqual(claim["evidence_id"], "c5258a75-75ec-465f-8cbc-1212b749fddd")
        self.assertEqual(story["copy"]["claim_refs"], [claim["claim_id"]])
        self.assertIn("解码", story["copy"]["headline"])
        self.assertIn("37.625000000001 tok/s", story["copy"]["body"])
        self.assertEqual(story["attribution"], self.observation["source"])
        self.assertEqual(story["evidence_destination"], f"https://benchmark.example/releases/{release_id}/benchmark.html#citation")
        self.assertEqual(story["rights"]["decision_id"], self.observation["rights"]["decision_id"])
        self.assertEqual(story["media"], [])
        self.assertNotIn(b"private calibration note", path.read_bytes())

    def test_shared_cpu_decode_draft_preserves_claim_identity_across_languages(self):
        observation = candidate({
            "runner": {"cpu_model": "Test CPU", "architecture": "x86_64", "image_version": "test"},
            "run_url": "https://benchmark.example/test-cpu-attempt",
            "median_tokens_per_second": "37.624926513815",
            "samples_ns": [3_402_000_000] * 7,
        }, "a" * 64)
        observation["rights"] = self.observation["rights"]
        for field in observation["fields"].values():
            field["rights"] = "allow"
        release_id = self.store.publish(observation)
        claim_id = f"{release_id}:{observation['evidence_id']}:llama-bench-decode@1"
        drafts = set()
        for locale, wording in (
            ("en", ("shared CI runner", "one CPU thread", "empty KV cache", "7 repetitions")),
            ("zh-CN", ("共享 CI 运行器", "单个 CPU 线程", "空 KV 缓存", "7 次重复测量")),
            ("zh-TW", ("共用 CI 執行器", "單一 CPU 執行緒", "空的 KV 快取", "7 次重複測量")),
        ):
            with self.subTest(locale=locale):
                _, package = self.draft("--locale", locale, "--release", release_id)
                self.assertEqual(package["outcome"], "story")
                story = package["story"]
                self.assertEqual(story["claims"], [{
                    **observation["metric"], "claim_id": claim_id, "evidence_id": observation["evidence_id"],
                }])
                self.assertEqual(story["copy"]["claim_refs"], [claim_id])
                self.assertEqual(story["benchmark_conditions"]["workload"], observation["workload"])
                self.assertEqual(story["attribution"], observation["source"])
                self.assertEqual(story["media"], [])
                for phrase in (*wording, "37.624926513815 tok/s"):
                    self.assertIn(phrase, story["copy"]["body"])
                drafts.add(package["draft_revision"])
        self.assertEqual(len(drafts), 3)

    def test_ineligible_release_records_no_story_without_exposing_claims(self):
        _, missing = self.draft()
        self.assertEqual(missing["outcome"], "no_story")
        self.assertEqual(missing["reason"], "no_current_release")
        self.assertIsNone(missing["release"])

        self.observation["kind"] = "synthetic"
        self.observation["metric"]["value"] = "19.75"
        release_id = self.store.publish(self.observation)
        _, synthetic = self.draft()
        self.assertEqual(synthetic["outcome"], "no_story")
        self.assertEqual(synthetic["reason"], "synthetic_release")
        self.assertEqual(synthetic["release"]["release_id"], release_id)
        self.assertNotIn("story", synthetic)

        self.store.withdraw(self.observation["evidence_id"], "internal withdrawal reason")
        path, withdrawn = self.draft("--release", release_id)
        self.assertEqual(withdrawn["outcome"], "no_story")
        self.assertEqual(withdrawn["reason"], "withdrawn_release")
        self.assertEqual(withdrawn["release"]["release_id"], release_id)
        self.assertNotIn("story", withdrawn)
        self.assertNotIn(b"19.75", path.read_bytes())
        self.assertNotIn(b"internal withdrawal reason", path.read_bytes())

    def test_replay_preserves_existing_package_for_parallel_retries(self):
        release_id = self.store.publish(self.observation)
        path, package = self.draft()
        modified = path.stat().st_mtime_ns
        options = ("--release", release_id)
        with ThreadPoolExecutor(max_workers=2) as workers:
            replayed = list(workers.map(lambda _: self.draft(*options), range(2)))
        self.assertEqual(replayed, [(path, package), (path, package)])
        self.assertEqual(path.stat().st_mtime_ns, modified)
        self.assertEqual(list(path.parent.iterdir()), [path])

        revision = package.pop("draft_revision")
        canonical = json.dumps(package, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        self.assertEqual(revision, sha256(canonical.encode("utf-8")).hexdigest())
        self.assertEqual(path.stem, revision)

    def test_correction_creates_a_new_revision_and_keeps_a_pinned_draft(self):
        original_id = self.store.publish(self.observation)
        original_path, original = self.draft("--locale", "zh-TW")
        self.assertEqual(original["story"]["kind"], "evergreen")
        self.assertIn("解碼", original["story"]["copy"]["headline"])

        self.observation["metric"]["value"] = "42.125000000001"
        self.observation["source"]["revision"] = "fixture-v2"
        corrected_id = self.store.publish(self.observation)
        corrected_path, corrected = self.draft("--locale", "zh-TW")
        self.assertNotEqual(corrected_path, original_path)
        self.assertEqual(corrected["release"]["release_id"], corrected_id)
        self.assertEqual(corrected["release"]["revision"], 2)
        self.assertEqual(corrected["story"]["kind"], "correction")
        self.assertIn("修訂", corrected["story"]["copy"]["headline"])
        self.assertIn("42.125000000001 tok/s", corrected["story"]["copy"]["body"])
        self.assertNotIn("37.625000000001", corrected["story"]["copy"]["body"])
        self.assertEqual(self.draft("--locale", "zh-TW", "--release", original_id), (original_path, original))

    def test_unrecognized_benchmark_records_no_story_instead_of_mislabeled_copy(self):
        self.sql("""
            INSERT INTO fastest_release.metric_definition
                (metric_key, version, unit, statistic, boundary)
            VALUES ('prefill-throughput', 1, 'tok/s', 'median', 'Tokens per second during prefill.');
        """)
        self.observation["metric"].update(id="prefill-throughput", boundary="Tokens per second during prefill.")
        release_id = self.store.publish(self.observation)
        _, package = self.draft()
        self.assertEqual(package["outcome"], "no_story")
        self.assertEqual(package["reason"], "unsupported_metric")
        self.assertEqual(package["release"]["release_id"], release_id)
