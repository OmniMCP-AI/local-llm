import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from test_image_team import PRODUCTION, example


def invoke(database, *options):
    return subprocess.run(
        [sys.executable, "-B", "-m", "fastest_image_team", "--database-url", database, *options],
        cwd=PRODUCTION, capture_output=True, text=True, timeout=10,
    )


def consented_fixture():
    # An in-test stand-in for a reviewed scenario, never imported by production.
    def test_evidence(value):
        if isinstance(value, dict):
            return {key: test_evidence(item) for key, item in value.items()}
        if isinstance(value, str):
            if value == "fictional":
                return "reviewed"
            return value.replace("Fictional", "Test-only").replace("fictional", "test-only")
        return value

    scenario = test_evidence(example())
    scenario["kind"] = "consented"
    return scenario


class ImageTeamImportValidationTest(unittest.TestCase):
    def test_import_rejects_inputs_outside_approved_aggregate_scope_before_connecting(self):
        unapproved = consented_fixture()
        unapproved["workload"]["public_aggregate_allowed"] = False
        individual_data = consented_fixture()
        individual_data["workload"]["individual_activity"] = ["private-activity-marker"]
        unreviewed = consented_fixture()
        unreviewed["workload"]["source"]["kind"] = "fictional"
        duplicate_kind = '{"kind":"illustrative",' + json.dumps(consented_fixture())[1:]
        cases = (
            (json.dumps(example()), "consented"),
            (json.dumps(unapproved), "requires consent"),
            (json.dumps(individual_data), "workload must contain exactly"),
            (json.dumps(unreviewed), "must be reviewed"),
            (duplicate_kind, "unique object fields"),
        )
        with tempfile.TemporaryDirectory(prefix="image-team-input-") as directory:
            scenario = Path(directory) / "scenario.json"
            for data, reason in cases:
                with self.subTest(reason=reason):
                    scenario.write_text(data, encoding="utf-8")
                    result = invoke("invalid connection string", "ingest-approved", str(scenario))
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn(reason, result.stderr)
                    self.assertNotIn("private-activity-marker", result.stderr)
                    self.assertEqual(result.stdout, "")


