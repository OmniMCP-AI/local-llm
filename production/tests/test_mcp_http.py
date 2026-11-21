"""Exercise Streamable HTTP over a real loopback socket with the official SDK."""

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import timedelta
import json
from pathlib import Path
import sys
import unittest

from test_mcp import HAS_SDK, get, mcp_client
from test_public_api import api_server


@asynccontextmanager
async def mcp_http_server(port, *options):
    prefix = b"Uvicorn running on http://127.0.0.1:"
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-B", "-m", "fastest_mcp", "--port", str(port),
        "--transport", "streamable-http", "--http-port", "0", *options,
        cwd=Path(__file__).resolve().parents[1],
        stderr=asyncio.subprocess.PIPE,
    )
    startup = []
    try:
        async with asyncio.timeout(10):
            while line := await process.stderr.readline():
                startup.append(line)
                if prefix in line:
                    listener = int(line.split(prefix, 1)[1].split()[0])
                    break
            else:
                raise RuntimeError(b"".join(startup).decode())
        yield f"http://127.0.0.1:{listener}/mcp"
    finally:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.terminate()
            try:
                await asyncio.wait_for(process.communicate(), 5)
            except TimeoutError:
                with suppress(ProcessLookupError):
                    process.kill()
                await process.wait()
        assert process.returncode is not None


@asynccontextmanager
async def mcp_http_client(url):
    from httpx import AsyncClient
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with AsyncClient(timeout=10, trust_env=False) as http:
        async with streamable_http_client(url, http_client=http) as (reader, writer, get_session_id):
            async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=10)) as client:
                handshake = await client.initialize()
                assert get_session_id() is None
                yield client, handshake


@unittest.skipUnless(HAS_SDK, "Install fastest_mcp/requirements.txt to test HTTP MCP")
class McpHttpTest(unittest.IsolatedAsyncioTestCase):
    async def test_streamable_http_replays_the_same_read_only_decision_as_stdio(self):
        from mcp import McpError

        with api_server() as server:
            port = server.server_port
            async with mcp_http_server(port) as url, mcp_http_client(url) as (http, handshake):
                async with mcp_client(port) as stdio:
                    self.assertEqual(handshake, await stdio.initialize())
                    self.assertEqual(handshake.protocolVersion, "2025-11-25")
                    self.assertEqual(await http.list_tools(), await stdio.list_tools())
                    self.assertEqual(await http.list_resources(), await stdio.list_resources())
                    self.assertEqual(await http.list_resource_templates(), await stdio.list_resource_templates())
                    self.assertEqual(await http.read_resource("fastest://v1/catalog"),
                                     await stdio.read_resource("fastest://v1/catalog"))

                    args = {"scenario": "illustrative", "monthly_accepted": 1800, "months": 24}
                    decision = await http.call_tool("v1_calculator", args)
                    self.assertEqual(decision, await stdio.call_tool("v1_calculator", args))
                    self.assertFalse(decision.isError)
                    result = decision.structuredContent
                    status, body = get(port, "/api/v1/calculator", args)
                    self.assertEqual(status, 200)
                    self.assertEqual(result, json.loads(body))
                    self.assertEqual(result["options"]["upgrade"]["totals"]["nominal_cost"], "589.472")
                    self.assertEqual(result["options"]["api"]["monthly"]["recurring_cost"], "4.1984")
                    status, html = get(port, result["url"])
                    self.assertEqual(status, 200)
                    self.assertIn(result["revision"], html)
                    self.assertIn("589.472", html)

                    for name, arguments in (
                        ("v1_search", {"fields": ["unpublished_operator_note"]}),
                        ("v1_search", {"q": "x" * 129}),
                        ("v1_search", {"offset": 10001}),
                        ("v1_withdraw", {"release": "current"}),
                        ("run_command", {"command": "unexpected"}),
                    ):
                        with self.subTest(tool=name):
                            denied = await http.call_tool(name, arguments)
                            self.assertEqual(denied, await stdio.call_tool(name, arguments))
                            self.assertTrue(denied.isError)
                            self.assertIsNone(denied.structuredContent)
                    with self.assertRaises(McpError):
                        await http.read_resource("file:///etc/passwd")

    async def test_http_rejects_untrusted_authorities_and_oversized_uploads(self):
        from httpx import AsyncClient

        origins = {"Host": "mcp.example", "Origin": "https://mcp.example"}
        headers = {
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2025-11-25",
            "Content-Type": "application/json",
        }
        ping = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        with api_server() as server:
            async with mcp_http_server(server.server_port, "--http-origin", "https://mcp.example") as url:
                async with AsyncClient(timeout=5, trust_env=False, headers=headers) as http:
                    for authority in ({}, {"Origin": url.removesuffix("/mcp")}, {"Host": "mcp.example"}, origins):
                        with self.subTest(authority=authority):
                            response = await http.post(url, headers=authority, json=ping)
                            self.assertEqual(response.status_code, 200)
                            self.assertEqual(response.json()["result"], {})
                            self.assertEqual(response.headers["cache-control"], "no-store")

                    for rejected, status in (
                        ({"Host": "mcp.example.invalid"}, 421),
                        ({"Origin": "https://untrusted.example"}, 403),
                        ({"Origin": "https://mcp.example"}, 403),
                        ({"Origin": ""}, 403),
                        ({**origins, "Origin": "null"}, 403),
                        ({**origins, "Origin": "https://mcp.example:444"}, 403),
                    ):
                        with self.subTest(headers=rejected):
                            self.assertEqual((await http.post(url, headers=rejected, json=ping)).status_code, status)

                    duplicate = await http.post(
                        url, json=ping, headers=[*origins.items(), ("Origin", "https://untrusted.example")],
                    )
                    self.assertEqual(duplicate.status_code, 403)
                    stream = await http.get(url, headers={**origins, "Accept": "text/event-stream"})
                    self.assertEqual(stream.status_code, 405)
                    self.assertEqual(stream.headers["allow"], "POST")
                    self.assertEqual((await http.post(url + "/", json=ping)).status_code, 404)

                    self.assertEqual((await http.post(url, content=b"x" * (64 * 1024 + 1))).status_code, 413)

                    async def chunks():
                        for _ in range(3):
                            yield b"x" * (32 * 1024)

                    self.assertEqual((await http.post(url, content=chunks())).status_code, 413)
                    self.assertEqual((await http.post(url, json=ping)).status_code, 200)
