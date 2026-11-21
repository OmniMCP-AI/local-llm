"""Read public evidence and catalog metadata over MCP."""

import argparse
import asyncio
from contextlib import closing
from functools import partial
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from importlib.metadata import version
import json
import re
from urllib.parse import urlencode, urlsplit

from jsonschema import Draft202012Validator
from mcp import McpError, types
from mcp.server import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.stdio import stdio_server
from referencing import Registry

SDK_VERSION = "1.30.0"
PROTOCOL_VERSION = "2025-11-25"
API_VERSION = "1.0.0"
OPENAPI_PATH = "/api/v1/openapi.json"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
CATALOG_URI = "fastest://v1/catalog"
PAGES_CATALOG_PATH = "/api/v1/catalog"
PAGES_CATALOG_TOOL = "v1_catalog"
PAGES_CATALOG_INPUT = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["cards", "machines", "models", "runtimes"]},
        "revision": {"type": "string", "pattern": "^v1-[a-f0-9]{16}$"},
        "q": {"type": "string", "maxLength": 200},
        "limit": {"type": "integer", "minimum": 1, "maximum": 25},
        "offset": {"type": "integer", "minimum": 0, "maximum": 999999},
    },
    "required": ["kind"],
    "additionalProperties": False,
    "if": {"properties": {"offset": {"minimum": 1}}, "required": ["offset"]},
    "then": {"required": ["revision"]},
}
EVIDENCE_TEMPLATE = "fastest://v1/releases/{release_id}/evidence"
EVIDENCE_URI = re.compile(r"fastest://v1/releases/([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})/evidence")
AGENT_TASK_TOOL = "v1_agent_task"
AGENT_TASK_TEMPLATE = "fastest://v1/agent-task/{pin}"
AGENT_TASK_URI = re.compile(r"fastest://v1/agent-task/([a-f0-9]{64})")
TOOL_PATHS = {
    "v1_search": "/api/v1/search",
    "v1_coverage": "/api/v1/coverage",
    "v1_evidence": "/api/v1/evidence",
    "v1_comparison": "/api/v1/comparison",
    "v1_profile_comparison": "/api/v1/comparison/profile",
    AGENT_TASK_TOOL: "/api/v1/comparison/agent-task",
    "v1_historical_offers": "/api/v1/historical-offers",
    "v1_calculator": "/api/v1/calculator",
}
PUBLIC_ERRORS = {
    400: "Invalid public evidence selection.",
    404: "Public release or operation unavailable.",
    410: "Public rights have ended for this release.",
    429: "Public evidence request limit reached.",
}
UNAVAILABLE = "Public evidence service unavailable."


class PublicApiError(Exception):
    pass


def get_json(connect, path, arguments=None):
    try:
        if arguments:
            path += "?" + urlencode(arguments)
        with closing(connect()) as client:
            client.request("GET", path)
            response = client.getresponse()
            if response.status != 200:
                raise PublicApiError(PUBLIC_ERRORS.get(response.status, UNAVAILABLE))
            if response.headers.get_content_type() not in {"application/json", "application/vnd.oai.openapi+json"}:
                raise PublicApiError(UNAVAILABLE)
            body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise PublicApiError("Public response exceeds the MCP limit. Select a smaller page where available.")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise PublicApiError(UNAVAILABLE)
        return data
    except (HTTPException, OSError, ValueError, RecursionError):
        raise PublicApiError(UNAVAILABLE) from None


def pages_connection(origin):
    invalid = PublicApiError("--catalog-origin must be an HTTPS origin or a loopback HTTP origin.")
    if any(ord(character) < 33 or ord(character) == 127 or character in "?#\\" for character in origin):
        raise invalid
    try:
        url = urlsplit(origin)
        host, port = url.hostname, url.port
    except ValueError:
        raise invalid from None
    if not host or port == 0 or url.username is not None or url.path not in {"", "/"}:
        raise invalid
    if url.scheme == "https":
        return partial(HTTPSConnection, host, port, timeout=5)
    if url.scheme == "http" and host in {"127.0.0.1", "::1"}:
        return partial(HTTPConnection, host, port, timeout=5)
    raise invalid


