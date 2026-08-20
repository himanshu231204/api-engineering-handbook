"""
Provider adapters for the minimal LLM gateway example.

Each provider is wrapped behind the same `ProviderAdapter` interface so the
gateway's routing/fallback logic (see gateway.py) never has to know which
concrete provider it's calling. This is the same idea as
../../docs/15-production-ai-systems/multi-provider-architecture.md: a
single normalized request/response shape, with provider-specific quirks
absorbed inside each adapter.

Neither concrete adapter below calls a real API. If its API key env var is
unset, it returns a locally-simulated response so the gateway (routing,
fallback, rate limiting, cost tracking) is runnable and demonstrably
correct with zero provider credentials. If the key IS set, it routes to a
clearly-commented pseudo-implementation showing the shape of a real call —
left as a `NotImplementedError` stub since we can't assume which provider
or valid credentials you have. See the README for how to wire up a real
call.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderUnavailableError(Exception):
    """Raised when a provider adapter fails to produce a response — a
    timeout, a non-2xx response, etc. The gateway catches this to decide
    whether to fall back to the next provider."""


@dataclass
class GenerationResult:
    content: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str
    latency_ms: int


class ProviderAdapter(ABC):
    """Common interface every concrete provider adapter implements.

    Keeping this abstract and narrow is what lets gateway.route() treat
    every provider identically — it only ever calls `generate()` and
    handles `ProviderUnavailableError`, never anything provider-specific.
    """

    name: str

    @abstractmethod
    async def generate(self, prompt: str, *, max_tokens: int, timeout_seconds: float) -> GenerationResult:
        raise NotImplementedError


class ProviderAAdapter(ProviderAdapter):
    """Illustrative adapter for an Anthropic-style chat/messages API."""

    name = "provider_a"
    model = "provider-a-balanced-v1"

    def __init__(self) -> None:
        self._api_key = os.environ.get("PROVIDER_A_API_KEY")

    async def generate(self, prompt: str, *, max_tokens: int, timeout_seconds: float) -> GenerationResult:
        start = time.monotonic()

        if self._api_key:
            return await self._call_real_api(prompt, max_tokens=max_tokens, timeout_seconds=timeout_seconds)

        try:
            await asyncio.wait_for(asyncio.sleep(0.05), timeout=timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise ProviderUnavailableError(f"{self.name}: request timed out") from exc

        content = f"[simulated {self.name} response] {prompt[:80]}"
        latency_ms = int((time.monotonic() - start) * 1000)
        return GenerationResult(
            content=content,
            input_tokens=_estimate_tokens(prompt),
            output_tokens=_estimate_tokens(content),
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
        )

    async def _call_real_api(self, prompt: str, *, max_tokens: int, timeout_seconds: float) -> GenerationResult:
        """Illustrative pseudo-implementation of a real call to an
        Anthropic-style chat/messages endpoint:

            import httpx

            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    "https://api.provider-a.example/v1/messages",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                return GenerationResult(
                    content=data["content"][0]["text"],
                    input_tokens=data["usage"]["input_tokens"],
                    output_tokens=data["usage"]["output_tokens"],
                    provider=self.name,
                    model=self.model,
                    latency_ms=...,
                )

        Wrap the actual HTTP call in try/except and raise
        `ProviderUnavailableError` on timeout or non-2xx status so
        gateway.route() can fall back to the next provider correctly.
        """
        raise NotImplementedError(
            f"{self.name.upper()}_API_KEY is set, but _call_real_api() is still a stub. "
            "Plug in a real provider SDK/HTTP call here, following the shape "
            "described in this function's docstring."
        )


class ProviderBAdapter(ProviderAdapter):
    """Illustrative adapter for an OpenAI-compatible chat/completions API."""

    name = "provider_b"
    model = "provider-b-fast-v1"

    def __init__(self) -> None:
        self._api_key = os.environ.get("PROVIDER_B_API_KEY")

    async def generate(self, prompt: str, *, max_tokens: int, timeout_seconds: float) -> GenerationResult:
        start = time.monotonic()

        if self._api_key:
            return await self._call_real_api(prompt, max_tokens=max_tokens, timeout_seconds=timeout_seconds)

        try:
            await asyncio.wait_for(asyncio.sleep(0.05), timeout=timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise ProviderUnavailableError(f"{self.name}: request timed out") from exc

        content = f"[simulated {self.name} response] {prompt[:80]}"
        latency_ms = int((time.monotonic() - start) * 1000)
        return GenerationResult(
            content=content,
            input_tokens=_estimate_tokens(prompt),
            output_tokens=_estimate_tokens(content),
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
        )

    async def _call_real_api(self, prompt: str, *, max_tokens: int, timeout_seconds: float) -> GenerationResult:
        """Illustrative pseudo-implementation of a real call to an
        OpenAI-compatible chat/completions endpoint:

            import httpx

            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    "https://api.provider-b.example/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                return GenerationResult(
                    content=data["choices"][0]["message"]["content"],
                    input_tokens=data["usage"]["prompt_tokens"],
                    output_tokens=data["usage"]["completion_tokens"],
                    provider=self.name,
                    model=self.model,
                    latency_ms=...,
                )

        Wrap the actual HTTP call in try/except and raise
        `ProviderUnavailableError` on timeout or non-2xx status so
        gateway.route() can fall back to the next provider correctly.
        """
        raise NotImplementedError(
            f"{self.name.upper()}_API_KEY is set, but _call_real_api() is still a stub. "
            "Plug in a real provider SDK/HTTP call here, following the shape "
            "described in this function's docstring."
        )


class UnreliableTestAdapter(ProviderAdapter):
    """A third adapter that fails a configurable fraction of the time and
    never requires any credentials.

    Exists purely so the gateway's fallback path (see gateway.route()) is
    easy to exercise out of the box — placed first in the default provider
    priority list, its (default 50%) simulated failure rate means you'll
    regularly see requests fall through to `provider_a` without needing to
    take down a real provider to prove fallback works. Control the failure
    rate with FLAKY_PROVIDER_FAILURE_RATE.
    """

    name = "flaky_test_provider"
    model = "flaky-test-v1"

    def __init__(self) -> None:
        self._failure_rate = float(os.environ.get("FLAKY_PROVIDER_FAILURE_RATE", "0.5"))

    async def generate(self, prompt: str, *, max_tokens: int, timeout_seconds: float) -> GenerationResult:
        start = time.monotonic()
        if random.random() < self._failure_rate:
            raise ProviderUnavailableError(f"{self.name}: simulated failure")

        await asyncio.sleep(0.02)
        content = f"[simulated {self.name} response] {prompt[:80]}"
        latency_ms = int((time.monotonic() - start) * 1000)
        return GenerationResult(
            content=content,
            input_tokens=_estimate_tokens(prompt),
            output_tokens=_estimate_tokens(content),
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
        )


def _estimate_tokens(text: str) -> int:
    """Extremely rough token estimate (chars / 4) for demo cost tracking.
    Real token counts come from the provider's `usage` field in its
    response — never estimate for actual billing. See
    ../../docs/14-ai-api-engineering/tokens-and-tokenization.md."""
    return max(1, len(text) // 4)
