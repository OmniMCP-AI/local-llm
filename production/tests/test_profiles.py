from contextlib import closing

import http.client
import json
from threading import Thread
import unittest

from fastest_release.http import make_server


class ProfileRoutesTest(unittest.TestCase):
    def test_planned_release_has_four_reciprocal_profiles_without_measured_rows(self):
        with make_server(None, port=0) as server:
            worker = Thread(target=server.serve_forever)
            worker.start()
            try:
                with closing(http.client.HTTPConnection(*server.server_address, timeout=5)) as client:
                    def get(path):
                        client.request("GET", path)
                        response = client.getresponse()
                        return response.status, response.getheader("Location"), response.read().decode()

                    status, index_path, _ = get("/profiles")
                    self.assertEqual(status, 307)
                    self.assertRegex(index_path, r"^/profiles/v1-[a-f0-9]{16}/index\.html$")
                    status, _, index = get(index_path)
                    self.assertEqual(status, 200)
                    base = index_path.removesuffix("index.html")
                    identities = {
                        "machines": ("apple-m4", "rtx-4090"),
                        "models": ("qwen2.5-7b-instruct", "sdxl-turbo"),
                    }
                    for kind, ids in identities.items():
                        for identity in ids:
                            path = f"{base}{kind}/{identity}"
                            self.assertIn(path + ".html", index)
                            status, _, body = get(path + ".json")
                            self.assertEqual(status, 200)
                            data = json.loads(body)
                            self.assertEqual(data["profile"]["id"], identity)
                            self.assertEqual(len(data["cohorts"]), 2 if kind == "machines" else 1)
                            for cohort in data["cohorts"]:
                                self.assertEqual(cohort["ranking"], [])
                                self.assertEqual(cohort["map"], [])
                                self.assertEqual(cohort["rows"], [])
                                for exclusion in cohort["exclusions"]:
                                    self.assertEqual(exclusion["status"], "blocked")
                                    self.assertIn(base, exclusion["profile_url"])
                            status, _, html = get(path + ".html")
                            self.assertEqual(status, 200)
                            self.assertIn("No eligible measured runs", html)
                            self.assertIn("Access blocker", html)
                            status, _, markdown = get(path + ".md")
                            self.assertEqual(status, 200)
                            self.assertIn(data["release"], markdown)
                    self.assertEqual(get(base + "machines/unlisted.html")[0], 404)
            finally:
                server.shutdown()
                worker.join(timeout=5)
                self.assertFalse(worker.is_alive())
