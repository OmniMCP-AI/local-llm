"""Exercise the private meter intake command with synthetic recorder evidence."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from test_serving import configured_service, result_row, serving_record, serving_result


class ServingMeterTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory(prefix="fastest-serving-meter-test-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.run = self.root / "run"
        self.run.mkdir()
        self.capture_path = self.run / "capture.json"
        self.meter_path = self.root / "meter.json"
        self.output_path = self.root / "meter-receipt.json"
        self.capture = {
            "kind": "private-capture", "protocol": "four-user-fixed-token-serving@1",
            "diagnostic_reason": None, "status": "complete", "duration_ms": 144000,
            "server": {"ip": "192.0.2.25", "port": 8080}, "attempts": serving_record()["attempts"],
            "power": {"status": "missing", "reason": "No calibrated meter supplied."},
            "window_started_ns": 12345678901, "window_ended_ns": 156345678901,
            "meter_window": {
                "capture_id": "248f9d4e-cac3-4017-abcb-e000d5e20ef5", "start_ns": 12345678901,
                "end_ns": 156345678901,
                "clock": {"source": "linux-clock-monotonic", "boot_id": "cebb3678-779c-4b1d-a0df-d83885982ed0",
                          "time_namespace": 4026531834},
            },
        }
        self.meter = {
            "schema_version": 1, "capture_id": "248f9d4e-cac3-4017-abcb-e000d5e20ef5",
            "clock": dict(self.capture["meter_window"]["clock"]),
            "alignment": "latched-on-client-monotonic-clock",
            "meter_id": "Fixture meter 123", "calibration_ref": "certificate fixture-123",
            "raw_log_ref": "native fixture export", "boundary": "serving-host-ac-input",
            "server_ip": "192.0.2.25", "feeds": ["server input A", "server input B"], "unit": "J",
            "samples": [
                {"sampled_ns": 12345678901, "joules": "2500", "counter_epoch": "native session 1"},
                {"sampled_ns": 156345678901, "joules": "11800", "counter_epoch": "native session 1"},
            ],
        }

    def intake(self, output=None):
        self.capture_path.write_text(json.dumps(self.capture) + "\n")
        self.meter_path.write_text(json.dumps(self.meter) + "\n")
        return subprocess.run([sys.executable, "-B", "-m", "fastest_serving.meter", self.run,
                               self.meter_path, self.output_path if output is None else output],
                              cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=10)

    def test_retains_bound_meter_evidence_for_existing_review(self):
        result = self.intake()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(self.output_path.read_text())
        self.assertEqual(receipt["power"], {
            "status": "measured", "boundary": "serving-host-ac-input", "meter": "Fixture meter 123",
            "start_ms": 0, "end_ms": 144000, "start_joules": "2500", "end_joules": "11800",
        })
        self.assertEqual(receipt["meter_log"], self.meter)
        self.assertEqual(receipt["meter_log_sha256"], sha256(self.meter_path.read_bytes()).hexdigest())
        self.assertEqual(receipt["capture_sha256"], sha256(self.capture_path.read_bytes()).hexdigest())
        self.assertEqual(self.capture_path.read_text(), json.dumps(self.capture) + "\n")
        self.assertEqual(self.output_path.stat().st_mode & 0o777, 0o600)
        record = serving_record()
        record["power"] = receipt["power"]
        row = result_row(serving_result(configured_service(self.root, record), wall_energy="100"))
        self.assertEqual(row["serving"]["wall_joules"], "9300")
        self.assertEqual(row["goals"]["wall_energy"]["value"], "100")

    def test_rejects_diagnostic_partial_and_unannounced_captures(self):
        original = self.capture
        for changes, reason in (
            ({"kind": "diagnostic"}, "non-diagnostic"),
            ({"status": "partial"}, "complete serving capture"),
            ({"duration_ms": 143999}, "complete serving capture"),
            ({"attempts": original["attempts"][:-1]}, "all scheduled attempts"),
            ({"attempts": original["attempts"][:-1] + original["attempts"][:1]}, "Duplicate serving request"),
            ({"meter_window": None}, "announced meter window"),
            ({"window_ended_ns": 156345678900}, "captured monotonic window"),
        ):
            with self.subTest(changes=list(changes), reason=reason):
                self.capture = {**original, **changes}
                result = self.intake()
                self.assertEqual(result.returncode, 1)
                self.assertIn(reason, result.stderr)
                self.assertFalse(self.output_path.exists())
                self.assertEqual(json.loads(self.capture_path.read_text())["power"]["status"], "missing")

    def test_rejects_unbound_or_invalid_recorder_evidence(self):
        original = self.meter
        start, end = original["samples"]
        clock = original["clock"]
        for changes, reason in (
            ({"capture_id": "51e5d684-d86a-49bf-954c-1e2f8f0b63fd"}, "another capture"),
            ({"clock": {**clock, "boot_id": "51e5d684-d86a-49bf-954c-1e2f8f0b63fd"}}, "same client monotonic clock"),
            ({"clock": {**clock, "time_namespace": 42}}, "same client monotonic clock"),
            ({"clock": {**clock, "time_namespace": float(clock["time_namespace"])}}, "same client monotonic clock"),
            ({"alignment": "wall-clock"}, "same client monotonic clock"),
            ({"calibration_ref": ""}, "calibration_ref"),
            ({"boundary": "gpu-board"}, "serving host AC input"),
            ({"unit": "kWh"}, "cumulative joules"),
            ({"feeds": []}, "covered serving host feeds"),
            ({"server_ip": "192.0.2.26"}, "captured serving host"),
            ({"samples": [start]}, "both capture boundaries"),
            ({"samples": [{**start, "sampled_ns": start["sampled_ns"] + 1}, end]}, "exact captured monotonic boundaries"),
            ({"samples": [start, {**end, "sampled_ns": end["sampled_ns"] - 1}]}, "exact captured monotonic boundaries"),
            ({"samples": [start, {**end, "sampled_ns": end["sampled_ns"] + 1}]}, "inside the captured monotonic window"),
            ({"samples": [start, {**end, "joules": "NaN"}]}, "nonnegative decimal joules"),
            ({"samples": [start, {**end, "joules": "2500"}]}, "must increase"),
            ({"samples": [start, {**end, "counter_epoch": "native session 2"}]}, "reset, wrapped or decreased"),
            ({"samples": [start, {**start, "sampled_ns": start["sampled_ns"] + 1, "joules": "42"}, end]},
             "reset, wrapped or decreased"),
        ):
            with self.subTest(changes=changes):
                self.meter = {**original, **changes}
                result = self.intake()
                self.assertEqual(result.returncode, 1)
                self.assertIn(reason, result.stderr)
                self.assertFalse(self.output_path.exists())

    def test_retries_and_capture_path_collisions_never_overwrite_evidence(self):
        created = self.intake()
        self.assertEqual(created.returncode, 0, created.stderr)
        before = self.output_path.read_bytes()
        for destination in (self.output_path, self.capture_path, self.meter_path):
            with self.subTest(destination=destination.name):
                result = self.intake(destination)
                self.assertEqual(result.returncode, 1)
                self.assertIn("File exists", result.stderr)
        self.assertEqual(self.output_path.read_bytes(), before)
        self.assertEqual(json.loads(self.capture_path.read_text()), self.capture)
        self.assertEqual(json.loads(self.meter_path.read_text()), self.meter)
        self.assertEqual(list(self.root.glob(".serving-meter-*")), [])
        self.assertEqual(list(self.run.glob(".serving-meter-*")), [])