def build_server(port, catalog_origin=None):
    connect_evidence = partial(HTTPConnection, "127.0.0.1", port, timeout=5)
    connect_catalog = pages_connection(catalog_origin) if catalog_origin is not None else None
    description = get_json(connect_evidence, OPENAPI_PATH)
    if description.get("info", {}).get("version") != API_VERSION:
        raise PublicApiError("The listener must serve public API version " + API_VERSION + ".")

    tools = {}
    validators = {}

    def register_tool(name, summary, input_schema, *, open_world=False):
        tools[name] = types.Tool(
            name=name, description=summary, inputSchema=input_schema,
            annotations=types.ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=open_world),
        )
        validators[name] = Draft202012Validator(input_schema, registry=Registry())

    for name, path in TOOL_PATHS.items():
        operation = description["paths"].get(path, {}).get("get")
        if operation is None:
            continue
        properties, required = {}, []
        for parameter in operation["parameters"]:
            schema = dict(parameter["schema"])
            if schema["type"] == "string":
                schema.setdefault("maxLength", 128)
            properties[parameter["name"]] = schema
            if parameter["required"]:
                required.append(parameter["name"])
        input_schema = {"type": "object", "properties": properties, "required": required,
                        "additionalProperties": False}
        register_tool(name, operation["summary"], input_schema)

    if connect_catalog is not None:
        register_tool(
            PAGES_CATALOG_TOOL,
            "Browse or search the published Pages catalog. Use an exact owner/repository ID for model lookups. "
            "Use the result revision and nextOffset to fetch the next page. "
            f"Resolve relative profile and manifest links against {catalog_origin.rstrip('/')}.",
            PAGES_CATALOG_INPUT,
            open_world=True,
        )

    server = Server("fastest-ai-evidence", version=API_VERSION,
                    instructions="Cite the public result's release or revision ID with its sources and exclusions.")

    async def read(path, arguments=None):
        result = await asyncio.to_thread(get_json, connect_evidence, path, arguments)
        if result.get("api_version") != API_VERSION:
            raise PublicApiError(UNAVAILABLE)
        return result

    @server.list_tools()
    async def list_tools():
        return list(tools.values())

    @server.call_tool(validate_input=False)
    async def call_tool(name, arguments):
        # Reject invalid selectors without echoing client-supplied values.
        try:
            if name == PAGES_CATALOG_TOOL and connect_catalog is None:
                raise PublicApiError("Configure --catalog-origin to enable the Pages catalog tool.")
            if name not in tools:
                raise PublicApiError("Unsupported read-only tool.")
            if not validators[name].is_valid(arguments):
                raise PublicApiError(PUBLIC_ERRORS[400])
            if name == PAGES_CATALOG_TOOL:
                result = await asyncio.to_thread(get_json, connect_catalog, PAGES_CATALOG_PATH, arguments)
                if result.get("apiVersion") != "1":
                    raise PublicApiError(UNAVAILABLE)
                return result
            return await read(TOOL_PATHS[name], arguments)
        except PublicApiError as error:
            return types.CallToolResult(isError=True, content=[types.TextContent(type="text", text=str(error))])

    @server.list_resources()
    async def list_resources():
        return [types.Resource(uri=CATALOG_URI, name="Public catalog", mimeType="application/json")]

    @server.list_resource_templates()
    async def list_resource_templates():
        return [
            types.ResourceTemplate(uriTemplate=template, name=label, mimeType="application/json")
            for name, template, label in (
                ("v1_evidence", EVIDENCE_TEMPLATE, "Pinned public evidence"),
                (AGENT_TASK_TOOL, AGENT_TASK_TEMPLATE, "Pinned public agent-task comparison"),
            )
            if name in tools
        ]

    @server.read_resource()
    async def read_resource(uri):
        address = str(uri)
        evidence = EVIDENCE_URI.fullmatch(address)
        agent_task = AGENT_TASK_URI.fullmatch(address)
        if address == CATALOG_URI:
            name, arguments = "v1_search", None
        elif evidence and "v1_evidence" in tools:
            name, arguments = "v1_evidence", {"release": evidence[1]}
        elif agent_task and AGENT_TASK_TOOL in tools:
            name, arguments = AGENT_TASK_TOOL, {"release": agent_task[1]}
        else:
            raise McpError(types.ErrorData(code=-32002, message="Public resource unavailable."))
        try:
            result = await read(TOOL_PATHS[name], arguments)
        except PublicApiError as error:
            raise McpError(types.ErrorData(code=-32002, message=str(error))) from None
        return [ReadResourceContents(content=json.dumps(result, ensure_ascii=False), mime_type="application/json")]

    return server


async def serve(server):
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def http_origin(origin):
    match = re.fullmatch(r"https://[a-z0-9-]+(?:\.[a-z0-9-]+)*(?::([1-9][0-9]{0,4}))?", origin)
    port = int(match[1]) if match and match[1] else None
    if not match or (port is not None and (port == 443 or port > 65535)):
        raise argparse.ArgumentTypeError("--http-origin must be a canonical HTTPS origin (omit the default port)")
    return origin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=8000, type=int,
                        help="Port of the local public API listener on 127.0.0.1 (default 8000)")
    parser.add_argument("--catalog-origin", help="Optional origin of the published Pages catalog (HTTPS or loopback HTTP)")
    parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio",
                        help="MCP transport (default stdio)")
    parser.add_argument("--http-port", default=8001, type=int,
                        help="Streamable HTTP listener on 127.0.0.1 (default 8001)")
    parser.add_argument("--http-origin", type=http_origin,
                        help="Optional canonical HTTPS origin for a reverse proxy in Streamable HTTP mode")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be from 1 to 65535")
    if not 0 <= args.http_port <= 65535:
        parser.error("--http-port must be from 0 to 65535")
    if args.http_origin and args.transport != "streamable-http":
        parser.error("--http-origin requires --transport streamable-http")
    if version("mcp") != SDK_VERSION or types.LATEST_PROTOCOL_VERSION != PROTOCOL_VERSION:
        parser.exit(1, f"Install MCP Python SDK {SDK_VERSION} from fastest_mcp/requirements.txt.\n")
    try:
        server = build_server(args.port, args.catalog_origin)
    except (PublicApiError, KeyError, TypeError, AttributeError) as error:
        parser.exit(1, (str(error) if isinstance(error, PublicApiError) else UNAVAILABLE) + "\n")
    if args.transport == "streamable-http":
        from .http import serve_http

        serve_http(server, args.http_port, args.http_origin)
    else:
        asyncio.run(serve(server))


if __name__ == "__main__":
    main()
