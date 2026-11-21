import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
from hashlib import sha256
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
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from fastest_release import InvalidObservation, ReleaseError, ReleaseStore
from fastest_release.capture_cpu import candidate as cpu_baseline_candidate
from fastest_prices import PriceStore
from fastest_release.research import SEED_ROOT
from test_mcp import HAS_SDK, get as get_public, mcp_client
from test_mcp_http import mcp_http_client, mcp_http_server
from test_public_api import api_client, api_server
from test_scaling import BASELINE, COMPARISON, fixture_releases
from fastest_release.scaling import scaling_report


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
    def deployed_origin(self):
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
                     image, "--trusted-host", "origin.example"],
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
            [sys.executable, "-m", "fastest_release", "serve", "--port", "0"],
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
