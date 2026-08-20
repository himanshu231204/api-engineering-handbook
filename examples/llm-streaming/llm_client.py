"""
Minimal, provider-agnostic streaming LLM client abstraction.

This module deliberately does NOT depend on any specific provider SDK. It
defines the *shape* a real streaming chat-completion call takes — an async
generator that yields text chunks as they arrive — and a clearly-marked
pseudo-implementation showing where a real HTTP call to an
Anthropic/OpenAI-compatible-style streaming chat completion API would go.

To use this against a real provider:
  1. `pip install anthropic` (or `openai`, or whichever SDK you use).
  2. Replace the body of `stream_chat_completion` below with a real call to
     that SDK's streaming chat/messages endpoint, yielding each text delta
     as it's received instead of the simulated tokens here.
  3. Set the corresponding API key as an environment variable (see
     `.env.example`) — never hardcode it in source.

No API key is required to run this example as-is: `stream_chat_completion`
falls back to a small local token generator so the FastAPI SSE endpoint is
runnable and demonstrably correct without any provider credentials.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

# Read the API key (and model) from the environment. Never hardcode a key
# here — see ../../docs/10-api-security/secrets-management.md.
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "example-model-v1")


async def stream_chat_completion(prompt: str) -> AsyncIterator[str]:
    """Yield response text incrementally, one chunk at a time.

    This is the abstraction the rest of the app depends on. Swap the
    implementation freely (Anthropic, OpenAI, a local model server, ...) —
    callers only need an async iterator of text chunks.
    """
    if LLM_API_KEY:
        async for chunk in _stream_from_real_provider(prompt):
            yield chunk
    else:
        # No credentials configured: fall back to a local simulation so this
        # example is runnable end-to-end out of the box.
        async for chunk in _stream_simulated(prompt):
            yield chunk


async def _stream_from_real_provider(prompt: str) -> AsyncIterator[str]:
    """Illustrative pseudo-implementation of a real streaming call.

    This is intentionally NOT wired up to a real HTTP client — the exact
    request/response shape differs by provider. Below is the general
    pattern shared by Anthropic/OpenAI-compatible-style streaming chat
    completion APIs, using `httpx` as a generic async HTTP client:

        import httpx, json

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "https://api.your-provider.example/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Accept": "text/event-stream",
                },
                json={
                    "model": LLM_MODEL,
                    "stream": True,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line.removeprefix("data:").strip()
                    if not payload or payload == "[DONE]":
                        continue
                    event = json.loads(payload)
                    # Provider-specific: pull the incremental text out of
                    # the event shape your provider actually sends, e.g.
                    # event["choices"][0]["delta"].get("content") for an
                    # OpenAI-compatible API, or event["delta"]["text"] for
                    # an Anthropic-style content-block delta.
                    delta = event.get("delta", {}).get("text")
                    if delta:
                        yield delta

    See ../../docs/14-ai-api-engineering/streaming-llm-responses.md for the
    full write-up of this pattern, including how to buffer (rather than
    incrementally parse) tool-call arguments.
    """
    raise NotImplementedError(
        "Plug in a real provider SDK/HTTP call here. See the docstring "
        "above for the general shape of a streaming chat completion call."
    )
    yield ""  # pragma: no cover - keeps this an async generator for typing


async def _stream_simulated(prompt: str) -> AsyncIterator[str]:
    """Local, credential-free fallback so the example runs out of the box.

    Splits a canned response into word-sized chunks and yields them with a
    small delay between each, mimicking token-by-token streaming.
    """
    canned = (
        f"This is a simulated streaming response to your prompt: "
        f"\"{prompt.strip()}\". No LLM_API_KEY was found in the environment, "
        f"so llm_client.py is yielding these words locally instead of "
        f"calling a real provider. Set LLM_API_KEY and implement "
        f"_stream_from_real_provider to see this replaced with real model "
        f"output."
    )
    for word in canned.split(" "):
        await asyncio.sleep(0.05)
        yield word + " "
