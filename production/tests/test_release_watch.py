from contextlib import closing, redirect_stderr
from copy import deepcopy
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastest_release import ReleaseStore
from fastest_release_watch.__main__ import main as watch_main
from fastest_release_watch.feed import decode
from fastest_release_watch.postgres import PostgresStore
from test_public_api import api_client


PRODUCTION = Path(__file__).resolve().parents[1]
REPOSITORY = "ggml-org/llama.cpp"
DAY_ONE = "2026-11-20T01:00:00Z"
DAY_TWO = "2026-11-21T01:00:00Z"


def github_release(release_id, tag, published_at, *, body="Original notes", prerelease=False,
                   repository=REPOSITORY):
    return {
        "id": release_id,
        "tag_name": tag,
        "url": f"https://api.github.com/repos/{repository}/releases/{release_id}",
        "html_url": f"https://github.com/{repository}/releases/tag/{tag}",
        "name": tag,
        "published_at": published_at,
        "draft": False,
        "prerelease": prerelease,
        "immutable": False,
        "target_commitish": "master",
        "body": body,
        "assets": [],
    }


class ReleaseWatchScenarios:
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="release-watch-20-")))
        self.feed = self.directory / "feed.json"

    def prepare_history(self):
        pass

    def refresh(self, rows, at, *options, success=True):
        self.feed.write_text(json.dumps(rows), encoding="utf-8")
        result = self.invoke("refresh", "--fixture", self.feed, "--observed-at", at, *options)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def report(self, as_of=DAY_TWO, *options):
        result = self.invoke("report", "--as-of", as_of, *options)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_official_feeds_keep_independent_history_and_freshness(self):
        self.prepare_history()
        llama = github_release(100, "b100", DAY_ONE)
        vllm = github_release(100, "v0.34.0", DAY_ONE, repository="vllm-project/vllm")
        sglang = github_release(100, "v0.5.23", DAY_TWO, repository="sgl-project/sglang")
        ollama = github_release(100, "v0.40.17", DAY_TWO, repository="ollama/ollama")
        self.refresh([llama], DAY_ONE)
        self.refresh([vllm], DAY_ONE, "--source", "vllm")
        self.refresh([sglang], DAY_TWO, "--source", "sglang")
        self.refresh([ollama], DAY_TWO, "--source", "ollama")
        self.refresh([ollama], DAY_TWO, "--source", "vllm", success=False)

        report = self.report("2026-11-21T01:00:01Z")
        sources = report["sources"]
        self.assertEqual(sources["vllm"]["last_attempt"], DAY_TWO)
        self.assertEqual(sources["vllm"]["last_successful_refresh"], DAY_ONE)
        self.assertIn("official vLLM", sources["vllm"]["last_error"])
        self.assertTrue(sources["vllm"]["stale"])
        self.assertIsNone(sources["llama.cpp"]["last_error"])
        self.assertEqual(report["last_successful_refresh"], DAY_ONE)
        self.assertFalse(sources["sglang"]["stale"])
        self.assertFalse(sources["ollama"]["stale"])
        self.assertCountEqual(
            [(r["runtime_id"], r["tag"], r["status"], r["applicability"]) for r in report["releases"]],
            [
                ("llama.cpp", "b100", "current", []),
                ("vllm", "v0.34.0", "current", []),
                ("sglang", "v0.5.23", "current", []),
                ("ollama", "v0.40.17", "current", []),
            ],
        )

    def test_repeat_and_older_replay_preserve_revision_identity_and_last_success(self):
        self.prepare_history()
        older = github_release(100, "fixture-b1", "2026-11-19T01:00:00Z")
        edited = {**older, "body": "<script>raw release text</script>"}
        newer = github_release(101, "fixture-b2", DAY_TWO)
        preview = github_release(102, "fixture-b3", DAY_TWO, prerelease=True)

        self.refresh([older], DAY_ONE)
        original = self.report()["releases"][0]["revision_id"]
        self.refresh([edited, newer, preview], DAY_TWO)
        updated = self.report()
        self.refresh([preview, edited, newer], DAY_TWO)
        self.refresh([older], DAY_ONE)
        self.assertEqual(self.report(), updated)

        late_edit_at = "2026-11-20T23:00:00Z"
        self.refresh([{**older, "body": "Previously unobserved edit"}], late_edit_at)
        with_late_edit = self.report()
        self.assertEqual(with_late_edit["last_attempt"], DAY_TWO)
        self.assertEqual(with_late_edit["last_successful_refresh"], DAY_TWO)
        self.assertEqual(with_late_edit["releases"][:3], updated["releases"][:3])
        self.assertEqual(with_late_edit["releases"][-2]["first_seen_at"], late_edit_at)
        self.assertEqual(with_late_edit["releases"][-2]["status"], "superseded_revision")
        self.assertEqual(with_late_edit["releases"][-1]["revision_id"], original)
        self.assertEqual(updated["last_successful_refresh"], DAY_TWO)
        self.assertEqual(updated["source"]["mode"], "fixture")
        self.assertEqual(
            [(r["tag"], r["status"]) for r in updated["releases"]],
            [("fixture-b3", "prerelease"), ("fixture-b2", "current"),
             ("fixture-b1", "superseded_release"), ("fixture-b1", "superseded_revision")],
        )
        self.assertEqual(updated["releases"][-1]["revision_id"], original)
        self.assertEqual(updated["releases"][-1]["source_url"],
                         "https://github.com/ggml-org/llama.cpp/releases/tag/fixture-b1")
        self.assertNotIn("raw release text", json.dumps(updated))

    def test_bad_feed_attempt_keeps_last_success_and_flags_stale_history(self):
        self.prepare_history()
        release = github_release(100, "fixture-b1", DAY_ONE)
        self.refresh([release], DAY_ONE)
        first_snapshot = self.report(DAY_ONE)
        self.assertFalse(first_snapshot["stale"])
        bad_release = {**github_release(101, "fixture-b2", DAY_TWO), "url": "https://other.example/releases/101"}
        self.refresh([github_release(102, "fixture-b3", DAY_TWO), bad_release], DAY_TWO, success=False)

        failed = self.report("2026-11-21T01:00:01Z")
        self.assertEqual(failed["last_successful_refresh"], DAY_ONE)
        self.assertEqual(failed["last_attempt"], DAY_TWO)
        self.assertIn("official llama.cpp", failed["last_error"])
        self.assertTrue(failed["stale"])
        self.assertEqual(failed["releases"], first_snapshot["releases"])

    def test_authored_note_links_only_the_named_card_configuration_and_revision(self):
        self.prepare_history()
        release = github_release(100, "fixture-b1", DAY_ONE)
        self.refresh([release], DAY_ONE)
        original = self.report()["releases"][0]["revision_id"]
        self.refresh([{**release, "body": "Revised notes"}], DAY_TWO)
        path = self.directory / "notes.json"
        note = {
            "id": "fixture-offload",
            "revision_id": original,
            "card_id": "nvidia-geforce-rtx-3060",
            "source_url": "https://github.com/ggml-org/llama.cpp/tree/1111111111111111111111111111111111111111",
            "source_label": "Synthetic fixture source",
            "status": "suggested",
            "technique": "Try <script>alert(1)</script> partial offload",
            "prerequisites": "Native CUDA build",
            "limits": "One 12 GiB board variant only",
            "failure_modes": "Allocation can fail",
            "configuration": {
                "id": "fixture-ubuntu24-3060-12gb",
                "variant": "GeForce RTX 3060 12 GiB",
                "os": "Ubuntu 24.04.1",
                "driver": "550.120",
                "backend": "CUDA",
                "build_sha": "1111111111111111111111111111111111111111",
                "flags": ["--gpu-layers", "20"],
                "workload_id": "solo-decode",
                "workload_version": 1,
                "model_artifact": "fixture/model@revision/configured.gguf",
            },
        }
        path.write_text(json.dumps({"notes": [note]}), encoding="utf-8")
        report = self.report(DAY_TWO, "--notes", path)
        revised, older = report["releases"]
        self.assertEqual(revised["applicability"], [])
        application = older["applicability"][0]
        self.assertEqual(application["card"]["id"], "nvidia-geforce-rtx-3060")
        self.assertEqual(application["configuration"], note["configuration"])
        self.assertEqual(application["status"], "suggested")
        self.assertEqual(older["status"], "superseded_revision")
        self.assertEqual(application["source_url"], note["source_url"])
        self.assertEqual(application["build_url"],
                         "https://github.com/ggml-org/llama.cpp/commit/1111111111111111111111111111111111111111")

        for format_name in ("html", "markdown"):
            with self.subTest(format=format_name):
                rendered = self.invoke("report", "--as-of", DAY_TWO, "--notes", path, "--format", format_name)
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                self.assertIn("NVIDIA GeForce RTX 3060", rendered.stdout)
                self.assertIn("550.120", rendered.stdout)
                self.assertIn("Superseded revision", rendered.stdout)
                self.assertIn("Suggested", rendered.stdout)
                self.assertNotIn("<script>", rendered.stdout)

        for correction in ({"card_id": "any-rtx"}, {"revision_id": "unknown"}, {"measured_gain": "10%"},
                           {"status": "fastest_ai_verified"}, {"source_url": "javascript:alert(1)"}):
            with self.subTest(correction=correction):
                path.write_text(json.dumps({"notes": [{**note, **correction}]}), encoding="utf-8")
                rejected = self.invoke("report", "--as-of", DAY_TWO, "--notes", path)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(rejected.stdout, "")


