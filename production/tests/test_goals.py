from contextlib import contextmanager
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen

from fastest_goals import GoalService
from fastest_release.http import make_server


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic-text-pilot.json"
PRICE_ID = "ee436650-1a1d-45e4-995d-c3be9b443f0d"


def read_price(release_id):
    return {
        "release_id": release_id, "status": "published", "data_class": "authorized_observations", "adapter_status": "fresh",
        "market": "US", "destination": "US-CA, ZIP 95814", "currency": "USD", "condition": "new",
        "scope": {"kind": "whole_build", "id": "apple-m4", "revision_id": "fixture-m4-build-v1"},
        "offers": [{
            "latest_for_listing": True, "freshness": "fresh", "kind": "asking",
            "stock": "in_stock", "confirmation": "seller_confirmed", "discount": "unconditional",
            "landed_price": "1199.95", "observed_at": "2026-11-03T12:00:00Z",
            "seller": "fixture seller", "listing_id": "fixture-listing", "source_locator": "example/feed/quote",
        }],
    }


@contextmanager
def fixture_service(*, price=read_price, modify_record=None, privacy="local-only"):
    with TemporaryDirectory(prefix="fastest-goals-fixtures-") as temp:
        root = Path(temp)
        for name, backend, prefill, decode in (
            ("apple-m4", "Metal", 1_000_000_000, 2_000_000_000),
            ("rtx-4090", "CUDA", 1_280_000_000, 1_000_000_000),
        ):
            record = json.loads(FIXTURE.read_text())
            record.update(kind="measured", cell_id=name, attempts=[
                {"phase": "prefill", "number": 1, "outcome": "success", "elapsed_ns": prefill},
                {"phase": "decode", "number": 1, "outcome": "success", "elapsed_ns": decode},
            ])
            record["runtime_build"]["backend"] = backend
            record["quality_reviews"][1]["scores"]["facts"] = True
            if modify_record:
                modify_record(record)
            (root / f"{name}.json").write_text(json.dumps(record))
        manifest = {
            "schema_version": 1,
            "records": ["apple-m4.json", "rtx-4090.json"],
            "market": {"market": "US", "destination": "US-CA, ZIP 95814", "currency": "USD", "condition": "new"},
            "candidates": {
                "apple-m4": {"build_revision": "fixture-m4-build-v1", "price_release": PRICE_ID,
                             "privacy": {"value": privacy, "source": "fixture execution review"}},
                "rtx-4090": {"privacy": {"value": "local-only", "source": "fixture execution review"}},
            },
        }
        path = root / "cohort.json"
        path.write_text(json.dumps(manifest))
        yield GoalService(path, price_reader=price)


def rows(result):
    return {row["id"]: row for row in result["rows"]}


@contextmanager
def server(service=None, *, history=()):
    with make_server(None, port=0, goals=service, goal_history=history) as http:
        worker = Thread(target=http.serve_forever)
        worker.start()
        try:
            yield f"http://127.0.0.1:{http.server_port}"
        finally:
            http.shutdown()
            worker.join()


