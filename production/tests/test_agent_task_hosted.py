import hashlib
import json
import unittest

from fastest_agent_task.harness import plan
from fastest_agent_task.publication import report_artifacts


def hosted_record(protocol, raw_attempts):
    context = protocol["contexts"][0]
    return {
        "kind": "measured", "context_id": context["id"], "context_sha256": context["sha256"],
        "environment": {
            "hardware": "GitHub-hosted AMD EPYC 7763, 4 vCPUs",
            "os": "Ubuntu 24.04 x86_64", "backend": "CPU",
            "runtime_binary_sha256": protocol["runtime"]["binary_sha256"],
            "adapter_sha256": protocol["harness"]["files"]["measure.py"],
            "source": {
                "run_url": "https://github.com/OmniMCP-AI/local-llm/actions/runs/123/attempts/1",
                "checkout_sha": "3" * 40, "runner_image_version": "20261115.1.0",
            },
        },
        "attempts": raw_attempts,
    }


class HostedAgentTaskTest(unittest.TestCase):
    def test_hosted_plan_keeps_task_and_budgets_and_preserves_original_context_pins(self):
        from fastest_agent_task.hosted import hosted_plan

        original, hosted = plan(), hosted_plan()
        for key in ("task", "artifact", "budget"):
            self.assertEqual(original[key], hosted[key])
        for key in ("turns", "privacy", "trial_order", "wall", "vary"):
            self.assertEqual(original["controls"][key], hosted["controls"][key])
        self.assertEqual([context["sha256"] for context in original["contexts"]], [
            "282ad775dbe0bd443b54f7ef257185893224c9f78be462039cb0c2ac70460fa5",
            "243e269029875ed6ab16e11017433d3e438502cb51c5db6ab0997908c1d2f970",
        ])
        self.assertEqual([context["id"] for context in hosted["contexts"]], ["bundle", "split"])
        self.assertNotEqual(original["contexts"], hosted["contexts"])
        self.assertEqual(hosted["settings"]["gpu_layers"], 0)
        self.assertEqual(hosted["settings"]["threads"], 4)
        self.assertIn("Physical host load is unknown", hosted["controls"]["session"])

    def test_reviewed_hosted_records_render_failures_without_the_wrong_answer(self):
        from fastest_agent_task.hosted import hosted_plan

        bundle = hosted_record(hosted_plan(), [{
            "trial": 1, "attempt": 1, "wall_ns": 20_000, "generated_tokens": 9, "reasoning_tokens": 0,
            "termination": "answered", "outcome": "rubric_mismatch", "answer": None, "tool_reads": [],
        }])
        review = {
            "decision_id": "fb03a586-85a3-448f-8e67-0dc3cfde31dc",
            "evidence_id": "22d82897-9c5e-597d-b469-ff2f7d98c66c",
            "retained_sha256": "1" * 64, "ownership": "operator-owned",
            "destination": "public-release", "decision": "allow",
        }
        with self.assertRaises(ValueError):
            report_artifacts([bundle])

        approved = {**bundle, "review": review}
        files = report_artifacts([approved])
        report = json.loads(files["agent-task.json"])
        rendered = report["contexts"][0]
        self.assertEqual(rendered["attempts"][0]["outcome"], "rubric_mismatch")
        self.assertIsNone(rendered["attempts"][0]["accepted_output"])
        self.assertEqual(rendered["trials"][0]["status"], "pending_retry")
        self.assertEqual(rendered["counts"]["failed_attempts"], 1)
        self.assertEqual(report["contexts"][1]["status"], "missing")
        self.assertEqual(report["environment"]["backend"], "CPU")
        self.assertIn("Physical host load is unknown", files["agent-task.md"])
        self.assertEqual(json.loads(files["manifest.json"])["sha256"]["agent-task.json"],
                         hashlib.sha256(files["agent-task.json"].encode()).hexdigest())

        for invalid in (
            {**approved, "context_sha256": plan()["contexts"][0]["sha256"]},
            {**approved, "environment": {**bundle["environment"], "backend": "Metal"}},
            {**approved, "attempts": [{**bundle["attempts"][0], "answer": {"open_units": 16}}]},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                report_artifacts([invalid])

    def test_packet_verifier_replays_both_policies_and_detects_timing_tampering(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from fastest_agent_task.capture_hosted import verify
        from fastest_agent_task.hosted import TRIAL_ORDER, hosted_plan

        protocol = hosted_plan()
        with TemporaryDirectory() as temporary:
            packet = Path(temporary)
            files = {}
            evidence = {}
            for context in protocol["contexts"]:
                name = context["id"]
                record = hosted_record(protocol, [{
                    "trial": trial, "attempt": 1, "wall_ns": 25_000, "generated_tokens": 16,
                    "reasoning_tokens": 0, "termination": "answered", "outcome": "accepted",
                    "answer": {"open_units": 17}, "tool_reads": context["allowed_reads"],
                } for trial in range(1, 3)])
                record.update(context_id=name, context_sha256=context["sha256"])
                path = packet / f"{name}-candidate.json"
                path.write_text(json.dumps(record))
                files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                evidence[name] = {"bundle": "22d82897-9c5e-597d-b469-ff2f7d98c66c",
                                  "split": "647e0cc3-2d79-5466-9cc5-b0e6586a26ac"}[name]
            receipt = {
                "schema_version": 1, "protocol_id": protocol["protocol_id"],
                "source": record["environment"]["source"], "artifact": protocol["artifact"],
                "runtime": {
                    **protocol["runtime"],
                    "archive_url": "https://github.com/ggml-org/llama.cpp/releases/download/b5163/llama-b5163-bin-ubuntu-x64.zip",
                    "archive_sha256": "9663781ea5cd79035fcecb1f3e00b8aabcf559a181984d96ce5cfdeef9d7c2b7",
                }, "controls": {
                    "guest_before": {"idle_percent": 98, "steal_percent": 0},
                    "guest_after": {"idle_percent": 96, "steal_percent": 0},
                    "cpu_affinity_vcpus": 4, "cpu_quota_allows_vcpus": 4,
                    "cpu_only": True, "warmups": ["bundle", "split"],
                    "attempts_with_kv_reset": [[policy, trial, 1] for policy, trial in TRIAL_ORDER],
                }, "files": files, "evidence_ids": evidence,
            }
            (packet / "receipt.json").write_text(json.dumps(receipt))
            self.assertEqual(verify(packet), receipt)
            candidate = packet / "bundle-candidate.json"
            candidate.write_text(candidate.read_text().replace("25000", "26000"))
            with self.assertRaisesRegex(ValueError, "digest"):
                verify(packet)

    def test_startup_diagnostics_extract_controls_without_private_log_text(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from fastest_agent_task.capture_hosted import startup_diagnostics

        with TemporaryDirectory() as temporary:
            log = Path(temporary) / "server.log"
            log.write_text(
                "system info: n_threads = 4, n_threads_batch = 4, total_threads = 4\n"
                "main: setting address family to AF_UNIX\n"
                "load_tensors: CPU_Mapped model buffer size = 4334.28 MiB\n"
                "llama_kv_cache: CPU KV buffer size = 112.00 MiB\n"
                "llama_context: CPU compute buffer size = 304.00 MiB\n"
                "llama_context: n_ctx         = 2048\n"
                "llama_context: n_batch       = 512\n"
                "srv init: initializing slots, n_slots = 1\n"
                "server listening at /private/random/uid/run.sock\n"
            )
            self.assertEqual(startup_diagnostics(log), {
                "log_available": True, "buffers": {"model": ["CPU_Mapped"], "kv": ["CPU"], "compute": ["CPU"]},
                "devices": [], "offloaded_layers": [], "context_tokens": [2048], "batch_tokens": [512],
                "slots": [1], "threads": [4, 4, 4], "unix_socket": True,
            })


class HostedSlotRecoveryTest(unittest.TestCase):
    def test_pre_attempt_reset_drains_a_timed_out_slot_without_extending_the_attempt(self):
        self.exercise_reset()

    def test_stuck_slot_fails_closed_at_the_reset_stage(self):
        self.exercise_reset(reset_error=TimeoutError)

    def test_rejected_reset_redacts_the_untrusted_response(self):
        self.exercise_reset(reset_error=ValueError)

    def exercise_reset(self, reset_error=None):
        from pathlib import Path
        import sys
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        from fastest_agent_task.harness import BUDGET
        from fastest_agent_task.hosted import hosted_plan
        from fastest_agent_task.measure import run

        stage_log = []
        started_attempts = 0
        slot_busy = False
        clock_ns = 0

        def monotonic_ns():
            nonlocal clock_ns
            clock_ns += 1_000
            return clock_ns

        def exchange(_listener, endpoint, timeout, body=None):
            nonlocal started_attempts, slot_busy, clock_ns
            if endpoint == "/health":
                return {"status": "ok"}
            if endpoint == "/slots/0?action=erase":
                if slot_busy:
                    if reset_error is not None:
                        raise reset_error("private socket information")
                    if timeout < 90:
                        raise TimeoutError("private socket information")
                    slot_busy = False
                return {"id_slot": 0, "n_erased": 0}
            self.assertFalse(slot_busy)
            messages = body["messages"]
            phase, requests = messages[0]["content"].split("\nAllowed tool requests: ")
            self.assertTrue(phase)
            reads = json.loads(requests)
            turn = (len(messages) - 1) // 2
            if turn == 0:
                started_attempts += 1
                if started_attempts == 3:
                    self.assertGreater(timeout, 29.99)
                    self.assertLessEqual(timeout, 30)
                    clock_ns += int(timeout * 1_000_000_000)
                    slot_busy = True
                    raise TimeoutError("private socket information")
            answer = reads[turn] if turn < len(reads) else {"open_units": 17}
            return {
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(answer)}}],
                "usage": {"completion_tokens": 9},
            }

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "test-llama-server"
            binary.write_text(f"#!{sys.executable}\nimport sys, time\n"
                              'if "--version" in sys.argv:\n    print("version: 5163 (84a9bf2f)")\n'
                              "else:\n    time.sleep(300)\n")
            binary.chmod(0o700)
            model = root / "test-model.gguf"
            model.write_bytes(b"tiny test model")
            protocol = hosted_plan()
            protocol["artifact"]["shards"] = [{
                "path": model.name, "bytes": model.stat().st_size, "sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
            }]
            with (
                patch("fastest_agent_task.measure.exchange", exchange),
                patch("fastest_agent_task.measure.platform.system", return_value="Linux"),
                patch("fastest_agent_task.measure.time.monotonic_ns", monotonic_ns),
            ):
                def capture():
                    run(root / "capture", binary, model, "host", "os", "CPU", "none",
                        protocol=protocol, report_progress=stage_log.append)

                if reset_error is None:
                    capture()
                else:
                    with self.assertRaisesRegex(RuntimeError, f"kv_reset.*{reset_error.__name__}") as failure:
                        capture()
                    self.assertNotIn("private socket information", str(failure.exception))

            bundle = json.loads((root / "capture" / "bundle-draft.json").read_text())
            first = bundle["attempts"][0]
            self.assertEqual(first["termination"], "timeout")
            self.assertLess(first["wall_ns"], BUDGET["wall_ns_per_attempt"] + 100_000)
            self.assertIn({"stage": "measured_attempt", "status": "finished", "context_id": "bundle",
                           "trial": 1, "attempt": 1, "outcome": "timeout", "wall_ns": first["wall_ns"]}, stage_log)
            outcomes = [attempt["termination"] for attempt in bundle["attempts"]]
            if reset_error is not None:
                self.assertEqual(outcomes, ["timeout"])
                self.assertEqual(started_attempts, 3)
                self.assertTrue(any(row.get("stage") == "kv_reset" and row.get("status") == "failed"
                                    and row.get("error_type") == reset_error.__name__ for row in stage_log))
            else:
                self.assertEqual(outcomes, ["timeout", "answered", "answered"])
                self.assertEqual(started_attempts, 7)
            self.assertNotIn("private socket information", repr(stage_log))