class ReleaseWatchTest(ReleaseWatchScenarios, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.database = self.directory / "watch.sqlite3"

    def invoke(self, *options):
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_release_watch", "--db", self.database, *options],
            cwd=PRODUCTION,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_origin_watch_configuration_requires_database_and_explicit_enablement(self):
        for option, expected in (
            (["--runtime-release-watch"], "requires FASTEST_DATABASE_URL or --database-url"),
            (["--runtime-release-watch-notes", "reviewed.json"], "requires --runtime-release-watch"),
        ):
            with self.subTest(option=option):
                result = subprocess.run(
                    [sys.executable, "-B", "-m", "fastest_release", "--database-url", "",
                     "serve", *option],
                    cwd=PRODUCTION, capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn(expected, result.stderr)

    def test_official_request_rejects_redirects_without_following_them(self):
        from fastest_release_watch.feed import fetch

        with patch("http.client.HTTPSConnection") as transport:
            connection = transport.return_value
            connection.getresponse.return_value = BytesIO(b"")
            connection.getresponse.return_value.status = 302
            with self.assertRaisesRegex(ValueError, "HTTP 302"):
                fetch()
            connection.request.assert_called_once()
            self.assertEqual(connection.request.call_args.args,
                             ("GET", "/repos/ggml-org/llama.cpp/releases?per_page=10&page=1"))

    def test_all_live_refreshes_continue_after_feed_failure(self):
        feeds = {
            "ggml-org/llama.cpp": "b100",
            "sgl-project/sglang": "v0.5.23",
            "vllm-project/vllm": None,
            "ollama/ollama": "v0.40.17",
        }

        def response(_, path, **kwargs):
            repository = path.removeprefix("/repos/").split("/releases?")[0]
            tag = feeds[repository]
            rows = [github_release(100, tag, DAY_ONE, repository=repository)] if tag else []
            body = BytesIO(json.dumps(rows).encode())
            body.status = 200 if tag else 429
            transport.return_value.getresponse.return_value = body

        argv = ["fastest_release_watch", "--db", str(self.database), "refresh", "--source", "all"]
        with patch.object(sys, "argv", argv), patch("http.client.HTTPSConnection") as transport, \
                redirect_stderr(StringIO()) as stderr:
            transport.return_value.request.side_effect = response
            with self.assertRaises(SystemExit) as result:
                watch_main()
        self.assertEqual(result.exception.code, 1)
        self.assertIn("vllm: GitHub release feed returned HTTP 429", stderr.getvalue())

        report = self.report()
        self.assertCountEqual([r["runtime_id"] for r in report["releases"]], ["llama.cpp", "sglang", "ollama"])
        self.assertIsNone(report["sources"]["vllm"]["last_successful_refresh"])
        self.assertIn("HTTP 429", report["sources"]["vllm"]["last_error"])
        self.assertIsNotNone(report["sources"]["ollama"]["last_successful_refresh"])

    def test_existing_sqlite_history_remains_readable_and_survives_first_new_source(self):
        row, = decode(json.dumps([github_release(100, "legacy-b100", DAY_ONE)]).encode())
        with closing(sqlite3.connect(self.database)) as db, db:
            db.executescript("""
                CREATE TABLE source_status (
                    id INTEGER PRIMARY KEY CHECK (id = 1), mode TEXT NOT NULL,
                    last_attempt TEXT, last_error TEXT, last_success TEXT
                );
                CREATE TABLE release_revision (
                    revision_id TEXT PRIMARY KEY NOT NULL, release_id INTEGER NOT NULL,
                    observed_at TEXT NOT NULL, document TEXT NOT NULL
                );
            """)
            db.execute("INSERT INTO source_status VALUES (1, 'fixture', ?, NULL, ?)", (DAY_ONE, DAY_ONE))
            db.execute("INSERT INTO release_revision VALUES (?, 100, ?, ?)",
                       (row["revision_id"], DAY_ONE, json.dumps(row)))
        before = self.report()
        self.assertEqual(before["releases"][0]["revision_id"], row["revision_id"])
        self.assertEqual(before["last_successful_refresh"], DAY_ONE)
        self.refresh([github_release(100, "v0.34.0", DAY_TWO, repository="vllm-project/vllm")],
                     DAY_TWO, "--source", "vllm")
        after = self.report()
        self.assertEqual(after["sources"]["llama.cpp"], before["sources"]["llama.cpp"])
        self.assertEqual([r for r in after["releases"] if r["runtime_id"] == "llama.cpp"], before["releases"])

    def test_only_measured_retests_with_matching_conditions_are_linked(self):
        from fastest_release_watch.retest import approved_links

        first_id = "3a76f0db-50f3-40c7-a31e-377fe32361b3"
        second_id = "39779f33-5941-4d7a-855b-949c4cee3aa9"
        pair = {"baseline_release_id": first_id, "tuned_release_id": second_id}
        config = {
            "id": "config-3060",
            "os": "Ubuntu 24.04",
            "driver": "550.120",
            "backend": "CUDA",
            "build_sha": "1" * 40,
            "flags": ["--gpu-layers", "20"],
            "workload_id": "solo-decode",
            "workload_version": 1,
            "model_artifact": "fastest-ai/fixture-model@synthetic-v1/production/fixtures/synthetic-artifact.txt",
        }
        note = {"card_id": "nvidia-geforce-rtx-3060", "configuration": config}
        row = json.loads((PRODUCTION / "fixtures/synthetic-observation.json").read_text(encoding="utf-8"))
        row["kind"] = "measured"
        row["fields"] = {
            key: {"status": "known", "value": value}
            for key, value in {
                "card_id": note["card_id"], "configuration_id": config["id"], "os_version": config["os"],
                "driver_version": config["driver"], "backend": config["backend"],
                "runtime_build": config["build_sha"], "runtime_id": "llama.cpp",
                "runtime_flags": '["--gpu-layers", "0"]',
            }.items()
        }
        tuned = deepcopy(row)
        tuned["evidence_id"] = "8e285620-7a53-4d83-a30e-9fa48a707475"
        tuned["metric"]["value"] = "43.5"
        tuned["fields"]["runtime_flags"]["value"] = '["--gpu-layers", "20"]'
        published = {
            first_id: {"release_id": first_id, "status": "published", "row": row},
            second_id: {"release_id": second_id, "status": "published", "row": tuned},
        }
        self.assertEqual(
            approved_links(published.__getitem__, note, pair, "https://benchmark.example"),
            {
                "baseline_url": "https://benchmark.example/releases/3a76f0db-50f3-40c7-a31e-377fe32361b3/benchmark.html",
                "tuned_url": "https://benchmark.example/releases/39779f33-5941-4d7a-855b-949c4cee3aa9/benchmark.html",
            },
        )
        with self.assertRaisesRegex(ValueError, "matched"):
            approved_links(published.__getitem__, note, pair, "https://benchmark.example", runtime_id="vllm")
        tuned["fields"]["driver_version"]["value"] = "560.120"
        with self.assertRaisesRegex(ValueError, "matched"):
            approved_links(published.__getitem__, note, pair, "https://benchmark.example")
        published[second_id] = {"release_id": second_id, "status": "withdrawn"}
        with self.assertRaisesRegex(ValueError, "published measured"):
            approved_links(published.__getitem__, note, pair, "https://benchmark.example")


@unittest.skipUnless(
    all(shutil.which(tool) for tool in ("initdb", "postgres", "pg_isready", "createdb", "psql")),
    "PostgreSQL command-line tools required",
)
class PostgresReleaseWatchTest(ReleaseWatchScenarios, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        work = Path(cls.enterClassContext(tempfile.TemporaryDirectory(prefix="fastest-release-watch-pg-", dir="/tmp")))
        data = work / "db"
        subprocess.run(
            ["initdb", "-D", data, "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True, capture_output=True, timeout=20,
        )
        log = work / "postgres.log"
        with log.open("w") as output:
            postgres = subprocess.Popen(
                ["postgres", "-D", data, "-k", work, "-c", "listen_addresses="],
                stdout=output, stderr=subprocess.STDOUT,
            )
        cls.addClassCleanup(cls.stop_postgres, postgres)
        cls.socket = work
        cls.maintenance_url = f"host={work} dbname=postgres"
        for _ in range(100):
            ready = subprocess.run(["pg_isready", "-d", cls.maintenance_url], capture_output=True, timeout=3)
            if ready.returncode == 0:
                break
            if postgres.poll() is not None:
                raise RuntimeError(log.read_text())
            time.sleep(0.05)
        else:
            raise RuntimeError("Watcher test PostgreSQL did not start")

    @staticmethod
    def stop_postgres(postgres):
        if postgres.poll() is None:
            postgres.send_signal(signal.SIGINT)
            try:
                postgres.wait(timeout=10)
            except subprocess.TimeoutExpired:
                postgres.send_signal(signal.SIGQUIT)
                postgres.wait(timeout=10)

    def setUp(self):
        super().setUp()
        database = f"watch_{uuid4().hex}"
        subprocess.run(
            ["createdb", "--maintenance-db", self.maintenance_url, database],
            check=True, capture_output=True, timeout=15,
        )
        self.database_url = f"host={self.socket} dbname={database}"

    def invoke(self, *options, read_only=False):
        env = {**os.environ, "FASTEST_DATABASE_URL": self.database_url}
        if read_only:
            env["PGOPTIONS"] = "-c default_transaction_read_only=on"
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_release_watch", "--postgres", *options],
            cwd=PRODUCTION, env=env, capture_output=True, text=True, timeout=15,
        )

    def prepare_history(self):
        migrated = self.invoke("migrate")
        self.assertEqual(migrated.returncode, 0, migrated.stderr)

    def test_explicit_migration_enables_read_only_report(self):
        before = self.invoke("report", "--as-of", DAY_ONE)
        self.assertNotEqual(before.returncode, 0)
        self.assertEqual(before.stdout, "")
        for _ in range(2):
            migrated = self.invoke("migrate")
            self.assertEqual(migrated.returncode, 0, migrated.stderr)

        result = self.invoke("report", "--as-of", DAY_ONE, read_only=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        sources = report.pop("sources")
        self.assertEqual(set(sources), {"llama.cpp", "sglang", "vllm", "ollama"})
        self.assertTrue(all(source["stale"] and source["mode"] is None for source in sources.values()))
        self.assertEqual(report, {
            "schema": "fastest.ai/runtime-release-watch/v1",
            "source": {
                "repository": REPOSITORY,
                "feed_url": "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=10&page=1",
                "page_size": 10,
                "mode": None,
            },
            "last_attempt": None,
            "last_error": None,
            "last_successful_refresh": None,
            "stale": True,
            "releases": [],
        })

    def test_existing_postgres_history_survives_idempotent_migration(self):
        subprocess.run(
            ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-d", self.database_url],
            input="""
                CREATE SCHEMA fastest_release_watch;
                CREATE TABLE fastest_release_watch.source_status (
                    id smallint PRIMARY KEY CHECK (id = 1), mode text NOT NULL,
                    last_attempt timestamptz, last_error text, last_success timestamptz
                );
                INSERT INTO fastest_release_watch.source_status
                VALUES (1, 'fixture', '2026-11-21T01:00:00Z', 'Original failure', '2026-11-20T01:00:00Z');
                CREATE TABLE fastest_release_watch.release_revision (
                    revision_id text PRIMARY KEY, release_id bigint NOT NULL,
                    observed_at timestamptz NOT NULL, ingest_order bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
                    document jsonb NOT NULL
                );
                INSERT INTO fastest_release_watch.release_revision (revision_id, release_id, observed_at, document)
                VALUES ('legacy-revision', 100, '2026-11-20T01:00:00Z',
                        '{"runtime_id":"llama.cpp","release_id":100,"revision_id":"legacy-revision",
                          "tag":"b100","published_at":"2026-11-20T01:00:00Z","prerelease":false}'::jsonb);
            """,
            check=True, capture_output=True, text=True, timeout=15,
        )
        self.prepare_history()
        self.prepare_history()
        self.refresh([github_release(100, "v0.5.23", DAY_TWO, repository="sgl-project/sglang")],
                     DAY_TWO, "--source", "sglang")
        report = self.report()
        self.assertEqual(report["last_successful_refresh"], DAY_ONE)
        self.assertEqual(report["last_attempt"], DAY_TWO)
        self.assertEqual(report["last_error"], "Original failure")
        self.assertEqual(report["sources"]["sglang"]["last_successful_refresh"], DAY_TWO)
        self.assertEqual(
            [(r["runtime_id"], r["tag"], r["status"]) for r in report["releases"]],
            [("sglang", "v0.5.23", "current"), ("llama.cpp", "b100", "current")],
        )
        self.assertEqual(report["releases"][1]["revision_id"], "legacy-revision")
        self.assertEqual(report["releases"][1]["first_seen_at"], DAY_ONE)

    def test_origin_exposes_retained_release_history_and_refresh_status(self):
        self.prepare_history()
        watch = PostgresStore(self.database_url)
        first_success = "2001-01-01T01:00:00Z"
        last_success = "2001-01-02T01:00:00Z"
        published = github_release(100, "test-b100", first_success)
        edited = {**published, "body": "Edited release notes"}
        preview = github_release(101, "test-b101", last_success, prerelease=True)
        watch.record("live", first_success, decode(json.dumps([published]).encode()))
        watch.record("live", last_success, decode(json.dumps([edited, preview]).encode()))
        vllm_release = github_release(100, "test-vllm", last_success, repository="vllm-project/vllm")
        watch.record("live", last_success, decode(json.dumps([vllm_release]).encode(), runtime_id="vllm"),
                     runtime_id="vllm")
        watch.record("live", "2001-01-03T01:00:00Z", error="GitHub release feed timed out")
        store = ReleaseStore(self.database_url)

        with api_client(store) as request:
            self.assertNotIn('/runtime-releases', request("/", decode=False)[2])
            self.assertEqual(request("/runtime-releases", decode=False)[0], 404)

        reader_watch = PostgresStore(self.database_url + " options='-c default_transaction_read_only=on'")
        with patch("http.client.HTTPSConnection", side_effect=AssertionError("GET must use retained data")), \
                api_client(store, runtime_watch=reader_watch) as request:
            index = request("/", decode=False)[2]
            status, headers, report = request("/runtime-releases.json")
            canonical = self.invoke("report", read_only=True)
            self.assertEqual(canonical.returncode, 0, canonical.stderr)
            self.assertEqual(status, 200)
            self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual(report, json.loads(canonical.stdout))
            self.assertEqual(report["last_successful_refresh"], last_success)
            self.assertTrue(report["stale"])
            self.assertEqual(report["last_error"], "GitHub release feed timed out")
            self.assertEqual(report["sources"]["vllm"]["last_successful_refresh"], last_success)
            self.assertIsNone(report["sources"]["vllm"]["last_error"])
            self.assertEqual([release["status"] for release in report["releases"] if release["runtime_id"] == "llama.cpp"],
                             ["prerelease", "current", "superseded_revision"])
            for path, content_type in [("/runtime-releases", "text/html"),
                                       ("/runtime-releases.md", "text/markdown")]:
                with self.subTest(path=path):
                    self.assertIn(f'href="{path}"', index)
                    status, headers, body = request(path, decode=False)
                    self.assertEqual(status, 200)
                    self.assertEqual(headers.get_content_type(), content_type)
                    self.assertIn(last_success, body)
                    self.assertIn("GitHub release feed timed out", body)
                    self.assertIn("stale", body)
                    self.assertIn("Superseded revision", body)
                    self.assertIn("vLLM", body)
                    self.assertIn("https://github.com/vllm-project/vllm/releases/tag/test-vllm", body)
            self.assertIn('href="/runtime-releases.json"', index)
            self.assertEqual(request("/runtime-releases", "HEAD", decode=False)[2], "")

    def test_origin_distinguishes_empty_live_history_from_a_service_outage(self):
        watch = PostgresStore(self.database_url)
        with api_client(runtime_watch=watch) as request:
            for path, content_type in (("/runtime-releases", "text/html"), ("/runtime-releases.md", "text/markdown"),
                                       ("/runtime-releases.json", "application/json")):
                with self.subTest(path=path):
                    status, headers, body = request(path, decode=False)
                    self.assertEqual(status, 503)
                    self.assertEqual(headers.get_content_type(), content_type)
                    self.assertIn("Runtime release watch unavailable.", body)
                    self.assertNotIn("last_successful_refresh", body)
                    self.assertNotIn("source_status", body)

            self.prepare_history()
            status, _, report = request("/runtime-releases.json")
            self.assertEqual(status, 200)
            self.assertEqual(report["releases"], [])
            self.assertIsNone(report["last_successful_refresh"])
            self.assertTrue(report["stale"])

            self.refresh([github_release(100, "test-only-tag", DAY_ONE, repository="vllm-project/vllm")],
                         DAY_ONE, "--source", "vllm")
            status, _, body = request("/runtime-releases.json", decode=False)
            self.assertEqual(status, 503)
            self.assertNotIn("test-only-tag", body)

    def test_origin_rechecks_matched_retest_rights(self):
        self.prepare_history()
        watch = PostgresStore(self.database_url)
        fixture_directory = PRODUCTION / "fixtures/release-watch"
        note = json.loads((fixture_directory / "applicability.json").read_text())["notes"][0]
        upstream = github_release(100, "test-vllm", DAY_ONE, repository="vllm-project/vllm")
        revision, = decode(json.dumps([upstream]).encode(), runtime_id="vllm")
        watch.record("live", DAY_ONE, [revision], runtime_id="vllm")
        note["revision_id"] = revision["revision_id"]
        fixture = PRODUCTION / "fixtures/synthetic-observation.json"
        baseline = json.loads(fixture.read_text())
        artifact = baseline["artifact"]
        note["configuration"]["model_artifact"] = f"{artifact['repository']}@{artifact['revision']}/{artifact['path']}"
        config = note["configuration"]
        baseline["kind"] = "measured"
        baseline["fields"] = {
            field: {"status": "known", "value": value, "rights": "allow"}
            for field, value in {
                "card_id": note["card_id"], "configuration_id": config["id"], "os_version": config["os"],
                "driver_version": config["driver"], "backend": config["backend"],
                "runtime_build": config["build_sha"], "runtime_id": "vllm",
                "runtime_flags": '["--gpu-layers", "0"]',
            }.items()
        }
        tuned = deepcopy(baseline)
        tuned["evidence_id"] = str(uuid4())
        tuned["fields"]["runtime_flags"]["value"] = json.dumps(config["flags"])
        publisher = ReleaseStore(self.database_url)
        publisher.migrate()
        note["status"] = "fastest_ai_verified"
        baseline_id = publisher.publish(baseline)
        tuned_id = publisher.publish(tuned)
        note["retest"] = {"baseline_release_id": baseline_id, "tuned_release_id": tuned_id}
        notes = self.directory / "reviewed.json"
        notes.write_text(json.dumps({"notes": [note]}))

        reader_url = self.database_url + " options='-c default_transaction_read_only=on'"
        with api_client(ReleaseStore(reader_url), runtime_watch=PostgresStore(reader_url),
                        runtime_watch_notes=notes) as request:
            for path in ("/runtime-releases", "/runtime-releases.md", "/runtime-releases.json"):
                with self.subTest(path=path):
                    status, _, body = request(path, decode=False)
                    self.assertEqual(status, 200)
                    self.assertIn("550.120", body)
                    self.assertIn(f"https://github.com/vllm-project/vllm/commit/{config['build_sha']}", body)
                    self.assertIn(f"/releases/{baseline_id}/benchmark.html", body)
                    self.assertIn(f"/releases/{tuned_id}/benchmark.html", body)

            publisher.withdraw(tuned["evidence_id"], "Private fixture withdrawal reason")
            for path in ("/runtime-releases", "/runtime-releases.md", "/runtime-releases.json"):
                with self.subTest(path=path):
                    status, headers, body = request(path, decode=False)
                    self.assertEqual(status, 503)
                    self.assertEqual(headers["Cache-Control"], "no-store")
                    self.assertNotIn(tuned_id, body)
                    self.assertNotIn("Private fixture withdrawal reason", body)
