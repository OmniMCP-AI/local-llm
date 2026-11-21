from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from uuid import uuid4


PRODUCTION = Path(__file__).resolve().parents[1]
FIXTURES = PRODUCTION / "fixtures" / "discoveries"
VIDEO_SAMPLE = Path("opendesign/mockups/llm-observatory/battle-title-sample.json")
ORIGINAL = "https://forum.example/topics/local-models/18"
SOURCE_DATE = "2026-11-19T12:30:00Z"
CROSS_POST = "https://video.example/watch/local-models-repost"
DISCOVERY_ONLY = "https://social.example/posts/63"
DELETED = "https://forum.example/topics/local-models/24"
LOCAL_ENV = {key: value for key, value in os.environ.items() if not key.startswith("PG")}


class DiscoveryCases:
    connection = None

    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="fastest-discoveries-22-")))
        self.database = self.directory / "discoveries.sqlite3"

    def invoke_cli(self, *args, connection=None, legacy=False):
        database_url = None if legacy else connection or self.connection
        options = ["--db", self.database] if database_url is None else []
        env = {**LOCAL_ENV}
        if database_url is not None:
            env["FASTEST_DISCOVERIES_DATABASE_URL"] = database_url
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_discoveries", *options, *args],
            cwd=PRODUCTION, env=env, capture_output=True, text=True, timeout=15,
        )

    def run_cli(self, *args, succeeds=True, **kwargs):
        result = self.invoke_cli(*args, **kwargs)
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result.stderr

    def review(self, source, choice, **kwargs):
        return self.run_cli(
            "review", source, choice, "--reviewer", "fixture-editor",
            "--reason", "Reviewed public permalink and opt-in.", **kwargs,
        )

    def test_attributed_submission_is_private_until_approved(self):
        first = self.run_cli("submit", FIXTURES / "original.json")
        self.assertEqual(self.run_cli("submit", FIXTURES / "original.json"), first)
        candidate, = self.run_cli("queue")["entries"]
        self.assertEqual(candidate["source_url"], ORIGINAL)
        self.assertEqual(candidate["original_url"], ORIGINAL)
        self.assertEqual(candidate["published_at"], SOURCE_DATE)
        self.assertEqual(candidate["consent"]["authority"], "rights_holder")
        self.assertEqual(candidate["consent"]["reference"], "fixture-original-grant")
        self.assertEqual(candidate["status"], "pending")
        self.assertEqual(self.run_cli("public")["entries"], [])

        decision = self.review(ORIGINAL, "approve")
        self.assertEqual(decision["choice"], "approve")
        self.assertEqual(self.run_cli("public")["entries"], [{
            "status": "approved", "reason": "source_link_approved",
            "source_url": ORIGINAL, "published_at": SOURCE_DATE,
        }])

    def test_cross_post_points_to_original_and_never_publishes_twice(self):
        self.run_cli("submit", FIXTURES / "cross-post.json")
        duplicate, = self.run_cli("queue")["entries"]
        self.assertEqual((duplicate["source_url"], duplicate["original_url"]), (CROSS_POST, ORIGINAL))
        self.assertEqual(duplicate["reason"], "cross_post")
        self.assertIn("cross_post", self.review(CROSS_POST, "approve", succeeds=False))

        self.run_cli("submit", FIXTURES / "original.json")
        self.review(ORIGINAL, "approve")
        self.assertEqual(self.run_cli("public")["entries"], [
            {"status": "approved", "reason": "source_link_approved", "source_url": ORIGINAL,
             "published_at": SOURCE_DATE},
            {"status": "withheld", "reason": "cross_post"},
        ])

    def test_discovery_only_is_attributed_internally_and_withheld_publicly(self):
        self.run_cli("submit", FIXTURES / "discovery-only.json")
        restricted, = self.run_cli("queue")["entries"]
        self.assertEqual(restricted["source_url"], DISCOVERY_ONLY)
        self.assertIsNone(restricted["published_at"])
        self.assertEqual(restricted["consent"]["scope"], "discovery_only")
        self.assertIn("discovery_only", self.review(DISCOVERY_ONLY, "approve", succeeds=False))
        self.review(DISCOVERY_ONLY, "withhold")
        self.assertEqual(self.run_cli("public")["entries"], [
            {"status": "withheld", "reason": "discovery_only"},
        ])

    def test_deleted_source_suppresses_a_previous_approval_after_replay(self):
        self.run_cli("submit", FIXTURES / "deleted.json")
        prior = self.review(DELETED, "approve")
        self.assertEqual(self.run_cli("public")["entries"][0]["source_url"], DELETED)

        withdrawal = self.run_cli("withdraw", DELETED, "--reason", "source_deleted")
        self.assertEqual(self.run_cli("withdraw", DELETED, "--reason", "source_deleted"), withdrawal)
        self.run_cli("submit", FIXTURES / "deleted.json")
        self.assertEqual(self.review(DELETED, "approve"), prior)

        deleted, = self.run_cli("queue")["entries"]
        self.assertEqual(deleted["review"]["choice"], "approve")
        self.assertEqual(deleted["withdrawal"]["reason"], "source_deleted")
        self.assertEqual(self.run_cli("public")["entries"], [
            {"status": "withheld", "reason": "source_deleted"},
        ])

    def test_review_cannot_be_replaced_or_publish_the_editor_note(self):
        self.run_cli("submit", FIXTURES / "original.json")
        decision = self.review(ORIGINAL, "withhold")
        self.assertEqual(self.review(ORIGINAL, "withhold"), decision)
        self.assertIn("immutable", self.review(ORIGINAL, "approve", succeeds=False))
        self.assertEqual(self.run_cli("queue")["entries"][0]["review"]["reason"], decision["reason"])
        self.assertEqual(self.run_cli("public")["entries"], [
            {"status": "withheld", "reason": "editor_withheld"},
        ])

    def test_submission_requires_explicit_scope_and_excludes_private_payload(self):
        valid = json.loads((FIXTURES / "original.json").read_text(encoding="utf-8"))
        draft = self.directory / "submission.json"
        for invalid in (
            {**valid, "consent": {**valid["consent"], "scope": "unknown"}},
            {**valid, "consent": {**valid["consent"], "authority": "anonymous"}},
            {**valid, "body": "private body"},
            {**valid, "source_url": "https://forum.example/topics/18?token=secret"},
            {**valid, "source_url": "https://forum.example/topics/18#access_token=secret"},
        ):
            draft.write_text(json.dumps(invalid), encoding="utf-8")
            self.run_cli("submit", draft, succeeds=False)
        conflicting_scope = json.dumps(valid).replace(
            '"scope": "public_source_link"',
            '"scope": "discovery_only", "scope": "public_source_link"',
        )
        draft.write_text(conflicting_scope, encoding="utf-8")
        self.assertIn("duplicate", self.run_cli("submit", draft, succeeds=False))
        self.assertEqual(self.run_cli("queue")["entries"], [])


