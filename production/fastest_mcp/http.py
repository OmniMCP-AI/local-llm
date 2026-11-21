"""Run the read-only MCP adapter over a loopback Streamable HTTP listener."""

import asyncio
from contextlib import asynccontextmanager

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.datastructures import MutableHeaders
from starlette.requests import ClientDisconnect, Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route, Router
import uvicorn

MAX_REQUEST_BYTES = 64 * 1024
BODY_TIMEOUT_SECONDS = 10


class Gateway:
    def __init__(self, server, public_origin):
        self.sessions = StreamableHTTPSessionManager(server, stateless=True, json_response=True)
        self.public_origin = public_origin

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)

        async def send_no_store(message):
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["Cache-Control"] = "no-store"
            await send(message)

        async def reject(status, text, headers=None):
            await PlainTextResponse(text, status_code=status, headers=headers)(scope, receive, send_no_store)

        port = scope["server"][1]
        allowed = {}
        for host in ("127.0.0.1", "localhost"):
            authority = f"{host}:{port}"
            origin = "http://" + (host if port == 80 else authority)
            allowed[authority] = origin
            if port == 80:
                allowed[host] = origin
        if self.public_origin:
            allowed[self.public_origin.removeprefix("https://")] = self.public_origin

        hosts = request.headers.getlist("host")
        if len(hosts) != 1 or hosts[0].lower() not in allowed:
            await reject(421, "Invalid Host header")
            return
        origins = request.headers.getlist("origin")
        if origins and origins != [allowed[hosts[0].lower()]]:
            await reject(403, "Invalid Origin header")
            return
        if request.method != "POST":
            await reject(405, "Only POST is supported", {"Allow": "POST"})
            return
        length = request.headers.get("content-length", "0").lstrip("0") or "0"
        if len(length) > len(str(MAX_REQUEST_BYTES)) or int(length) > MAX_REQUEST_BYTES:
            await reject(413, "MCP request exceeds 64 KiB")
            return

        body = bytearray()
        try:
            async with asyncio.timeout(BODY_TIMEOUT_SECONDS):
                async for chunk in request.stream():
                    if len(body) + len(chunk) > MAX_REQUEST_BYTES:
                        await reject(413, "MCP request exceeds 64 KiB")
                        return
                    body.extend(chunk)
        except ClientDisconnect:
            return
        except TimeoutError:
            await reject(408, "MCP request body timed out")
            return

        async def receive_body():
            nonlocal body
            if body is not None:
                buffered, body = bytes(body), None
                return {"type": "http.request", "body": buffered, "more_body": False}
            return await receive()

        await self.sessions.handle_request(scope, receive_body, send_no_store)


def serve_http(server, port, public_origin):
    gateway = Gateway(server, public_origin)

    @asynccontextmanager
    async def lifespan(_app):
        async with gateway.sessions.run():
            yield

    app = Router(routes=[Route("/mcp", gateway)], lifespan=lifespan, redirect_slashes=False)
    uvicorn.run(app, host="127.0.0.1", port=port, proxy_headers=False, ws="none",
                access_log=False, limit_concurrency=32, workers=1)
