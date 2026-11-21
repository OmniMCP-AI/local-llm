import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager, redirect_stderr
from hashlib import sha256
from io import StringIO
import http.client
import json
from pathlib import Path
import os
import select
import shutil
import signal
import subprocess
import sys
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from fastest_release import InvalidObservation, ReleaseError, ReleaseStore, capture_scaling
from fastest_release.capture_cpu import candidate as cpu_baseline_candidate
from fastest_prices import PriceStore
from fastest_release.research import SEED_ROOT
from test_mcp import HAS_SDK, get as get_public, mcp_client
from test_mcp_http import mcp_http_client, mcp_http_server
from test_public_api import api_client, api_server
from test_scaling import BASELINE, COMPARISON, fixture_releases
from fastest_release.scaling import PLAN, scaling_report
from test_scaling_capture import BENCH, FIRST, SECOND
from fastest_serving import capture


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic-observation.json"
CPU_BASELINE_CONDITIONS = {
    "comparison_eligibility": {
        "status": "known", "value": "Standalone shared CI CPU baseline. Excluded from the quiet-host 7B text pilot.",
    },
    "runner_image_version": {"status": "known", "value": "20261120.1.0"},
    "wall_power": {"status": "missing", "reason": "The GitHub-hosted runner has no wall power meter."},
}


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
        self.socket_path = Path(workspace, "socket")
        self.socket_path.mkdir(mode=0o755)
        subprocess.run(
            ["initdb", "-D", str(cluster), "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True,
            capture_output=True,
            text=True,
        )
        with open(Path(workspace, "postgres.log"), "w") as log:
            postgres = subprocess.Popen(
                ["postgres", "-D", str(cluster), "-k", str(self.socket_path), "-c", "listen_addresses="],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        self.addCleanup(self.stop_postgres, postgres)
        self.database_url = f"host={self.socket_path} dbname=postgres"
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

    @contextmanager
    def deployed_origin(self, *options):
        image = os.environ.get("FASTEST_ORIGIN_TEST_IMAGE")
        if image:
            name = "fastest-origin-" + uuid4().hex
            port = "8077"
            try:
                subprocess.run(
                    ["docker", "run", "--detach", "--read-only", "--name", name, "--health-interval", "1s",
                     "-p", f"127.0.0.1::{port}", "-e", f"PORT={port}",
                     "-e", "FASTEST_DATABASE_URL=host=/reader dbname=postgres user=origin_reader",
                     "--mount", f"type=bind,src={self.socket_path},dst=/reader,readonly",
                     image, "--trusted-host", "origin.example", *options],
                    check=True, capture_output=True, text=True, timeout=30,
                )
                for _ in range(100):
                    state = subprocess.check_output(
                        ["docker", "inspect", "-f", "{{.State.Health.Status}}", name],
                        text=True, timeout=5,
                    ).strip()
                    if state == "healthy":
                        break
                    if state == "unhealthy":
                        self.fail(subprocess.check_output(
                            ["docker", "inspect", "-f", "{{json .State.Health}}", name], text=True, timeout=5,
                        ))
                    time.sleep(0.1)
                else:
                    self.fail("The release image did not become healthy")
                address = subprocess.check_output(
                    ["docker", "port", name, port], text=True, timeout=5,
                ).strip()
                yield "http://" + address, "origin.example"
            finally:
                subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=15)
                leftover = subprocess.check_output(
                    ["docker", "ps", "-aq", "--filter", f"name=^/{name}$"], timeout=5,
                )
                self.assertFalse(leftover)
            return

        env = {**os.environ, "FASTEST_DATABASE_URL": self.database_url + " user=origin_reader"}
        with subprocess.Popen(
            [sys.executable, "-B", "-m", "fastest_release", "serve", "--port", "0", *options],
            cwd=FIXTURE.parents[1], env=env, stderr=subprocess.PIPE, text=True,
        ) as server:
            try:
                self.assertTrue(select.select([server.stderr], [], [], 10)[0], "The release listener did not start")
                address = server.stderr.readline().strip()
                self.assertRegex(address, r"^Listening on 127\.0\.0\.1:[0-9]+$")
                yield "http://" + address.removeprefix("Listening on "), None
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)

    def test_private_tariff_intake_preserves_legacy_batches_and_public_cost_gate(self):
        bundle_path = self.socket_path.parent / "capture.json"

        def intake(command, bundle=None, *, check=True):
            args = [sys.executable, "-B", "-m", "fastest_intake", "--database-url", self.database_url, command]
            if bundle is not None:
                bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
                args.append(str(bundle_path))
            return subprocess.run(args, cwd=FIXTURE.parents[1], text=True, capture_output=True,
                                  check=check, timeout=30)

        old_bundle = {
            "checked_at": "2026-11-20T00:00:00Z",
            "note": "Fixture capture.",
            "sources": [{"source": "fixture-utility", "url": "https://utility.example/schedule",
                         "status": "captured", "note": "Synthetic tariff."}],
            "prices": [],
            "evaluations": [],
        }
        intake("migrate")
        legacy = json.loads(intake("ingest", old_bundle).stdout)
        self.assertEqual(legacy["batch_id"], "b8fcf73b7d7d0b828a9e63efa6447570029513a22210ee7866869e622f86bba7")
        tariff = {
            "id": "fixture-power-off-peak", "source": "fixture-utility", "locator": "Schedule A, page 2",
            "kind": "electricity", "provider": "Fixture Energy", "offering": "Residential Schedule A",
            "revision": "fixture-schedule-2026", "market": "US", "region": "US-CA fixture territory",
            "currency": "USD", "amount": "0.12345", "unit": "kwh", "component": "off-peak",
            "effective_from": "2026-01-01", "effective_until": "2027-01-01",
            "qualification": "Residential accounts in the fixture territory.",
        }
        bundle = {**old_bundle, "tariffs": [tariff]}
        with api_client(self.store) as request:
            before = request("/api/v1/calculator")
            imported = json.loads(intake("ingest", bundle).stdout)
            self.assertEqual(imported["tariff_candidates"], 1)
            self.assertEqual(imported["batches"], 2)
            self.assertEqual(json.loads(intake("ingest", bundle).stdout), imported)
            self.assertEqual(json.loads(intake("ingest", old_bundle).stdout)["batch_id"], legacy["batch_id"])
            after = request("/api/v1/calculator")
            self.assertEqual((before[0], before[2]), (after[0], after[2]))
            self.assertEqual(after[2]["estimate_kind"], "unavailable")

        self.assertEqual(self.store._query("""
            SELECT amount, unit, currency, effective_from, effective_until, region
            FROM fastest_intake.tariff_candidate
        """), "0.12345|kwh|USD|2026-01-01|2027-01-01|US-CA fixture territory")
        blocked = {**bundle, "sources": [{**old_bundle["sources"][0], "status": "no_quote"}]}
        rejected = intake("ingest", blocked, check=False)
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("captured source probe", rejected.stderr)
        self.assertEqual(json.loads(intake("stats").stdout)["batches"], 2)
        self.store._query("CREATE ROLE intake_public_reader LOGIN;")
        with self.assertRaisesRegex(ReleaseError, "permission denied"):
            ReleaseStore(self.database_url + " user=intake_public_reader")._query(
                "SELECT amount FROM fastest_intake.tariff_candidate"
            )

    def inference_intake(self, command, bundle=None, *, check=True):
        args = [sys.executable, "-B", "-m", "fastest_intake", "--database-url", self.database_url, command]
        if bundle is not None:
            bundle_path = self.socket_path.parent / "inference-capture.json"
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            args.append(str(bundle_path))
        result = subprocess.run(args, cwd=FIXTURE.parents[1], text=True, capture_output=True, timeout=30)
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_private_inference_intake_preserves_the_reported_measurement_on_replay(self):
        trial = {
            "id": "dual-decode", "source": "fixture-benchmark", "locator": "Decode table, dual Vulkan row",
            "outcome": "measured", "gpu_count": 2, "gpu_ids": ["Fixture Radeon", "Fixture RTX"],
            "model": "Fixture 27B", "model_revision": "published-model-revision",
            "artifact": "Fixture-27B-Q6_K.gguf", "artifact_revision": "published-artifact-revision",
            "runtime": "llama.cpp", "runtime_revision": "reported-runner-revision", "backend": "Vulkan",
            "quantization": "Q6_K", "context_tokens": 4096, "observed_on": "2026-11-19",
            "metric": "tg128", "amount": "42.60", "unit": "tok/s", "statistic": "arithmetic_mean",
            "sample_count": 3, "reported_uncertainty": "0.10", "uncertainty_kind": "standard_deviation",
            "placement": "Proportional layer split.", "transport": "Direct device transfer was observed.",
            "context": {"prompt_tokens": 512, "generated_tokens": 128},
            "qualification": "Only summary statistics are available.",
        }
        bundle = {
            "checked_at": "2026-11-20T00:00:00Z", "note": "Synthetic inference benchmark capture.",
            "sources": [{"source": "fixture-benchmark", "url": "https://benchmark.example/results#decode",
                         "status": "captured", "note": "Fixture benchmark report."}],
            "prices": [], "evaluations": [], "inference_trials": [trial],
        }

        self.inference_intake("migrate")
        receipt = json.loads(self.inference_intake("ingest", bundle).stdout)
        self.assertEqual((receipt["batches"], receipt["source_probes"], receipt["inference_trials"]), (1, 1, 1))
        self.assertEqual(json.loads(self.inference_intake("ingest", bundle).stdout), receipt)

        [row] = json.loads(self.store._query("""
            SELECT json_agg(to_jsonb(trial) || jsonb_build_object(
                'amount', trial.amount::text, 'reported_uncertainty', trial.reported_uncertainty::text,
                'url', probe.url
            ))
            FROM fastest_intake.inference_trial AS trial
            JOIN fastest_intake.source_probe AS probe USING (batch_id, source)
        """))
        self.assertEqual(row, {**trial, "batch_id": receipt["batch_id"], "url": bundle["sources"][0]["url"]})

        self.store._query("CREATE ROLE inference_public_reader LOGIN;")
        reader = ReleaseStore(self.database_url + " user=inference_public_reader")
        with self.assertRaisesRegex(ReleaseError, "permission denied"):
            reader._query("SELECT amount FROM fastest_intake.inference_trial")

    def test_private_inference_intake_preserves_partial_and_missing_evidence(self):
        trial = {
            "source": "fixture-benchmark", "locator": "Excerpt",
            "qualification": "The excerpt omits run details.",
        }
        bundle = {
            "checked_at": "2026-11-20T00:00:00Z", "note": "Synthetic partial benchmark.",
            "sources": [{"source": "fixture-benchmark", "url": "https://benchmark.example/summary",
                         "status": "captured", "note": "Fixture benchmark excerpt."}],
            "prices": [], "evaluations": [],
            "inference_trials": [
                {**trial, "id": "partial", "outcome": "measured", "gpu_count": 2, "gpu_ids": ["Fixture RTX"],
                 "metric": "decode", "amount": "12", "unit": "tokens/s", "transport": None,
                 "context": {"topology": "NVLink present", "probe_scope": "Separate link test."}},
                {**trial, "id": "oom", "outcome": "oom", "gpu_count": 1, "model": "Fixture model"},
                {**trial, "id": "failed", "outcome": "failed", "placement": "One device."},
                {**trial, "id": "unknown", "outcome": "unknown"},
            ],
        }
        self.inference_intake("migrate")
        receipt = json.loads(self.inference_intake("ingest", bundle).stdout)
        self.assertEqual(receipt["inference_trials"], 4)
        self.assertEqual(self.store._query("""
            SELECT id, outcome, gpu_count, gpu_ids, metric, amount, unit, transport, context->>'probe_scope'
            FROM fastest_intake.inference_trial ORDER BY id
        """).splitlines(), [
            "failed|failed|||||||",
            "oom|oom|1||||||",
            'partial|measured|2|{"Fixture RTX"}|decode|12|tokens/s||Separate link test.',
            "unknown|unknown|||||||",
        ])

    def test_private_inference_intake_rejects_invalid_evidence_without_partial_writes(self):
        trial = {
            "id": "decode", "source": "fixture-benchmark", "locator": "Benchmark row",
            "outcome": "measured", "metric": "decode", "amount": "12", "unit": "tokens/s",
            "qualification": "Fixture report.",
        }
        source = {
            "source": "fixture-benchmark", "url": "https://benchmark.example/summary",
            "status": "captured", "note": "Fixture benchmark report.",
        }
        bundle = {
            "checked_at": "2026-11-20T00:00:00Z", "note": "Synthetic benchmark.",
            "sources": [source], "prices": [], "evaluations": [],
        }
        self.inference_intake("migrate")
        initial = json.loads(self.inference_intake("stats").stdout)
        for changes in ({"metric": None}, {"amount": None}, {"unit": None}, {"outcome": "oom"}):
            with self.subTest(changes=changes):
                result = self.inference_intake("ingest", {
                    **bundle, "inference_trials": [trial, {**trial, **changes, "id": "invalid"}],
                }, check=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn("inference_trial_outcome_measurement_check", result.stderr)
                self.assertEqual(json.loads(self.inference_intake("stats").stdout), initial)

        result = self.inference_intake("ingest", {
            **bundle, "sources": [{**source, "status": "no_verified_result"}], "inference_trials": [trial],
        }, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("captured source probe", result.stderr)
        self.assertEqual(json.loads(self.inference_intake("stats").stdout), initial)

    def test_private_retail_intake_upgrades_legacy_rows_and_preserves_batch_replay(self):
        production = FIXTURE.parents[1]
        bundle_path = self.socket_path.parent / "retail-capture.json"

        def intake(command, bundle=None, *, check=True):
            args = [sys.executable, "-B", "-m", "fastest_intake", "--database-url", self.database_url, command]
            if bundle is not None:
                bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
                args.append(str(bundle_path))
            result = subprocess.run(args, cwd=production, text=True, capture_output=True, timeout=30)
            if check:
                self.assertEqual(result.returncode, 0, result.stderr)
            return result

        legacy_id = "9e9ad7e3222a231a1893b24f0eb7ac61ba700fc41d72626d113a9da7149450a0"
        legacy_price = {
            "id": "fixture-legacy", "source": "fixture-retailer", "locator": "Product page",
            "gpu_id": "arc-pro-b60", "board": "Fixture B60", "channel": "Fixture retail",
            "market": "US", "currency": "USD", "amount": "599.95", "kind": "asking_price",
            "condition": "new", "source_date": "2026-11-19", "listing_url": "https://retail.example/card",
            "qualification": "Original figure.",
        }
        legacy_bundle = {
            "checked_at": "2026-11-20T00:00:00Z", "note": "Fixture retail capture.",
            "sources": [{"source": "fixture-retailer", "url": "https://retail.example/card",
                         "status": "captured", "note": "Synthetic GPU listing."}],
            "prices": [legacy_price], "evaluations": [],
        }
        self.store._query((production / "fixtures" / "legacy-price-intake.sql").read_text(encoding="utf-8"))
        self.store._query(f"""
            INSERT INTO fastest_intake.batch VALUES ('{legacy_id}', '2026-11-20T00:00:00Z', 'Fixture retail capture.');
            INSERT INTO fastest_intake.source_probe VALUES ('{legacy_id}', 'fixture-retailer',
                'https://retail.example/card', 'captured', 'Synthetic GPU listing.');
            INSERT INTO fastest_intake.price_candidate VALUES ('{legacy_id}', 'fixture-legacy', 'fixture-retailer',
                'Product page', 'arc-pro-b60', 'Fixture B60', 'Fixture retail', 'US', 'USD', 599.95,
                'asking_price', 'new', '2026-11-19', 'https://retail.example/card', 'Original figure.');
        """)
        intake("migrate")
        legacy_receipt = json.loads(intake("ingest", legacy_bundle).stdout)
        self.assertEqual((legacy_receipt["batch_id"], legacy_receipt["price_candidates"]), (legacy_id, 1))

        bundle = {**legacy_bundle, "prices": [
            {**legacy_price, "id": "retail", "seller_business_name": "Fixture Retail LLC",
             "listing_status": "in_stock", "shipping_amount": "0"},
            {**legacy_price, "id": "completed", "kind": "completed_listing_price", "listing_status": "ended",
             "condition": "open_box", "shipping_amount": "14.95", "tax_amount": "25.10"},
            {**legacy_price, "id": "best-offer", "kind": "best_offer_accepted", "listing_status": "sold"},
            {**legacy_price, "id": "best-offer-hidden", "kind": "best_offer_accepted", "listing_status": "sold",
             "amount": None},
            {**legacy_price, "id": "settlement", "kind": "verified_settlement", "listing_status": "sold",
             "amount": "429.90"},
        ]}
        receipt = json.loads(intake("ingest", bundle).stdout)
        self.assertEqual((receipt["batches"], receipt["price_candidates"]), (2, 6))
        intake("migrate")
        self.assertEqual(json.loads(intake("ingest", bundle).stdout), receipt)
        self.assertEqual(json.loads(intake("ingest", legacy_bundle).stdout)["batch_id"], legacy_id)
        self.assertEqual(self.store._query("""
            SELECT id, kind, amount, condition, seller_business_name, listing_status, shipping_amount, tax_amount
            FROM fastest_intake.price_candidate ORDER BY id
        """).splitlines(), [
            "best-offer|best_offer_accepted|599.95|new||sold||",
            "best-offer-hidden|best_offer_accepted||new||sold||",
            "completed|completed_listing_price|599.95|open_box||ended|14.95|25.10",
            "fixture-legacy|asking_price|599.95|new||||",
            "retail|asking_price|599.95|new|Fixture Retail LLC|in_stock|0|",
            "settlement|verified_settlement|429.90|new||sold||",
        ])

        for changes, constraint in [
            ({"kind": "verified_settlement", "listing_status": "in_stock"}, "price_candidate_kind_status_check"),
            ({"kind": "completed_listing_price"}, "price_candidate_kind_status_check"),
            ({"kind": "verified_settlement", "listing_status": "sold", "amount": None}, "price_candidate_amount_required"),
            ({"shipping_amount": "-1"}, "price_candidate_shipping_amount_check"),
        ]:
            with self.subTest(changes=changes):
                rejected = intake("ingest", {**legacy_bundle, "prices": [{**legacy_price, **changes}]}, check=False)
                self.assertEqual(rejected.returncode, 1)
                self.assertIn(constraint, rejected.stderr)
        stats = json.loads(intake("stats").stdout)
        self.assertEqual(stats, {key: value for key, value in receipt.items() if key != "batch_id"})

    def test_private_image_pilot_intake_pins_timing_rows_and_keeps_release_unchanged(self):
        production = FIXTURE.parents[1]
        plan_path = production / "fastest_image" / "plan.json"
        plan = json.loads(plan_path.read_bytes())
        packet = self.socket_path.parent / "private-image-packet"
        (packet / "run").mkdir(parents=True, mode=0o700)
        provenance = {
            "start_utc": "2026-11-21T00:00:00Z", "hardware": "Fixture Apple M4",
            "checkpoint": plan["artifact"], "workflow_sha256": plan["workflow"]["sha256"],
            "lock_sha256": plan["cells"][0]["lock"]["sha256"],
            "runtime": plan["runtime"], "protocol": plan["protocol"],
            "client_command": ["private environment sentinel"],
        }
        output = "f" * 64
        attempts = [
            {"phase": "warmup", "seed": 731000, "outcome": "success", "elapsed_ns": 9_000,
             "phase_end_ns": {"sampler": 10, "decode": 20, "save": 30, "complete": 40},
             "output_sha256": output},
            {"phase": "repeat", "seed": 731001, "outcome": "oom", "elapsed_ns": 2_000,
             "phase_end_ns": {"sampler": 10}, "reason": "ComfyUI reported OutOfMemoryError."},
        ]
        members = {"provenance.json": provenance, "run/attempts.json": attempts}

        def packet_manifest():
            checksums = {"run/sample-00.png": output}
            for name, document in members.items():
                content = json.dumps(document).encode()
                (packet / name).write_bytes(content)
                checksums[name] = sha256(content).hexdigest()
            manifest = "".join(f"{value}  {name}\n" for name, value in checksums.items()).encode()
            (packet / "SHA256SUMS").write_bytes(manifest)
            return sha256(manifest).hexdigest(), checksums

        def intake(command, *args, check=True):
            return subprocess.run(
                [sys.executable, "-B", "-m", "fastest_intake", "--database-url", self.database_url,
                 command, *args], cwd=production, text=True, capture_output=True, check=check, timeout=30,
            )

        manifest, checksums = packet_manifest()
        self.observation["kind"] = "measured"
        release_id = self.store.publish(self.observation)
        before = self.store.read(release_id)
        intake("migrate")
        imported = json.loads(intake("ingest-image-pilot", str(packet)).stdout)
        self.assertEqual(imported, {"manifest_sha256": manifest, "attempts": 2, "successful": 1, "failed": 1})
        self.assertEqual(json.loads(intake("ingest-image-pilot", str(packet)).stdout), imported)
        self.assertEqual(self.store.read(release_id), before)
        self.assertEqual(self.store._query("SELECT count(*) FROM fastest_release.observation_revision"), "1")
        [run] = json.loads(self.store._query("SELECT json_agg(run) FROM fastest_intake.image_pilot_run AS run"))
        for key, expected in {
            "manifest_sha256": manifest, "ledger_sha256": checksums["run/attempts.json"],
            "provenance_sha256": checksums["provenance.json"], "packet_locator": str(packet.resolve()),
            "plan_sha256": sha256(plan_path.read_bytes()).hexdigest(), "cell_id": "apple-m4",
            "protocol_id": plan["protocol"]["id"], "workflow_sha256": plan["workflow"]["sha256"],
            "artifact_sha256": plan["artifact"]["sha256"], "artifact_revision": plan["artifact"]["revision"],
            "runtime_revision": plan["runtime"]["revision"], "lock_sha256": plan["cells"][0]["lock"]["sha256"],
            "eligibility": "exploratory", "quality_status": "pending",
        }.items():
            self.assertEqual(run[key], expected, key)
        self.assertNotIn("private environment sentinel", json.dumps(run))
        rows = json.loads(self.store._query("""
            SELECT json_agg(attempt ORDER BY attempt_index) FROM fastest_intake.image_pilot_attempt AS attempt
        """))
        self.assertEqual([(row["phase"], row["seed"], row["elapsed_ns"], row["outcome"]) for row in rows], [
            ("warmup", 731000, 9_000, "success"), ("repeat", 731001, 2_000, "oom"),
        ])
        self.assertEqual(rows[0]["output_sha256"], output)
        self.assertEqual(rows[1]["phase_end_ns"], {"sampler": 10})
        self.assertEqual(rows[1]["failure_reason"], "ComfyUI reported OutOfMemoryError.")
        self.store._query("CREATE ROLE intake_public_reader LOGIN;")
        reader = ReleaseStore(self.database_url + " user=intake_public_reader")
        for table in ("image_pilot_run", "image_pilot_attempt"):
            with self.assertRaisesRegex(ReleaseError, "permission denied"):
                reader._query(f"SELECT * FROM fastest_intake.{table}")
        (packet / "run/attempts.json").write_text("[]")
        invalid = intake("ingest-image-pilot", str(packet), check=False)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("run/attempts.json does not match SHA256SUMS", invalid.stderr)
        provenance["workflow_sha256"] = "0" * 64
        packet_manifest()
        invalid = intake("ingest-image-pilot", str(packet), check=False)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("workflow", invalid.stderr)
        self.assertEqual(self.store._query("SELECT count(*) FROM fastest_intake.image_pilot_run"), "1")
        self.assertEqual(self.store._query("SELECT count(*) FROM fastest_intake.image_pilot_attempt"), "2")

    def serving_capture_packet(
        self, *, diagnostic=False, cancel_at=None, miss_slot=False, meter=False, fail_warmup=False,
    ):
        packet = self.socket_path.parent / f"private-serving-{uuid4().hex}"
        now = 10_000_000_000
        calls = 0
        window_start = None

        async def sleep_until(target_ns):
            nonlocal now, window_start
            if window_start is None:
                window_start = target_ns
            if cancel_at is not None and target_ns == window_start + cancel_at * 6_000_000_000:
                raise asyncio.CancelledError
            now = max(now, target_ns)
            if miss_slot and target_ns == window_start + 6_000_000_000:
                now += 101_000_000

        async def post(_host, _port, path, payload, started_ns, _timeout):
            nonlocal now, calls
            response = {"started_ns": started_ns, "http_status": 200, "response_headers": "private trace header"}
            elapsed_ns = 12_000_001
            if path != "/completion":
                body = {"id_slot": int(path.split("/")[2][0]), "n_erased": 1024}
            else:
                calls += 1
                user = {1251: 1, 1502: 2, 1753: 3, 1004: 4}[json.loads(payload)["prompt"][0]]
                body = {"stop": True, "tokens": [42] * 128, "content": "private response body"}
                if fail_warmup and calls == 1:
                    response["http_status"] = 503
                elif calls > 4:
                    if user == 2:
                        body["tokens"].pop()
                    elif user == 3:
                        response["http_status"] = 503
                    elif user == 4:
                        elapsed_ns = 5_000_000_001
                        response["timeout"] = True
            response["finished_ns"] = started_ns + elapsed_ns
            await asyncio.sleep(0)
            now = max(now, response["finished_ns"])
            return response, json.dumps(body).encode()

        clock = {"source": "linux-clock-monotonic", "boot_id": "cebb3678-779c-4b1d-a0df-d83885982ed0",
                 "time_namespace": 4026531834}
        with patch.multiple(capture, monotonic_ns=lambda: now, _post=post, _sleep_until=sleep_until,
                            _meter_clock=lambda: clock), patch.object(capture.platform, "node", return_value="private hostname"):
            try:
                asyncio.run(capture.capture(
                    packet, "127.0.0.1" if diagnostic else "192.0.2.25", 8080,
                    diagnostic_reason="private diagnostic reason" if diagnostic else None,
                    notes="private operator notes", meter_lead_ms=10 if meter else None,
                ))
            except asyncio.CancelledError:
                if cancel_at is None:
                    raise
            except ValueError as error:
                if not fail_warmup or "Warmup did not complete successfully" not in str(error):
                    raise
        return packet

    def serving_intake(self, command, *args):
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_intake", "--database-url", self.database_url,
             command, *args], cwd=FIXTURE.parents[1], capture_output=True, text=True, timeout=30,
        )

    def scaling_capture_packet(self, bench=BENCH):
        root = Path(self.socket_path.parent, f"fixture-{uuid4().hex}")
        root.mkdir()
        packet = root / "capture"
        runtime, inventory = root / "llama-bench", root / "nvidia-smi"
        for path, body in ((runtime, bench), (inventory, f'''
print({FIRST!r} + ", 00000000:01:00.0, Fixture A, 570.10")
print({SECOND!r} + ", 00000000:02:00.0, Fixture B, 570.10")
''')):
            path.write_text(f"#!{sys.executable}\n" + body)
            path.chmod(0o700)
        devices, build = root / "devices.json", root / "build.txt"
        devices.write_text(json.dumps([{"uuid": FIRST, "slot": "first"}, {"uuid": SECOND, "slot": "second"}]))
        build.write_text("Private synthetic build fixture.")
        shards = []
        for index, shard in enumerate(PLAN["artifact"]["shards"]):
            payload = f"Fixture shard {index}".encode()
            (root / shard["path"]).write_bytes(payload)
            shards.append({**shard, "bytes": len(payload), "sha256": sha256(payload).hexdigest()})
        with redirect_stderr(StringIO()), patch.dict(PLAN["artifact"], {"shards": shards}), patch.dict(os.environ, {
            "PATH": f"{root}{os.pathsep}{os.environ['PATH']}", "CUDA_VISIBLE_DEVICES": f"{FIRST},{SECOND}",
        }):
            capture_scaling.main([
                "capture", str(packet), "--bench", str(runtime), "--model-dir", str(root),
                "--devices", str(devices), "--host-revision", "fixture-r1", "--build-evidence", str(build),
            ])
        # The ingest process has the usual production pins. Only the synthetic collector needed stand-in shards.
        manifest_file = packet / "capture.json"
        manifest = json.loads(manifest_file.read_bytes())
        manifest["artifact"] = PLAN["artifact"]
        manifest_file.write_text(json.dumps(manifest))
        return packet

    def test_private_scaling_intake_preserves_ordered_integer_samples_with_idempotent_replay(self):
        self.serving_intake("migrate").check_returncode()
        bench = BENCH.replace("list(range(100, 120))", "[9007199254740993] + list(range(101, 120))")
        packet = self.scaling_capture_packet(bench)
        result = self.serving_intake("ingest-scaling-capture", packet)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["capture_sha256"], sha256((packet / "capture.json").read_bytes()).hexdigest())
        self.assertEqual(receipt["capture_status"], "complete")
        self.assertEqual(receipt["transport_status"], "unknown")
        self.assertEqual(receipt["review_status"], "held")
        self.assertEqual(json.loads(self.serving_intake("ingest-scaling-capture", packet).stdout), receipt)
        self.assertEqual(self.store._query("""
            SELECT role, outcome, array_to_string(samples_ns, ',')
            FROM fastest_intake.scaling_capture_attempt ORDER BY role;
        """).splitlines(), [
            "baseline|complete|9007199254740993,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119",
            "comparison|complete|9007199254740993,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119",
        ])
        stats = json.loads(self.serving_intake("stats").stdout)
        self.assertEqual((stats["scaling_capture_runs"], stats["scaling_capture_attempts"]), (1, 2))

        log = packet / "baseline/stderr.log"
        log.write_bytes(log.read_bytes() + b"\nResealed after edit.\n")
        attempt = packet / "baseline/attempt.json"
        revised = json.loads(attempt.read_bytes())
        revised["files"]["stderr.log"] = sha256(log.read_bytes()).hexdigest()
        attempt.write_text(json.dumps(revised))
        conflict = self.serving_intake("ingest-scaling-capture", packet)
        self.assertEqual(conflict.returncode, 1, conflict.stderr)
        self.assertIn("conflicting evidence", conflict.stderr)

    def test_private_scaling_intake_adds_transport_only_after_verifying_the_attachment(self):
        self.serving_intake("migrate").check_returncode()
        packet = self.scaling_capture_packet()
        first = json.loads(self.serving_intake("ingest-scaling-capture", packet).stdout)
        self.assertEqual(first["transport_status"], "unknown")
        run = json.loads((packet / "comparison/attempt.json").read_bytes())
        trace, links = packet.parent / "trace.bin", packet.parent / "links.json"
        trace.write_bytes(b"Private synthetic trace content\x00")
        link = {"from": "0000:01:00.0", "to": "0000:02:00.0", "path": "host-staged",
                "interconnect": "PCIe", "direction": "one-way", "payload_bytes": 8192,
                "scope": "Synthetic timed decode", "method": "Fixture trace",
                "rated": None, "negotiated": None, "bandwidth_gb_s": None}
        links.write_text(json.dumps({"run_id": run["run_id"], "links": [link]}))
        self.assertEqual(capture_scaling.main(["attach-transport", str(packet), "--trace", str(trace),
                                               "--links", str(links)]), 0)
        trace_copy = packet / "transport/trace"
        trace_copy.write_bytes(b"Tampered trace")
        result = self.serving_intake("ingest-scaling-capture", packet)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("SHA-256 mismatch", result.stderr)
        self.assertEqual(self.store._query("SELECT count(*) FROM fastest_intake.scaling_capture_transport"), "0")
        trace_copy.write_bytes(trace.read_bytes())
        checked = self.serving_intake("ingest-scaling-capture", packet)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        receipt = json.loads(checked.stdout)
        self.assertEqual(receipt["transport_status"], "supplied")
        self.assertEqual(receipt["capture_sha256"], first["capture_sha256"])
        self.assertEqual(receipt["transport_receipt_sha256"],
                         sha256((packet / "transport/receipt.json").read_bytes()).hexdigest())
        self.assertEqual(json.loads(self.serving_intake("ingest-scaling-capture", packet).stdout), receipt)
        self.assertEqual(self.store._query("""
            SELECT comparison_run_id, trace_sha256, links->0->>'path' FROM fastest_intake.scaling_capture_transport
        """), f"{run['run_id']}|{sha256(trace.read_bytes()).hexdigest()}|host-staged")

        trace_copy.write_bytes(b"Another trace with a fresh seal")
        receipt_file = packet / "transport/receipt.json"
        alternate = json.loads(receipt_file.read_bytes())
        alternate["files"]["trace"] = sha256(trace_copy.read_bytes()).hexdigest()
        receipt_file.write_text(json.dumps(alternate))
        conflict = self.serving_intake("ingest-scaling-capture", packet)
        self.assertEqual(conflict.returncode, 1, conflict.stderr)
        self.assertIn("conflicting evidence", conflict.stderr)
        self.assertEqual(self.store._query("SELECT count(*) FROM fastest_release.observation_revision"), "0")
        self.store._query("CREATE ROLE scaling_public_reader LOGIN;")
        reader = ReleaseStore(self.database_url + " user=scaling_public_reader")
        for table in ("scaling_capture_run", "scaling_capture_attempt", "scaling_capture_transport"):
            with self.assertRaisesRegex(ReleaseError, "permission denied"):
                reader._query(f"SELECT * FROM fastest_intake.{table}")

    def test_private_scaling_intake_refuses_missing_tampered_or_unmatched_evidence(self):
        self.serving_intake("migrate").check_returncode()
        packet = self.scaling_capture_packet()
        stdout = packet / "comparison/stdout.jsonl"
        raw = stdout.read_bytes()
        attempt = packet / "comparison/attempt.json"
        record = json.loads(attempt.read_bytes())
        attempt_raw = attempt.read_bytes()
        for path, original, changed, error in (
            (stdout, raw, None, "Missing or invalid evidence file"),
            (stdout, raw, b'{"samples_ns":[100]}', "SHA-256 mismatch"),
            (attempt, attempt_raw, json.dumps({**record, "samples_ns": [1] * 20}).encode(), "timings disagree"),
            (attempt, attempt_raw, json.dumps({**record, "timeout_seconds": 10}).encode(), "same runtime controls"),
        ):
            with self.subTest(error=error):
                if changed is None:
                    path.unlink()
                else:
                    path.write_bytes(changed)
                result = self.serving_intake("ingest-scaling-capture", packet)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(error, result.stderr)
                path.write_bytes(original)

        manifest = packet / "capture.json"
        claims = json.loads(manifest.read_bytes())
        claims["status"] = "incomplete"
        manifest.write_text(json.dumps(claims))
        result = self.serving_intake("ingest-scaling-capture", packet)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("status disagrees", result.stderr)
        self.assertEqual(self.store._query("SELECT count(*) FROM fastest_intake.scaling_capture_run"), "0")

    def test_private_scaling_intake_preserves_failed_attempts_and_unavailable_comparisons(self):
        self.serving_intake("migrate").check_returncode()
        packet = self.scaling_capture_packet(BENCH.replace("for index in range(len(visible)):", """
if len(visible) == 1:
    print("CUDA_ERROR_OUT_OF_MEMORY", file=sys.stderr)
    sys.exit(1)
print("llama_decode: failed to decode", file=sys.stderr)
for index in range(len(visible)):
"""))
        result = self.serving_intake("ingest-scaling-capture", packet)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["capture_status"], "incomplete")
        self.assertEqual(self.store._query("""
            SELECT outcome, cardinality(samples_ns) FROM fastest_intake.scaling_capture_attempt ORDER BY role;
        """).splitlines(), ["oom|0", "failed|20"])

        packet = self.scaling_capture_packet()
        manifest = packet / "capture.json"
        capture = json.loads(manifest.read_bytes())
        capture["status"] = "interrupted"
        capture["reason"] = "Fixture interruption"
        del capture["attempts"]["comparison"]
        manifest.write_text(json.dumps(capture))
        # Interruption after the disk receipt is finalized and before it is registered in capture.json.
        result = self.serving_intake("ingest-scaling-capture", packet)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["capture_status"], "interrupted")
        self.assertEqual(receipt["transport_status"], "unknown")
        self.assertEqual(self.store._query(f"""
            SELECT outcome, cardinality(samples_ns)
            FROM fastest_intake.scaling_capture_attempt WHERE capture_sha256 = '{receipt["capture_sha256"]}'
            ORDER BY role;
        """).splitlines(), ["complete|20", "unavailable|20"])

    def test_private_scaling_intake_retains_interruption_during_log_creation(self):
        self.serving_intake("migrate").check_returncode()
        packet = self.scaling_capture_packet()
        manifest = packet / "capture.json"
        capture = json.loads(manifest.read_bytes())
        capture.update(status="interrupted", reason="Fixture interruption opening the runner logs")
        del capture["attempts"]["comparison"]
        manifest.write_text(json.dumps(capture))
        comparison = packet / "comparison"
        receipt_file = comparison / "attempt.json"
        receipt = json.loads(receipt_file.read_bytes())
        receipt.update(outcome="interrupted", exit_code=None, reason="Operator interrupted the subprocess.")
        del receipt["placement_mib"], receipt["samples_ns"], receipt["files"]["stderr.log"]
        stdout = comparison / "stdout.jsonl"
        stdout.write_bytes(b"")
        receipt["files"]["stdout.jsonl"] = sha256(b"").hexdigest()
        (comparison / "stderr.log").unlink()
        receipt_file.write_text(json.dumps(receipt))

        result = self.serving_intake("ingest-scaling-capture", packet)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.store._query("""
            SELECT outcome || '|' || cardinality(samples_ns)
            FROM fastest_intake.scaling_capture_attempt WHERE role = 'comparison';
        """), "interrupted|0")

    def test_private_serving_capture_intake_preserves_actual_timing_and_raw_digests(self):
        self.serving_intake("migrate").check_returncode()
        packet = self.serving_capture_packet(diagnostic=True)
        for body in packet.glob("*.bin"):
            body.unlink()
        result = self.serving_intake("ingest-serving-capture", packet)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        capture_hash = sha256((packet / "capture.json").read_bytes()).hexdigest()
        trace_hash = sha256((packet / "trace.jsonl").read_bytes()).hexdigest()
        self.assertEqual(receipt, {
            "capture_sha256": capture_hash, "trace_sha256": trace_hash,
            "kind": "diagnostic", "capture_status": "complete",
            "review_status": "held", "separate_host_status": "unverified", "power_status": "missing",
            "planned": 96, "attempted": 96, "unrecorded": 0, "accepted": 24, "accepted_output_tokens": 3072,
        })
        self.assertEqual(json.loads(self.serving_intake("ingest-serving-capture", packet).stdout), receipt)
        self.assertEqual(self.store._query("""
            SELECT user_slot, outcome, elapsed_ms, observed_elapsed_ns, output_tokens
            FROM fastest_intake.serving_capture_attempt WHERE request_number = 1 ORDER BY user_slot
        """).splitlines(), [
            "1|accepted|13|12000001|128", "2|rejected|13|12000001|127",
            "3|failed|13|12000001|0", "4|timeout|5000|5000000001|0",
        ])
        stats = json.loads(self.serving_intake("stats").stdout)
        self.assertEqual((stats["serving_capture_runs"], stats["serving_capture_attempts"]), (1, 96))
        rows = self.store._query("""
            SELECT row_to_json(run) FROM fastest_intake.serving_capture_run AS run;
            SELECT row_to_json(attempt) FROM fastest_intake.serving_capture_attempt AS attempt;
        """)
        for private in (str(packet), "127.0.0.1", "private hostname", "private trace header",
                        "private diagnostic reason", "private operator notes", "private response body"):
            self.assertNotIn(private, rows)
        self.assertEqual(self.store._query("SELECT count(*) FROM fastest_release.observation_revision"), "0")
        self.store._query("CREATE ROLE serving_public_reader LOGIN;")
        reader = ReleaseStore(self.database_url + " user=serving_public_reader")
        for table in ("serving_capture_run", "serving_capture_attempt"):
            with self.assertRaisesRegex(ReleaseError, "permission denied"):
                reader._query(f"SELECT * FROM fastest_intake.{table}")

    def test_private_serving_capture_intake_rejects_trace_drift_and_false_claims(self):
        self.serving_intake("migrate").check_returncode()
        packet = self.serving_capture_packet(diagnostic=True)
        self.serving_intake("ingest-serving-capture", packet).check_returncode()
        ledger = packet / "capture.json"
        trace = packet / "trace.jsonl"
        original_ledger, original_trace = ledger.read_bytes(), trace.read_bytes()

        events = [json.loads(line) for line in original_trace.splitlines()]
        first_timed = next(index for index, event in enumerate(events) if event["phase"] == "timed")
        reordered = events[:first_timed] + events[first_timed + 4:first_timed + 8] + events[first_timed:first_timed + 4]
        reordered += events[first_timed + 8:]

        def encoded(items):
            return ("\n".join(json.dumps(item) for item in items) + "\n").encode()

        for changed, error in (
            (encoded(reordered), "out of schedule order"),
            (encoded(events[:-1]), "missing a timed request"),
            (original_trace.replace(b'"elapsed_ms":13', b'"elapsed_ms":12', 1), "disagrees with monotonic"),
            (original_trace.replace(b'"private trace header"', b'"alternate private header"', 1), "different trace.jsonl SHA-256"),
        ):
            with self.subTest(error=error):
                trace.write_bytes(changed)
                result = self.serving_intake("ingest-serving-capture", packet)
                self.assertEqual(result.returncode, 1)
                self.assertIn(error, result.stderr)
        trace.write_bytes(original_trace)
        data = json.loads(original_ledger)
        for change, error in (
            ({"kind": "private-capture"}, "agree with its diagnostic reason"),
            ({"kind": "private-capture", "diagnostic_reason": None}, "Loopback captures require"),
            ({"status": "capturing"}, "must be finalized"),
            ({"power": {"status": "measured"}}, "must report missing power"),
        ):
            with self.subTest(change=change):
                ledger.write_text(json.dumps({**data, **change}))
                result = self.serving_intake("ingest-serving-capture", packet)
                self.assertEqual(result.returncode, 1)
                self.assertIn(error, result.stderr)
        stats = json.loads(self.serving_intake("stats").stdout)
        self.assertEqual((stats["serving_capture_runs"], stats["serving_capture_attempts"]), (1, 96))

    def test_private_serving_capture_intake_holds_incomplete_captures_and_announced_meter_window(self):
        self.serving_intake("migrate").check_returncode()
        for options, status, attempted, unrecorded, accepted in (
            ({"fail_warmup": True}, "failed", 0, 96, 0),
            ({"cancel_at": 1}, "interrupted", 4, 92, 1),
            ({"miss_slot": True}, "partial", 92, 4, 23),
            ({"meter": True}, "complete", 96, 0, 24),
        ):
            with self.subTest(status=status):
                packet = self.serving_capture_packet(**options)
                ledger = json.loads((packet / "capture.json").read_bytes())
                self.assertEqual(ledger["status"], status)
                self.assertEqual("meter_window" in ledger, options.get("meter", False))
                result = self.serving_intake("ingest-serving-capture", packet)
                self.assertEqual(result.returncode, 0, result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(
                    [receipt[key] for key in ("kind", "capture_status", "review_status", "separate_host_status",
                                              "power_status", "attempted", "unrecorded", "accepted")],
                    ["private-capture", status, "held", "unverified", "missing", attempted, unrecorded, accepted],
                )
                self.assertEqual(self.store._query(f"""
                    SELECT count(*) FROM fastest_intake.serving_capture_attempt
                    WHERE capture_sha256 = '{receipt["capture_sha256"]}'
                      AND outcome = 'unrecorded' AND elapsed_ms IS NULL AND output_tokens IS NULL
                """), "4" if status == "partial" else "0")

    def test_agent_task_report_uses_reviewed_postgres_artifacts_and_live_withdrawal(self):
        from fastest_agent_task.harness import plan

        context = plan()["contexts"][0]
        record = {
            "kind": "measured", "context_id": context["id"], "context_sha256": context["sha256"],
            "environment": {
                "hardware": "Apple M4, 24 GiB", "os": "macOS 15.7", "backend": "Metal",
                "runtime_binary_sha256": "1" * 64, "adapter_sha256": "2" * 64,
            },
            "review": {
                "decision_id": str(uuid4()), "evidence_id": str(uuid4()), "retained_sha256": "3" * 64,
                "ownership": "operator-owned", "destination": "public-release", "decision": "allow",
            },
            "attempts": [
                {
                    "trial": 1, "attempt": 1, "wall_ns": 30_000_000_000, "generated_tokens": None,
                    "reasoning_tokens": 0, "termination": "timeout", "answer": None, "tool_reads": [],
                },
                {
                    "trial": 1, "attempt": 2, "wall_ns": 25_000, "generated_tokens": 16,
                    "reasoning_tokens": 0, "termination": "answered", "answer": {"open_units": 17},
                    "tool_reads": [{"tool": "read_bundle", "resource": "inventory"}],
                },
            ],
        }
        submitted = self.socket_path.parent / "reviewed.json"

        def publish(*arguments, check=True):
            submitted.write_text(json.dumps(record), encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-B", "-m", "fastest_release", "--database-url", self.database_url,
                 "publish-agent-task", "--record", str(submitted), *arguments],
                cwd=FIXTURE.parents[1], capture_output=True, text=True, check=check, timeout=15,
            )

        published = publish()
        pin = published.stdout.strip()
        self.assertRegex(pin, r"^[a-f0-9]{64}$")
        self.assertEqual(publish().stdout.strip(), pin)
        exported = self.socket_path.parent / "offline-report"
        subprocess.run([sys.executable, "-B", "-m", "fastest_agent_task", "build", str(exported),
                        "--record", str(submitted)], cwd=FIXTURE.parents[1], check=True,
                       capture_output=True, timeout=15)
        self.store._query("""
            CREATE ROLE task_reader LOGIN;
            GRANT USAGE ON SCHEMA fastest_release TO task_reader;
            GRANT EXECUTE ON FUNCTION fastest_release.read_agent_task_artifact(text, text),
                fastest_release.read_release(uuid) TO task_reader;
        """)
        reader = ReleaseStore(self.database_url + " user=task_reader")
        api_path = "/api/v1/comparison/agent-task"
        api_query = f"{api_path}?release={pin}"
        with api_client(reader) as request:
            self.assertNotIn(api_path, request("/api/v1/openapi.json")[2]["paths"])
            self.assertEqual(request(api_query)[0], 404)
            preview = request("/agent-task")[1]["Location"].split("/")[2]
        with api_client(reader, agent_task_release=pin) as request:
            self.assertEqual(request("/releases/current/benchmark.html", decode=False)[0], 404)
            status, headers, _ = request("/agent-task")
            self.assertEqual(status, 307)
            base = f"/agent-task/{pin}/"
            self.assertEqual(headers["Location"], base + "agent-task.html")
            _, _, manifest = request(base + "manifest.json", decode=False)
            self.assertEqual(sha256(manifest.encode()).hexdigest(), pin)
            self.assertEqual(manifest.encode(), (exported / "manifest.json").read_bytes())
            for name, digest in json.loads(manifest)["sha256"].items():
                status, headers, body = request(base + name, decode=False)
                self.assertEqual(status, 200)
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertEqual(sha256(body.encode()).hexdigest(), digest)
                self.assertEqual(body.encode(), (exported / name).read_bytes())
                if name.endswith((".html", ".md")):
                    self.assertIn("timeout", body)
                    self.assertIn("25000", body)
                    self.assertIn("open_units", body)
            _, _, measured = request(base + "agent-task.json")
            bundle, split = measured["contexts"]
            self.assertEqual([row["outcome"] for row in bundle["attempts"]], ["timeout", "accepted"])
            self.assertEqual(bundle["attempts"][1]["accepted_output"], {"open_units": 17})
            self.assertEqual([bundle["counts"]["failed_attempts"], split["counts"]["attempts"]], [1, 0])

            catalog = request("/.well-known/api-catalog")[2]
            description = request(catalog["linkset"][0]["service-desc"][0]["href"])[2]
            operation = description["paths"][api_path]["get"]
            self.assertEqual([(p["name"], p["required"]) for p in operation["parameters"]], [("release", True)])
            status, headers, result = request(api_query)
            self.assertEqual(status, 200)
            self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual(result, {
                "api_version": "1.0.0", "pin": pin, "report": measured,
                "url": base + "agent-task.html",
                "citations": [{"url": base + "agent-task.json"}, {"url": base + "manifest.json", "sha256": pin}],
                "rights": {"export_scope": "public-release"}, "units": {"wall_time": "ns"},
            })
            self.assertEqual([(a["outcome"], a["wall_ns"]) for a in result["report"]["contexts"][0]["attempts"]],
                             [("timeout", 30_000_000_000), ("accepted", 25_000)])
            self.assertEqual(result["report"]["contexts"][0]["trials"][0]["recorded_attempt_wall_ns"], 30_000_025_000)
            self.assertNotIn("answer", result["report"]["contexts"][0]["attempts"][0])
            self.assertEqual(request(api_query, "POST", decode=False)[0], 501)
            for bad_query in ("", "?release=current", "?release=invalid", "?release=" + pin.upper(),
                              f"?release={pin}&release={pin}", f"?release={pin}&artifact=private"):
                self.assertEqual(request(api_path + bad_query)[0], 400)
            self.assertEqual(request(f"{api_path}?release={'0' * 64}")[0], 404)
            self.assertEqual(request(f"{api_path}?release={preview}")[0], 404)

            record["review"]["evidence_id"] = str(uuid4())
            expired = publish("--expires-at", "2000-01-01T00:00:00Z").stdout.strip()
            self.assertEqual(request(f"/agent-task/{expired}/agent-task.json", decode=False)[0], 410)
            self.assertEqual(request(f"{api_path}?release={expired}")[0], 410)
            self.assertEqual(request(f"/agent-task/{'0' * 64}/task.json", decode=False)[0], 404)
            status, headers, _ = request("/agent-task")
            self.assertEqual(status, 307)
            self.assertEqual(headers["Location"], base + "agent-task.html")
            self.store.withdraw(bundle["review"]["evidence_id"], "Private review withdrawal")
            for name in (*json.loads(manifest)["sha256"], "manifest.json"):
                status, _, body = request(base + name, decode=False)
                self.assertEqual(status, 410)
                self.assertNotIn(bundle["review"]["evidence_id"], body)
            status, _, result = request(api_query)
            self.assertEqual(status, 410)
            self.assertEqual(result, {"api_version": "1.0.0", "error": "Public rights have ended", "status": "withdrawn"})
            record["review"]["evidence_id"] = bundle["review"]["evidence_id"]
            self.assertNotEqual(publish(check=False).returncode, 0)

    @unittest.skipUnless(HAS_SDK, "Install fastest_mcp/requirements.txt to test MCP")
    def test_mcp_replays_hosted_agent_task_evidence_and_rechecks_withdrawal(self):
        from mcp import McpError

        from fastest_agent_task.hosted import evidence_id, hosted_plan
        from test_agent_task_hosted import hosted_record

        protocol = hosted_plan()
        record = hosted_record(protocol, [
            {"trial": 1, "attempt": 1, "wall_ns": 30_000_000_123, "generated_tokens": None,
             "reasoning_tokens": 0, "termination": "timeout", "outcome": "timeout", "answer": None, "tool_reads": []},
            {"trial": 1, "attempt": 2, "wall_ns": 3_427_008_101, "generated_tokens": 16,
             "reasoning_tokens": 0, "termination": "answered", "outcome": "accepted",
             "answer": {"open_units": 17}, "tool_reads": protocol["contexts"][0]["allowed_reads"]},
        ])
        source = record["environment"]["source"]
        evidence = evidence_id(source["run_url"], "bundle")
        record["review"] = {
            "decision_id": str(uuid4()), "evidence_id": evidence, "retained_sha256": "3" * 64,
            "ownership": "operator-owned", "destination": "public-release", "decision": "allow",
        }
        pin = self.store.publish_agent_task([record])
        self.store._query("""
            CREATE ROLE task_reader LOGIN;
            GRANT USAGE ON SCHEMA fastest_release TO task_reader;
            GRANT EXECUTE ON FUNCTION fastest_release.read_agent_task_artifact(text, text) TO task_reader;
        """)
        reader = ReleaseStore(self.database_url + " user=task_reader")
        api_path = "/api/v1/comparison/agent-task"
        args = {"release": pin}
        uri = f"fastest://v1/agent-task/{pin}"

        async def check(port):
            async with (
                mcp_client(port) as client,
                mcp_http_server(port) as url,
                mcp_http_client(url) as (http, handshake),
            ):
                self.assertEqual(handshake, await client.initialize())
                self.assertEqual(handshake.protocolVersion, "2025-11-25")
                self.assertEqual(await http.list_tools(), await client.list_tools())
                self.assertEqual(await http.list_resource_templates(), await client.list_resource_templates())
                tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                self.assertTrue(tools["v1_agent_task"].annotations.readOnlyHint)
                templates = (await client.list_resource_templates()).resourceTemplates
                self.assertIn("fastest://v1/agent-task/{pin}", [resource.uriTemplate for resource in templates])

                result = await client.call_tool("v1_agent_task", args)
                self.assertEqual(result, await http.call_tool("v1_agent_task", args))
                self.assertFalse(result.isError)
                status, api = get_public(port, api_path, args)
                self.assertEqual(status, 200)
                payload = result.structuredContent
                self.assertEqual(payload, json.loads(api))
                resource = await client.read_resource(uri)
                self.assertEqual(resource, await http.read_resource(uri))
                self.assertEqual(payload, json.loads(resource.contents[0].text))

                status, site = get_public(port, payload["citations"][0]["url"])
                self.assertEqual(status, 200)
                self.assertEqual(payload["report"], json.loads(site))
                self.assertEqual(payload["report"]["environment"]["source"], source)
                bundle, split = payload["report"]["contexts"]
                self.assertEqual(split["status"], "missing")
                self.assertEqual(bundle["review"]["evidence_id"], evidence)
                self.assertEqual([(a["outcome"], a["wall_ns"]) for a in bundle["attempts"]],
                                 [("timeout", 30_000_000_123), ("accepted", 3_427_008_101)])
                self.assertEqual(bundle["trials"][0]["recorded_attempt_wall_ns"], 33_427_008_224)
                for route in (payload["url"], payload["url"].removesuffix(".html") + ".md"):
                    status, text = get_public(port, route)
                    self.assertEqual(status, 200)
                    self.assertIn(evidence, text)
                    self.assertIn("30000000123", text)
                    self.assertIn("timeout", text)

                for arguments in ({}, {"release": "current"}, {"release": "0" * 64}, {**args, "fields": ["raw_turns"]},
                                  {**args, "sql": "SELECT *"}, {**args, "artifact": "private.json"}):
                    with self.subTest(arguments=arguments):
                        invalid = await client.call_tool("v1_agent_task", arguments)
                        self.assertEqual(invalid, await http.call_tool("v1_agent_task", arguments))
                        self.assertTrue(invalid.isError)
                        self.assertIsNone(invalid.structuredContent)
                for invalid_uri in (uri + "?artifact=private.json", uri + "/raw-turns", uri + "#data",
                                    "fastest://v1/agent-task/current", "fastest://v1/agent-task/" + "0" * 64):
                    with self.subTest(uri=invalid_uri), self.assertRaises(McpError):
                        await client.read_resource(invalid_uri)
                    with self.subTest(uri=invalid_uri), self.assertRaises(McpError):
                        await http.read_resource(invalid_uri)

                self.store.withdraw(evidence, "private withdrawal reason")
                withdrawn = await client.call_tool("v1_agent_task", args)
                self.assertEqual(withdrawn, await http.call_tool("v1_agent_task", args))
                self.assertTrue(withdrawn.isError)
                self.assertIsNone(withdrawn.structuredContent)
                self.assertEqual(withdrawn.content[0].text, "Public rights have ended for this release.")
                with self.assertRaisesRegex(McpError, "Public rights have ended"):
                    await client.read_resource(uri)
                with self.assertRaisesRegex(McpError, "Public rights have ended"):
                    await http.read_resource(uri)

        with api_server(reader, agent_task_release=pin) as server:
            asyncio.run(check(server.server_port))

    def test_deployed_origin_serves_only_pinned_reviewed_tariff_references(self):
        def invoke(module, *args, check=True):
            result = subprocess.run(
                [sys.executable, "-B", "-m", module, "--database-url", self.database_url, *args],
                cwd=FIXTURE.parents[1], capture_output=True, text=True, timeout=30,
            )
            if check:
                self.assertEqual(result.returncode, 0, result.stderr)
            return result

        checked = "2025-11-01T12:30:00+08:00"
        source = "private-intake-source"
        expected_citation = "https://utility.example/schedule#off-peak"
        row = {
            "id": "fixture-power", "source": source, "locator": "private-candidate-locator",
            "kind": "electricity", "provider": "Fixture Energy", "offering": "Residential Schedule A",
            "revision": "fixture-schedule@1", "market": "CA", "region": "Ontario", "currency": "CAD",
            "amount": "0.123450", "unit": "kwh", "component": "Off peak",
            "effective_from": "2020-01-01", "effective_until": None,
            "qualification": "Eligible homes outside weekday peak hours.",
        }
        bundle = {
            "checked_at": checked, "note": "private-batch-note", "prices": [], "evaluations": [],
            "sources": [{"source": source, "url": expected_citation, "status": "captured", "note": "private-probe-note"}],
            "tariffs": [
                row,
                {**row, "id": "fixture-held", "amount": "8.00", "component": "Unreviewed rate"},
                {**row, "id": "fixture-past", "effective_until": "2022-01-01"},
                {**row, "id": "fixture-future", "effective_from": "2099-10-01"},
            ],
        }
        path = self.socket_path.parent / "tariffs.json"
        path.write_text(json.dumps(bundle), encoding="utf-8")
        invoke("fastest_intake", "migrate")
        batch = json.loads(invoke("fastest_intake", "ingest", path).stdout)["batch_id"]

        selection = {"batch_id": batch, "source": source, "id": row["id"], "source_label": "Utility rate schedule"}
        selected = [selection, {**selection, "id": "fixture-past"}, {**selection, "id": "fixture-future"}]
        approval = {"schema_version": 1, "decision_id": str(uuid4()), "expires_at": "2099-11-30T00:00:00Z"}
        review_path = self.socket_path.parent / "review.json"

        def approve(candidates, *, check=True, **changes):
            review_path.write_text(json.dumps({**approval, **changes, "candidates": candidates}), encoding="utf-8")
            return invoke("fastest_cost", "approve", review_path, check=check)

        rejected = approve([{**selection, "source": "wrong-source"}], check=False)
        self.assertEqual(rejected.returncode, 1, rejected.stderr)
        self.assertIn("captured tariff candidate", rejected.stderr)
        expired = approve(selected, expires_at="2020-01-01T00:00:00Z", check=False)
        self.assertEqual(expired.returncode, 1, expired.stderr)
        self.assertIn("future UTC expiry", expired.stderr)
        pin = approve(selected).stdout.strip()
        self.assertRegex(pin, r"^[a-f0-9]{64}$")
        self.assertEqual(approve(list(reversed(selected))).stdout.strip(), pin)
        conflict = approve([{**selection, "source_label": "A different public label"}], check=False)
        self.assertEqual(conflict.returncode, 1, conflict.stderr)
        self.assertIn("decision ID already identifies a different tariff approval", conflict.stderr)
        path.write_text(json.dumps({**bundle, "tariffs": [{**row, "amount": "0.29"}]}), encoding="utf-8")
        later_batch = json.loads(invoke("fastest_intake", "ingest", path).stdout)["batch_id"]
        next_pin = approve([{**selection, "batch_id": later_batch}],
                           decision_id=str(uuid4())).stdout.strip()
        self.assertNotEqual(next_pin, pin)

        PriceStore(self.database_url).migrate()
        self.store._query("""
            CREATE ROLE origin_reader LOGIN;
            CREATE ROLE ungranted_reader LOGIN;
            GRANT USAGE ON SCHEMA fastest_release, fastest_prices, fastest_cost_public TO origin_reader;
            GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid), fastest_release.read_evidence(uuid),
                fastest_prices.read_release(uuid), fastest_cost_public.read_tariff_references(text) TO origin_reader;
            GRANT USAGE ON SCHEMA fastest_cost_public TO ungranted_reader;
        """)
        for role, query in (
            ("origin_reader", "SELECT * FROM fastest_intake.tariff_candidate"),
            ("origin_reader", "SELECT * FROM fastest_intake.tariff_reference_review"),
            ("ungranted_reader", "SELECT fastest_cost_public.read_tariff_references(NULL)"),
        ):
            with self.subTest(role=role, query=query), self.assertRaisesRegex(ReleaseError, "permission denied"):
                ReleaseStore(f"{self.database_url} user={role}")._query(query)

        def get(origin, host, route, status=200):
            def open_route():
                return urlopen(Request(origin + route, headers={"Host": host} if host else {}), timeout=5)

            if status == 200:
                response = open_route()
            else:
                with self.assertRaises(HTTPError) as error:
                    open_route()
                response = error.exception
            with response:
                self.assertEqual(response.code, status)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                return response.read().decode()

        with self.deployed_origin() as (origin, host):
            base = json.loads(get(origin, host, "/costs.json"))
            self.assertNotIn("tariff_references", base)
        with self.deployed_origin("--cost-tariff-references-pin", pin) as (origin, host):
            result = json.loads(get(origin, host, "/costs.json"))
            block = result["tariff_references"]
            self.assertEqual(block["revision"], pin)
            self.assertEqual(block["authorization"], {"status": "approved", "decision_id": approval["decision_id"],
                                                       "expires_at": approval["expires_at"]})
            expected = {key: value for key, value in row.items() if key != "locator"}
            expected.update(source="Utility rate schedule", checked_at="2025-11-01T04:30:00Z",
                            citation={"locator": expected_citation, "revision": row["revision"]})
            self.assertEqual(block["references"], [expected])
            calculator = json.loads(get(origin, host, "/api/v1/calculator"))
            self.assertEqual(calculator["tariff_references"], block)
            routes = ("/costs", "/costs.md", "/costs.json", "/api/v1/calculator")
            for route in routes:
                content = get(origin, host, route + "?revision=" + result["revision"])
                self.assertIn("0.123450", content)
                self.assertIn(expected_citation, content)
                for private in (batch, source, "private-probe-note", "private-batch-note", row["locator"], "fixture-held"):
                    self.assertNotIn(private, content)
            self.assertEqual({key: value for key, value in result.items() if key not in {"revision", "tariff_references"}},
                             {key: value for key, value in base.items() if key != "revision"})
            advisor_route = "/api/v1/advisor?decision=cost&monthly_accepted=1800&months=24&privacy=allow-external"
            advisor = json.loads(get(origin, host, advisor_route))
            self.assertEqual(advisor["costs"]["revision"], result["revision"])
            self.assertEqual(advisor["status"], "abstain")

            invoke("fastest_cost", "withdraw", pin)
            invoke("fastest_cost", "withdraw", pin)
            invoke("fastest_intake", "migrate")
            self.assertEqual(approve(selected).stdout.strip(), pin)
            stats = json.loads(invoke("fastest_intake", "stats").stdout)
            self.assertEqual((stats["tariff_reference_reviews"], stats["tariff_reference_withdrawals"]), (2, 1))
            self.assertEqual(json.loads(get(origin, host, "/costs.json")), base)
            self.assertEqual(json.loads(get(origin, host, advisor_route))["costs"]["revision"], base["revision"])
            for route in routes + (advisor_route,):
                separator = "&" if "?" in route else "?"
                response = get(origin, host, route + separator + "revision=" + result["revision"], status=404)
                self.assertNotIn(expected_citation, response)

        with self.deployed_origin("--cost-tariff-references-pin", next_pin) as (origin, host):
            alternate = json.loads(get(origin, host, "/costs.json"))["tariff_references"]
            self.assertEqual(alternate["revision"], next_pin)
            self.assertEqual(alternate["references"][0]["amount"], "0.29")

    def test_deployed_origin_replays_published_values_after_restart(self):
        self.observation["kind"] = "measured"
        release = self.store.publish(self.observation)
        prices = PriceStore(self.database_url)
        prices.migrate()
        fixture = json.loads(FIXTURE.with_name("synthetic-price-cohort.json").read_text(encoding="utf-8"))
        fixture["cohort"]["data_class"] = "authorized_observations"
        cohort = prices.ingest(fixture)
        offerings = prices.publish(cohort, "2026-11-01", "2026-11-04")
        self.store._query("""
            CREATE ROLE origin_reader LOGIN;
            GRANT USAGE ON SCHEMA fastest_release, fastest_prices TO origin_reader;
            GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid),
                fastest_release.read_evidence(uuid), fastest_prices.read_release(uuid) TO origin_reader;
        """)
        image_plan = json.loads((FIXTURE.parents[1] / "fastest_image" / "plan.json").read_text(encoding="utf-8"))
        text_plan = json.loads((FIXTURE.parents[1] / "fastest_text" / "plan.json").read_text(encoding="utf-8"))

        def replay(origin, host):
            headers = {"Host": host} if host else {}

            def get(path, *, decode=True):
                with urlopen(Request(origin + path, headers=headers), timeout=5) as response:
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
                    return json.load(response) if decode else response.read().decode()

            catalog = get("/.well-known/api-catalog")
            spec = get(catalog["linkset"][0]["service-desc"][0]["href"])
            self.assertEqual(spec["info"]["version"], "1.0.0")
            self.assertIn("/api/v1/evidence", spec["paths"])
            self.assertIn("/api/v1/historical-offers", spec["paths"])
            evidence = get(f"/api/v1/evidence?evidence_id={self.observation['evidence_id']}")
            self.assertEqual(evidence["release_id"], release)
            self.assertEqual(evidence["metric"]["value"], "37.625")
            self.assertEqual(evidence["metric"]["unit"], "tok/s")
            self.assertEqual(evidence["conditions"]["driver_version"]["status"], "missing")
            self.assertIn("37.625", get(evidence["url"], decode=False))
            path = f"/api/v1/historical-offers?release={offerings}&limit=1"
            first = get(path)
            self.assertEqual(first["offers"][0]["price"], "240.00")
            second = get(path + f"&offset={first['pagination']['next_offset']}")
            self.assertEqual(second["offers"][0]["landed_price"], "253.80")
            self.assertEqual(get(second["url"])["offers"][1]["landed_price"], "253.80")
            costs = get("/api/v1/calculator?scenario=illustrative")
            self.assertEqual(costs["options"]["upgrade"]["totals"]["nominal_cost"], "589.472")
            self.assertIn("589.472", get(costs["url"], decode=False))
            with urlopen(Request(origin + "/image-pilot", headers=headers), timeout=5) as response:
                report_path = response.geturl().removeprefix(origin)
                self.assertRegex(report_path, r"^/image-pilot/[a-f0-9]{64}/image-pilot\.html$")
                self.assertIn(b"Exact workflow", response.read())
            report_base = report_path.removesuffix("image-pilot.html")
            pilot = get(report_base + "image-pilot.json")
            self.assertEqual(pilot["evidence_kind"], "planned")
            self.assertEqual(pilot["workflow"], image_plan["workflow"])
            workflow = get(report_base + image_plan["workflow"]["path"], decode=False)
            self.assertEqual(sha256(workflow.encode("utf-8")).hexdigest(), image_plan["workflow"]["sha256"])
            with urlopen(Request(origin + "/text-pilot", headers=headers), timeout=5) as response:
                report_path = response.geturl().removeprefix(origin)
                self.assertRegex(report_path, r"^/text-pilot/[a-f0-9]{64}/text-pilot\.html$")
                self.assertIn(b"Chinese task quality review", response.read())
            text_base = report_path.removesuffix("text-pilot.html")
            text = get(text_base + "text-pilot.json")
            self.assertEqual(text["evidence_kind"], "planned")
            self.assertEqual(text["artifact"], text_plan["artifact"])
            self.assertEqual(text["runtime"], text_plan["runtime"])
            with urlopen(Request(origin + "/agent-task", headers=headers), timeout=5) as response:
                report_path = response.geturl().removeprefix(origin)
                self.assertRegex(report_path, r"^/agent-task/[a-f0-9]{64}/agent-task\.html$")
                self.assertIn(b"0 accepted of 0 attempted trials", response.read())
            task_base = report_path.removesuffix("agent-task.html")
            task = get(task_base + "agent-task.json")
            self.assertEqual([context["status"] for context in task["contexts"]], ["missing", "missing"])
            task_fixture = get(task_base + "task.json", decode=False)
            self.assertEqual(sha256(task_fixture.encode()).hexdigest(), task["conditions"]["task"]["fixture_sha256"])
            return evidence, first, second, costs, pilot, text, task

        with self.deployed_origin() as (origin, host):
            initial = replay(origin, host)
            if host is None:
                healthcheck = [sys.executable, "-m", "fastest_release.healthcheck", origin]
                subprocess.run(healthcheck, cwd=FIXTURE.parents[1], check=True, timeout=15)
                self.store._query("REVOKE EXECUTE ON FUNCTION fastest_prices.read_release(uuid) FROM origin_reader;")
                offline = subprocess.run(healthcheck, cwd=FIXTURE.parents[1], capture_output=True, timeout=15)
                self.assertEqual(offline.returncode, 1)
                self.assertIn(b"503", offline.stderr)
                self.store._query("GRANT EXECUTE ON FUNCTION fastest_prices.read_release(uuid) TO origin_reader;")
        with self.deployed_origin() as (origin, host):
            self.assertEqual(replay(origin, host), initial)
            self.store.withdraw(self.observation["evidence_id"], "Private fixture withdrawal")
            headers = {"Host": host} if host else {}
            path = f"/api/v1/evidence?release={release}"
            with self.assertRaises(HTTPError) as refused:
                urlopen(Request(origin + path, headers=headers), timeout=5).close()
            with refused.exception as response:
                self.assertEqual(response.code, 410)
                self.assertNotIn(b"37.625", response.read())

    def test_scaling_uses_only_approved_fields_from_pinned_postgres_rows(self):
        fixture = fixture_releases()
        baseline = fixture[BASELINE]["row"]
        comparison = fixture[COMPARISON]["row"]
        for row in (baseline, comparison):
            for field in row["fields"].values():
                field["rights"] = "allow"
        one = self.store.publish(baseline)
        comparison["fields"]["gpu_scaling_v1"]["rights"] = "deny"
        private = self.store.publish(comparison)
        self.assertEqual(scaling_report(self.store, (one, private))["reason"], "metadata")

        comparison["fields"]["gpu_scaling_v1"]["rights"] = "allow"
        many = self.store.publish(comparison)
        report = scaling_report(self.store, (one, many))
        self.assertEqual(report["comparison"]["release_id"], many)
        self.assertEqual(report["speedup"]["numerator"], "50000000000001")
        self.assertEqual(scaling_report(self.store, (one, private))["reason"], "metadata")

        self.store.withdraw(baseline["evidence_id"], "Synthetic fixture withdrawal")
        withdrawn = scaling_report(self.store, (one, many))
        self.assertEqual(withdrawn["reason"], "baseline_withdrawn")
        self.assertIsNone(withdrawn["speedup"])

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

    def test_operator_correction_and_withdrawal_account_for_exact_published_benchmark_bytes(self):
        from fastest_release.resolution import resolve_benchmark

        first = self.store.publish(self.observation)
        evidence_id = self.observation["evidence_id"]
        locator = self.observation["source"]["locator"]
        original_chart = self.store.artifact(first, "chart.json")
        self.observation["metric"]["value"] = "41.000000000001"
        self.observation["source"]["revision"] = "fixture-v2"
        self.observation["rights"]["decision_id"] = str(uuid4())
        arguments = {"evidenceId": evidence_id, "sourceLocator": locator, "previousRelease": first}
        with self.assertRaises(ReleaseError):
            resolve_benchmark(self.store, {**arguments, "sourceLocator": "different",
                                          "action": "correct", "correction": self.observation})
        corrected = resolve_benchmark(self.store, {**arguments, "action": "correct", "correction": self.observation})
        second = corrected["release"]
        self.assertEqual(self.store.read()["previous_release_id"], first)
        self.assertIn(sha256(original_chart.encode()).hexdigest(), corrected["earlierExports"].values())
        self.assertIn("41.000000000001", self.store.artifact(second, "chart.json"))
        self.assertEqual(self.store.artifact(first, "chart.json"), original_chart)
        self.assertEqual(resolve_benchmark(self.store, {**arguments, "action": "correct", "correction": self.observation}),
                         corrected)

        withdrawal = {**arguments, "action": "withdraw"}
        withdrawn = resolve_benchmark(self.store, withdrawal)
        self.assertEqual(resolve_benchmark(self.store, withdrawal), withdrawn)
        by_path = {entry["path"]: entry for entry in withdrawn["changes"]}
        old_chart = by_path[f"/releases/{first}/chart.json"]
        self.assertEqual(old_chart["before"], sha256(original_chart.encode()).hexdigest())
        self.assertEqual(old_chart["after"], sha256(self.store.artifact(first, "chart.json").encode()).hexdigest())
        self.assertIn(f"/releases/{second}/benchmark.md", by_path)
        self.assertEqual(self.store.read()["status"], "withdrawn")
        self.assertEqual(self.store.read(first)["status"], "withdrawn")
        self.assertNotIn("37.625", self.store.artifact(first, "chart.json"))

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

    def reviewed_profile_fixture(self):
        # All measurements in this disposable PostgreSQL cluster are invented test values.
        # The positive fixture uses the reviewed-row shape to exercise the production read.
        plan = json.loads(Path(FIXTURE.parents[1], "fastest_text", "plan.json").read_text())
        artifact = plan["artifact"]
        releases = []
        ids = {}
        for cell, values in zip(plan["cells"], [("12.125", "850.500"), ("42.000", "1200")]):
            run_id, hardware_id = str(uuid4()), str(uuid4())
            ids[cell["id"]] = run_id
            for phase, value in zip(("decode", "prefill"), values):
                observation = {
                    "evidence_id": str(uuid4()), "kind": "measured",
                    "hardware": {"revision_id": hardware_id, "revision": 1, "name": cell["name"],
                                 "configuration": "Synthetic test setup with known hardware and runtime settings"},
                    "artifact": {"artifact_id": "4b4a731f-3d6e-4b15-a8d5-9997bc93fd3d", "repository": artifact["repository"],
                                 "revision": artifact["revision"], "format": "GGUF", "quantization": artifact["quantization"],
                                 "path": artifact["shards"][0]["path"], "sha256": artifact["shards"][0]["sha256"]},
                    "workload": {"id": "llama-bench-solo-empty-kv", "version": 1, "description": "Fixture protocol"},
                    "metric": {"id": f"llama-bench-{phase}", "version": 1, "unit": "tok/s", "statistic": "median",
                               "boundary": plan["protocol"]["phases"][phase]["boundary"], "sample_count": 20, "value": value},
                    "source": {"label": "Synthetic test fixture", "locator": "https://example.invalid/fixture", "revision": "fixture-v1"},
                    "rights": self.observation["rights"],
                    "fields": {key: {"value": value, "rights": "allow", "status": "known"} for key, value in {
                        "profile_cell": cell["id"], "backend": cell["backend"], "run_id": run_id,
                        "runtime_revision": plan["runtime"]["revision"], "artifact_companion_sha256": artifact["shards"][1]["sha256"],
                    }.items()},
                }
                observation["fields"]["unpublished_operator_note"] = self.observation["fields"]["unpublished_operator_note"]
                releases.append(self.store.publish(observation))
                if cell["id"] == "rtx-4090" and phase == "decode":
                    withdrawn_evidence = observation["evidence_id"]
                    for field, value in [("kind", "synthetic"), ("sample_count", 2), ("artifact_companion_sha256", "a" * 64)]:
                        invalid = json.loads(json.dumps(observation))
                        invalid["evidence_id"] = str(uuid4())
                        invalid["fields"]["run_id"]["value"] = str(uuid4())
                        invalid["metric"]["value"] = "9999.125"
                        if field == "kind":
                            invalid[field] = value
                        elif field == "sample_count":
                            invalid["metric"][field] = value
                        else:
                            invalid["fields"][field]["value"] = value
                        releases.append(self.store.publish(invalid))
        return releases, ids, withdrawn_evidence

    def test_pinned_profile_round_trip_through_a_rights_filtered_reviewed_release(self):
        from fastest_release.http import make_server

        releases, ids, withdrawn_evidence = self.reviewed_profile_fixture()

        server = make_server(self.store, port=0, profile_releases=releases)
        worker = Thread(target=server.serve_forever)
        worker.start()
        try:
            def get(path, expected=200):
                with closing(http.client.HTTPConnection(*server.server_address, timeout=5)) as client:
                    client.request("GET", path)
                    response = client.getresponse()
                    self.assertEqual(response.status, expected)
                    self.assertEqual(response.getheader("Cache-Control"), "no-store")
                    return response.getheader("Location"), response.read().decode()

            index, _ = get("/profiles", 307)
            base = index.removesuffix("index.html")
            model = base + "models/qwen2.5-7b-instruct"
            _, raw = get(model + ".json")
            cohort = json.loads(raw)["cohorts"][0]
            selected = ids["rtx-4090"]
            self.assertEqual(cohort["ranking"], [selected, ids["apple-m4"]])
            self.assertEqual(cohort["map"], cohort["ranking"])
            self.assertNotIn("9999.125", raw)
            self.assertEqual([entry["status"] for entry in cohort["exclusions"]], ["artifact_mismatch", "insufficient_samples", "synthetic"])
            row = cohort["rows"][0]
            self.assertEqual(row["metrics"]["llama-bench-decode"]["value"], "42.000")
            self.assertEqual(row["model_url"], f"{model}.html?run={selected}#run-{selected}")
            _, machine_html = get(row["machine_url"].split("#")[0])
            self.assertIn(f'data-run-id="{selected}"', machine_html)
            self.assertIn(f'id="run-{selected}" open', machine_html)
            self.assertIn(row["model_url"], machine_html)
            self.assertIn("42.000", machine_html)
            _, model_html = get(row["model_url"].split("#")[0])
            self.assertIn(f'id="run-{selected}" open', model_html)
            self.assertGreaterEqual(model_html.count(f'data-run-id="{selected}"'), 3)
            self.assertIn("850.500", model_html)
            _, markdown = get(model + ".md")
            self.assertIn("42.000", markdown)
            self.assertIn(row["machine_url"], markdown)
            api_query = ("/api/v1/comparison/profile?kind=models&id=qwen2.5-7b-instruct"
                         f"&revision={base.split('/')[2]}&limit=1")
            _, raw = get(api_query)
            api_run = json.loads(raw)["results"][0]
            self.assertEqual(api_run["run_id"], selected)
            self.assertEqual(api_run["metrics"]["llama-bench-decode"]["value"], "42.000")
            self.assertEqual(api_run["metrics"]["llama-bench-decode"]["unit"], "tok/s")

            self.store.withdraw(withdrawn_evidence, "Fixture withdrawal")
            _, raw = get(model + ".json")
            after = json.loads(raw)["cohorts"][0]
            self.assertEqual(after["ranking"], [ids["apple-m4"]])
            self.assertEqual(after["map"], after["ranking"])
            self.assertNotIn("42.000", raw)
            self.assertIn("withdrawn", {entry["status"] for entry in after["exclusions"]})
            _, updated = get(api_query)
            self.assertNotIn("42.000", updated)
        finally:
            server.shutdown()
            worker.join(5)
            server.server_close()
            self.assertFalse(worker.is_alive())

    @unittest.skipUnless(HAS_SDK, "Install fastest_mcp/requirements.txt to test MCP")
    def test_mcp_pinned_evidence_and_comparisons_follow_live_release_rights(self):
        from mcp import McpError

        releases, ids, withdrawn_evidence = self.reviewed_profile_fixture()

        async def check(port):
            async with (
                mcp_client(port) as client,
                mcp_http_server(port) as url,
                mcp_http_client(url) as (http, handshake),
            ):
                self.assertEqual(handshake, await client.initialize())
                self.assertEqual(await http.list_tools(), await client.list_tools())
                self.assertEqual(await http.list_resource_templates(), await client.list_resource_templates())
                names = {tool.name for tool in (await client.list_tools()).tools}
                self.assertIn("v1_evidence", names)
                self.assertNotIn("v1_historical_offers", names)
                templates = (await client.list_resource_templates()).resourceTemplates
                self.assertEqual([template.uriTemplate for template in templates],
                                 ["fastest://v1/releases/{release_id}/evidence"])

                args = {"kind": "models", "id": "qwen2.5-7b-instruct"}
                comparison = await client.call_tool("v1_profile_comparison", args)
                self.assertEqual(comparison, await http.call_tool("v1_profile_comparison", args))
                self.assertFalse(comparison.isError)
                result = comparison.structuredContent
                args["revision"] = result["revision"]
                status, api = get_public(port, "/api/v1/comparison/profile", args)
                self.assertEqual(status, 200)
                self.assertEqual(result, json.loads(api))
                status, website = get_public(port, result["url"].removesuffix(".html") + ".json")
                self.assertEqual(status, 200)
                cohort = json.loads(website)["cohorts"][0]
                self.assertEqual(cohort["ranking"], [ids["rtx-4090"], ids["apple-m4"]])
                row = result["results"][0]
                self.assertEqual(row["run_id"], cohort["ranking"][0])
                excluded = [entry["status"] for entry in result["results"] if entry["type"] == "exclusion"]
                self.assertEqual(excluded, [entry["status"] for entry in cohort["exclusions"]])
                self.assertEqual(excluded, ["artifact_mismatch", "insufficient_samples", "synthetic"])
                measurement = cohort["rows"][0]["metrics"]["llama-bench-decode"]
                self.assertEqual(row["metrics"]["llama-bench-decode"]["evidence_id"], measurement["evidence_id"])
                self.assertEqual(measurement["evidence_id"], withdrawn_evidence)
                release_id = measurement["release_id"]
                uri = f"fastest://v1/releases/{release_id}/evidence"
                resource = await client.read_resource(uri)
                self.assertEqual(resource, await http.read_resource(uri))
                saved = json.loads(resource.contents[0].text)
                status, api = get_public(port, "/api/v1/evidence", {"release": release_id})
                self.assertEqual(status, 200)
                self.assertEqual(saved, json.loads(api))
                self.assertEqual(saved["release_id"], release_id)
                self.assertEqual(saved["evidence_id"], withdrawn_evidence)
                self.assertEqual(saved["metric"]["value"], "42.000")
                self.assertEqual(resource.contents[0].mimeType, "application/json")
                status, html = get_public(port, saved["url"])
                self.assertEqual(status, 200)
                for value in (release_id, withdrawn_evidence, "42.000"):
                    self.assertIn(value, html)
                self.assertNotIn("private calibration note", resource.contents[0].text)
                self.assertNotIn("unpublished_operator_note", resource.contents[0].text)
                evidence = await client.call_tool("v1_evidence", {"evidence_id": withdrawn_evidence})
                self.assertFalse(evidence.isError)
                self.assertEqual(evidence.structuredContent, saved)

                self.store.withdraw(withdrawn_evidence, "Private fixture withdrawal reason")
                status, _ = get_public(port, saved["url"])
                self.assertEqual(status, 410)
                with self.assertRaises(McpError) as denied:
                    await client.read_resource(uri)
                self.assertIn("Public rights have ended", str(denied.exception))
                with self.assertRaisesRegex(McpError, "Public rights have ended"):
                    await http.read_resource(uri)
                evidence = await client.call_tool("v1_evidence", {"release": release_id})
                self.assertTrue(evidence.isError)
                self.assertIn("Public rights have ended", evidence.content[0].text)
                self.assertNotIn("Private fixture withdrawal reason", evidence.content[0].text)
                after = await client.call_tool("v1_profile_comparison", args)
                self.assertEqual(after, await http.call_tool("v1_profile_comparison", args))
                self.assertFalse(after.isError)
                self.assertNotIn("42.000", after.content[0].text)
                self.assertIn("withdrawn", {entry.get("status") for entry in after.structuredContent["results"]})

        with api_server(self.store, profile_releases=releases) as server:
            asyncio.run(check(server.server_port))

    @unittest.skipUnless(HAS_SDK, "Install fastest_mcp/requirements.txt to test MCP")
    def test_mcp_evidence_matches_the_standalone_cpu_release(self):
        release = self.store.publish(self.cpu_baseline_observation())

        async def check(port):
            args = {"release": release}
            status, body = get_public(port, "/api/v1/evidence", args)
            self.assertEqual(status, 200)
            api = json.loads(body)
            async with mcp_client(port) as client:
                await client.initialize()
                result = await client.call_tool("v1_evidence", args)
                self.assertFalse(result.isError)
                self.assertEqual(result.structuredContent, api)
                resource = await client.read_resource(f"fastest://v1/releases/{release}/evidence")
                self.assertEqual(json.loads(resource.contents[0].text), api)
                for name, expected in CPU_BASELINE_CONDITIONS.items():
                    self.assertEqual(result.structuredContent["conditions"][name], expected)

        with api_server(self.store) as server:
            asyncio.run(check(server.server_port))

    def cpu_baseline_observation(self):
        observation = cpu_baseline_candidate({
            "runner": {"architecture": "x86_64", "cpu_model": "Synthetic CPU", "image_version": "20261120.1.0"},
            "run_url": "https://github.com/OmniMCP-AI/local-llm/actions/runs/123456/attempts/2",
            "median_tokens_per_second": "53.500", "samples_ns": [2_392_523_364] * 7,
        }, "a" * 64)
        observation["rights"] = {**self.observation["rights"], "expires_at": "2099-01-01T00:00:00Z"}
        observation["fields"] = {
            **{key: {**field, "rights": "allow"} for key, field in observation["fields"].items()},
            **self.observation["fields"],
            "settings": {"status": "known", "value": "outside the measured API fields", "rights": "allow"},
        }
        return observation

    def test_api_evidence_projects_only_released_fields_and_honors_expiring_rights(self):
        synthetic = self.store.publish(self.observation)
        cpu_baseline = self.cpu_baseline_observation()
        release = self.store.publish(cpu_baseline)
        contributor = self.store.publish({
            **cpu_baseline, "evidence_id": str(uuid4()), "kind": "contributor",
            "fields": {
                **cpu_baseline["fields"],
                "comparison_eligibility": {
                    "status": "known", "rights": "allow",
                    "value": "Excluded from controlled comparisons. The measurement is contributor-reported.",
                },
            },
        })
        cpu_baseline["fields"]["runner_image_version"]["rights"] = "deny"
        denied = self.store.publish({**cpu_baseline, "evidence_id": str(uuid4())})
        cpu_baseline["evidence_id"] = str(uuid4())
        cpu_baseline["rights"]["expires_at"] = "2000-01-01T00:00:00Z"
        expired = self.store.publish(cpu_baseline)
        cpu_baseline["rights"]["expires_at"] = "9999-02-31T00:00:00Z"
        with self.assertRaises(InvalidObservation):
            self.store.publish(cpu_baseline)

        self.store._query("""
            CREATE ROLE api_evidence_reader NOLOGIN;
            GRANT USAGE ON SCHEMA fastest_release TO api_evidence_reader;
            GRANT EXECUTE ON FUNCTION fastest_release.read_release(uuid), fastest_release.read_evidence(uuid)
                TO api_evidence_reader;
        """)
        reader = ReleaseStore(self.database_url + " options='-c role=api_evidence_reader'")
        with api_client(reader) as request:
            status, _, data = request(f"/api/v1/evidence?release={release}")
            self.assertEqual(status, 200)
            self.assertEqual(data["release_id"], release)
            self.assertEqual(data["metric"]["value"], "53.500")
            self.assertEqual(data["conditions"]["driver_version"]["status"], "missing")
            for name, expected in CPU_BASELINE_CONDITIONS.items():
                self.assertEqual(data["conditions"].get(name), expected, name)
            self.assertEqual(data["rights"]["expires_at"], "2099-01-01T00:00:00Z")
            self.assertNotIn("settings", data["conditions"])
            self.assertNotIn("physical_host_revision", data["conditions"])
            self.assertNotIn("private calibration note", json.dumps(data))
            self.assertEqual(request(f"/api/v1/evidence?evidence_id={data['evidence_id']}")[2], data)
            status, _, protected = request(f"/api/v1/evidence?release={denied}")
            self.assertEqual(status, 200)
            self.assertNotIn("runner_image_version", protected["conditions"])
            self.assertEqual(protected["conditions"]["wall_power"], CPU_BASELINE_CONDITIONS["wall_power"])
            status, _, reported = request(f"/api/v1/evidence?release={contributor}")
            self.assertEqual(status, 200)
            self.assertEqual(reported["kind"], "contributor")
            self.assertEqual(set(reported["conditions"]), {"comparison_eligibility", "runtime_revision", "settings"})
            status, _, html = request(data["url"], decode=False)
            self.assertEqual(status, 200)
            self.assertIn("53.500", html)
            self.assertIn(release, html)
            for artifact in ("chart.json", "table.json"):
                status, _, dataset = request(f"/releases/{release}/{artifact}")
                self.assertEqual(status, 200)
                fields = dataset["rows"][0]["fields"]
                self.assertEqual({name: fields[name] for name in CPU_BASELINE_CONDITIONS}, CPU_BASELINE_CONDITIONS)
            self.assertEqual(request(f"/api/v1/evidence?release={synthetic}")[0], 404)
            for path in (f"/api/v1/evidence?release={expired}", f"/releases/{expired}/benchmark.html"):
                status, _, body = request(path, decode=False)
                self.assertEqual(status, 410)
                self.assertNotIn("53.500", body)

            status, _, spec = request("/api/v1/openapi.json")
            self.assertEqual(status, 200)
            response = spec["paths"]["/api/v1/evidence"]["get"]["responses"]["200"]
            conditions = response["content"]["application/json"]["schema"]["properties"]["conditions"]
            self.assertFalse(conditions.get("required"))
            self.assertNotIn("physical_host_revision", conditions["properties"])
            for name in CPU_BASELINE_CONDITIONS:
                known, missing = conditions["properties"][name]["oneOf"]
                self.assertEqual(known["properties"]["status"]["const"], "known")
                self.assertEqual(known["properties"]["value"]["type"], "string")
                self.assertEqual(missing["properties"]["status"]["const"], "missing")
                self.assertEqual(missing["properties"]["reason"]["type"], "string")

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
        for release_id in ("current", original, corrected):
            for name in ("benchmark.md", "benchmark.html", "chart.json", "table.json", "manifest.json"):
                with self.subTest(release_id=release_id, name=name):
                    status, headers, body = request("GET", f"/releases/{release_id}/{name}",
                                                    **{"If-None-Match": '"prior-public-release"'})
                    self.assertEqual(status, 410)
                    self.assertEqual(headers["Cache-Control"], "no-store")
                    for private in ("37.625", "41.125", self.observation["evidence_id"], "Private withdrawal reason"):
                        self.assertNotIn(private, body)
        with self.assertRaises(ReleaseError):
            self.store.publish(self.observation)
