from copy import deepcopy
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
from unittest.mock import patch
from uuid import uuid4

from fastest_release import ReleaseStore
from fastest_release_watch.feed import decode
from fastest_release_watch.postgres import PostgresStore
from test_public_api import api_client


PRODUCTION = Path(__file__).resolve().parents[1]
REPOSITORY = "ggml-org/llama.cpp"
DAY_ONE = "2026-11-20T01:00:00Z"
DAY_TWO = "2026-11-21T01:00:00Z"


def github_release(release_id, tag, published_at, *, body="Original notes", prerelease=False):
    return {
        "id": release_id,
        "tag_name": tag,
        "url": f"https://api.github.com/repos/{REPOSITORY}/releases/{release_id}",
        "html_url": f"https://github.com/{REPOSITORY}/releases/tag/{tag}",
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

    def refresh(self, rows, at, *, success=True):
        self.feed.write_text(json.dumps(rows), encoding="utf-8")
        result = self.invoke("refresh", "--fixture", self.feed, "--observed-at", at)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def report(self, as_of=DAY_TWO, *options):
        result = self.invoke("report", "--as-of", as_of, *options)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

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
        import io

        from fastest_release_watch.feed import fetch

        with patch("http.client.HTTPSConnection") as transport:
            connection = transport.return_value
            connection.getresponse.return_value = io.BytesIO(b"")
            connection.getresponse.return_value.status = 302
            with self.assertRaisesRegex(ValueError, "HTTP 302"):
                fetch()
            connection.request.assert_called_once()
            self.assertEqual(connection.request.call_args.args,
                             ("GET", "/repos/ggml-org/llama.cpp/releases?per_page=10&page=1"))

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
        self.assertEqual(json.loads(result.stdout), {
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
            self.assertEqual([release["status"] for release in report["releases"]],
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

            self.refresh([github_release(100, "test-only-tag", DAY_ONE)], DAY_ONE)
            status, _, body = request("/runtime-releases.json", decode=False)
            self.assertEqual(status, 503)
            self.assertNotIn("test-only-tag", body)

    def test_origin_rechecks_matched_retest_rights(self):
        self.prepare_history()
        watch = PostgresStore(self.database_url)
        fixture_directory = PRODUCTION / "fixtures/release-watch"
        watch.record("live", DAY_ONE, decode((fixture_directory / "releases.json").read_bytes()))
        note = json.loads((fixture_directory / "applicability.json").read_text())["notes"][0]
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
                "runtime_build": config["build_sha"], "runtime_id": "llama.cpp",
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
