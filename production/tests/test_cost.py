from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from fastest_cost import calculate


class CostComparisonTests(unittest.TestCase):
    def test_same_accepted_work_prices_all_four_options(self):
        result = calculate({"scenario": "illustrative"})
        self.assertEqual(result["estimate_kind"], "illustrative")
        self.assertEqual(result["workload"]["id"], "zh-copy-brief-01")
        self.assertEqual(result["assumptions"]["monthly_accepted"], 1800)
        keep, upgrade, rental, api = (result["options"][key] for key in ("keep", "upgrade", "rental", "api"))
        self.assertEqual(keep["service"]["attempts"], 2000)
        self.assertEqual(keep["monthly"]["load_kwh"], "2")
        self.assertEqual(keep["monthly"]["idle_kwh"], "4.5")
        self.assertEqual(keep["monthly"]["cooling_kwh"], "1.3")
        self.assertEqual(keep["monthly"]["recurring_cost"], "5.56")
        self.assertEqual(upgrade["purchase"]["gpu_only"], "500")
        self.assertEqual(upgrade["purchase"]["reused_parts"], "425")
        self.assertEqual(upgrade["purchase"]["whole_build"], "1025")
        self.assertEqual(upgrade["purchase"]["upfront"], "600")
        self.assertEqual(upgrade["monthly"]["recurring_cost"], "3.728")
        self.assertEqual(rental["monthly"]["billed_hours"], "7")
        self.assertEqual(rental["monthly"]["recurring_cost"], "7.25")
        self.assertEqual(api["monthly"]["uncached_input_tokens"], 1536000)
        self.assertEqual(api["monthly"]["cached_input_tokens"], 512000)
        self.assertEqual(api["monthly"]["recurring_cost"], "4.1984")
        self.assertEqual(upgrade["totals"]["nominal_cost"], "589.472")
        self.assertEqual(upgrade["totals"]["terminal_residual"], "100")

    def test_curves_and_sensitivity_share_the_capacity_gate(self):
        result = calculate({"scenario": "illustrative", "monthly_accepted": "18000", "months": "12"})
        keep = result["options"]["keep"]
        self.assertEqual(keep["service"]["maximum_monthly_accepted"], 14400)
        self.assertEqual(keep["service"]["reasons"], ["insufficient_capacity"])
        self.assertIsNone(keep["monthly"]["recurring_cost"])
        self.assertTrue(all(point["keep"] is None for point in result["cumulative_cost"]))
        self.assertEqual(result["payback"][0]["status"], "infeasible_service")
        self.assertIsNone(result["payback"][0]["payback_months"])
        low, high = result["sensitivity"][:2]
        self.assertEqual((low["value"], high["value"]), (9000, 27000))
        self.assertEqual(low["options"]["keep"]["service_status"], "feasible")
        self.assertEqual(high["options"]["keep"]["service_status"], "infeasible")
        self.assertEqual(len(result["cumulative_cost"]), 13)
        for key, option in result["options"].items():
            self.assertEqual(result["cumulative_cost"][-1][key], option["totals"]["nominal_cost"])

    def test_payback_requires_positive_recurring_savings_and_ignores_residual(self):
        result = calculate({"scenario": "illustrative"})
        rows = {(row["option"], row["baseline"]): row for row in result["payback"]}
        self.assertEqual(rows["upgrade", "keep"]["monthly_savings"], "1.832")
        self.assertEqual(rows["upgrade", "keep"]["payback_months"], "327.510917")
        self.assertEqual(rows["upgrade", "keep"]["status"], "beyond_horizon")
        self.assertEqual(rows["keep", "api"]["monthly_savings"], "-1.3616")
        self.assertIsNone(rows["keep", "api"]["payback_months"])
        self.assertEqual(rows["keep", "api"]["status"], "nonpositive_savings")

    def test_unavailable_service_has_null_costs_without_using_fixture_prices(self):
        result = calculate()
        self.assertEqual(result["estimate_kind"], "unavailable")
        self.assertIsNone(result["inputs"]["price_basis"]["electricity"]["per_kwh"])
        self.assertIsNone(result["options"]["keep"]["purchase"]["upfront"])
        self.assertIsNone(result["options"]["keep"]["monthly"]["idle_kwh"])
        self.assertEqual(result["options"]["rental"]["purchase"]["upfront"], "0")
        for option in result["options"].values():
            self.assertEqual(option["service"]["status"], "unknown")
            self.assertIsNone(option["totals"]["nominal_cost"])
        self.assertTrue(all(row["status"] == "unknown_inputs" for row in result["payback"]))

    def test_selectors_are_bounded_and_revision_pins_normalized_values(self):
        for selection in ({"months": "0"}, {"monthly_accepted": "1.5"}, {"scenario": "other"},
                          {"months": "121"}, {"nonsense": "1"}):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                calculate(selection)
        result = calculate({"scenario": "illustrative"})
        self.assertEqual(result, calculate({"months": "024", "scenario": "illustrative", "monthly_accepted": "1800"}))
        self.assertNotEqual(result["revision"], calculate({"scenario": "illustrative", "months": 12})["revision"])


