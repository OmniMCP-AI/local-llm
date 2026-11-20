import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PRODUCTION = Path(__file__).resolve().parents[1]
FIXTURES = PRODUCTION / "fixtures" / "discoveries"
ORIGINAL = "https://forum.example/topics/local-models/18"
SOURCE_DATE = "2026-11-19T12:30:00Z"
CROSS_POST = "https://video.example/watch/local-models-repost"
DISCOVERY_ONLY = "https://social.example/posts/63"
DELETED = "https://forum.example/topics/local-models/24"


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="fastest-discoveries-22-")))
        self.database = self.directory / "discoveries.sqlite3"

    def run_cli(self, *args, succeeds=True):
        result = subprocess.run(
            [sys.executable, "-B", "-m", "fastest_discoveries", "--db", self.database, *args],
            cwd=PRODUCTION, capture_output=True, text=True, timeout=10,
        )
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result.stderr

    def test_attributed_submission_is_private_until_approved(self):
        first = self.run_cli("submit", FIXTURES / "original.json")
        self.assertEqual(self.run_cli("submit", FIXTURES / "original.json"), first)
        candidate, = self.run_cli("queue")["entries"]
        self.assertEqual(candidate["source_url"], ORIGINAL)
        self.assertEqual(candidate["original_url"], ORIGINAL)
        self.assertEqual(candidate["published_at"], SOURCE_DATE)
        self.assertEqual(candidate["consent"]["authority"], "rights_holder")
        self.assertEqual(candidate["consent"]["reference"], "fixture-original-grant")
        self.assertEqual(candidate["status"], "pending")
        self.assertEqual(self.run_cli("public")["entries"], [])

        decision = self.review(ORIGINAL, "approve")
        self.assertEqual(decision["choice"], "approve")
        self.assertEqual(self.run_cli("public")["entries"], [{
            "status": "approved", "reason": "source_link_approved",
            "source_url": ORIGINAL, "published_at": SOURCE_DATE,
        }])

    def review(self, source, choice, *, succeeds=True):
        return self.run_cli(
            "review", source, choice, "--reviewer", "fixture-editor",
            "--reason", "Reviewed public permalink and opt-in.", succeeds=succeeds,
        )

    def test_cross_post_points_to_original_and_never_publishes_twice(self):
        self.run_cli("submit", FIXTURES / "cross-post.json")
        duplicate, = self.run_cli("queue")["entries"]
        self.assertEqual((duplicate["source_url"], duplicate["original_url"]), (CROSS_POST, ORIGINAL))
        self.assertEqual(duplicate["reason"], "cross_post")
        self.assertIn("cross_post", self.review(CROSS_POST, "approve", succeeds=False))

        self.run_cli("submit", FIXTURES / "original.json")
        self.review(ORIGINAL, "approve")
        self.assertEqual(self.run_cli("public")["entries"], [
            {"status": "approved", "reason": "source_link_approved", "source_url": ORIGINAL,
             "published_at": SOURCE_DATE},
            {"status": "withheld", "reason": "cross_post"},
        ])

    def test_discovery_only_is_attributed_internally_and_withheld_publicly(self):
        self.run_cli("submit", FIXTURES / "discovery-only.json")
        restricted, = self.run_cli("queue")["entries"]
        self.assertEqual(restricted["source_url"], DISCOVERY_ONLY)
        self.assertIsNone(restricted["published_at"])
        self.assertEqual(restricted["consent"]["scope"], "discovery_only")
        self.assertIn("discovery_only", self.review(DISCOVERY_ONLY, "approve", succeeds=False))
        self.review(DISCOVERY_ONLY, "withhold")
        self.assertEqual(self.run_cli("public")["entries"], [
            {"status": "withheld", "reason": "discovery_only"},
        ])

    def test_deleted_source_suppresses_a_previous_approval_after_replay(self):
        self.run_cli("submit", FIXTURES / "deleted.json")
        prior = self.review(DELETED, "approve")
        self.assertEqual(self.run_cli("public")["entries"][0]["source_url"], DELETED)

        withdrawal = self.run_cli("withdraw", DELETED, "--reason", "source_deleted")
        self.assertEqual(self.run_cli("withdraw", DELETED, "--reason", "source_deleted"), withdrawal)
        self.run_cli("submit", FIXTURES / "deleted.json")
        self.assertEqual(self.review(DELETED, "approve"), prior)

        deleted, = self.run_cli("queue")["entries"]
        self.assertEqual(deleted["review"]["choice"], "approve")
        self.assertEqual(deleted["withdrawal"]["reason"], "source_deleted")
        self.assertEqual(self.run_cli("public")["entries"], [
            {"status": "withheld", "reason": "source_deleted"},
        ])

    def test_review_cannot_be_replaced_or_publish_the_editor_note(self):
        self.run_cli("submit", FIXTURES / "original.json")
        decision = self.review(ORIGINAL, "withhold")
        self.assertEqual(self.review(ORIGINAL, "withhold"), decision)
        self.assertIn("immutable", self.review(ORIGINAL, "approve", succeeds=False))
        self.assertEqual(self.run_cli("queue")["entries"][0]["review"]["reason"], decision["reason"])
        self.assertEqual(self.run_cli("public")["entries"], [
            {"status": "withheld", "reason": "editor_withheld"},
        ])

    def test_submission_requires_explicit_scope_and_excludes_private_payload(self):
        valid = json.loads((FIXTURES / "original.json").read_text(encoding="utf-8"))
        draft = self.directory / "submission.json"
        for invalid in (
            {**valid, "consent": {**valid["consent"], "scope": "unknown"}},
            {**valid, "consent": {**valid["consent"], "authority": "anonymous"}},
            {**valid, "body": "private body"},
            {**valid, "source_url": "https://forum.example/topics/18?token=secret"},
            {**valid, "source_url": "https://forum.example/topics/18#access_token=secret"},
        ):
            draft.write_text(json.dumps(invalid), encoding="utf-8")
            self.run_cli("submit", draft, succeeds=False)
        conflicting_scope = json.dumps(valid).replace(
            '"scope": "public_source_link"',
            '"scope": "discovery_only", "scope": "public_source_link"',
        )
        draft.write_text(conflicting_scope, encoding="utf-8")
        self.assertIn("duplicate", self.run_cli("submit", draft, succeeds=False))
        self.assertEqual(self.run_cli("queue")["entries"], [])


if __name__ == "__main__":
    unittest.main()
