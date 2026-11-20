from contextlib import contextmanager
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

from fastest_release.http import make_server


REQUEST = {
    "machine": "llmfit-nvidia-rtx-4090",
    "artifact": "ca59ca7f13d0e15a8cfa77bd17e65d24f6844b554a7b6c12e07a5f89ff76844e",
    "runtime": "llama.cpp",
    "context": "4096",
    "ram_reserved_gib": "8",
    "vram_reserved_gib": "2",
}
OFFLOAD = {**REQUEST, "vram_reserved_gib": "23.5", "cpu_cores": "8"}
MISSING = {"machine": REQUEST["machine"]}
Q4 = "74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db"


def read_estimate(base, selection):
    with urlopen(f"{base}/fit.json?{urlencode(selection)}", timeout=10) as response:
        return json.load(response)


@contextmanager
def fit_server(engine):
    with make_server(None, port=0, fit_engine=engine) as server:
        worker = threading.Thread(target=server.serve_forever)
        worker.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            worker.join()


@unittest.skipUnless(os.environ.get("FASTEST_FIT_TEST_ENGINE"), "run the pinned fit fixture verifier")
class FitRequestTests(unittest.TestCase):
    def server(self):
        return fit_server(Path(os.environ["FASTEST_FIT_TEST_ENGINE"]))

    def test_selected_machine_and_artifact_fit_on_the_public_path(self):
        with self.server() as base:
            with urlopen(base, timeout=10) as response:
                self.assertIn('href="/fit"', response.read().decode())
            with urlopen(f"{base}/fit?machine={REQUEST['machine']}", timeout=10) as response:
                form = response.read().decode()
            with urlopen(f"{base}/fit?{urlencode(REQUEST)}", timeout=10) as response:
                self.assertIn("Perfect · Gpu · Q8_0", response.read().decode())
            result = read_estimate(base, REQUEST)

        self.assertIn(f'value="{REQUEST["machine"]}" selected', form)
        self.assertIn(REQUEST["artifact"], form)
        self.assertEqual(result["kind"], "fit_estimate")
        self.assertEqual(result["status"], "estimated")
        self.assertEqual(result["engine"]["revision"], "26450cccaf3a3f14b1822875f2473847a744a718")
        self.assertEqual(result["artifact"]["sha256"], REQUEST["artifact"])
        self.assertTrue(result["artifact"]["source"].endswith("-q8_0.gguf"))
        self.assertEqual(result["runtime"]["tag"], "v1.0.0")
        self.assertEqual(result["assumptions"]["context_tokens"], 4096)
        self.assertEqual(result["assumptions"]["ram_reserved_gib"], 8)
        self.assertEqual(result["assumptions"]["vram_reserved_gib"], 2)
        self.assertEqual(result["estimate"]["quantization"], "Q8_0")
        self.assertEqual(result["estimate"]["fit_level"], "Perfect")
        self.assertEqual(result["estimate"]["run_mode"], "Gpu")
        self.assertEqual(result["estimate"]["memory_available_gib"], 22)
        self.assertAlmostEqual(result["estimate"]["memory_required_gib"], 1.0656094064)
        self.assertAlmostEqual(result["estimate"]["decode_tokens_per_second"], 1122.192769205139)
        self.assertRegex(result["id"], r"^[0-9a-f]{64}$")

    def test_worker_settings_do_not_change_cpu_offload_estimates(self):
        with self.server() as base, TemporaryDirectory(prefix="fastest-fit-worker-") as temp:
            worker_model = Path(temp) / "models.json"
            worker_model.write_text(json.dumps([{
                "name": "Qwen/Qwen2.5-0.5B-Instruct",
                "provider": "Worker override",
                "parameter_count": "1B",
                "parameters_raw": 1_000_000_000,
                "min_ram_gb": 2,
                "recommended_ram_gb": 4,
                "quantization": "Q8_0",
                "format": "gguf",
                "context_length": 32768,
                "use_case": "chat",
            }]), encoding="utf-8")
            with patch.dict(os.environ, {"LLMFIT_DDR_BANDWIDTH": "12", "LLMFIT_CUSTOM_MODELS": str(worker_model)}):
                first = read_estimate(base, OFFLOAD)
            with patch.dict(os.environ, {"LLMFIT_DDR_BANDWIDTH": "750", "LLMFIT_CUSTOM_MODELS": "/nonexistent"}):
                second = read_estimate(base, OFFLOAD)

        self.assertEqual(first, second)
        self.assertEqual(first["status"], "estimated")
        self.assertEqual(first["estimate"]["run_mode"], "CpuOffload")
        self.assertEqual(first["estimate"]["memory_available_gib"], 56)
        self.assertEqual(first["estimate"]["decode_basis"]["ddr_bandwidth_gbps"], 89.6)
        self.assertAlmostEqual(first["estimate"]["decode_tokens_per_second"], 181.36448795234568)

    def test_partial_profiles_and_missing_artifact_inputs_are_qualified(self):
        with self.server() as base:
            partial = read_estimate(base, {**REQUEST, "machine": "V001-HP-G001"})
            missing = read_estimate(base, MISSING)
            unknown_quant = read_estimate(base, {
                **REQUEST,
                "artifact": "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe",
                "runtime": "vllm",
            })

        for result in [partial, missing, unknown_quant]:
            self.assertEqual(result["status"], "insufficient_input")
            self.assertIsNone(result["estimate"])
        self.assertEqual(partial["qualification"], "machine_fit_inputs_unavailable")
        self.assertEqual(missing["qualification"], "missing_request_inputs")
        self.assertIn("context", missing["missing"])
        self.assertEqual(unknown_quant["qualification"], "artifact_quantization_unavailable")

    def test_suggested_quantization_does_not_become_the_selected_artifacts_fit(self):
        with self.server() as base:
            result = read_estimate(base, {**REQUEST, "artifact": Q4})

        self.assertEqual(result["status"], "qualified")
        self.assertEqual(result["qualification"], "core_selected_different_quantization")
        self.assertEqual(result["artifact"]["quantization"], "Q4_K_M")
        self.assertEqual(result["engine_suggested_quantization"], "Q8_0")
        self.assertAlmostEqual(result["requested_artifact_memory_required_gib"], 0.83341400544)
        self.assertIsNone(result["estimate"])

    def test_offload_decode_requires_the_requested_context(self):
        with self.server() as base:
            result = read_estimate(base, {
                **REQUEST, "context": "32768", "vram_reserved_gib": "23.5", "cpu_cores": "8",
            })

        self.assertEqual(result["estimate"]["run_mode"], "CpuOffload")
        self.assertIsNone(result["estimate"]["decode_tokens_per_second"])
        self.assertEqual(result["estimate"]["decode_qualification"], "core_offload_context_cap")
        self.assertAlmostEqual(result["estimate"]["memory_required_gib"], 1.3937344064)

    def test_out_of_range_request_number_returns_a_client_error(self):
        with self.server() as base, self.assertRaises(HTTPError) as error:
            read_estimate(base, {**REQUEST, "context": "9" * 400})

        self.assertEqual(error.exception.code, 400)
        error.exception.close()
