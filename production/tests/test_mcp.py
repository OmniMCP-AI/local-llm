"""Exercise the local MCP transport with the official SDK in a subprocess."""

from contextlib import asynccontextmanager, closing, contextmanager
from datetime import timedelta
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from importlib.util import find_spec
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread
from urllib.parse import urlencode
import unittest

from test_public_api import api_server


HAS_SDK = find_spec("mcp") is not None


@asynccontextmanager
async def mcp_client(port, *options):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    command = StdioServerParameters(
        command=sys.executable,
        args=["-B", "-m", "fastest_mcp", "--port", str(port), *options],
        cwd=Path(__file__).resolve().parents[1],
    )
    async with stdio_client(command) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=10)) as client:
            yield client


def get(port, path, arguments=None):
    if arguments:
        path += "?" + urlencode(arguments)
    with closing(HTTPConnection("127.0.0.1", port, timeout=5)) as connection:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.read().decode()


@contextmanager
def pages_catalog(routes):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, body = routes.get(self.path, (404, {"error": "Not found"}))
            self.send_response(status)
            if status == 302:
                self.send_header("Location", body)
                self.end_headers()
                return
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        worker = Thread(target=server.serve_forever)
        worker.start()
        try:
            yield server.server_port
        finally:
            server.shutdown()
            worker.join(timeout=5)
            if worker.is_alive():
                raise RuntimeError("Catalog test did not stop its HTTP listener")


