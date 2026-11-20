from contextlib import closing
import http.client
import json
from pathlib import Path
from threading import Thread
import unittest

from fastest_release.http import make_server


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
PLAN = json.loads((FIXTURES.parent / "fastest_text" / "plan.json").read_text())
BASELINE = "11111111-1111-1111-1111-111111111111"
COMPARISON = "22222222-2222-2222-2222-222222222222"
ROUTE = "/topology/scaling"


def fixture_releases():
    """Synthetic comparator inputs shaped like rights-filtered measured releases."""
    snapshots = {}
    for release_id, run_id, active_count, value in (
        (BASELINE, "aaaa1111-1111-1111-1111-111111111111", 1, "30.000000000001"),
        (COMPARISON, "aaaa2222-2222-2222-2222-222222222222", 2, "50.000000000001"),
    ):
        row = json.loads((FIXTURES / "synthetic-observation.json").read_text())
        row.update(kind="measured", evidence_id=run_id, workload={
            "id": "llama-bench-solo-gpu-scaling", "version": 1,
            "description": "Controlled solo decode with one or more active GPUs.",
        })
        row["hardware"].update(name="Synthetic scaling fixture host",
                               configuration="Two simulated GPUs with one or both active.")
        artifact = PLAN["artifact"]
        first, second = artifact["shards"]
        row["artifact"].update(repository=artifact["repository"], revision=artifact["revision"], format="GGUF",
                               quantization=artifact["quantization"], path=first["path"], sha256=first["sha256"])
        row["metric"] = {
            "id": "llama-bench-decode", "version": 1, "unit": "tok/s", "statistic": "median",
            "boundary": PLAN["protocol"]["phases"]["decode"]["boundary"], "sample_count": 20, "value": value,
        }
        row["fields"] = {
            key: {"status": "known", "value": item}
            for key, item in {
                "run_id": run_id, "backend": "CUDA", "runtime_revision": PLAN["runtime"]["revision"],
                "artifact_companion_sha256": second["sha256"],
            }.items()
        }
        first_gpu, second_gpu = "0000:01:00.0", "0000:02:00.0"
        devices = [
            {"id": first_gpu, "slot": "PCIEX16_1", "card": "Fixture GPU", "placement": "Layers 0–27"},
            {"id": second_gpu, "slot": "PCIEX16_2", "card": "Fixture GPU", "placement": "Layers 28–39"},
        ][:active_count]
        if active_count == 1:
            devices[0]["placement"] = "All layers and KV cache"
        metadata = {
            "outcome": "success", "binary_sha256": "a" * 64, "os_driver": "Fixture OS and driver",
            "quality": {"protocol": PLAN["rubric"]["id"], "accepted": True},
            "load": "One foreground sequence on an otherwise idle host.",
            "settings": {key: value for key, value in PLAN["protocol"]["settings"].items()
                         if key not in ("split_mode", "main_gpu")},
            "devices": devices, "primary_device": first_gpu,
            "strategy": "single-device" if active_count == 1 else "layer",
            "treatment": "One active device" if active_count == 1 else "Split model layers between both GPUs",
            "transports": [] if active_count == 1 else [{
                "from": first_gpu, "to": second_gpu, "path": "host-staged", "interconnect": "PCIe via host memory",
                "direction": "one-way", "payload_bytes": 4194304, "scope": "transfer microbenchmark",
                "method": "GPU to pinned system RAM to GPU; synchronized copy timing",
                "rated": {"generation": 4, "width": 16, "rate": "16 GT/s per lane"},
                "negotiated": {"generation": 4, "width": 8, "rate": "16 GT/s per lane"},
                "bandwidth_gb_s": "10.125",
            }],
        }
        row["fields"]["gpu_scaling_v1"] = {"status": "known", "value": json.dumps(metadata, separators=(",", ":"))}
        snapshots[release_id] = {"release_id": release_id, "status": "published", "row": row}
    return snapshots


def edit_metadata(snapshots, release_id, edit):
    field = snapshots[release_id]["row"]["fields"]["gpu_scaling_v1"]
    metadata = json.loads(field["value"])
    edit(metadata)
    field["value"] = json.dumps(metadata)


class FixtureStore:
    """A synthetic substitute for PostgreSQL's read_many release boundary."""

    def __init__(self, snapshots):
        self.snapshots = snapshots

    def read_many(self, release_ids):
        return [self.snapshots.get(identifier, {"release_id": identifier, "status": "unavailable"})
                for identifier in sorted(release_ids)]


