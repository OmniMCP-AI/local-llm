from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from hashlib import sha256
import http.client
import json
from pathlib import Path
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from threading import Thread
import time
import unittest

from fastest_release import InvalidObservation, ReleaseError, ReleaseStore
from fastest_release.research import SEED_ROOT


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

    def test_research_import_replays_with_source_ids_and_projection_status(self):
        release_id = self.store.publish(self.observation)

        def research(*args):
            result = self.research_command(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        imported = research("research-import")
        self.assertEqual(research("research-import"), imported)
        seed_id = imported["seed_id"]
        manifest = research("research-read", seed_id)
        self.assertEqual(manifest["counts"], {
            "profiles": 116,
            "components": 487,
            "legacy_hardware": 99,
            "series": 242,
            "observations": 450,
            "qualified_associations": 293,
            "unassigned_observations": 157,
            "native_hardware_profiles": 16,
            "partial_hardware_profiles": 100,
            "complete_builds": 0,
            "structural_benchmarks": 127,
            "research_only_observations": 323,
            "partial_model_references": 140,
            "native_models": 0,
            "native_community_submissions": 0,
        })

        rows = {}
        for kind, count in (
            ("profile", 116),
            ("component", 487),
            ("legacy_hardware", 99),
            ("series", 242),
            ("observation", 450),
            ("profile_association", 293),
            ("model_reference", 140),
        ):
            rows[kind] = research("research-read", seed_id, kind)
            self.assertEqual(len(rows[kind]), count, kind)
            self.assertEqual(len({row["id"] for row in rows[kind]}), count, kind)
        observations = rows["observation"]
        self.assertEqual(sum(row["hardware_profile_id"] is None for row in observations), 157)
        self.assertEqual(sum(row["benchmark_entry"] is not None for row in observations), 127)
        self.assertEqual(sum(row["hardware_profile"] is not None for row in rows["profile"]), 16)
        chosen = research("research-read", seed_id, "observation", "V001-P001")
        self.assertEqual(chosen["original"]["value"], "53")
        self.assertEqual(chosen["original"]["unit"], "tokens/s")
        self.assertEqual(chosen["original"]["source_start_ms"], "301010")
        self.assertEqual(chosen["source"], {"path": "performance-observations.csv", "line": 2})
        self.assertEqual(chosen["series_id"], "V001-S01")
        self.assertEqual(chosen["model_reference_id"], "V001-M01")
        self.assertEqual(chosen["hardware_profile_id"], "V001-HP-G001")
        self.assertEqual(chosen["benchmark_entry"]["tokSOut"], 53.0)
        association = research("research-read", seed_id, "profile_association", "V001-P001")
        self.assertIn("not independently identicalphysicalhost", association["original"]["association"])
        self.assertEqual(
            research("research-read", seed_id, "observation", "V001-P004")["hardware_profile_id"],
            None,
        )
        self.assertIsNone(research("research-read", seed_id, "observation", "V001-P011")["benchmark_entry"])
        model = research("research-read", seed_id, "model_reference", "V001-M01")
        self.assertEqual(model["llm_model_partial"], {"parameter_count": "7B"})
        self.assertIsNone(model["llm_model"])

        profile = research("research-read", seed_id, "profile", "V005-HP-TEST")
        self.assertEqual(profile["hardware_profile"]["hardware"]["total_ram_gb"], 64)
        self.assertFalse(profile["complete_build"])
        self.assertEqual(profile["original"]["source_hardware_record_ids"], ["V005-TEST", "V005-G001"])
        part = research("research-read", seed_id, "component", "2")
        self.assertEqual(part["original"]["profile_id"], "V005-HP-TEST")
        self.assertEqual(part["original"]["exact_part_model"], "Not reported in available captions")
        legacy = research("research-read", seed_id, "legacy_hardware", "V005-TEST")
        self.assertEqual(legacy["original"]["system_ram"], "64GB")
        ttft = research("research-read", seed_id, "observation", "V001-P021")
        self.assertEqual((ttft["original"]["value"], ttft["original"]["unit"]), ("31", "seconds"))
        self.assertEqual(ttft["benchmark_entry"]["ttftMs"], 31_000)
        self.assertEqual(ttft["unit_conversion"]["original"]["factor"], 1000)

        self.assertEqual(self.store.read()["release_id"], release_id)
        self.assertNotIn("V001-P001", self.store.artifact(release_id, "chart.json"))
        subprocess.run(
            ["psql", "-XqAtw", "-v", "ON_ERROR_STOP=1", "-d", self.database_url],
            input=(
                "CREATE ROLE research_boundary_reader LOGIN;"
                "GRANT USAGE ON SCHEMA fastest_release TO research_boundary_reader;"
                "GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid) TO research_boundary_reader;"
            ),
            text=True,
            check=True,
        )
        reader = ReleaseStore(f"{self.database_url} user=research_boundary_reader")
        self.assertEqual(reader.read()["release_id"], release_id)
        refused = self.research_command("research-read", seed_id, database_url=reader.database_url)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("permission denied", refused.stderr)

    def test_research_import_rejects_a_qualified_association_with_a_conflicting_locator(self):
        temp = self.enterContext(tempfile.TemporaryDirectory(prefix="fastest-seed-test-"))
        seed = Path(temp, "seed")
        shutil.copytree(SEED_ROOT, seed)
        associations = seed / "profile-performance-links.csv"
        original = associations.read_bytes()
        revised = original.replace(b"v=2L_RB-XqisE&t=301s", b"v=2L_RB-XqisE&t=302s", 1)
        self.assertNotEqual(original, revised)
        associations.write_bytes(revised)

        result = self.research_command("research-import", "--seed-dir", str(seed))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V001-P001 association locator", result.stderr)

    def research_command(self, *args, database_url=None):
        return subprocess.run(
            [sys.executable, "-m", "fastest_release", "--database-url", database_url or self.database_url, *args],
            cwd=FIXTURE.parents[1],
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=30,
        )

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