@contextmanager
def cost_server(**options):
    from fastest_release.http import make_server

    with make_server(None, port=0, **options) as server:
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("Cost test did not stop its HTTP listener")


def reviewed_scenario():
    return {
        "schema_version": 1,
        "revision": "fixture-reviewed-cost-v1",
        "authorization": {"status": "approved", "decision_id": "88392cd1-c0d7-45bc-9140-bdd4c01b6d4a",
                          "expires_at": "2099-11-30T00:00:00Z"},
        "workload": {key: calculate()["workload"][key] for key in (
            "id", "revision", "quality_rubric", "concurrency", "latency_boundary",
            "input_tokens_per_attempt", "output_tokens_per_attempt",
        )},
        "price_basis": {"market": "US", "destination": "US-CA, ZIP 95814", "currency": "USD",
                        "as_of": datetime.now(timezone.utc).date().isoformat(), "method": "Fictional operator test evidence.",
                        "electricity": None},
        "options": {"api": {
            "configuration": "Fixture endpoint", "configuration_revision": "fixture-endpoint@1",
            "service": {"revision": "fixture-same-task@1", "quality": "pass", "privacy": "pass",
                        "p95_latency_ms": 8000, "seconds_per_attempt": "6", "sample_count": 100,
                        "accepted_count": 100, "available_hours": "100", "utilization": "0.8"},
            "operation": {"revision": "fixture-api-tariff@1", "eligibility": "Standard fixture account",
                          "billing": "Per million tokens",
                          "input_per_million": "2", "cached_input_per_million": "1", "output_per_million": "8",
                          "cached_input_ratio": "0", "monthly_fee": "0"},
        }},
        "citations": {
            "scenario": {"locator": "https://example.test/scenarios/cost", "revision": "fixture-reviewed-cost-v1"},
            "api.service": {"locator": "https://example.test/runs/fixture", "revision": "fixture-same-task@1"},
            "api.operation": {"locator": "https://example.test/tariffs/fixture", "revision": "fixture-api-tariff@1"},
        },
    }


def reviewed_tariff_references():
    return {
        "schema_version": 1,
        "revision": "fixture-tariff-references-v1",
        "authorization": {"status": "approved", "decision_id": "88392cd1-c0d7-45bc-9140-bdd4c01b6d4a",
                          "expires_at": "2099-11-30T00:00:00Z"},
        "references": [
            {
                "id": "fixture-on-peak", "kind": "electricity", "provider": "Fixture Electric",
                "offering": "Residential time-of-use", "revision": "fixture-residential@1",
                "market": "CA", "region": "Ontario", "currency": "CAD", "amount": "0.3100", "unit": "kwh",
                "component": "On peak", "effective_from": "2020-01-01", "effective_until": "2099-12-01",
                "qualification": "Weekdays 5–8 p.m. local time.", "source": "Utility rate schedule",
                "checked_at": "2025-11-01T00:00:00Z",
                "citation": {"locator": "https://example.test/electricity#time-of-use",
                             "revision": "fixture-residential@1"},
            },
            {
                "id": "fixture-monthly", "kind": "electricity", "provider": "Fixture Electric",
                "offering": "Residential time-of-use", "revision": "fixture-residential@1",
                "market": "CA", "region": "Ontario", "currency": "CAD", "amount": "24.00", "unit": "month",
                "component": "Fixed service charge", "effective_from": "2020-01-01", "effective_until": "2099-12-01",
                "qualification": "One charge per eligible customer account.", "source": "Utility rate schedule",
                "checked_at": "2025-11-01T00:00:00Z",
                "citation": {"locator": "https://example.test/electricity#monthly",
                             "revision": "fixture-residential@1"},
            },
            {
                "id": "fixture-cloud", "kind": "rental", "provider": "Fixture Cloud", "offering": "Fixture GPU Linux",
                "revision": "fixture-cloud@1", "market": "US", "region": "West", "currency": "USD",
                "amount": "0.52600", "unit": "instance_hour", "component": "Base compute",
                "effective_from": "2025-01-01", "effective_until": None,
                "qualification": "Linux on demand. Storage and transfer charges may apply.",
                "source": "Cloud pricing catalog", "checked_at": "2025-11-01T00:00:00Z",
                "citation": {"locator": "https://example.test/cloud#meter", "revision": "fixture-cloud@1"},
            },
        ],
    }


