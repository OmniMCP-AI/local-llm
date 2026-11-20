from contextlib import contextmanager
import json
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
def cost_server():
    from fastest_release.http import make_server

    with make_server(None) as server:
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("Cost test did not stop its HTTP listener")


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
                    self.assertIn("scenario=illustrative&amp;monthly_accepted=18000&amp;months=12", content)
            with urlopen(base + "/costs") as response:
                content = response.read().decode()
                self.assertIn("No approved comparable", content)
                self.assertNotIn("Example GPU B", content)

    def test_http_rejects_invalid_and_repeated_parameters(self):
        with cost_server() as base:
            for query in ("?months=1&months=2", "?months=0", "?unknown=1"):
                with self.subTest(query=query), self.assertRaises(HTTPError) as error:
                    urlopen(base + "/costs" + query)
                with error.exception as response:
                    self.assertEqual(response.code, 400)