class ScalingTest(unittest.TestCase):
    def start(self, store=None, pair=()):
        with_server = {"scaling_pair": pair} if pair else {}
        server = self.enterContext(make_server(store, port=0, **with_server))
        worker = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        worker.start()
        self.addCleanup(worker.join, 5)
        self.addCleanup(server.shutdown)
        client = self.enterContext(closing(http.client.HTTPConnection(*server.server_address, timeout=5)))

        def get(path):
            client.request("GET", path)
            response = client.getresponse()
            return response.status, response.getheader("Location"), response.read().decode()

        return get

    def test_unconfigured_topology_report_explains_missing_evidence(self):
        get = self.start()
        status, _, html = get(ROUTE)
        self.assertEqual(status, 200)
        self.assertIn("No reviewed 1→N GPU pair is pinned", html)
        status, _, body = get(ROUTE + ".json")
        self.assertEqual(status, 200)
        report = json.loads(body)
        self.assertEqual(report["status"], "unavailable")
        self.assertIsNone(report["speedup"])
        self.assertIsNone(report["efficiency"])

    def test_pinned_pair_uses_exact_throughputs_and_shows_actual_transport(self):
        get = self.start(FixtureStore(fixture_releases()), (BASELINE, COMPARISON))
        status, pinned, _ = get(ROUTE)
        self.assertEqual(status, 307)
        self.assertEqual(pinned, f"{ROUTE}/{BASELINE}/{COMPARISON}")
        status, _, body = get(pinned + ".json")
        self.assertEqual(status, 200)
        report = json.loads(body)
        self.assertEqual(report["status"], "measured")
        self.assertEqual(report["speedup"], {"numerator": "50000000000001", "denominator": "30000000000001"})
        self.assertEqual(report["efficiency"], {"numerator": "50000000000001", "denominator": "60000000000002"})
        self.assertEqual(report["comparison"]["active_count"], 2)
        self.assertEqual(report["comparison"]["devices"][1]["slot"], "PCIEX16_2")
        self.assertEqual(report["comparison"]["transports"][0]["path"], "host-staged")
        status, _, html = get(pinned)
        self.assertEqual(status, 200)
        for text in ("All layers and KV cache", "Split model layers between both GPUs", "host-staged",
                     "4194304", "one-way", "transfer microbenchmark", "Negotiated", "Rated", "10.125",
                     f"/releases/{BASELINE}/benchmark.html"):
            self.assertIn(text, html)
        self.assertEqual(get(f"{ROUTE}/{COMPARISON}/{BASELINE}")[0], 404)

    def test_exclusions_never_derive_scaling_from_ineligible_pairs(self):
        baseline_oom = lambda rows: edit_metadata(rows, BASELINE, lambda m: m.update(outcome="oom"))
        missing_path = lambda rows: edit_metadata(rows, COMPARISON, lambda m: m.update(transports=[]))
        duplicate_device = lambda rows: edit_metadata(
            rows, COMPARISON, lambda m: m["devices"][1].update(id=m["devices"][0]["id"]))
        runtime_mismatch = lambda rows: edit_metadata(rows, COMPARISON, lambda m: m.update(binary_sha256="b" * 64))
        load_mismatch = lambda rows: edit_metadata(rows, COMPARISON, lambda m: m.update(load="Four concurrent requests"))
        quality_mismatch = lambda rows: edit_metadata(rows, COMPARISON, lambda m: m["quality"].update(accepted=False))
        disconnected_gpu = lambda rows: edit_metadata(rows, COMPARISON, lambda m: m["devices"].append(
            {"id": "0000:03:00.0", "slot": "PCIEX16_3", "card": "Fixture GPU", "placement": "KV cache"}))
        for mutate, reason in (
            (baseline_oom, "baseline_oom"),
            (missing_path, "path_unavailable"),
            (disconnected_gpu, "path_unavailable"),
            (duplicate_device, "devices"),
            (lambda rows: edit_metadata(rows, COMPARISON, lambda m: m.update(strategy="unknown")), "strategy"),
            (runtime_mismatch, "runtime_mismatch"),
            (load_mismatch, "load_mismatch"),
            (quality_mismatch, "quality_mismatch"),
            (lambda rows: rows[COMPARISON]["row"]["artifact"].update(sha256="d" * 64), "artifact_mismatch"),
            (lambda rows: rows[COMPARISON]["row"]["metric"].update(boundary="Time to first visible token"), "metric_mismatch"),
            (lambda rows: rows[COMPARISON]["row"]["hardware"].update(revision=2), "host_mismatch"),
            (lambda rows: rows[COMPARISON]["row"].update(kind="synthetic"), "synthetic"),
            (lambda rows: rows.pop(COMPARISON), "comparison_unavailable"),
        ):
            with self.subTest(reason=reason):
                snapshots = fixture_releases()
                mutate(snapshots)
                get = self.start(FixtureStore(snapshots), (BASELINE, COMPARISON))
                _, _, body = get(f"{ROUTE}/{BASELINE}/{COMPARISON}.json")
                report = json.loads(body)
                self.assertEqual(report["status"], "excluded")
                self.assertEqual(report["reason"], reason)
                self.assertIsNone(report["speedup"])
                self.assertIsNone(report["efficiency"])

    def test_direct_peer_remains_distinct_and_unknown_link_properties_are_visible(self):
        snapshots = fixture_releases()
        edit_metadata(snapshots, COMPARISON, lambda m: m["transports"][0].update(
            path="direct-peer", rated=None, negotiated=None, bandwidth_gb_s=None,
            interconnect="Direct link", method="Backend peer-copy trace",
        ))
        get = self.start(FixtureStore(snapshots), (BASELINE, COMPARISON))
        url = f"{ROUTE}/{BASELINE}/{COMPARISON}"
        status, _, html = get(url)
        self.assertEqual(status, 200)
        self.assertIn("direct-peer · Direct link", html)
        self.assertNotIn("host-staged", html)
        self.assertIn("<td>Unknown</td>", html)
        report = json.loads(get(url + ".json")[2])
        self.assertEqual(report["status"], "measured")
        self.assertIsNone(report["comparison"]["transports"][0]["bandwidth_gb_s"])

    def test_withdrawal_is_rechecked_before_replaying_pinned_pair(self):
        snapshots = fixture_releases()
        get = self.start(FixtureStore(snapshots), (BASELINE, COMPARISON))
        url = f"{ROUTE}/{BASELINE}/{COMPARISON}.json"
        self.assertEqual(json.loads(get(url)[2])["status"], "measured")
        snapshots[COMPARISON] = {"release_id": COMPARISON, "status": "withdrawn"}
        status, _, body = get(url)
        self.assertEqual(status, 410)
        report = json.loads(body)
        self.assertEqual(report["reason"], "comparison_withdrawn")
        self.assertIsNone(report["comparison"])
        self.assertNotIn("50.000000000001", body)
