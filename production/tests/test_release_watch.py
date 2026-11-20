import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PRODUCTION = Path(__file__).resolve().parents[1]
REPOSITORY = "ggml-org/llama.cpp"
DAY_ONE = "2026-11-20T01:00:00Z"
DAY_TWO = "2026-11-21T01:00:00Z"


def github_release(release_id, tag, published_at, *, body="Original notes", prerelease=False):
    return {
        "id": release_id,
        "tag_name": tag,
        "url": f"https://api.github.com/repos/{REPOSITORY}/releases/{release_id}",
        "html_url": f"https://github.com/{REPOSITORY}/releases/tag/{tag}",
        "name": tag,
        "published_at": published_at,
        "draft": False,
        "prerelease": prerelease,
        "immutable": False,
        "target_commitish": "master",
        "body": body,
        "assets": [],
    }


class ReleaseWatchTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="release-watch-20-")))
        self.database = self.directory / "watch.sqlite3"
        self.feed = self.directory / "feed.json"

    def invoke(self, *options):
        return subprocess.run(
            [sys.executable, "-B", "-m", "fastest_release_watch", "--db", self.database, *options],
            cwd=PRODUCTION,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def refresh(self, rows, at, *, success=True):
        self.feed.write_text(json.dumps(rows), encoding="utf-8")
        result = self.invoke("refresh", "--fixture", self.feed, "--observed-at", at)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def report(self, as_of=DAY_TWO, *options):
        result = self.invoke("report", "--as-of", as_of, *options)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_repeat_and_older_replay_preserve_revision_identity_and_last_success(self):
        older = github_release(100, "fixture-b1", "2026-11-19T01:00:00Z")
        edited = {**older, "body": "<script>raw release text</script>"}
        newer = github_release(101, "fixture-b2", DAY_TWO)
        preview = github_release(102, "fixture-b3", DAY_TWO, prerelease=True)

        self.refresh([older], DAY_ONE)
        original = self.report()["releases"][0]["revision_id"]
        self.refresh([edited, newer, preview], DAY_TWO)
        updated = self.report()
        self.refresh([preview, edited, newer], DAY_TWO)
        self.refresh([older], DAY_ONE)
        self.assertEqual(self.report(), updated)
        self.assertEqual(updated["last_successful_refresh"], DAY_TWO)
        self.assertEqual(updated["source"]["mode"], "fixture")
        self.assertEqual(
            [(r["tag"], r["status"]) for r in updated["releases"]],
            [("fixture-b3", "prerelease"), ("fixture-b2", "current"),
             ("fixture-b1", "superseded_release"), ("fixture-b1", "superseded_revision")],
        )
        self.assertEqual(updated["releases"][-1]["revision_id"], original)
        self.assertEqual(updated["releases"][-1]["source_url"],
                         "https://github.com/ggml-org/llama.cpp/releases/tag/fixture-b1")
        self.assertNotIn("raw release text", json.dumps(updated))

    def test_bad_feed_attempt_keeps_last_success_and_flags_stale_history(self):
        release = github_release(100, "fixture-b1", DAY_ONE)
        self.refresh([release], DAY_ONE)
        first_snapshot = self.report(DAY_ONE)
        self.assertFalse(first_snapshot["stale"])
        bad_release = {**github_release(101, "fixture-b2", DAY_TWO), "url": "https://other.example/releases/101"}
        self.refresh([github_release(102, "fixture-b3", DAY_TWO), bad_release], DAY_TWO, success=False)

        failed = self.report("2026-11-21T01:00:01Z")
        self.assertEqual(failed["last_successful_refresh"], DAY_ONE)
        self.assertEqual(failed["last_attempt"], DAY_TWO)
        self.assertIn("official llama.cpp", failed["last_error"])
        self.assertTrue(failed["stale"])
        self.assertEqual(failed["releases"], first_snapshot["releases"])

    def test_official_request_rejects_redirects_without_following_them(self):
        import io
        from unittest.mock import patch

        from fastest_release_watch.feed import fetch

        with patch("http.client.HTTPSConnection") as transport:
            connection = transport.return_value
            connection.getresponse.return_value = io.BytesIO(b"")
            connection.getresponse.return_value.status = 302
            with self.assertRaisesRegex(ValueError, "HTTP 302"):
                fetch()
            connection.request.assert_called_once()
            self.assertEqual(connection.request.call_args.args,
                             ("GET", "/repos/ggml-org/llama.cpp/releases?per_page=10&page=1"))

    def test_authored_note_links_only_the_named_card_configuration_and_revision(self):
        release = github_release(100, "fixture-b1", DAY_ONE)
        self.refresh([release], DAY_ONE)
        original = self.report()["releases"][0]["revision_id"]
        self.refresh([{**release, "body": "Revised notes"}], DAY_TWO)
        path = self.directory / "notes.json"
        note = {
            "id": "fixture-offload",
            "revision_id": original,
            "card_id": "nvidia-geforce-rtx-3060",
            "source_url": "https://github.com/ggml-org/llama.cpp/tree/1111111111111111111111111111111111111111",
            "source_label": "Synthetic fixture source",
            "status": "suggested",
            "technique": "Try <script>alert(1)</script> partial offload",
            "prerequisites": "Native CUDA build",
            "limits": "One 12 GiB board variant only",
            "failure_modes": "Allocation can fail",
            "configuration": {
                "id": "fixture-ubuntu24-3060-12gb",
                "variant": "GeForce RTX 3060 12 GiB",
                "os": "Ubuntu 24.04.1",
                "driver": "550.120",
                "backend": "CUDA",
                "build_sha": "1111111111111111111111111111111111111111",
                "flags": ["--gpu-layers", "20"],
                "workload_id": "solo-decode",
                "workload_version": 1,
                "model_artifact": "fixture/model@revision/configured.gguf",
            },
        }
        path.write_text(json.dumps({"notes": [note]}), encoding="utf-8")
        report = self.report(DAY_TWO, "--notes", path)
        revised, older = report["releases"]
        self.assertEqual(revised["applicability"], [])
        application = older["applicability"][0]
        self.assertEqual(application["card"]["id"], "nvidia-geforce-rtx-3060")
        self.assertEqual(application["configuration"], note["configuration"])
        self.assertEqual(application["status"], "suggested")
        self.assertEqual(older["status"], "superseded_revision")
        self.assertEqual(application["source_url"], note["source_url"])
        self.assertEqual(application["build_url"],
                         "https://github.com/ggml-org/llama.cpp/commit/1111111111111111111111111111111111111111")

        for format_name in ("html", "markdown"):
            with self.subTest(format=format_name):
                rendered = self.invoke("report", "--as-of", DAY_TWO, "--notes", path, "--format", format_name)
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                self.assertIn("NVIDIA GeForce RTX 3060", rendered.stdout)
                self.assertIn("550.120", rendered.stdout)
                self.assertIn("Superseded revision", rendered.stdout)
                self.assertIn("Suggested", rendered.stdout)
                self.assertNotIn("<script>", rendered.stdout)

        for correction in ({"card_id": "any-rtx"}, {"revision_id": "unknown"}, {"measured_gain": "10%"},
                           {"status": "fastest_ai_verified"}, {"source_url": "javascript:alert(1)"}):
            with self.subTest(correction=correction):
                path.write_text(json.dumps({"notes": [{**note, **correction}]}), encoding="utf-8")
                rejected = self.invoke("report", "--as-of", DAY_TWO, "--notes", path)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(rejected.stdout, "")

    def test_only_measured_retests_with_matching_conditions_are_linked(self):
        from copy import deepcopy

        from fastest_release_watch.retest import approved_links

        first_id = "3a76f0db-50f3-40c7-a31e-377fe32361b3"
        second_id = "39779f33-5941-4d7a-855b-949c4cee3aa9"
        pair = {"baseline_release_id": first_id, "tuned_release_id": second_id}
        config = {
            "id": "config-3060",
            "os": "Ubuntu 24.04",
            "driver": "550.120",
            "backend": "CUDA",
            "build_sha": "1" * 40,
            "flags": ["--gpu-layers", "20"],
            "workload_id": "solo-decode",
            "workload_version": 1,
            "model_artifact": "fastest-ai/fixture-model@synthetic-v1/production/fixtures/synthetic-artifact.txt",
        }
        note = {"card_id": "nvidia-geforce-rtx-3060", "configuration": config}
        row = json.loads((PRODUCTION / "fixtures/synthetic-observation.json").read_text(encoding="utf-8"))
        row["kind"] = "measured"
        row["fields"] = {
            key: {"status": "known", "value": value}
            for key, value in {
                "card_id": note["card_id"], "configuration_id": config["id"], "os_version": config["os"],
                "driver_version": config["driver"], "backend": config["backend"],
                "runtime_build": config["build_sha"], "runtime_id": "llama.cpp",
                "runtime_flags": '["--gpu-layers", "0"]',
            }.items()
        }
        tuned = deepcopy(row)
        tuned["evidence_id"] = "8e285620-7a53-4d83-a30e-9fa48a707475"
        tuned["metric"]["value"] = "43.5"
        tuned["fields"]["runtime_flags"]["value"] = '["--gpu-layers", "20"]'
        published = {
            first_id: {"release_id": first_id, "status": "published", "row": row},
            second_id: {"release_id": second_id, "status": "published", "row": tuned},
        }
        self.assertEqual(
            approved_links(published.__getitem__, note, pair, "https://benchmark.example"),
            {
                "baseline_url": "https://benchmark.example/releases/3a76f0db-50f3-40c7-a31e-377fe32361b3/benchmark.html",
                "tuned_url": "https://benchmark.example/releases/39779f33-5941-4d7a-855b-949c4cee3aa9/benchmark.html",
            },
        )
        tuned["fields"]["driver_version"]["value"] = "560.120"
        with self.assertRaisesRegex(ValueError, "matched"):
            approved_links(published.__getitem__, note, pair, "https://benchmark.example")
        published[second_id] = {"release_id": second_id, "status": "withdrawn"}
        with self.assertRaisesRegex(ValueError, "published measured"):
            approved_links(published.__getitem__, note, pair, "https://benchmark.example")
