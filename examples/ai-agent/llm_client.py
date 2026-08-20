"""
Minimal, provider-agnostic "chat completion with tools" client abstraction
for the agent loop example.

Follows the same pattern as examples/llm-streaming/llm_client.py: a generic
call function that routes to a real provider if `LLM_API_KEY` is
configured (a clearly-commented pseudo-implementation only — we can't
assume which provider/SDK you have), and otherwise falls back to a small
local simulation so the whole agent loop is runnable and demonstrably
correct with zero external credentials.

Response shape (Anthropic/OpenAI-compatible-style, matching
../../docs/14-ai-api-engineering/tool-calling.md):

    {
      "content": [
        {"type": "text", "text": "..."} |
        {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
      ],
      "stop_reason": "tool_use" | "end_turn"
    }
"""

from __future__ import annotations

import os
import re
from typing import Any

LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "example-model-v1")


async def call_llm_with_tools(
    messages: list[dict[str, Any]], tools_schema: list[dict[str, Any]]
) -> dict[str, Any]:
    """Send the conversation so far plus the available tool schemas, and
    get back either a tool-use request or a final text answer."""
    if LLM_API_KEY:
        return await _call_real_provider(messages, tools_schema)
    return _simulate_response(messages, tools_schema)


async def _call_real_provider(
    messages: list[dict[str, Any]], tools_schema: list[dict[str, Any]]
) -> dict[str, Any]:
    """Illustrative pseudo-implementation of a real tool-calling chat
    completion call. The general shape, using `httpx` as a generic HTTP
    client:

        import httpx

        response = httpx.post(
            "https://api.your-provider.example/v1/messages",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={
                "model": LLM_MODEL,
                "max_tokens": 500,
                "tools": tools_schema,
                "messages": messages,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    See ../../docs/14-ai-api-engineering/tool-calling.md for the full
    request/response shape, including how `tool_use_id` correlates a
    `tool_result` back to the specific call it answers.
    """
    raise NotImplementedError(
        "LLM_API_KEY is set, but _call_real_provider() is still a stub. "
        "Plug in a real provider SDK/HTTP call here, following the shape "
        "described in this function's docstring."
    )


_MATH_RE = re.compile(r"^[\s\d+\-*/().]+$")
_SEARCH_TRIGGER_RE = re.compile(r"\b(search for|search|look up|what is|find|please)\b")


def _simulate_response(
    messages: list[dict[str, Any]], tools_schema: list[dict[str, Any]]
) -> dict[str, Any]:
    """A small rule-based stand-in for a model deciding whether to call a
    tool. Good enough to exercise the full agent loop end-to-end with zero
    provider credentials — this is NOT a real language model."""
    last = messages[-1]
    last_content = last.get("content")

    # If the most recent message is a tool result being fed back in, give a
    # final answer summarizing it instead of calling another tool. This
    # keeps the simulated loop to two iterations (call tool, then answer),
    # which is enough to exercise the loop mechanics end-to-end.
    if isinstance(last_content, list) and any(
        block.get("type") == "tool_result" for block in last_content
    ):
        tool_result_text = next(
            block["content"] for block in last_content if block.get("type") == "tool_result"
        )
        return {
            "content": [{"type": "text", "text": f"Here's what I found: {tool_result_text}"}],
            "stop_reason": "end_turn",
        }

    # Otherwise this is the user's original question — use simple
    # heuristics to decide if it looks like a job for one of our tools.
    user_text = last_content if isinstance(last_content, str) else ""
    available = {tool["name"] for tool in tools_schema}

    stripped = user_text.strip().rstrip("? ")
    if "calculator" in available and stripped and _MATH_RE.match(stripped) and any(c.isdigit() for c in stripped):
        return _tool_use_response("calculator", {"expression": stripped})

    lowered = user_text.lower()
    if "get_current_time" in available and "time" in lowered:
        return _tool_use_response("get_current_time", {})

    if "search" in available and _SEARCH_TRIGGER_RE.search(lowered):
        query = _SEARCH_TRIGGER_RE.sub("", lowered).strip(" ?.")
        return _tool_use_response("search", {"query": query or user_text})

    return {
        "content": [{"type": "text", "text": f'(simulated, no tool needed) You said: "{user_text}"'}],
        "stop_reason": "end_turn",
    }


def _tool_use_response(name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{"type": "tool_use", "id": f"toolu_sim_{name}", "name": name, "input": tool_input}],
        "stop_reason": "tool_use",
    }
