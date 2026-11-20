from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from hashlib import sha256
import http.client
import json
from pathlib import Path
import signal
import subprocess
import tempfile
from threading import Thread
import time
import unittest

from fastest_release import InvalidObservation, ReleaseError, ReleaseStore


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic-observation.json"


class ReleaseTest(unittest.TestCase):
    def run(self, result=None):
        try:
            return super().run(result)
        finally:
            self.doCleanups()

    def setUp(self):
        sandbox = tempfile.TemporaryDirectory(prefix="fastest-pg-", dir="/tmp")
        self.addCleanup(lambda: self.assertFalse(Path(sandbox.name).exists()))
        workspace = self.enterContext(sandbox)
        cluster = Path(workspace, "db")
        subprocess.run(
            ["initdb", "-D", str(cluster), "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True,
            capture_output=True,
            text=True,
        )
        with open(Path(workspace, "postgres.log"), "w") as log:
            postgres = subprocess.Popen(
                ["postgres", "-D", str(cluster), "-k", workspace, "-c", "listen_addresses="],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        self.addCleanup(self.stop_postgres, postgres)
        self.database_url = f"host={workspace} dbname=postgres"
        for _ in range(100):
            probe = subprocess.run(["pg_isready", "-d", self.database_url], capture_output=True)
            if probe.returncode == 0:
                break
            if postgres.poll() is not None:
                self.fail(Path(workspace, "postgres.log").read_text())
            time.sleep(0.05)
        else:
            self.fail("PostgreSQL did not start")
        self.store = ReleaseStore(self.database_url)
        self.store.migrate()
        self.observation = json.loads(FIXTURE.read_text(encoding="utf-8"))

    @staticmethod
    def stop_postgres(postgres):
        if postgres.poll() is None:
            postgres.send_signal(signal.SIGINT)
            try:
                postgres.wait(timeout=10)
            except subprocess.TimeoutExpired:
                postgres.send_signal(signal.SIGQUIT)
                postgres.wait(timeout=10)
        # Popen.wait reaps the owned postmaster before the cluster directory is removed.
        assert postgres.returncode is not None

    def test_public_snapshot_carries_one_observation_into_all_surfaces(self):
        release_id = self.store.publish(self.observation)
        snapshot = self.store.read(release_id)
        self.assertEqual(snapshot["release_id"], release_id)
        self.assertEqual(snapshot["row"]["hardware"]["revision_id"], "f701c689-5f03-45da-bc5b-9e271336489e")
        self.assertEqual(
            snapshot["row"]["artifact"]["sha256"],
            sha256(FIXTURE.with_name("synthetic-artifact.txt").read_bytes()).hexdigest(),
        )
        self.assertEqual(snapshot["row"]["workload"]["id"], "solo-decode")
        self.assertEqual(snapshot["row"]["source"]["locator"], "production/fixtures/synthetic-observation.json#/metric")
        self.assertEqual(snapshot["row"]["rights"]["decision_id"], "ec133ed3-267a-410f-8776-ecc5c0961d25")
        self.assertEqual(
            snapshot["row"]["fields"]["driver_version"],
            {"status": "missing", "reason": "The synthetic fixture does not define a driver."},
        )
        self.assertNotIn("unpublished_operator_note", snapshot["row"]["fields"])

        evidence_id = "c5258a75-75ec-465f-8cbc-1212b749fddd"
        for name in ("benchmark.md", "benchmark.html", "chart.json", "table.json"):
            artifact = self.store.artifact(release_id, name)
            with self.subTest(artifact=name):
                for value in (evidence_id, "37.625", "tok/s", "synthetic", release_id):
                    self.assertIn(value, artifact)
                self.assertNotIn("private calibration note", artifact)
                self.assertNotIn("unpublished_operator_note", artifact)

        markdown = self.store.artifact(release_id, "benchmark.md")
        self.assertIn("[Chart data](./chart.json)", markdown)
        self.assertIn("[Table data](./table.json)", markdown)
        self.assertIn("[Citation](#citation)", markdown)
        chart = json.loads(self.store.artifact(release_id, "chart.json"))
        table = json.loads(self.store.artifact(release_id, "table.json"))
        self.assertEqual(chart["rows"], table["rows"])
        self.assertEqual(chart["rows"][0]["metric"]["value"], "37.625")
        self.assertEqual(chart["rows"][0]["metric"]["unit"], "tok/s")
        self.assertEqual(chart["rows"][0]["evidence_id"], evidence_id)

    def test_correction_creates_new_revision_and_replays_keep_current(self):
        with ThreadPoolExecutor(max_workers=2) as writers:
            first, replay = writers.map(self.store.publish, [self.observation, self.observation])
        self.assertEqual(first, replay)
        original = first
        names = ("benchmark.md", "benchmark.html", "chart.json", "table.json", "manifest.json")
        originals = {name: self.store.artifact(original, name) for name in names}
        original_input = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(self.store.publish(original_input), original)

        self.observation["metric"]["value"] = "41.000000000001"
        self.observation["source"]["revision"] = "fixture-v2"
        self.observation["rights"]["decision_id"] = "0a4080df-52f1-42fc-8c5c-d03fff57501d"
        corrected = self.store.publish(self.observation)
        self.assertNotEqual(original, corrected)
        self.assertEqual(self.store.publish(self.observation), corrected)
        self.assertEqual(self.store.publish(original_input), original)

        active = self.store.read()
        self.assertEqual(active["release_id"], corrected)
        self.assertEqual(active["previous_release_id"], original)
        self.assertEqual(active["revision"], 2)
        self.assertEqual(active["row"]["evidence_id"], original_input["evidence_id"])
        for name, original_body in originals.items():
            self.assertEqual(self.store.artifact(original, name), original_body)
            if name != "manifest.json":
                self.assertIn("41.000000000001", self.store.artifact(corrected, name))
        manifest = json.loads(self.store.artifact(corrected, "manifest.json"))
        for name, digest in manifest["artifacts"].items():
            self.assertEqual(digest, sha256(self.store.artifact(corrected, name).encode()).hexdigest())

    def test_ineligible_observation_does_not_advance_current(self):
        original = self.store.publish(self.observation)
        self.observation["rights"]["core"] = "deny"
        with self.assertRaises(InvalidObservation):
            self.store.publish(self.observation)
        self.observation["rights"]["core"] = "allow"
        self.observation["metric"]["unit"] = "ms"
        with self.assertRaises(ReleaseError):
            self.store.publish(self.observation)
        self.store.migrate()
        self.assertEqual(self.store.read()["release_id"], original)

    def test_public_routes_pin_current_and_quarantine_withdrawn_evidence(self):
        from fastest_release.http import make_server

        original = self.store.publish(self.observation)
        self.observation["metric"]["value"] = "41.125"
        corrected = self.store.publish(self.observation)
        subprocess.run(
            ["psql", "-XqAtw", "-v", "ON_ERROR_STOP=1", "-d", self.database_url],
            input="""
                CREATE ROLE release_reader LOGIN;
                GRANT USAGE ON SCHEMA fastest_release TO release_reader;
                GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid) TO release_reader;
            """,
            text=True,
            check=True,
        )
        reader = ReleaseStore(f"{self.database_url} user=release_reader")
        with self.assertRaises(ReleaseError):
            reader.withdraw(self.observation["evidence_id"], "Unexpected reader write")
        server = make_server(reader, "127.0.0.1", 0)
        thread = Thread(target=server.serve_forever)

        def stop_http():
            if thread.is_alive():
                server.shutdown()
                thread.join(5)
            server.server_close()
            self.assertFalse(thread.is_alive())

        self.addCleanup(stop_http)
        thread.start()

        def request(method, path, **headers):
            with closing(http.client.HTTPConnection(*server.server_address, timeout=5)) as connection:
                connection.request(method, path, headers=headers)
                response = connection.getresponse()
                return response.status, dict(response.getheaders()), response.read().decode()

        original_url = f"/releases/{original}/benchmark.html"
        status, headers, body = request("GET", original_url)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("37.625", body)
        status, headers, _ = request("GET", "/releases/current/benchmark.html")
        self.assertEqual(status, 307)
        self.assertEqual(headers["Location"], f"/releases/{corrected}/benchmark.html")
        status, _, _ = request("GET", original_url, Host="untrusted.example")
        self.assertEqual(status, 400)
        status, _, _ = request("POST", original_url)
        self.assertEqual(status, 501)

        self.store.withdraw(self.observation["evidence_id"], "Private withdrawal reason")
        self.store.withdraw(self.observation["evidence_id"], "Retry")
        for release_id in (original, corrected):
            for name in ("benchmark.md", "benchmark.html", "chart.json", "table.json", "manifest.json"):
                with self.subTest(release_id=release_id, name=name):
                    status, headers, body = request("GET", f"/releases/{release_id}/{name}")
                    self.assertEqual(status, 410)
                    self.assertEqual(headers["Cache-Control"], "no-store")
                    for private in ("37.625", "41.125", self.observation["evidence_id"], "Private withdrawal reason"):
                        self.assertNotIn(private, body)
        with self.assertRaises(ReleaseError):
            self.store.publish(self.observation)