class CostHttpTests(unittest.TestCase):
    def test_html_markdown_and_json_use_the_same_revision_and_workload(self):
        query = "?scenario=illustrative&monthly_accepted=18000&months=12"
        with cost_server() as base:
            with urlopen(base + "/costs.json" + query) as response:
                result = json.load(response)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
            for extension, media in (("", "text/html"), (".md", "text/markdown")):
                with urlopen(base + "/costs" + extension + query) as response:
                    content = response.read().decode()
                    self.assertEqual(response.headers.get_content_type(), media)
                for text in (result["revision"], "Illustrative", "Sensitivity", "Cumulative cost",
                             "Insufficient capacity", "GPU-only"):
                    self.assertIn(text, content)
                self.assertIn(result["options"]["upgrade"]["totals"]["nominal_cost"], content)
                if extension == "":
                    self.assertIn("<svg", content)
                    self.assertIn("Show point labels", content)
                    self.assertIn("Ownership month: 0 · Cumulative cost:", content)
                    self.assertIn("scenario=illustrative&amp;monthly_accepted=18000&amp;months=12", content)
            with urlopen(base + "/costs") as response:
                content = response.read().decode()
                self.assertIn("No approved comparable", content)
                self.assertNotIn("Example GPU B", content)

    def test_operator_reviewed_scenario_reaches_html_api_and_advisor_with_same_evidence(self):
        with TemporaryDirectory(prefix="fastest-cost-test-") as root:
            path = Path(root) / "scenario.json"
            scenario = reviewed_scenario()
            path.write_text(json.dumps(scenario))
            with cost_server(cost_scenario=path) as base:
                def read(route):
                    with urlopen(base + route, timeout=5) as response:
                        return response.read().decode()
                query = "scenario=evidence&monthly_accepted=1800&months=24"
                result = json.loads(read("/costs.json?" + query))
                self.assertEqual(result["estimate_kind"], "reviewed")
                self.assertEqual(result["options"]["api"]["totals"]["nominal_cost"], "132.7104")
                self.assertIsNone(result["options"]["keep"]["totals"]["nominal_cost"])
                self.assertIn("https://example.test/tariffs/fixture", read("/costs?" + query))
                self.assertIn(result["revision"], read("/costs.md?" + query))
                calculator = json.loads(read("/api/v1/calculator?" + query))
                advisor = json.loads(read("/api/v1/advisor?decision=cost&privacy=allow-external&" + query))
                self.assertEqual(calculator["revision"], result["revision"])
                self.assertEqual(advisor["costs"]["options"]["api"]["nominal_cost"], "132.7104")
                self.assertEqual(advisor["citations"], result["citations"])

                scenario["authorization"]["status"] = "withdrawn"
                path.write_text(json.dumps(scenario))
                retired = json.loads(read("/costs.json?" + query))
                self.assertEqual(retired["estimate_kind"], "unavailable")
                self.assertIsNone(retired["options"]["api"]["totals"]["nominal_cost"])
                self.assertNotIn("example.test", json.dumps(retired))

    def test_reviewed_tariff_references_have_format_and_api_parity_without_pricing_the_workload(self):
        with TemporaryDirectory(prefix="fastest-cost-test-") as root:
            path = Path(root) / "tariffs.json"
            manifest = reviewed_tariff_references()
            path.write_text(json.dumps(manifest))
            with cost_server(cost_tariff_references=path) as base:
                def read(route):
                    with urlopen(base + route, timeout=5) as response:
                        self.assertEqual(response.headers["Cache-Control"], "no-store")
                        return response.read().decode()

                result = json.loads(read("/costs.json"))
                block = result["tariff_references"]
                self.assertEqual(block["revision"], "fixture-tariff-references-v1")
                self.assertEqual(block["references"], manifest["references"])
                calculator = json.loads(read("/api/v1/calculator"))
                self.assertEqual(calculator["tariff_references"], block)
                api = json.loads(read("/api/v1/openapi.json"))
                schema = api["paths"]["/api/v1/calculator"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
                self.assertNotIn("tariff_references", schema["required"])
                row_schema = schema["properties"]["tariff_references"]["properties"]["references"]["items"]
                self.assertEqual(row_schema["properties"]["amount"]["type"], "string")
                self.assertEqual(row_schema["properties"]["effective_until"]["type"], ["string", "null"])
                self.assertEqual(calculator["revision"], result["revision"])
                self.assertIn("revision=" + result["revision"], calculator["url"])
                query = "?" + calculator["url"].partition("?")[2]
                self.assertEqual(json.loads(read("/costs.json" + query)), result)
                self.assertEqual(json.loads(read("/api/v1/calculator" + query)), calculator)
                for route in ("/costs", "/costs.md"):
                    content = read(route + query)
                    for expected in (result["revision"], "Reviewed tariff references", "CAD 0.3100",
                                     "CAD 24.00", "USD 0.52600", "instance hour", "2020-01-01", "2099-12-01",
                                     "Weekdays 5–8 p.m. local time.", "Linux on demand.",
                                     "https://example.test/electricity#time-of-use", "https://example.test/cloud#meter"):
                        self.assertIn(expected, content)
                    self.assertIn("revision=" + result["revision"], content)
                base_result = calculate()
                self.assertNotEqual(base_result["revision"], result["revision"])
                self.assertEqual({key: value for key, value in result.items() if key not in
                                  {"revision", "tariff_references"}}, {
                                      key: value for key, value in base_result.items() if key != "revision"
                                  })
                self.assertEqual(json.loads(read("/costs.json?scenario=illustrative")),
                                 calculate({"scenario": "illustrative"}))

    def test_tariff_reference_effective_dates_and_authorization_retire_exact_replays(self):
        with TemporaryDirectory(prefix="fastest-cost-test-") as root:
            path = Path(root) / "tariffs.json"
            scenario_path = Path(root) / "scenario.json"
            scenario_path.write_text(json.dumps(reviewed_scenario()))
            manifest = reviewed_tariff_references()
            path.write_text(json.dumps(manifest))
            with cost_server(cost_scenario=scenario_path, cost_tariff_references=path) as base:
                def fetch(route):
                    with urlopen(base + route, timeout=5) as response:
                        return response.read().decode()

                def assert_retired(query):
                    for route in ("/costs", "/costs.md", "/costs.json", "/api/v1/calculator"):
                        with self.assertRaises(HTTPError) as error:
                            fetch(route + query)
                        with error.exception as response:
                            self.assertEqual(response.code, 404)
                            self.assertNotIn("Fixture Electric", response.read().decode())

                original = json.loads(fetch("/costs.json"))
                original_query = "?revision=" + original["revision"]
                manifest["references"][0]["effective_until"] = datetime.now(timezone.utc).date().isoformat()
                manifest["references"][1]["effective_from"] = "2099-01-01"
                path.write_text(json.dumps(manifest))
                current = json.loads(fetch("/api/v1/calculator"))
                self.assertEqual([row["id"] for row in current["tariff_references"]["references"]], ["fixture-cloud"])
                for route in ("/costs", "/costs.md"):
                    self.assertNotIn("Fixture Electric", fetch(route))
                self.assertEqual(current["options"]["api"]["totals"]["nominal_cost"], "132.7104")
                self.assertEqual(original["options"], current["options"])
                assert_retired(original_query)

                current_query = "?revision=" + current["revision"]
                for authorization in ({"status": "withdrawn"}, {"expires_at": "2020-01-01T00:00:00Z"}):
                    manifest["authorization"] = {**reviewed_tariff_references()["authorization"], **authorization}
                    path.write_text(json.dumps(manifest))
                    for route in ("/costs.json", "/api/v1/calculator"):
                        retired = json.loads(fetch(route))
                        self.assertNotIn("tariff_references", retired)
                        self.assertNotIn("Fixture Cloud", json.dumps(retired))
                        self.assertEqual(retired["options"], original["options"])
                    for route in ("/costs", "/costs.md"):
                        self.assertNotIn("Reviewed tariff references", fetch(route))
                    assert_retired(current_query)

    def test_reviewed_bom_uses_the_exact_live_whole_build_price_rights(self):
        scenario = reviewed_scenario()
        release = "ee436650-1a1d-45e4-995d-c3be9b443f0d"
        scenario["price_basis"]["electricity"] = {"revision": "power@1", "per_kwh": "0.2"}
        scenario["options"]["keep"] = {
            "configuration": "Fixture build", "configuration_revision": "build@1",
            "purchase": {"revision": "bom@1", "price_release": release, "scope_id": "fixture-build",
                         "condition": "used", "parts": [
                {"sku": "Fixture whole-build part", "kind": "gpu", "condition": "used", "quantity": 1,
                 "unit_price": "250", "reused": True},
            ]},
            "service": {**scenario["options"]["api"]["service"], "revision": "local-service@1"},
            "operation": {"revision": "meter@1", "load_watts": "200", "idle_watts": "50",
                          "external_cooling_ratio": "0", "monthly_maintenance": "0", "terminal_residual": "0"},
        }
        scenario["citations"].update({
            "electricity": {"locator": "https://example.test/power", "revision": "power@1"},
            "keep.purchase": {"locator": "https://example.test/bom", "revision": "bom@1"},
            "keep.service": {"locator": "https://example.test/local-run", "revision": "local-service@1"},
            "keep.operation": {"locator": "https://example.test/meter", "revision": "meter@1"},
        })
        quote = {
            "status": "published", "release_id": release, "data_class": "authorized_observations",
            "adapter_status": "fresh", "market": "US", "destination": "US-CA, ZIP 95814", "currency": "USD",
            "as_of": scenario["price_basis"]["as_of"], "condition": "used",
            "scope": {"kind": "whole_build", "id": "fixture-build", "revision_id": "build@1"},
            "offers": [{"latest_for_listing": True, "freshness": "fresh", "kind": "asking",
                        "stock": "in_stock", "confirmation": "seller_confirmed", "discount": "unconditional",
                        "landed_price": "250", "source_locator": "https://example.test/quote", "listing_id": "1"}],
        }
        with TemporaryDirectory(prefix="fastest-cost-test-") as root:
            path = Path(root) / "scenario.json"
            path.write_text(json.dumps(scenario))
            def read_price(identifier):
                self.assertEqual(identifier, release)
                return quote
            eligible = calculate(reviewed_path=path, price_reader=read_price)
            self.assertEqual(eligible["options"]["keep"]["purchase"]["whole_build"], "250")
            self.assertEqual(eligible["options"]["keep"]["totals"]["nominal_cost"], "26.16")
            self.assertIn({"scope": "keep.price_release", "locator": "https://example.test/quote", "revision": release},
                          eligible["citations"])
            for patch in ({"status": "withdrawn"}, {"scope": {**quote["scope"], "revision_id": "other"}},
                          {"adapter_status": "stale"}):
                ineligible = calculate(reviewed_path=path, price_reader=lambda identifier: {**quote, **patch})
                self.assertIsNone(ineligible["options"]["keep"]["totals"]["nominal_cost"])
                self.assertNotIn("example.test/bom", json.dumps(ineligible))

    def test_operator_input_rejects_a_different_workload_and_unbound_citation(self):
        with TemporaryDirectory(prefix="fastest-cost-test-") as root:
            path = Path(root) / "scenario.json"
            for mutate in (
                lambda scenario: scenario["workload"].update(concurrency=4),
                lambda scenario: scenario["citations"]["api.service"].update(revision="wrong"),
                lambda scenario: scenario["options"]["api"]["service"].update(accepted_count=101),
            ):
                scenario = reviewed_scenario()
                mutate(scenario)
                path.write_text(json.dumps(scenario))
                with self.assertRaisesRegex(ValueError, "workload|citation|counts"):
                    calculate(reviewed_path=path)

    def test_http_rejects_invalid_and_repeated_parameters(self):
        with cost_server() as base:
            for query in ("?months=1&months=2", "?months=0", "?unknown=1"):
                with self.subTest(query=query), self.assertRaises(HTTPError) as error:
                    urlopen(base + "/costs" + query)
                with error.exception as response:
                    self.assertEqual(response.code, 400)