@unittest.skipUnless(HAS_SDK, "Install fastest_mcp/requirements.txt to test stdio MCP")
class McpTest(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_client_repeats_the_website_decision(self):
        with api_server() as server:
            port = server.server_port
            async with mcp_client(port) as client:
                handshake = await client.initialize()
                self.assertEqual(version("mcp"), "1.30.0")
                self.assertEqual(handshake.protocolVersion, "2025-11-25")
                self.assertEqual(handshake.serverInfo.name, "fastest-ai-evidence")
                self.assertIsNotNone(handshake.capabilities.tools)
                self.assertIsNotNone(handshake.capabilities.resources)
                tools = (await client.list_tools()).tools
                self.assertEqual({tool.name for tool in tools}, {
                    "v1_search", "v1_coverage", "v1_comparison", "v1_profile_comparison", "v1_calculator",
                })
                self.assertTrue(all(tool.annotations.readOnlyHint for tool in tools))
                catalog = await client.call_tool("v1_catalog", {"kind": "machines"})
                self.assertTrue(catalog.isError)
                self.assertIn("--catalog-origin", catalog.content[0].text)

                args = {"entry": "budget", "budget": "1200"}
                decision = await client.call_tool("v1_comparison", args)
                self.assertFalse(decision.isError)
                result = decision.structuredContent
                status, api = get(port, "/api/v1/comparison", args)
                self.assertEqual(status, 200)
                self.assertEqual(result, json.loads(api))
                self.assertEqual(json.loads(decision.content[0].text), result)
                self.assertIsNone(result["recommendation"])
                budget = result["rows"][0]["goals"]["budget"]
                self.assertEqual((budget["status"], budget["value"]), ("unknown", None))
                status, html = get(port, result["url"])
                self.assertEqual(status, 200)
                self.assertIn(result["release_id"], html)
                self.assertIn(budget["reason"], html)

                args = {"scenario": "illustrative", "monthly_accepted": 1800, "months": 24}
                cost = await client.call_tool("v1_calculator", args)
                self.assertFalse(cost.isError)
                result = cost.structuredContent
                status, api = get(port, "/api/v1/calculator", args)
                self.assertEqual(status, 200)
                self.assertEqual(result, json.loads(api))
                self.assertEqual(result["estimate_kind"], "illustrative")
                self.assertEqual(result["options"]["upgrade"]["totals"]["nominal_cost"], "589.472")
                self.assertEqual(result["options"]["api"]["monthly"]["recurring_cost"], "4.1984")
                status, html = get(port, result["url"])
                self.assertEqual(status, 200)
                self.assertIn(result["revision"], html)
                self.assertIn("589.472", html)

                resources = (await client.list_resources()).resources
                self.assertEqual([str(resource.uri) for resource in resources], ["fastest://v1/catalog"])
                catalog = await client.read_resource(resources[0].uri)
                status, api = get(port, "/api/v1/search")
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(catalog.contents[0].text), json.loads(api))
                self.assertEqual((await client.list_resource_templates()).resourceTemplates, [])


    async def test_sdk_client_reads_pinned_pages_catalog(self):
        revision = "v1-1234567890abcdef"
        root = "/catalog/" + revision
        snapshot = "1234567890abcdef" * 4
        first = {"kind": "runtimes", "limit": 1}
        second = {**first, "revision": revision, "offset": 1}

        def entry(identifier, name, source):
            return {
                "id": identifier, "name": name, "detail": None, "source": source,
                "html": f"{root}/runtimes/{identifier}.html",
                "markdown": f"{root}/runtimes/{identifier}.md",
            }

        def page(result, offset, next_offset):
            return {
                "apiVersion": "1", "revision": revision, "snapshotId": snapshot, "kind": "runtimes",
                "manifest": f"{root}/manifest.json",
                "scope": "Catalog metadata. Benchmark measurements are published separately.",
                "results": [result],
                "pagination": {"limit": 1, "offset": offset, "total": 2, "nextOffset": next_offset},
            }

        pages = (
            (first, page(entry("llama.cpp", "llama.cpp", "https://github.com/ggml-org/llama.cpp"), 0, 1)),
            (second, page(entry("vllm", "vLLM", "https://github.com/vllm-project/vllm"), 1, None)),
        )
        path = "/api/v1/catalog"
        routes = {path + "?" + urlencode(selection): (200, body) for selection, body in pages}
        with api_server() as evidence, pages_catalog(routes) as port:
            async with mcp_client(evidence.server_port, "--catalog-origin", f"http://127.0.0.1:{port}") as client:
                await client.initialize()
                tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                self.assertTrue(tools["v1_catalog"].annotations.readOnlyHint)
                self.assertIn("v1_search", tools)
                for selection, expected in pages:
                    result = await client.call_tool("v1_catalog", selection)
                    self.assertFalse(result.isError)
                    status, api = get(port, path, selection)
                    self.assertEqual(status, 200)
                    self.assertEqual(result.structuredContent, json.loads(api))
                    self.assertEqual(result.structuredContent, expected)


    async def test_sdk_pages_catalog_rechecks_withdrawals_and_refuses_redirects_and_extra_selectors(self):
        selection = {"kind": "cards", "revision": "v1-1234567890abcdef"}
        path = "/api/v1/catalog?" + urlencode(selection)
        page = {
            "apiVersion": "1", "revision": selection["revision"], "snapshotId": "1234567890abcdef" * 4,
            "kind": selection["kind"], "manifest": "/catalog/v1-1234567890abcdef/manifest.json",
            "scope": "Catalog metadata. Benchmark measurements are published separately.",
            "results": [], "pagination": {"limit": 25, "offset": 0, "total": 0, "nextOffset": None},
        }
        routes = {path: (200, page), "/private": (200, page)}
        with api_server() as evidence, pages_catalog(routes) as port:
            async with mcp_client(evidence.server_port, "--catalog-origin", f"http://127.0.0.1:{port}") as client:
                await client.initialize()
                initial = await client.call_tool("v1_catalog", selection)
                self.assertEqual(initial.structuredContent, page)

                routes[path] = (410, {"error": "Private upstream message"})
                withdrawn = await client.call_tool("v1_catalog", selection)
                self.assertTrue(withdrawn.isError)
                self.assertIsNone(withdrawn.structuredContent)
                self.assertEqual(withdrawn.content[0].text, "Public rights have ended for this release.")

                routes[path] = (302, "/private")
                redirected = await client.call_tool("v1_catalog", selection)
                self.assertTrue(redirected.isError)
                self.assertIsNone(redirected.structuredContent)

                for arguments in ({**selection, "url": "https://example.invalid/private"},
                                  {**selection, "limit": 26}, {"kind": "cards", "offset": 1}):
                    with self.subTest(arguments=arguments):
                        invalid = await client.call_tool("v1_catalog", arguments)
                        self.assertTrue(invalid.isError)
                        self.assertEqual(invalid.content[0].text, "Invalid public evidence selection.")

    def test_catalog_origin_configuration_requires_https_or_loopback_and_an_origin_only(self):
        for origin in ("http://example.invalid", "https://user@example.invalid",
                       "https://example.invalid/api/v1/catalog", "https://example.invalid/?q=cards"):
            with self.subTest(origin=origin):
                result = subprocess.run(
                    [sys.executable, "-B", "-m", "fastest_mcp", "--catalog-origin", origin],
                    cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("--catalog-origin must be an HTTPS origin", result.stderr)
                self.assertNotIn(origin, result.stderr)

    async def test_sdk_client_cannot_select_private_or_arbitrary_operations(self):
        from mcp import McpError

        with api_server() as server:
            async with mcp_client(server.server_port) as client:
                await client.initialize()
                for name, arguments in (
                    ("v1_search", {"fields": ["unpublished_operator_note"]}),
                    ("v1_search", {"sql": "SELECT * FROM editorial_notes"}),
                    ("v1_search", {"url": "https://example.invalid/private"}),
                    ("v1_search", {"q": "x" * 129}),
                    ("v1_search", {"limit": 101}),
                    ("v1_search", {"limit": "1"}),
                    ("v1_search", {"offset": 10001}),
                    ("v1_search", {"offset": 1}),
                    ("v1_profile_comparison", {"kind": "models", "id": "../private"}),
                    ("v1_withdraw", {"release": "current"}),
                ):
                    with self.subTest(tool=name, arguments=arguments):
                        result = await client.call_tool(name, arguments)
                        self.assertTrue(result.isError)
                        self.assertIsNone(result.structuredContent)

                for uri in ("file:///etc/passwd", "https://example.invalid/private", "fastest://v1/catalog?fields=private"):
                    with self.subTest(uri=uri), self.assertRaises(McpError):
                        await client.read_resource(uri)

                search = {"kind": "machines", "limit": 1}
                first = await client.call_tool("v1_search", search)
                self.assertFalse(first.isError)
                page = first.structuredContent
                self.assertEqual([item["id"] for item in page["results"]], ["apple-m4"])
                second = await client.call_tool("v1_search", {
                    **search, "revision": page["revision"], "offset": page["pagination"]["next_offset"],
                })
                self.assertFalse(second.isError)
                self.assertEqual([item["id"] for item in second.structuredContent["results"]], ["rtx-4090"])
                self.assertIsNone(second.structuredContent["pagination"]["next_offset"])
