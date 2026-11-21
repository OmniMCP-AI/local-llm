from contextlib import closing

from hashlib import sha256
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

    def test_sdxl_profile_links_to_pinned_image_pilot_and_exact_workflow(self):
        with make_server(None, port=0) as server:
            worker = Thread(target=server.serve_forever)
            worker.start()
            try:
                with closing(http.client.HTTPConnection(*server.server_address, timeout=5)) as client:
                    def get(path):
                        client.request("GET", path)
                        response = client.getresponse()
                        return response.status, response.headers, response.read()

                    _, index, _ = get("/profiles")
                    profile = index["Location"].removesuffix("index.html") + "models/sdxl-turbo"
                    for extension in ("html", "md"):
                        status, _, body = get(f"{profile}.{extension}")
                        self.assertEqual(status, 200)
                        self.assertIn(b"/image-pilot", body)

                    status, headers, _ = get("/image-pilot")
                    self.assertEqual(status, 307)
                    report = headers["Location"]
                    self.assertRegex(report, r"^/image-pilot/[a-f0-9]{64}/image-pilot\.html$")
                    base = report.removesuffix("image-pilot.html")
                    status, _, manifest = get(base + "manifest.json")
                    self.assertEqual(status, 200)
                    self.assertIn(sha256(manifest).hexdigest(), report)

                    files = {}
                    for name, digest in json.loads(manifest)["files"].items():
                        status, headers, body = get(base + name)
                        self.assertEqual(status, 200, name)
                        self.assertEqual(headers["Cache-Control"], "no-store")
                        self.assertEqual(sha256(body).hexdigest(), digest)
                        files[name] = body
                    dataset = json.loads(files["image-pilot.json"])
                    self.assertEqual(dataset["evidence_kind"], "planned")
                    self.assertEqual(dataset["protocol"]["warmup_seed"], 731000)
                    self.assertEqual(dataset["protocol"]["repeat_seeds"], [731001, 731002, 731003, 731004, 731005])
                    self.assertEqual([cell["id"] for cell in dataset["cells"]], ["apple-m4", "rtx-4090"])
                    for cell in dataset["cells"]:
                        self.assertEqual(cell["status"], "blocked")
                        self.assertIsNone(cell["metrics"]["seconds_per_accepted_image"]["value"])
                        self.assertIn(cell["blocker"].encode(), files["image-pilot.html"])
                    self.assertIn(b"Exact workflow", files["image-pilot.html"])
                    self.assertEqual(sha256(files["workflow.json"]).hexdigest(), dataset["workflow"]["sha256"])
                    self.assertEqual(get(base + "private.json")[0], 404)
            finally:
                server.shutdown()
                worker.join(timeout=5)
                self.assertFalse(worker.is_alive())

    def test_qwen_and_machine_profiles_link_to_the_pinned_text_pilot(self):
        with make_server(None, port=0) as server:
            worker = Thread(target=server.serve_forever)
            worker.start()
            try:
                with closing(http.client.HTTPConnection(*server.server_address, timeout=5)) as client:
                    def get(path):
                        client.request("GET", path)
                        response = client.getresponse()
                        return response.status, response.headers, response.read()

                    status, headers, _ = get("/text-pilot")
                    self.assertEqual(status, 307)
                    report = headers["Location"]
                    self.assertRegex(report, r"^/text-pilot/[a-f0-9]{64}/text-pilot\.html$")
                    base = report.removesuffix("text-pilot.html")
                    status, _, manifest = get(base + "manifest.json")
                    self.assertEqual(status, 200)
                    self.assertIn(sha256(manifest).hexdigest(), report)

                    hashes = json.loads(manifest)["files"]
                    self.assertEqual(set(hashes), {"text-pilot.html", "text-pilot.md", "text-pilot.json"})
                    files = {}
                    for name, digest in hashes.items():
                        status, headers, body = get(base + name)
                        self.assertEqual(status, 200, name)
                        self.assertEqual(headers["Cache-Control"], "no-store")
                        self.assertEqual(sha256(body).hexdigest(), digest)
                        files[name] = body
                    dataset = json.loads(files["text-pilot.json"])
                    self.assertEqual(dataset["evidence_kind"], "planned")
                    self.assertEqual(dataset["artifact"]["revision"], "bb5d59e06d9551d752d08b292a50eb208b07ab1f")
                    self.assertEqual(dataset["runtime"]["revision"], "84a9bf2fc2875205f0806fbbfbb66dc67204094c")
                    self.assertEqual([cell["id"] for cell in dataset["cells"]], ["apple-m4", "rtx-4090"])
                    for cell in dataset["cells"]:
                        self.assertEqual(cell["status"], "blocked")
                        self.assertEqual(cell["attempts"], [])
                        self.assertEqual(cell["quality"]["review_count"], 0)
                        self.assertEqual(set(cell["metrics"]), {"prefill", "decode", "ttft", "first_visible_answer"})
                        for metric in cell["metrics"].values():
                            self.assertEqual(metric["status"], "missing")
                            self.assertEqual(metric["sample_count"], 0)
                            self.assertIsNone(metric["value"])
                        for extension in ("html", "md"):
                            page = files[f"text-pilot.{extension}"].decode()
                            self.assertIn(cell["blocker"], page)
                            self.assertIn("事实保真", page)
                    self.assertIn(b'href="./text-pilot.md">Markdown</a>', files["text-pilot.html"])
                    self.assertEqual(get(base + "private.json")[0], 404)

                    _, index, _ = get("/profiles")
                    profile_base = index["Location"].removesuffix("index.html")
                    for profile in ("models/qwen2.5-7b-instruct", "machines/apple-m4", "machines/rtx-4090"):
                        for extension in ("html", "md"):
                            status, _, body = get(f"{profile_base}{profile}.{extension}")
                            self.assertEqual(status, 200)
                            self.assertIn(b"/text-pilot", body)
            finally:
                server.shutdown()
                worker.join(timeout=5)
                self.assertFalse(worker.is_alive())
