"""Exercise the local MCP transport with the official SDK in a subprocess."""

from contextlib import asynccontextmanager, closing
from datetime import timedelta
from http.client import HTTPConnection
from importlib.metadata import version
from importlib.util import find_spec
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
import unittest

from test_public_api import api_server


HAS_SDK = find_spec("mcp") is not None


@asynccontextmanager
async def mcp_client(port):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    command = StdioServerParameters(
        command=sys.executable,
        args=["-B", "-m", "fastest_mcp", "--port", str(port)],
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