class ImageTeamPostgresTest(unittest.TestCase):
    def run(self, result=None):
        try:
            return super().run(result)
        finally:
            self.doCleanups()

    def setUp(self):
        sandbox = tempfile.TemporaryDirectory(prefix="image-team-pg-", dir="/tmp")
        self.addCleanup(lambda: self.assertFalse(Path(sandbox.name).exists()))
        self.directory = Path(self.enterContext(sandbox))
        cluster = self.directory / "db"
        subprocess.run(
            ["initdb", "-D", str(cluster), "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True, capture_output=True, text=True,
        )
        with (self.directory / "postgres.log").open("w") as log:
            postgres = subprocess.Popen(
                ["postgres", "-D", str(cluster), "-k", str(self.directory), "-c", "listen_addresses="],
                stdout=log, stderr=subprocess.STDOUT,
            )
        self.addCleanup(self.stop_postgres, postgres)
        self.database = f"host={self.directory} dbname=postgres"
        for _ in range(100):
            if subprocess.run(["pg_isready", "-d", self.database], capture_output=True).returncode == 0:
                break
            if postgres.poll() is not None:
                self.fail((self.directory / "postgres.log").read_text())
            time.sleep(0.05)
        else:
            self.fail("Image team test database did not start")

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

    def succeed(self, *options):
        completed = invoke(self.database, *options)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout.strip()

    def test_approved_import_replays_the_same_bundle_after_a_new_revision(self):
        self.succeed("migrate")
        scenario = consented_fixture()
        scenario["workload"]["source"]["reference"] = "测试工作流 team's approved aggregate"
        source = self.directory / "scenario.json"
        source.write_text(json.dumps(scenario, ensure_ascii=False), encoding="utf-8")
        expected = self.directory / "file-comparison"
        self.succeed("build", expected, "--scenario", source)
        pin = self.succeed("ingest-approved", source)
        self.assertRegex(pin, r"^[a-f0-9]{64}$")

        first = self.directory / "first-comparison"
        self.succeed("build", first, "--scenario-pin", pin)
        source.write_text(json.dumps(scenario, sort_keys=True, indent=2), encoding="utf-8")
        self.assertEqual(self.succeed("ingest-approved", source), pin)
        self.succeed("migrate")

        scenario["workload"]["deadline_hours"] = "0.5"
        source.write_text(json.dumps(scenario), encoding="utf-8")
        changed_pin = self.succeed("ingest-approved", source)
        self.assertNotEqual(changed_pin, pin)
        source.unlink()

        changed = self.directory / "changed-comparison"
        self.succeed("build", changed, "--scenario-pin", changed_pin)
        comparison = json.loads((changed / "image-team.json").read_text())
        self.assertIn("peak_deadline_unmet", comparison["plans"]["cloud"]["reasons"])
        self.assertFalse(comparison["payback"]["local"]["supports_payback_claim"])

        replay = self.directory / "replay-comparison"
        self.succeed("build", replay, "--scenario-pin", pin)
        for directory in (expected, first, replay):
            self.assertEqual(
                {file.name for file in directory.iterdir()},
                {"image-team.json", "image-team.md", "image-team.html", "manifest.json"},
            )
        for file in expected.iterdir():
            self.assertEqual((first / file.name).read_bytes(), file.read_bytes())
            self.assertEqual((replay / file.name).read_bytes(), file.read_bytes())

    def test_withdrawal_blocks_new_bundles_even_after_reimport(self):
        self.succeed("migrate")
        source = self.directory / "scenario.json"
        scenario = consented_fixture()
        source.write_text(json.dumps(scenario), encoding="utf-8")
        pin = self.succeed("ingest-approved", source)
        original = self.directory / "before-withdrawal"
        self.succeed("build", original, "--scenario-pin", pin)

        scenario["revision"] = "independent-test-only-revision"
        source.write_text(json.dumps(scenario), encoding="utf-8")
        active_pin = self.succeed("ingest-approved", source)

        self.succeed("withdraw", pin)
        self.succeed("withdraw", pin)
        self.succeed("migrate")
        source.write_text(json.dumps(consented_fixture()), encoding="utf-8")
        self.assertEqual(self.succeed("ingest-approved", source), pin)
        for unavailable in (pin, "0" * 64):
            with self.subTest(pin=unavailable):
                output = self.directory / "unavailable"
                completed = invoke(self.database, "build", output, "--scenario-pin", unavailable)
                self.assertEqual(completed.returncode, 1, completed.stderr)
                self.assertIn("No active approved image-team scenario", completed.stderr)
                self.assertFalse(output.exists())
        self.succeed("build", self.directory / "active", "--scenario-pin", active_pin)
        self.assertTrue((original / "manifest.json").is_file())

    def test_scenario_storage_denies_a_nonoperator_with_intake_schema_access(self):
        self.succeed("migrate")
        source = self.directory / "scenario.json"
        source.write_text(json.dumps(consented_fixture()), encoding="utf-8")
        pin = self.succeed("ingest-approved", source)
        subprocess.run(
            ["psql", "-XqAtw", "-v", "ON_ERROR_STOP=1", "-d", self.database],
            input="CREATE ROLE intake_reader LOGIN; GRANT USAGE ON SCHEMA fastest_intake TO intake_reader;",
            check=True, capture_output=True, text=True, timeout=10,
        )
        output = self.directory / "unauthorized"
        denied = invoke(f"{self.database} user=intake_reader", "build", output, "--scenario-pin", pin)
        self.assertEqual(denied.returncode, 1, denied.stderr)
        self.assertIn("operator permissions", denied.stderr)
        self.assertFalse(output.exists())

        for options in ((), ("--illustrative",)):
            preview = self.directory / ("fictional" if options else "default")
            offline = invoke("invalid connection string", "build", preview, *options)
            self.assertEqual(offline.returncode, 0, offline.stderr)
            result = json.loads((preview / "image-team.json").read_text())
            self.assertEqual(result["estimate_kind"], "illustrative" if options else "unavailable")
