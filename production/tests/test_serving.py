"""Synthetic operator ledgers exercise the serving path without a real run."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen

from fastest_goals import GoalService
from test_goals import allow_observations, server


PLAN = Path(__file__).resolve().parents[1] / "fastest_text" / "plan.json"


def serving_record():
    text_plan = json.loads(PLAN.read_text())
    requests = [
        {"user": user, "request": request, "started_ms": (request - 1) * 6000,
         "outcome": "accepted", "elapsed_ms": user * 100 + request, "output_tokens": 128}
        for user in range(1, 5) for request in range(1, 25)
    ]
    requests[0].update(outcome="timeout", elapsed_ms=5000, reason="Client deadline elapsed.")
    requests[1].update(outcome="failed", elapsed_ms=120, reason="Server returned an error.")
    requests[2].update(outcome="rejected", elapsed_ms=250, output_tokens=127, reason="Output was too short.")
    return {
        "kind": "measured", "cell_id": "apple-m4", "protocol": "four-user-fixed-token-serving@1",
        "artifact_sha256": [shard["sha256"] for shard in text_plan["artifact"]["shards"]],
        "runtime_revision": text_plan["runtime"]["revision"],
        "runtime_build": {"backend": "Metal", "binary_sha256": "a" * 64,
                          "configuration": "Synthetic test runtime configuration."},
        "source": {"locator": "Example synthetic serving ledger", "revision": "fixture-1"},
        "rights": {"decision_id": "ee436650-1a1d-45e4-995d-c3be9b443f0d", "destination": "public-release",
                   "core": "allow", "basis": "Synthetic test evidence only."},
        "privacy": "local-only", "duration_ms": 144000, "attempts": requests,
        "power": {"status": "measured", "boundary": "serving-host-ac-input",
                  "meter": "Example synthetic cumulative joule meter", "start_ms": 0,
                  "end_ms": 144000, "start_joules": "2500", "end_joules": "11800"},
    }


def configured_service(root, record, *, include_solo=False):
    path = Path(root) / "goals.json"
    (path.parent / "serving.json").write_text(json.dumps(record))
    records = []
    if include_solo:
        solo = json.loads((PLAN.parents[1] / "fixtures" / "synthetic-text-pilot.json").read_text())
        solo["kind"] = "measured"
        (path.parent / "solo.json").write_text(json.dumps(solo))
        records.append("solo.json")
    path.write_text(json.dumps({
        "schema_version": 1, "market": {"market": "US", "destination": None, "currency": "USD", "condition": "new"},
        "records": records, "candidates": {}, "serving_records": ["serving.json"],
    }))
    service = GoalService(path, rights_path=path.parent / "rights.json")
    allow_observations(service)
    return service


def serving_result(service, **limits):
    return service.evaluate(service.selection({"entry": "serving", **limits}))


def result_row(result, cell="apple-m4"):
    return next(row for row in result["rows"] if row["id"] == cell)


class ServingTests(unittest.TestCase):
    def test_default_link_opens_pinned_unmeasured_comparison(self):
        with server() as base:
            with urlopen(base + "/goals", timeout=5) as response:
                self.assertIn("Team serving", response.read().decode())
            with urlopen(base + "/goals?entry=serving&user_p95=500", timeout=5) as response:
                pinned = urlsplit(response.url)
                html = response.read().decode()
            with urlopen(f"{base}{pinned.path}.json?{pinned.query}", timeout=5) as response:
                result = json.load(response)
        self.assertIn("<caption>Exact goal results</caption>", html)
        self.assertIn("No reviewed serving run was supplied", html)
        self.assertEqual(result["selection"]["user_p95"], "500")
        self.assertEqual(result["chart"]["points"], [])
        self.assertIsNone(result["recommendation"])
        self.assertEqual(result_row(result)["goals"]["user_p95"]["status"], "unknown")
        self.assertEqual(result_row(result)["serving"]["counts"]["attempted"], 0)

    def test_reviewed_serving_uses_accepted_work_and_whole_window_energy(self):
        with TemporaryDirectory(prefix="fastest-serving-test-") as root:
            service = configured_service(root, serving_record())
            result = serving_result(service, user_p95="400", capacity="80", wall_energy="100")
            with server(service) as base:
                with urlopen(base + service.url(result["selection"]), timeout=5) as response:
                    html = response.read().decode()
        row = result_row(result)
        self.assertEqual(row["serving"]["counts"], {
            "planned": 96, "attempted": 96, "accepted": 93, "failed": 1, "timeout": 1,
            "rejected": 1, "unrecorded": 0,
        })
        self.assertEqual([user["p95_ms"] for user in row["serving"]["users"]], [123, 223, 323, 423])
        self.assertEqual(row["goals"]["user_p95"]["gap"], "23")
        self.assertEqual(row["goals"]["capacity"]["value"], "82.666667")
        self.assertEqual(row["goals"]["wall_energy"]["value"], "100")
        self.assertEqual(row["serving"]["wall_joules"], "9300")
        self.assertIsNone(result["recommendation"])
        self.assertEqual(result["chart"]["points"], [{"id": "apple-m4", "x": "82.666667", "y": "423", "pareto": True}])
        for displayed in ("Client deadline elapsed.", "Server returned an error.", "423 ms", "9300 J",
                          "93 accepted", "serving-host-ac-input", "127"):
            self.assertIn(displayed, html)

    def test_withdrawn_serving_observation_is_denied_without_restarting(self):
        with TemporaryDirectory(prefix="fastest-serving-test-") as root:
            service = configured_service(root, serving_record(), include_solo=True)
            serving_url = service.url(service.selection({"entry": "serving"}), ".json")
            with server(service) as base:
                with urlopen(base + serving_url, timeout=5) as response:
                    self.assertEqual(result_row(json.load(response))["serving"]["counts"]["accepted"], 93)
                policy = json.loads(service.rights_path.read_text())
                policy["observations"][service.observation_digests["serving"]["apple-m4"]] = "withdrawn"
                service.rights_path.write_text(json.dumps(policy))
                for path in (serving_url, "/api/v1/comparison?entry=serving"):
                    with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                        urlopen(base + path, timeout=5)
                    with error.exception as response:
                        self.assertEqual(response.code, 410)
                with urlopen(base + f"/goals/{service.release_id}/text-pilot.json", timeout=5) as response:
                    self.assertEqual(response.status, 200)

    def test_api_reuses_the_pinned_serving_decision_and_citation(self):
        with TemporaryDirectory(prefix="fastest-serving-test-") as root:
            service = configured_service(root, serving_record())
            with server(service) as base:
                with urlopen(base + "/api/v1/comparison?entry=serving&user_p95=400&capacity=80&wall_energy=100",
                             timeout=5) as response:
                    result = json.load(response)
                with urlopen(base + result["url"], timeout=5) as response:
                    html = response.read().decode()
        self.assertEqual(result_row(result)["goals"]["user_p95"]["status"], "miss")
        self.assertEqual(result["rights"]["measurements"]["apple-m4"]["decision_id"],
                         "ee436650-1a1d-45e4-995d-c3be9b443f0d")
        self.assertEqual(result["citations"][0]["url"], result["url"])
        self.assertIn("423 ms", html)

    def test_missing_wall_meter_and_underpowered_latency_stay_unknown(self):
        record = serving_record()
        record["power"] = {"status": "missing", "reason": "No calibrated wall meter available."}
        for attempt in record["attempts"][3:5]:
            attempt.update(outcome="timeout", elapsed_ms=5000, reason="Client deadline elapsed.")
        with TemporaryDirectory(prefix="fastest-serving-test-") as root:
            row = result_row(serving_result(configured_service(root, record, include_solo=True), wall_energy="100"))
        self.assertIsNone(row["goals"]["user_p95"]["value"])
        self.assertIn("20 accepted", row["goals"]["user_p95"]["reason"])
        self.assertEqual(row["goals"]["capacity"]["status"], "pass")
        self.assertEqual(row["goals"]["wall_energy"]["status"], "unknown")
        self.assertIn("No calibrated wall meter", row["goals"]["wall_energy"]["reason"])

    def test_partial_window_cannot_supply_capacity_or_energy_per_request(self):
        record = serving_record()
        record["attempts"].pop()
        with TemporaryDirectory(prefix="fastest-serving-test-") as root:
            row = result_row(serving_result(configured_service(root, record), wall_energy="200"))
        self.assertEqual(row["serving"]["counts"]["unrecorded"], 1)
        self.assertEqual(row["goals"]["capacity"]["status"], "unknown")
        self.assertEqual(row["goals"]["wall_energy"]["status"], "unknown")

    def test_solo_hardware_power_and_estimates_are_ineligible_inputs(self):
        cases = (
            ("protocol", "llama-bench-solo-empty-kv@1", "pinned protocol"),
            ("kind", "synthetic", "measured"),
            ("power", {**serving_record()["power"], "boundary": "gpu-board"}, "wall meter"),
            ("power", {"status": "estimate", "watts": "300"}, "wall meter"),
            ("power", {**serving_record()["power"], "end_ms": 120000}, "full wall-meter window"),
        )
        for field, value, error in cases:
            with self.subTest(field=field, value=value), TemporaryDirectory(prefix="fastest-serving-test-") as root:
                record = serving_record()
                record[field] = value
                with self.assertRaisesRegex(ValueError, error):
                    configured_service(root, record)