class DiscoveryTest(DiscoveryCases, unittest.TestCase):
    pass


@unittest.skipUnless(
    all(shutil.which(tool) for tool in ("initdb", "postgres", "pg_isready", "createdb", "psql")),
    "PostgreSQL command-line tools required",
)
class PostgresDiscoveryTest(DiscoveryCases, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="fastest-discoveries-pg-", dir="/tmp")
        cls.addClassCleanup(cls.assert_removed, temporary.name)
        cls.socket = Path(cls.enterClassContext(temporary))
        cluster = cls.socket / "db"
        subprocess.run(
            ["initdb", "-D", cluster, "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True, capture_output=True, timeout=30, env=LOCAL_ENV,
        )
        server_log = cls.socket / "postgres.log"
        with server_log.open("w") as output:
            postgres = subprocess.Popen(
                ["postgres", "-D", cluster, "-k", cls.socket, "-c", "listen_addresses="],
                stdout=output, stderr=subprocess.STDOUT, env=LOCAL_ENV,
            )
        cls.addClassCleanup(cls.stop_postgres, postgres)
        cls.maintenance = f"host={cls.socket} dbname=postgres"
        for _ in range(100):
            ready = subprocess.run(
                ["pg_isready", "-d", cls.maintenance], capture_output=True, timeout=3, env=LOCAL_ENV,
            )
            if ready.returncode == 0:
                return
            if postgres.poll() is not None:
                raise RuntimeError(server_log.read_text(encoding="utf-8"))
            time.sleep(0.05)
        raise RuntimeError("Discovery test PostgreSQL did not start")

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

    @staticmethod
    def assert_removed(path):
        assert not Path(path).exists()

    def setUp(self):
        super().setUp()
        database_name = f"discoveries_{uuid4().hex}"
        subprocess.run(
            ["createdb", "--maintenance-db", self.maintenance, database_name],
            check=True, capture_output=True, timeout=15, env=LOCAL_ENV,
        )
        self.connection = f"host={self.socket} dbname={database_name}"
        self.run_cli("migrate")

    def test_reviewed_youtube_sample_stays_private_across_replay_and_withdrawal(self):
        sample = PRODUCTION.parent / VIDEO_SAMPLE
        excluded_from_single_gpu_ranking = "gvl3mo_LqFo"
        url = f"https://www.youtube.com/watch?v={excluded_from_single_gpu_ranking}"

        receipt = self.run_cli("intake-youtube-metadata", sample)
        self.assertEqual(receipt, {"discoveries": 12})
        first_queue = self.run_cli("queue")["entries"]
        self.assertEqual(len(first_queue), 12)
        for item in first_queue:
            self.assertRegex(item["source_url"], r"^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}$")
            self.assertEqual(item["original_url"], item["source_url"])
            self.assertEqual(item["source_format"], "video")
            self.assertIsNone(item["published_at"])
            self.assertIsNone(item["consent"])
            self.assertEqual(item["reason"], "discovery_only")
            self.assertEqual(set(item), {
                "source_url", "original_url", "source_format", "published_at", "submitted_at",
                "consent", "metadata", "status", "reason", "review", "withdrawal",
            })
        comparison = next(item for item in first_queue if item["source_url"] == url)
        self.assertEqual(comparison["metadata"], {
            "policy": "youtube_metadata_discovery_only_v1",
            "source_reference": f"{VIDEO_SAMPLE}@sha256:"
                "e0de59de5686414466374d3a68c0e05d957c085ee2a935e01e4c46574eb01842"
                f"#video={excluded_from_single_gpu_ranking}",
        })
        self.assertIn("discovery_only", self.review(url, "approve", succeeds=False))
        self.assertEqual(self.run_cli("intake-youtube-metadata", sample), receipt)
        self.assertEqual(self.run_cli("queue")["entries"], first_queue)

        self.run_cli("withdraw", url, "--reason", "source_deleted")
        self.assertEqual(self.run_cli("intake-youtube-metadata", sample), receipt)
        comparison = next(item for item in self.run_cli("queue")["entries"] if item["source_url"] == url)
        self.assertEqual(comparison["withdrawal"]["reason"], "source_deleted")
        self.assertEqual(comparison["reason"], "source_deleted")
        public = self.run_cli("public")["entries"]
        self.assertEqual(public.count({"status": "withheld", "reason": "source_deleted"}), 1)
        self.assertEqual(public.count({"status": "withheld", "reason": "discovery_only"}), 11)
        self.assertEqual(len(public), 12)

    def test_youtube_intake_requires_postgres_and_the_approved_snapshot(self):
        sample = PRODUCTION.parent / VIDEO_SAMPLE
        modified_sample = self.directory / sample.name
        modified_sample.write_bytes(sample.read_bytes() + b"\n")

        self.assertIn(
            "approved YouTube metadata snapshot",
            self.run_cli("intake-youtube-metadata", modified_sample, succeeds=False),
        )
        self.assertIn(
            "requires a PostgreSQL connection",
            self.run_cli("intake-youtube-metadata", sample, legacy=True, succeeds=False),
        )
        self.assertEqual(self.run_cli("queue")["entries"], [])
        self.assertFalse(self.database.exists())

    def test_verified_opt_in_can_be_reviewed_after_metadata_intake(self):
        sample = PRODUCTION.parent / VIDEO_SAMPLE
        video = "https://www.youtube.com/watch?v=xzwb94eJ-EE"
        deleted_video = "https://www.youtube.com/watch?v=H7Wa-WxPiAY"
        self.run_cli("intake-youtube-metadata", sample)
        metadata = next(item["metadata"] for item in self.run_cli("queue")["entries"] if item["source_url"] == video)
        self.assertIn("discovery_only", self.review(video, "withhold", succeeds=False))
        self.run_cli("withdraw", deleted_video, "--reason", "source_deleted")

        for source_url in (video, deleted_video):
            submission = json.loads((FIXTURES / "original.json").read_text(encoding="utf-8"))
            submission.update(source_url=source_url, original_url=source_url, source_format="video", published_at=None)
            opt_in = self.directory / "opt-in.json"
            opt_in.write_text(json.dumps(submission), encoding="utf-8")
            receipt = self.run_cli("submit", opt_in)
            self.assertEqual(self.run_cli("submit", opt_in), receipt)

        queue = {item["source_url"]: item for item in self.run_cli("queue")["entries"]}
        self.assertEqual(queue[video]["status"], "pending")
        self.assertEqual(queue[video]["metadata"], metadata)
        self.assertEqual(queue[video]["consent"]["reference"], "fixture-original-grant")
        self.assertFalse(any("source_url" in item for item in self.run_cli("public")["entries"]))
        self.assertIn("source_deleted", self.review(deleted_video, "approve", succeeds=False))
        self.review(video, "approve")
        prior_public = self.run_cli("public")

        self.assertEqual(self.run_cli("intake-youtube-metadata", sample), {"discoveries": 12})
        self.assertEqual(self.run_cli("public"), prior_public)
        self.assertIn({
            "status": "approved", "reason": "source_link_approved", "source_url": video, "published_at": None,
        }, prior_public["entries"])
        self.assertIn({"status": "withheld", "reason": "source_deleted"}, prior_public["entries"])

    def test_metadata_intake_preserves_prior_opt_in_review(self):
        url = "https://www.youtube.com/watch?v=xzwb94eJ-EE"
        submission = json.loads((FIXTURES / "original.json").read_text(encoding="utf-8"))
        submission.update(source_url=url, original_url=url, source_format="video")
        opt_in = self.directory / "opt-in.json"
        opt_in.write_text(json.dumps(submission), encoding="utf-8")
        self.run_cli("submit", opt_in)
        decision = self.review(url, "approve")
        approved, = self.run_cli("public")["entries"]

        self.assertEqual(self.run_cli("intake-youtube-metadata", PRODUCTION.parent / VIDEO_SAMPLE), {"discoveries": 12})
        entry = next(item for item in self.run_cli("queue")["entries"] if item["source_url"] == url)
        self.assertEqual(entry["review"]["reviewed_at"], decision["reviewed_at"])
        self.assertEqual(entry["consent"]["reference"], "fixture-original-grant")
        self.assertEqual(entry["metadata"]["policy"], "youtube_metadata_discovery_only_v1")
        self.assertIn(approved, self.run_cli("public")["entries"])

    def test_postgres_public_export_after_later_cross_post_and_withdrawal(self):
        receipt = self.run_cli("submit", FIXTURES / "original.json")
        self.assertEqual(self.run_cli("submit", FIXTURES / "original.json"), receipt)
        self.assertEqual(self.run_cli("public")["entries"], [])
        self.review(ORIGINAL, "approve")
        self.run_cli("submit", FIXTURES / "cross-post.json")
        self.run_cli("submit", FIXTURES / "discovery-only.json")
        self.run_cli("withdraw", DELETED, "--reason", "source_deleted")
        self.run_cli("submit", FIXTURES / "deleted.json")
        self.assertEqual(self.run_cli("public"), {
            "schema": "fastest.ai/discovery-public/v1",
            "entries": [
                {"status": "approved", "reason": "source_link_approved", "source_url": ORIGINAL,
                 "published_at": SOURCE_DATE},
                {"status": "withheld", "reason": "cross_post"},
                {"status": "withheld", "reason": "source_deleted"},
                {"status": "withheld", "reason": "discovery_only"},
            ],
        })
        self.assertEqual(
            self.run_cli("queue")["entries"][0]["consent"]["reference"], "fixture-original-grant",
        )
        catalog_stats = PRODUCTION.parent / "opendesign" / "mockups" / "llm-observatory" / "catalog-stats.sql"
        counts = subprocess.run(
            ["psql", "-XqAtw", "-d", self.connection, "-f", catalog_stats],
            check=True, capture_output=True, text=True, timeout=10, env=LOCAL_ENV,
        ).stdout.splitlines()
        self.assertIn("fastest_discoveries.discovery|4", counts)
        self.assertIn("fastest_discoveries.review|1", counts)
        self.assertIn("fastest_discoveries.withdrawal|1", counts)

    def test_import_keeps_original_history_and_pre_arrival_tombstones(self):
        self.run_cli("submit", FIXTURES / "original.json", legacy=True)
        self.review(ORIGINAL, "approve", legacy=True)
        self.run_cli("submit", FIXTURES / "cross-post.json", legacy=True)
        self.run_cli("submit", FIXTURES / "discovery-only.json", legacy=True)
        self.review(DISCOVERY_ONLY, "withhold", legacy=True)
        self.run_cli("withdraw", ORIGINAL, "--reason", "permission_revoked", legacy=True)
        tombstone = self.run_cli("withdraw", DELETED, "--reason", "source_deleted", legacy=True)
        previous_queue = self.run_cli("queue", legacy=True)
        previous_public = self.run_cli("public", legacy=True)
        source_contents = self.database.read_bytes()

        imported = self.run_cli("import-sqlite", self.database)
        self.assertEqual(imported, {"discoveries": 3, "reviews": 2, "withdrawals": 2})
        self.assertEqual(self.run_cli("import-sqlite", self.database), imported)
        self.assertEqual(self.run_cli("queue"), previous_queue)
        self.assertEqual(self.run_cli("public"), previous_public)
        self.assertEqual(self.database.read_bytes(), source_contents)
        self.assertEqual(self.run_cli("withdraw", DELETED, "--reason", "source_deleted"), tombstone)
        self.run_cli("submit", FIXTURES / "deleted.json")
        self.assertIn("source_deleted", self.review(DELETED, "approve", succeeds=False))

    def test_import_conflict_rolls_back_all_history(self):
        self.run_cli("submit", FIXTURES / "original.json", legacy=True)
        self.run_cli("withdraw", ORIGINAL, "--reason", "permission_revoked", legacy=True)
        self.run_cli("withdraw", DELETED, "--reason", "source_deleted", legacy=True)
        self.run_cli("withdraw", ORIGINAL, "--reason", "source_deleted")
        error = self.run_cli("import-sqlite", self.database, succeeds=False)
        self.assertIn("Conflicting legacy history", error)
        self.assertEqual(self.run_cli("queue")["entries"], [])
        self.run_cli("submit", FIXTURES / "deleted.json")
        self.review(DELETED, "approve")
        self.run_cli("submit", FIXTURES / "original.json")
        self.assertEqual(self.run_cli("queue")["entries"][0]["withdrawal"]["reason"], "source_deleted")

    def test_concurrent_duplicate_and_withdrawal_preserve_one_receipt(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            receipts = list(pool.map(lambda _: self.run_cli("submit", FIXTURES / "original.json"), range(4)))
            self.assertTrue(all(receipt == receipts[0] for receipt in receipts))

            review = pool.submit(
                self.invoke_cli, "review", ORIGINAL, "approve", "--reviewer", "fixture-editor",
                "--reason", "Reviewed public permalink and opt-in.",
            )
            withdrawals = list(pool.map(
                lambda _: self.run_cli("withdraw", ORIGINAL, "--reason", "permission_revoked"), range(2),
            ))
            self.assertEqual(withdrawals[0], withdrawals[1])
            attempted_review = review.result()

        queued, = self.run_cli("queue")["entries"]
        if attempted_review.returncode == 0:
            self.assertEqual(self.review(ORIGINAL, "approve"), json.loads(attempted_review.stdout))
            self.assertEqual(queued["review"]["choice"], "approve")
        else:
            self.assertIn("Publication is withheld: permission_revoked", attempted_review.stderr)
            self.assertIsNone(queued["review"])

        self.assertIn("already recorded", self.run_cli("withdraw", ORIGINAL, "--reason", "source_deleted", succeeds=False))
        self.assertEqual(self.run_cli("public")["entries"], [{"status": "withheld", "reason": "permission_revoked"}])

    def test_editor_and_public_reader_use_only_their_granted_operations(self):
        suffix = uuid4().hex
        editor, reader = (f"discovery_{role}_{suffix}" for role in ("editor", "reader"))
        grants = f"""
            CREATE ROLE {editor} LOGIN;
            CREATE ROLE {reader} LOGIN;
            GRANT USAGE ON SCHEMA fastest_discoveries TO {editor}, {reader};
            GRANT EXECUTE ON FUNCTION fastest_discoveries.submit(jsonb),
                fastest_discoveries.intake_youtube_metadata(text, jsonb),
                fastest_discoveries.review(text, text, text, text),
                fastest_discoveries.withdraw(text, text),
                fastest_discoveries.queue_entries() TO {editor};
            GRANT EXECUTE ON FUNCTION fastest_discoveries.public_report() TO {editor}, {reader};
            ALTER ROLE {reader} SET default_transaction_read_only = on;
        """
        psql = ["psql", "-XqAtw", "-v", "ON_ERROR_STOP=1", "-d"]
        subprocess.run(
            [*psql, self.connection], input=grants, check=True, capture_output=True,
            text=True, timeout=10, env=LOCAL_ENV,
        )
        editor_url = f"{self.connection} user={editor}"
        reader_url = f"{self.connection} user={reader}"

        self.run_cli("submit", FIXTURES / "original.json", connection=editor_url)
        self.review(ORIGINAL, "approve", connection=editor_url)
        self.assertEqual(self.run_cli("queue", connection=editor_url)["entries"][0]["consent"]["reference"],
                         "fixture-original-grant")
        self.assertEqual(self.run_cli("public", connection=reader_url)["entries"], [{
            "status": "approved", "reason": "source_link_approved",
            "source_url": ORIGINAL, "published_at": SOURCE_DATE,
        }])
        sample = PRODUCTION.parent / VIDEO_SAMPLE
        self.run_cli("queue", connection=reader_url, succeeds=False)
        self.run_cli("intake-youtube-metadata", sample, connection=reader_url, succeeds=False)
        self.run_cli("submit", FIXTURES / "deleted.json", connection=reader_url, succeeds=False)
        private_read = subprocess.run(
            [*psql, reader_url], input="SELECT consent_reference FROM fastest_discoveries.discovery;",
            capture_output=True, text=True, timeout=10, env=LOCAL_ENV,
        )
        self.assertNotEqual(private_read.returncode, 0)
        self.assertIn("permission denied", private_read.stderr)
        for restricted_url in (editor_url, reader_url):
            metadata_read = subprocess.run(
                [*psql, restricted_url], input="SELECT source_reference FROM fastest_discoveries.youtube_metadata;",
                capture_output=True, text=True, timeout=10, env=LOCAL_ENV,
            )
            self.assertNotEqual(metadata_read.returncode, 0)
            self.assertIn("permission denied", metadata_read.stderr)
        operator_access = subprocess.run(
            [*psql, reader_url], input="""
                SELECT has_function_privilege('fastest_discoveries.submit(jsonb)', 'EXECUTE')
                    OR has_function_privilege('fastest_discoveries.intake_youtube_metadata(text,jsonb)', 'EXECUTE')
                    OR has_function_privilege('fastest_discoveries.review(text,text,text,text)', 'EXECUTE')
                    OR has_function_privilege('fastest_discoveries.withdraw(text,text)', 'EXECUTE')
                    OR has_function_privilege('fastest_discoveries.queue_entries()', 'EXECUTE')
                    OR has_function_privilege('fastest_discoveries.import_history(jsonb)', 'EXECUTE');
            """, check=True, capture_output=True, text=True, timeout=10, env=LOCAL_ENV,
        )
        self.assertEqual(operator_access.stdout.strip(), "f")

        for unsafe_url in (
            "http://forum.example/posts/unsafe",
            "https://editor@forum.example/posts/unsafe",
            "https://forum.example/posts/unsafe?token=fixture-secret",
            "https://forum.example/posts/unsafe#access_token=fixture-secret",
        ):
            with self.subTest(unsafe_url=unsafe_url):
                unsafe = json.dumps({
                    "source_url": unsafe_url, "original_url": unsafe_url, "source_format": "forum",
                    "authority": "rights_holder", "consent_reference": "fixture-grant", "scope": "public_source_link",
                })
                direct_submission = subprocess.run(
                    [*psql, editor_url], input=f"SELECT fastest_discoveries.submit('{unsafe}'::jsonb);",
                    capture_output=True, text=True, timeout=10, env=LOCAL_ENV,
                )
                self.assertNotEqual(direct_submission.returncode, 0)
                self.assertIn("check constraint", direct_submission.stderr)

        video = "https://www.youtube.com/watch?v=qW2E2ay47dw#comments"
        submission = json.loads((FIXTURES / "original.json").read_text(encoding="utf-8"))
        submission.update(source_url=video, original_url=video, source_format="video")
        path = self.directory / "video.json"
        path.write_text(json.dumps(submission), encoding="utf-8")
        self.run_cli("submit", path, connection=editor_url)
        self.review(video, "approve", connection=editor_url)
        self.assertEqual(self.run_cli("public", connection=reader_url)["entries"][-1]["source_url"], video)
        self.assertEqual(self.run_cli("intake-youtube-metadata", sample, connection=editor_url),
                         {"discoveries": 12})
        self.assertEqual(self.run_cli("public", connection=reader_url)["entries"].count(
            {"status": "withheld", "reason": "discovery_only"},
        ), 12)


if __name__ == "__main__":
    unittest.main()
