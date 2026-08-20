"""
Tool definitions for the agent loop example.

Each tool has (1) a JSON schema describing its name, description, and input
shape — the same schema format an Anthropic/OpenAI-compatible tool-calling
API expects — and (2) an async Python function that actually executes it.
`register_tool` keeps the schema and handler for a given tool defined
together so they can't drift out of sync.

This is a minimal sketch. See
../../docs/17-ai-agents-and-mcp/tool-execution.md for the full production
discipline (argument validation with a real schema library, per-call
timeouts, sandboxing, least-privilege credentials) a real tool executor
needs beyond what's shown here.
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

ToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]

TOOL_REGISTRY: dict[str, ToolHandler] = {}
TOOL_SCHEMAS: list[dict[str, Any]] = []


def register_tool(schema: dict[str, Any]) -> Callable[[ToolHandler], ToolHandler]:
    def decorator(fn: ToolHandler) -> ToolHandler:
        TOOL_REGISTRY[schema["name"]] = fn
        TOOL_SCHEMAS.append(schema)
        return fn

    return decorator


# --- calculator -------------------------------------------------------------

_ALLOWED_OPERATORS: dict[type, Callable[..., float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    """Evaluate a restricted arithmetic AST: numbers, + - * / ** and
    parentheses only. Deliberately NOT a general `eval()` — no names, no
    attribute access, no function calls, no subscripting — so a malformed
    or adversarial expression can't do anything beyond arithmetic."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"unsupported expression syntax near: {ast.dump(node)}")


@register_tool(
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression (+, -, *, /, **, parentheses) and return the numeric result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "e.g. '(4 + 5) * 2'"},
            },
            "required": ["expression"],
        },
    }
)
async def calculator(args: dict[str, Any]) -> dict[str, Any]:
    expression = args["expression"]
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree)
    except Exception as exc:  # noqa: BLE001 - feed the error back to the caller, don't crash the loop
        return {"error": f"could not evaluate expression: {exc}"}
    return {"expression": expression, "result": result}


# --- get_current_time --------------------------------------------------------

@register_tool(
    {
        "name": "get_current_time",
        "description": "Get the current date and time in UTC.",
        "input_schema": {"type": "object", "properties": {}},
    }
)
async def get_current_time(args: dict[str, Any]) -> dict[str, Any]:
    return {"utc_time": datetime.now(timezone.utc).isoformat()}


# --- search (mock) ------------------------------------------------------------

_MOCK_INDEX: dict[str, str] = {
    "fastapi": "FastAPI is a modern, high-performance Python web framework based on standard type hints.",
    "rate limiting": "Rate limiting caps how many requests a client can make in a given time window, protecting a service from abuse.",
    "websocket": "WebSocket is a protocol providing full-duplex communication over a single long-lived TCP connection.",
    "mcp": "The Model Context Protocol (MCP) standardizes how AI applications connect to external tools and data sources.",
    "rag": "Retrieval-Augmented Generation (RAG) grounds an LLM's answer in content retrieved from an external knowledge source.",
}


@register_tool(
    {
        "name": "search",
        "description": "Search a small mock knowledge base for a topic and return a short summary. This is NOT a real web search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "topic to search for"},
            },
            "required": ["query"],
        },
    }
)
async def search(args: dict[str, Any]) -> dict[str, Any]:
    query = args["query"].strip().lower()
    for key, summary in _MOCK_INDEX.items():
        if key in query or query in key:
            return {"query": args["query"], "result": summary}
    return {"query": args["query"], "result": "No results found in the mock index."}
