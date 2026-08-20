"""
Minimal, illustrative MCP (Model Context Protocol) server.

This is a hand-rolled sketch of the JSON-RPC message shapes an MCP server
exchanges with a client, following the pattern described in
../../docs/17-ai-agents-and-mcp/mcp-servers.md. It exists to make that
protocol shape concrete and readable — it is NOT a production
implementation.

For real MCP servers, use the official MCP SDK (`pip install mcp` for
Python) instead of hand-rolling JSON-RPC framing the way this script does —
the SDK handles the initialize handshake, message framing, and error
formatting correctly, and gives you both stdio and HTTP+SSE transports for
free. See ../../docs/17-ai-agents-and-mcp/mcp-servers.md for why that
matters.

This server exposes ONE tool, `get_current_time`, reused directly from
tools.py (the same function the FastAPI agent in main.py calls), over
stdio: it reads one JSON-RPC request per line from stdin and writes one
JSON-RPC response per line to stdout — exactly the framing a host process
talking to a locally-spawned MCP server over a subprocess pipe would use.

Run it directly and paste requests in, one per line (Ctrl-D / Ctrl-C to
exit):

    python mcp_server_example.py

Try pasting these lines one at a time:

    {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_current_time", "arguments": {}}}
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from tools import TOOL_SCHEMAS, get_current_time

SERVER_INFO = {"name": "example-time-mcp-server", "version": "0.1.0"}

# Only expose get_current_time via this illustrative server. A real server
# would register every tool it wants to offer this way, each with its own
# schema (from tools.py) and handler.
EXPOSED_TOOL_SCHEMA = next(schema for schema in TOOL_SCHEMAS if schema["name"] == "get_current_time")


def _error(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _result(id_: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


async def handle_request(request: dict) -> dict:
    method = request.get("method")
    id_ = request.get("id")

    if method == "initialize":
        return _result(
            id_,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": SERVER_INFO,
                "capabilities": {"tools": {}},
            },
        )

    if method == "tools/list":
        return _result(id_, {"tools": [EXPOSED_TOOL_SCHEMA]})

    if method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name != "get_current_time":
            return _error(id_, -32602, f"unknown tool: {name}")

        try:
            # Same discipline a real handler needs: bound execution time so
            # a hung backend can't hang the whole MCP request indefinitely.
            # See ../../docs/17-ai-agents-and-mcp/tool-execution.md.
            output = await asyncio.wait_for(get_current_time(arguments), timeout=5.0)
        except asyncio.TimeoutError:
            return _result(id_, {"isError": True, "content": [{"type": "text", "text": "tool call timed out"}]})
        except Exception as exc:  # noqa: BLE001 - normalize any failure into an MCP error result
            return _result(id_, {"isError": True, "content": [{"type": "text", "text": str(exc)}]})

        return _result(id_, {"content": [{"type": "text", "text": json.dumps(output)}], "isError": False})

    return _error(id_, -32601, f"method not found: {method}")


async def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps(_error(None, -32700, "parse error")), flush=True)
            continue

        response = await handle_request(request)
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
