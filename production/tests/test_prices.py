from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from threading import Thread
import time
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen
from uuid import uuid4

from fastest_prices import PriceError, PriceStore
from test_goals import fixture_service
from test_public_api import api_client


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic-price-cohort.json"


class PriceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        work = Path(cls.enterClassContext(tempfile.TemporaryDirectory(prefix="fastest-price-pg-", dir="/tmp")))
        db = work / "db"
        subprocess.run(
            ["initdb", "-D", str(db), "--auth=trust", "--encoding=UTF8", "--no-locale"],
            check=True, capture_output=True,
        )
        with (work / "postgres.log").open("w") as log:
            postgres = subprocess.Popen(
                ["postgres", "-D", str(db), "-k", str(work), "-c", "listen_addresses="],
                stdout=log, stderr=subprocess.STDOUT,
            )
        cls.addClassCleanup(cls.stop_postgres, postgres)
        cls.database_url = f"host={work} dbname=postgres"
        for _ in range(100):
            if subprocess.run(["pg_isready", "-d", cls.database_url], capture_output=True).returncode == 0:
                break
            if postgres.poll() is not None:
                raise RuntimeError((work / "postgres.log").read_text())
            time.sleep(0.05)
        else:
            raise RuntimeError("PostgreSQL did not start")
        cls.store = PriceStore(cls.database_url)
        cls.store.migrate()

    @staticmethod
    def stop_postgres(postgres):
        if postgres.returncode is None:
            postgres.send_signal(signal.SIGINT)
            try:
                postgres.wait(timeout=10)
            except subprocess.TimeoutExpired:
                postgres.send_signal(signal.SIGQUIT)
                postgres.wait(timeout=10)

    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.cohort = self.fixture["cohort"]
        self.cohort["id"] = self._testMethodName

    def test_only_reviewed_exact_scope_can_enter_a_dated_release(self):
        disallowed = deepcopy(self.cohort)
        disallowed["authorization"]["display"] = "pending"
        with self.assertRaisesRegex(PriceError, "display"):
            self.store.approve(disallowed)

        self.store.approve(self.cohort)
        capture = self.fixture["captures"][0]
        wrong_scope = deepcopy(capture)
        wrong_scope["observations"][0]["scope"]["revision_id"] = "another-revision"
        with self.assertRaisesRegex(PriceError, "scope"):
            self.store.capture(self.cohort["id"], wrong_scope)

        expected = self.store.capture(self.cohort["id"], capture)
        self.assertEqual(self.store.capture(self.cohort["id"], capture), expected)
        as_of = "2026-11-04"
        first = self.store.publish(self.cohort["id"], "2026-11-01", as_of)
        self.assertEqual(self.store.publish(self.cohort["id"], "2026-11-01", as_of), first)
        result = self.store.read(first)
        self.assertEqual(result["data_class"], "illustrative")
        self.assertEqual(result["offers"][0]["source_locator"], "example-feed/2026-11-01/offer-a")
        self.assertEqual(result["offers"][0]["price"], "240.00")
        self.assertEqual(result["offers"][0]["currency"], "USD")
        self.assertEqual(result["offers"][0]["kind"], "asking")
        self.assertIsNone(result["offers"][0]["shipping"]["amount"])
        self.assertNotIn("authorization-file", json.dumps(result))

        amended = deepcopy(capture)
        amended["id"] = "morning-correction"
        amended["checked_at"] = "2026-11-01T14:00:00Z"
        amended["observations"][0]["observed_at"] = "2026-11-01T13:30:00Z"
        amended["observations"][0]["price"] = "241.00"
        self.store.capture(self.cohort["id"], amended)
        second = self.store.publish(self.cohort["id"], "2026-11-01", as_of)
        self.assertNotEqual(second, first)
        self.assertEqual(self.store.read(first), result)
        self.assertEqual(self.store.read(second)["offers"][0]["price"], "241.00")

    def test_reviewed_price_citations_replay_without_entering_offers(self):
        from fastest_prices.refresh import register

        product_url = "https://reference.example.test/product/example-accelerator-16"
        cohort = {
            **{key: self.cohort[key] for key in ("id", "source_id", "source_revision", "scope")},
            "source_type": "citation", "data_class": "reviewed_citations", "market": "CN", "currency": "CNY",
            "source_name": "Fixture Price Monitor", "source_locator": product_url, "price_basis": "post_coupon",
            "authorization": {**self.cohort["authorization"], "aggregate": "deny"},
        }
        capture = {
            "id": "review-1", "source_id": cohort["source_id"], "source_revision": cohort["source_revision"],
            "checked_at": "2026-11-03T13:00:00Z", "status": "success",
            "references": [{"observed_on": "2026-11-01", "marketplace": "Fixture Marketplace", "price": "812.30"}],
        }
        with self.assertRaisesRegex(PriceError, "aggregate"):
            self.store.approve({**cohort, "authorization": {**cohort["authorization"], "aggregate": "allow"}})
        self.store.ingest({"cohort": cohort, "captures": [capture]})
        self.assertEqual(self.store.capture(cohort["id"], capture), self.store.capture(cohort["id"], capture))
        with self.assertRaisesRegex(PriceError, "Capture type"):
            self.store.capture(cohort["id"], self.fixture["captures"][0])
        with self.assertRaisesRegex(PriceError, "exactly these fields"):
            reference = {**capture["references"][0], "seller": "invented seller"}
            self.store.capture(cohort["id"], {**capture, "references": [reference]})
        early = self.store.publish(cohort["id"], "2026-11-01", "2026-11-02")
        self.assertEqual(self.store.read(early)["references"], [])
        late = self.store.publish(cohort["id"], "2026-11-02", "2026-11-04")
        self.assertEqual(self.store.read(late)["references"], [])
        with self.assertRaisesRegex(PriceError, "one reviewed capture"):
            self.store.capture(cohort["id"], {**capture, "id": "later-capture"})
        with self.assertRaisesRegex(PriceError, "direct seller"):
            register(self.store, cohort["id"], {
                "url": "https://reference.example.test/feed", "minimum_interval_seconds": 120, "max_pages": 2,
            })

        release_id = self.store.publish(cohort["id"], "2026-11-01", "2026-11-04")
        payload = json.loads(self.store.artifact(release_id, "prices.json"))
        self.assertEqual(payload["offers"], [])
        self.assertIsNone(payload["sampling"]["median"])
        self.assertEqual(payload["sampling"]["range_status"], "rights_restricted")
        self.assertEqual(payload["source_locator"], product_url)
        self.assertEqual(payload["currency"], "CNY")
        self.assertEqual(payload["price_basis"], "post_coupon")
        reference, = payload["references"]
        self.assertEqual({key: reference[key] for key in capture["references"][0]}, capture["references"][0])
        for field in ("seller", "checkout_url", "landed_price", "tax", "shipping", "stock", "discount"):
            self.assertIsNone(reference[field], field)
        for field in ("destination", "condition"):
            self.assertIsNone(payload[field], field)
        for name in ("prices.html", "prices.md"):
            artifact = self.store.artifact(release_id, name)
            for expected in ("Historical price references", "Fixture Price Monitor", "2026-11-01", "812.30 CNY",
                             product_url, "Unknown", "post-coupon"):
                self.assertIn(expected, artifact)
            self.assertNotIn("authorization-file", artifact)
            self.assertNotIn("Comparable observed quotes", artifact)
        with api_client(price_reader=self.store.read) as request:
            status, _, served = request(f"/price-releases/{release_id}/prices.json")
            self.assertEqual(status, 200)
            self.assertEqual(served, payload)
            self.assertEqual(request(f"/api/v1/historical-offers?release={release_id}")[0], 404)
        self.store.withdraw(cohort["id"], "private citation withdrawal reason")
        self.assertNotIn("references", self.store.read(release_id))
        self.assertNotIn(product_url, self.store.artifact(release_id, "prices.html"))

    def test_dated_surfaces_preserve_gaps_freshness_and_quote_semantics(self):
        self.store.approve(self.cohort)
        for capture in self.fixture["captures"]:
            self.store.capture(self.cohort["id"], capture)

        result_id = self.store.publish(self.cohort["id"], "2026-11-01", "2026-11-04")
        result = json.loads(self.store.artifact(result_id, "prices.json"))
        self.assertEqual(result["result_type"], "regional-price-cohort")
        self.assertEqual(result["sampling"]["seller_count"], 1)
        self.assertEqual(result["sampling"]["sample_count"], 1)
        self.assertEqual(result["sampling"]["range_status"], "below_threshold")
        self.assertIsNone(result["sampling"]["median"])
        self.assertIsNone(result["sampling"]["q1"])
        self.assertIsNone(result["sampling"]["q3"])
        self.assertEqual(result["last_success_at"], "2026-11-03T13:00:00Z")
        self.assertEqual(result["adapter_status"], "fresh")
        self.assertEqual([day["status"] for day in result["days"]], [
            "no_comparable_offer", "capture_failed", "observed", "not_checked",
        ])
        self.assertEqual([offer["seller"] for offer in result["offers"]], ["example-seller"] * 2)
        self.assertEqual([offer["age_days"] for offer in result["offers"]], [3, 1])
        self.assertEqual([offer["freshness"] for offer in result["offers"]], ["stale", "fresh"])
        self.assertEqual([offer["latest_for_listing"] for offer in result["offers"]], [False, True])
        self.assertEqual([offer["landed_price"] for offer in result["offers"]], [None, "253.80"])

        for filename in ("prices.md", "prices.html"):
            with self.subTest(filename=filename):
                artifact = self.store.artifact(result_id, filename)
                for value in (
                    result_id, "Illustrative", "240.00", "235.00", "253.80",
                    "2026-11-02", "Capture failed", "2026-11-04", "Not checked",
                    "unknown", "example-feed/2026-11-01/offer-a", "Withheld",
                ):
                    self.assertIn(value, artifact)
                self.assertNotIn("illustrative-authorization-file", artifact)

    def test_recurring_feed_replays_and_recovers_without_filling_history_gaps(self):
        from fastest_prices.refresh import register, refresh

        def offer(event_id, version, observed_at, amount, expires_at):
            quote = deepcopy(self.fixture["captures"][2]["observations"][0])
            quote.update(price=amount, observed_at=observed_at, expires_at=expires_at)
            return {"id": event_id, "version": version, "offer": quote}

        original = offer("nov-01", 2, "2026-11-01T12:00:00Z", "240.00", "2026-11-02T00:00:00Z")
        correction = offer("nov-01", 3, "2026-11-01T12:00:00Z", "241.00", "2026-11-02T00:00:00Z")
        renewed = offer("nov-04", 1, "2026-11-04T12:00:00Z", "225.00", "2026-11-06T00:00:00Z")
        self.cohort["data_class"] = "authorized_observations"
        self.store.approve(self.cohort)
        key = self.cohort["id"]
        register(self.store, key, {
            "url": "https://seller.example.test/reviewed-prices",
            "minimum_interval_seconds": 300,
            "max_pages": 3,
        })

        def deliver(day, steps):
            expected = iter(steps)

            def fetch_page(cursor):
                expected_cursor, outcome = next(expected)
                self.assertEqual(cursor, expected_cursor)
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome

            result = refresh(self.store, key, fetch_page, checked_at=f"2026-11-{day:02}T13:00:00Z")
            self.assertEqual(list(expected), [])
            return result

        def page(cursor, complete, *rows):
            return {"cursor": cursor, "complete": complete, "observations": list(rows)}

        def release(day):
            release_id = self.store.publish(key, "2026-11-01", f"2026-11-{day:02}")
            result = json.loads(self.store.artifact(release_id, "prices.json"))
            return result, self.store.artifact(release_id, "prices.html")

        first = deliver(1, [(None, page("one", True, original, original))])
        self.assertEqual(first["status"], "success")
        self.assertEqual(first["observations_recorded"], 1)
        before, _ = release(1)
        self.assertEqual(before["offers"][0]["availability"], "available")

        interrupted = deliver(2, [
            ("one", page("partial", False, correction)),
            ("partial", OSError("fixture connection interrupted")),
        ])
        self.assertEqual(interrupted["status"], "incomplete")
        pending, html = release(2)
        self.assertEqual(pending["adapter_status"], "incomplete")
        self.assertEqual(pending["last_success_at"], "2026-11-01T13:00:00Z")
        self.assertEqual(pending["offers"][0]["price"], "240.00")
        self.assertEqual(pending["offers"][0]["availability"], "expired")
        self.assertEqual(pending["days"][1]["status"], "capture_incomplete")
        self.assertIn("Capture incomplete", html)
        self.assertIn("Expired", html)

        recovered = deliver(4, [
            ("one", page("partial", False, correction)),
            ("partial", page("four", True, original, renewed)),
        ])
        self.assertEqual(recovered["status"], "success")
        self.assertEqual(recovered["observations_recorded"], 2)
        current, html = release(4)
        self.assertEqual(current["adapter_status"], "fresh")
        self.assertEqual([row["status"] for row in current["days"]], [
            "observed", "capture_incomplete", "not_checked", "observed",
        ])
        self.assertEqual([row["price"] for row in current["offers"]], ["241.00", "225.00"])
        self.assertEqual([row["availability"] for row in current["offers"]], ["expired", "available"])
        chart = html.split('aria-label="Dated seller-day price dots"', 1)[1].split("</svg>", 1)[0]
        self.assertEqual(chart.count("<circle "), 2)
        for item in current["offers"]:
            title = f"Quote date (UTC): {item['observed_at'][:10]} · Landed price: {item['landed_price']} USD"
            self.assertIn(title, chart)
        with api_client(price_reader=self.store.read) as request:
            status, _, historical = request(f"/api/v1/historical-offers?release={current['release_id']}")
            self.assertEqual(status, 200)
            self.assertTrue(historical["offers"][0]["comparable_asking_quote"])
            self.assertEqual(historical["offers"][0]["availability"], "expired")
            self.assertEqual(historical["offers"][0]["expires_at"], "2026-11-02T00:00:00Z")
        self.assertEqual(self.store.read(before["release_id"]), before)
        self.assertEqual(self.store.read(pending["release_id"]), pending)

        repeated = deliver(5, [("four", page("five", True, original, correction, renewed))])
        self.assertEqual(repeated["observations_recorded"], 0)
        older = offer("nov-01", 1, "2026-11-01T12:00:00Z", "234.00", "2026-11-02T00:00:00Z")
        self.assertEqual(deliver(6, [("five", page("six", True, older))])["observations_recorded"], 1)
        caught_up, _ = release(6)
        self.assertEqual([row["price"] for row in caught_up["offers"]], ["241.00", "225.00"])
        stale, _ = release(9)
        self.assertEqual(stale["adapter_status"], "stale")
        self.assertEqual(stale["offers"][-1]["availability"], "expired")

    def test_recurring_feed_checks_rights_and_persists_quota_and_retry_after(self):
        from fastest_prices.refresh import RateLimited, register, refresh

        key = self.cohort["id"]
        config = {
            "url": "https://seller.example.test/reviewed-prices",
            "minimum_interval_seconds": 300,
            "max_pages": 1,
        }
        with self.assertRaisesRegex(PriceError, "approval is missing"):
            register(self.store, key, config)
        self.store.approve(self.cohort)
        register(self.store, key, config)
        with self.assertRaisesRegex(PriceError, "authorized observations"):
            refresh(self.store, key)

        def partial(cursor):
            self.assertIsNone(cursor)
            return {"cursor": "page-two", "complete": False, "observations": []}

        def limited(cursor):
            self.assertIsNone(cursor)
            raise RateLimited("3600")

        def unexpected(cursor):
            self.fail("A deferred or denied refresh contacted the feed")

        quota = refresh(self.store, key, partial, checked_at="2026-11-01T13:00:00Z")
        self.assertEqual((quota["status"], quota["reason"]), ("incomplete", "request_quota"))
        self.assertEqual(
            refresh(self.store, key, unexpected, checked_at="2026-11-01T13:01:00Z")["status"], "deferred",
        )
        backoff = refresh(self.store, key, limited, checked_at="2026-11-01T13:05:00Z")
        self.assertEqual((backoff["status"], backoff["reason"]), ("failed", "rate_limited"))
        self.assertEqual(
            refresh(self.store, key, unexpected, checked_at="2026-11-01T14:04:00Z")["status"], "deferred",
        )
        self.store.withdraw(key, "fixture withdrawal")
        with self.assertRaisesRegex(PriceError, "withdrawn"):
            refresh(self.store, key, unexpected, checked_at="2026-11-01T14:05:00Z")

    def test_seller_day_dedup_and_threshold_use_comparable_confirmed_offers(self):
        self.cohort["source_type"] = "feed"
        self.cohort["seller_aliases"]["Example B"] = "example-seller-b"
        self.store.approve(self.cohort)
        day1 = deepcopy(self.fixture["captures"][2])
        day1["id"] = "day-one"
        day1["checked_at"] = "2026-11-01T13:00:00Z"
        offer = day1["observations"][0]
        offer["observed_at"] = "2026-11-01T12:00:00Z"
        offer["tax"] = {"basis": "included", "amount": None}
        offer["price"] = "100.00"

        another_listing = {**offer, "listing_id": "offer-more-expensive", "price": "108.00"}
        alias_retry = {**offer, "seller": "Example store"}
        second_seller = {**offer, "seller": "Example B", "price": "120.00"}
        sale = {**offer, "kind": "sale", "price": "1.00"}
        conditional = {**offer, "listing_id": "conditional", "discount": "conditional", "price": "5.00"}
        day1["observations"] += [another_listing, alias_retry, second_seller, sale, conditional]
        self.store.capture(self.cohort["id"], day1)
        day3 = deepcopy(day1)
        day3["id"] = "day-three"
        day3["checked_at"] = "2026-11-03T13:00:00Z"
        day3["observations"] = [{**offer, "observed_at": "2026-11-03T12:00:00Z", "price": "140.00"}]
        self.store.capture(self.cohort["id"], day3)

        result_id = self.store.publish(self.cohort["id"], "2026-11-01", "2026-11-07")
        result = self.store.read(result_id)
        self.assertEqual(result["adapter_status"], "stale")
        self.assertEqual(len(result["offers"]), 6)
        self.assertEqual(result["sampling"]["sample_count"], 3)
        self.assertEqual(result["sampling"]["seller_count"], 2)
        self.assertEqual(result["sampling"]["range_status"], "published")
        for field, expected in (
            ("min", "100.00"), ("q1", "110.00"), ("median", "120.00"),
            ("q3", "130.00"), ("max", "140.00"),
        ):
            self.assertEqual(result["sampling"][field], expected)

    def test_withdrawing_approval_removes_every_public_surface(self):
        self.store.approve(self.cohort)
        self.store.capture(self.cohort["id"], self.fixture["captures"][0])
        result_id = self.store.publish(self.cohort["id"], "2026-11-01", "2026-11-01")
        self.store.withdraw(self.cohort["id"], "private withdrawal record")
        for filename in ("prices.json", "prices.md", "prices.html"):
            artifact = self.store.artifact(result_id, filename)
            self.assertIn("withdrawn", artifact.lower())
            self.assertNotIn("240.00", artifact)
            self.assertNotIn("private withdrawal", artifact)
        with self.assertRaisesRegex(PriceError, "withdrawn"):
            self.store.capture(self.cohort["id"], self.fixture["captures"][0])

    def test_release_origin_serves_exact_quotes_and_immediate_withdrawal(self):
        from fastest_release.http import make_server

        self.store.ingest(self.fixture)
        release_id = self.store.publish(self.cohort["id"], "2026-11-01", "2026-11-04")
        with make_server(None, port=0, price_reader=self.store.read) as server:
            worker = Thread(target=server.serve_forever)
            worker.start()
            base = f"http://127.0.0.1:{server.server_port}/price-releases/"
            try:
                with urlopen(f"{base}{release_id}/prices.json") as response:
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
                    result = json.load(response)
                    self.assertEqual(result, self.store.read(release_id))
                    self.assertEqual(result["market"], "US")
                    self.assertEqual(result["offers"][0]["price"], "240.00")
                with self.assertRaises(HTTPError) as missing:
                    urlopen(f"{base}{uuid4()}/prices.json")
                self.assertEqual(missing.exception.code, 404)
                missing.exception.close()

                self.store.withdraw(self.cohort["id"], "private authorization update")
                with self.assertRaises(HTTPError) as withdrawn:
                    urlopen(f"{base}{release_id}/prices.json")
                self.assertEqual(withdrawn.exception.code, 410)
                with withdrawn.exception as response:
                    self.assertNotIn("offers", json.load(response))
            finally:
                server.shutdown()
                worker.join(timeout=5)

    def test_api_prices_paginate_authorized_quotes_with_current_rights(self):
        illustrative = deepcopy(self.cohort)
        illustrative["id"] += "-illustrative"
        self.store.approve(illustrative)
        self.store.capture(illustrative["id"], self.fixture["captures"][0])
        demo = self.store.publish(illustrative["id"], "2026-11-01", "2026-11-04")
        self.cohort["data_class"] = "authorized_observations"
        authorization = self.cohort["authorization"]
        authorization["aggregate"] = "deny"
        authorization["expires_at"] = "2099-01-01T00:00:00Z"
        self.store.approve(self.cohort)
        for capture in self.fixture["captures"]:
            self.store.capture(self.cohort["id"], capture)
        release = self.store.publish(self.cohort["id"], "2026-11-01", "2026-11-04")

        with api_client(price_reader=self.store.read) as request:
            status, _, specification = request("/api/v1/openapi.json")
            self.assertEqual(status, 200)
            self.assertIn("/api/v1/historical-offers", specification["paths"])
            path = f"/api/v1/historical-offers?release={release}&limit=1"
            status, _, page = request(path)
            self.assertEqual(status, 200)
            self.assertEqual(page["release_id"], release)
            self.assertEqual(page["unit"], "USD")
            self.assertEqual(page["rights"]["expires_at"], "2099-01-01T00:00:00Z")
            self.assertEqual(page["sampling"]["range_status"], "rights_restricted")
            self.assertIsNone(page["sampling"]["sample_count"])
            self.assertEqual(page["offers"][0]["price"], "240.00")
            self.assertIsNone(page["offers"][0]["landed_price"])
            self.assertEqual(page["pagination"]["next_offset"], 1)
            status, _, second = request(path + "&offset=1")
            self.assertEqual(status, 200)
            self.assertEqual(second["offers"][0]["landed_price"], "253.80")
            self.assertIsNone(second["pagination"]["next_offset"])
            site_status, _, site = request(second["url"])
            self.assertEqual(site_status, 200)
            self.assertEqual(site["release_id"], second["release_id"])
            self.assertEqual(site["offers"][1]["landed_price"], second["offers"][0]["landed_price"])
            self.assertIn("253.80", self.store.artifact(release, "prices.html"))
            self.assertNotIn("authorization-file", json.dumps(second))
            self.assertEqual(request(f"/api/v1/historical-offers?release={demo}")[0], 404)

            now = datetime.now(timezone.utc)
            deadline = (now + timedelta(seconds=5)).replace(microsecond=0)
            expiring = deepcopy(self.cohort)
            expiring["id"] += "-expiring"
            expiring["authorization"]["expires_at"] = deadline.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.store.approve(expiring)
            self.store.capture(expiring["id"], self.fixture["captures"][0])
            saved = self.store.publish(expiring["id"], "2026-11-01", "2026-11-04")
            saved_path = f"/api/v1/historical-offers?release={saved}"
            self.assertEqual(request(saved_path)[0], 200)
            time.sleep(max(0, (deadline - datetime.now(timezone.utc)).total_seconds()) + 0.02)
            status, _, after = request(saved_path)
            self.assertEqual(status, 410)
            self.assertNotIn("offers", after)
            self.assertEqual(request(f"/price-releases/{saved}/prices.json")[0], 410)
            self.assertNotIn("240.00", self.store.artifact(saved, "prices.html"))

    def test_advisor_and_wizard_share_landed_postgres_quote_and_withdrawal(self):
        self.cohort.update(data_class="authorized_observations",
                           scope={"kind": "whole_build", "id": "apple-m4", "revision_id": "fixture-m4-build-v1"})
        capture = deepcopy(self.fixture["captures"][2])
        capture["observations"][0]["scope"] = self.cohort["scope"]
        self.store.approve(self.cohort)
        self.store.capture(self.cohort["id"], capture)
        release_id = self.store.publish(self.cohort["id"], "2026-11-01", "2026-11-04")
        query = "entry=budget&budget=254&decode=40&prefill=500&privacy=local-only"

        with fixture_service(price=self.store.read, price_release=release_id) as goals:
            with api_client(goals=goals, price_reader=self.store.read) as request:
                status, _, html = request("/advisor?" + query, decode=False)
                self.assertEqual(status, 200)
                self.assertIn("253.80 USD", html)
                self.assertNotIn("illustrative-authorization-file", html)
                status, _, advisor = request("/api/v1/advisor?" + query)
                self.assertEqual(status, 200)
                self.assertEqual(advisor["recommendation"], "apple-m4")
                citation = next(item for item in advisor["citations"] if item["kind"] == "landed-quote")
                self.assertEqual((citation["release_id"], citation["locator"]),
                                 (release_id, "example-feed/2026-11-03/offer-a"))
                status, _, wizard = request(advisor["comparison"]["replay_url"])
                self.assertEqual(status, 200)
                row = next(item for item in wizard["rows"] if item["id"] == "apple-m4")
                self.assertEqual(row["goals"]["budget"]["value"], "253.80")

                self.store.withdraw(self.cohort["id"], "private operator-only authorization update")
                status, _, html = request("/advisor?" + query, decode=False)
                self.assertEqual(status, 200)
                self.assertIn("Insufficient evidence", html)
                self.assertIn("The pinned price release was withdrawn.", html)
                self.assertNotIn("253.80 USD", html)
                self.assertNotIn("operator-only", html)

    def test_public_reader_cannot_read_private_inputs_or_write(self):
        self.store.approve(self.cohort)
        self.store.capture(self.cohort["id"], self.fixture["captures"][0])
        release_id = self.store.publish(self.cohort["id"], "2026-11-01", "2026-11-01")

        subprocess.run(
            ["psql", "-XqAtw", "-v", "ON_ERROR_STOP=1", "-d", self.database_url],
            input="""
                CREATE ROLE price_test_reader NOLOGIN;
                GRANT USAGE ON SCHEMA fastest_prices TO price_test_reader;
                GRANT EXECUTE ON FUNCTION fastest_prices.read_release(uuid) TO price_test_reader;
            """,
            text=True, capture_output=True, check=True,
        )
        reader = PriceStore(self.database_url + " options='-c role=price_test_reader'")
        self.assertEqual(reader.read(release_id), self.store.read(release_id))
        with self.assertRaisesRegex(PriceError, "permission denied"):
            reader.approve(self.cohort)
        for table in ("cohort", "capture", "observation", "withdrawal"):
            result = subprocess.run(
                ["psql", "-XqAtw", "-v", "ON_ERROR_STOP=1", "-d",
                 self.database_url + " options='-c role=price_test_reader'"],
                input=f"SELECT * FROM fastest_prices.{table};",
                text=True, capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("permission denied", result.stderr)

    def test_bundle_rejects_a_capture_from_a_different_source_atomically(self):
        self.fixture["captures"][1]["source_id"] = "other-feed"
        with self.assertRaisesRegex(PriceError, "Capture source"):
            self.store.ingest(self.fixture)
        with self.assertRaisesRegex(PriceError, "approval is missing"):
            self.store.publish(self.cohort["id"], "2026-11-01", "2026-11-04")

    def test_cli_replays_and_exports_an_illustrative_bundle(self):
        def cli(*args):
            return subprocess.run(
                [sys.executable, "-m", "fastest_prices", "--database-url", self.database_url, *args],
                check=True, capture_output=True, text=True,
            ).stdout

        cli("migrate")
        with tempfile.TemporaryDirectory(prefix="fastest-price-fixture-") as temporary:
            bundle = Path(temporary) / "reviewed.json"
            bundle.write_text(json.dumps(self.fixture), encoding="utf-8")
            self.assertEqual(cli("ingest", str(bundle)).strip(), self.cohort["id"])
            self.assertEqual(cli("ingest", str(bundle)).strip(), self.cohort["id"])
        self.assertFalse(Path(temporary).exists())
        release_id = cli("publish", self.cohort["id"], "2026-11-01", "2026-11-04").strip()
        for name in ("prices.md", "prices.html", "prices.json"):
            artifact = cli("artifact", release_id, name)
            self.assertEqual(artifact, self.store.artifact(release_id, name))
