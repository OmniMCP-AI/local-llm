from contextlib import closing, contextmanager
import http.client
import json
from threading import Thread
import unittest

from fastest_release.http import make_server


@contextmanager
def api_client(store=None, **settings):
    with make_server(store, port=0, **settings) as server:
        worker = Thread(target=server.serve_forever)
        worker.start()
        try:
            with closing(http.client.HTTPConnection(*server.server_address, timeout=5)) as client:
                def request(path, method="GET", *, decode=True):
                    client.request(method, path)
                    response = client.getresponse()
                    body = response.read().decode()
                    return response.status, response.headers, json.loads(body) if decode and body else body

                yield request
        finally:
            server.shutdown()
            worker.join(timeout=5)
            if worker.is_alive():
                raise RuntimeError("API test did not stop its HTTP listener")


class PublicApiTest(unittest.TestCase):
    def test_search_pages_are_revision_pinned_and_only_live_operations_are_discoverable(self):
        with api_client() as request:
            status, headers, page = request("/api/v1/search?kind=machines&limit=1")
            self.assertEqual(status, 200)
            self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual([entry["id"] for entry in page["results"]], ["apple-m4"])
            self.assertEqual(page["pagination"]["next_offset"], 1)
            revision = page["revision"]
            status, _, second = request(f"/api/v1/search?kind=machines&limit=1&offset=1&revision={revision}")
            self.assertEqual(status, 200)
            self.assertEqual([entry["id"] for entry in second["results"]], ["rtx-4090"])
            self.assertIsNone(second["pagination"]["next_offset"])
            status, _, site = request(second["results"][0]["url"], decode=False)
            self.assertEqual(status, 200)
            self.assertIn(revision, site)

            for query in ("limit=0", "limit=101", "offset=10001", "limit=1&limit=2", "sql=SELECT"):
                self.assertEqual(request("/api/v1/search?" + query)[0], 400)

            status, headers, description = request("/.well-known/api-catalog")
            self.assertEqual(status, 200)
            self.assertEqual(headers.get_content_type(), "application/linkset+json")
            spec_path = description["linkset"][0]["service-desc"][0]["href"]
            status, _, spec = request(spec_path)
            self.assertEqual(status, 200)
            self.assertEqual(spec["openapi"], "3.1.0")
            self.assertIn("/api/v1/search", spec["paths"])
            self.assertNotIn("/api/v1/historical-offers", spec["paths"])
            self.assertNotIn("/api/v1/evidence", spec["paths"])
            self.assertEqual(request("/api/v1/search", "HEAD")[2], "")
            self.assertEqual(request("/api/v1/search", "POST", decode=False)[0], 501)

    def test_comparisons_preserve_unknowns_and_share_site_revisions(self):
        with api_client() as request:
            status, _, coverage = request("/api/v1/coverage?kind=models&id=qwen2.5-7b-instruct&limit=1")
            self.assertEqual(status, 200)
            self.assertEqual(coverage["cohorts"][0]["metrics"]["llama-bench-decode"]["unit"], "tok/s")
            self.assertEqual(coverage["results"][0]["status"], "blocked")
            self.assertEqual(coverage["pagination"]["next_offset"], 1)
            revision = coverage["revision"]
            query = f"?revision={revision}&kind=models&id=qwen2.5-7b-instruct"
            status, _, comparison = request("/api/v1/comparison/profile" + query)
            self.assertEqual(status, 200)
            self.assertEqual(comparison["revision"], revision)
            self.assertEqual([entry["type"] for entry in comparison["results"]], ["exclusion", "exclusion"])
            self.assertIn("No eligible measured runs", request(comparison["url"], decode=False)[2])

            status, _, goals = request("/api/v1/comparison?entry=budget&budget=1200")
            self.assertEqual(status, 200)
            self.assertIsNone(goals["recommendation"])
            self.assertEqual(goals["metrics"]["budget"]["unit"], "USD")
            self.assertEqual(goals["rows"][0]["goals"]["budget"]["status"], "unknown")
            self.assertIsNone(goals["rows"][0]["goals"]["budget"]["value"])
            status, _, html = request(goals["url"], decode=False)
            self.assertEqual(status, 200)
            self.assertIn(goals["release_id"], html)
            self.assertIn(goals["rows"][0]["goals"]["budget"]["reason"], html)
            self.assertEqual(request(f"/api/v1/comparison?revision={goals['release_id']}&entry=budget&budget=1200")[2],
                             goals)

    def test_calculator_reproduces_decimal_costs_and_labels_illustrative_inputs(self):
        with api_client() as request:
            status, _, result = request("/api/v1/calculator?scenario=illustrative")
            self.assertEqual(status, 200)
            self.assertEqual(result["estimate_kind"], "illustrative")
            self.assertEqual(result["units"]["money"], "USD")
            self.assertEqual(result["options"]["upgrade"]["totals"]["nominal_cost"], "589.472")
            self.assertEqual(result["options"]["api"]["monthly"]["recurring_cost"], "4.1984")
            self.assertTrue(result["citations"])
            _, _, html = request(result["url"], decode=False)
            self.assertIn(result["revision"], html)
            self.assertIn("589.472", html)

            status, _, unknown = request("/api/v1/calculator")
            self.assertEqual(status, 200)
            self.assertIsNone(unknown["options"]["upgrade"]["totals"]["nominal_cost"])
            self.assertIn("missing_same_task_service_evidence", unknown["exclusions"]["upgrade"])
            self.assertEqual(request("/api/v1/calculator?months=121")[0], 400)
            self.assertEqual(request(f"/api/v1/calculator?revision={result['revision']}")[0], 404)