class GoalTests(unittest.TestCase):
    def test_pinned_default_preserves_goals_and_explains_no_match(self):
        with server() as base:
            with urlopen(base + "/goals?entry=machine&machine=rtx-4090&decode=75&prefill=900", timeout=5) as response:
                pinned = urlsplit(response.url)
                html = response.read().decode()
            self.assertRegex(pinned.path, r"^/goals/[a-f0-9]{64}$")
            self.assertIn("No setup meets every goal", html)
            self.assertIn('name="decode" type="number" value="75"', html)
            self.assertIn("No authorized GeForce RTX 4090 host", html)
            self.assertIn("<caption>Exact goal results</caption>", html)
            self.assertIn('id="goal-chart"', html)
            self.assertIn('id="goal-apple-m4"', html)
            with urlopen(f"{base}{pinned.path}.json?{pinned.query}", timeout=5) as response:
                result = json.load(response)
            with urlopen(f"{base}{pinned.path}/text-pilot.html", timeout=5) as response:
                self.assertIn("llama-bench-solo-empty-kv@1", response.read().decode())
            with self.assertRaises(HTTPError) as error:
                urlopen(base + "/goals/" + "a" * 64, timeout=5)
            with error.exception as response:
                self.assertEqual(response.code, 404)
        self.assertEqual(result["release_id"], pinned.path.split("/")[-1])
        self.assertEqual(result["selection"]["machine"], "rtx-4090")
        self.assertEqual(result["selection"]["decode"], "75")
        self.assertIsNone(result["recommendation"])
        self.assertEqual(result["chart"]["points"], [])
        self.assertEqual({row["status"] for row in result["rows"]}, {"unknown"})

    def test_entries_share_exact_cohort_and_directional_priority_is_independent(self):
        with fixture_service() as service:
            results = [service.evaluate(service.selection({"entry": entry, "budget": "1500", "priority": "prefill"}))
                       for entry in ("machine", "budget", "expert")]
            self.assertEqual({result["release_id"] for result in results}, {service.release_id})
            self.assertEqual([list(rows(result)) for result in results], [["apple-m4", "rtx-4090"]] * 3)
            self.assertEqual(results[0]["recommendation"], "apple-m4")
            self.assertEqual(rows(results[0])["rtx-4090"]["goals"]["budget"]["status"], "unknown")
            self.assertEqual(rows(results[0])["apple-m4"]["goals"]["budget"]["value"], "1199.95")
            self.assertEqual(results[1]["chart"]["x"], "budget")
            self.assertEqual(results[1]["selection"]["priority"], "prefill")

            selected = service.selection({"priority": "decode", "decode": "70"})
            result = service.evaluate(selected)
            self.assertEqual(result["recommendation"], "rtx-4090")
            self.assertEqual(result["alternatives"], ["apple-m4"])
            self.assertEqual(rows(result)["apple-m4"]["goals"]["decode"], {
                "status": "miss", "value": "64", "target": "70", "unit": "tok/s",
                "gap": "6", "reason": "6 tok/s below the minimum.",
            })
            self.assertEqual({point["id"] for point in result["chart"]["points"] if point["pareto"]},
                             {"rtx-4090", "apple-m4"})

    def test_price_withdrawal_staleness_and_exact_scope_are_never_values(self):
        def change_price(**changes):
            return lambda release_id: {**read_price(release_id), **changes}

        for price, reason in (
            (lambda release_id: {"release_id": release_id, "status": "withdrawn"}, "withdrawn"),
            (change_price(adapter_status="stale"), "stale"),
            (change_price(data_class="illustrative"), "illustrative"),
            (change_price(scope={"kind": "sku", "id": "apple-m4", "revision_id": "fixture-m4-build-v1"}),
             "whole-build revision"),
        ):
            with self.subTest(reason=reason), fixture_service(price=price) as service:
                result = service.evaluate(service.selection({"entry": "budget"}))
                quote = rows(result)["apple-m4"]["goals"]["budget"]
                self.assertIsNone(quote["value"])
                self.assertEqual(quote["status"], "unknown")
                self.assertIn(reason, quote["reason"])
                self.assertEqual(result["chart"]["points"], [])
                self.assertIsNone(result["recommendation"])

    def test_failed_quality_privacy_and_failed_runs_are_ineligible(self):
        def change_quality(record):
            if record["cell_id"] == "rtx-4090":
                record["quality_reviews"][1]["scores"]["facts"] = False

        with fixture_service(privacy="external", modify_record=change_quality) as service:
            result = service.evaluate(service.selection({}))
            checks = rows(result)
            self.assertEqual(checks["apple-m4"]["gates"]["privacy"]["status"], "ineligible")
            self.assertEqual(checks["rtx-4090"]["gates"]["quality"]["status"], "ineligible")
            self.assertEqual(result["chart"]["points"], [])
            self.assertFalse(result["alternatives"])
            result = service.evaluate(service.selection({"privacy": "allow-external"}))
            self.assertEqual(result["recommendation"], "apple-m4")

        def fail(record):
            for attempt in record["attempts"]:
                del attempt["elapsed_ns"]
                attempt.update(outcome="oom", reason="Out of memory")

        with fixture_service(modify_record=fail) as service:
            result = service.evaluate(service.selection({}))
            self.assertEqual({row["status"] for row in result["rows"]}, {"ineligible"})
            self.assertIn("Out of memory", rows(result)["apple-m4"]["gates"]["admission"]["reason"])

    def test_dominated_rows_and_table_chart_links_use_the_same_ids(self):
        def dominate(record):
            if record["cell_id"] == "rtx-4090":
                record["attempts"][0]["elapsed_ns"] = 500_000_000

        with fixture_service(modify_record=dominate) as service, server(service) as base:
            params = urlencode({"entry": "expert", "priority": "decode", "x": "prefill", "y": "decode"})
            with urlopen(f"{base}/goals?{params}", timeout=5) as response:
                pinned = urlsplit(response.url)
                html = response.read().decode()
            self.assertIn('href="#goal-apple-m4"', html)
            self.assertIn('href="#point-apple-m4"', html)
            self.assertIn('scope="row"', html)
            with urlopen(f"{base}{pinned.path}.json?{pinned.query}", timeout=5) as response:
                result = json.load(response)
            x, y = result["chart"]["x"], result["chart"]["y"]
            for point in result["chart"]["points"]:
                self.assertEqual(point["x"], rows(result)[point["id"]]["metrics"][x]["value"])
                self.assertEqual(point["y"], rows(result)[point["id"]]["metrics"][y]["value"])
            self.assertEqual([point["id"] for point in result["chart"]["points"] if point["pareto"]], ["rtx-4090"])

    def test_archived_view_retains_selection_and_rechecks_price_rights(self):
        withdrawn = False

        def price(release_id):
            return {"release_id": release_id, "status": "withdrawn"} if withdrawn else read_price(release_id)

        with fixture_service(price=price) as archived, fixture_service(privacy="external") as current:
            selection = archived.selection({"entry": "budget"})
            self.assertNotEqual(archived.release_id, current.release_id)
            with server(current, history=[archived]) as base:
                url = base + archived.url(selection, ".json")
                with urlopen(url, timeout=5) as response:
                    self.assertEqual(json.load(response)["recommendation"], "apple-m4")
                withdrawn = True
                with urlopen(url, timeout=5) as response:
                    result = json.load(response)
                self.assertEqual(result["selection"], selection)
                self.assertEqual(result["release_id"], archived.release_id)
                self.assertIsNone(result["recommendation"])
                self.assertNotIn("1199.95", json.dumps(result))

    def test_invalid_query_and_axes_return_bad_request(self):
        with server() as base:
            for query in ("decode=-1", "decode=nan", "decode=3&decode=4", "prefill=3&secret=1", "x=decode&y=decode"):
                with self.subTest(query=query), self.assertRaises(HTTPError) as error:
                    urlopen(base + "/goals?" + query, timeout=5)
                with error.exception as response:
                    self.assertEqual(response.code, 400)


if __name__ == "__main__":
    unittest.main()
