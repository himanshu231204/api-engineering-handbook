"""
Gateway core: provider routing with fallback, a token-bucket rate limiter,
and cost tracking via an illustrative pricing table.

See ../../docs/15-production-ai-systems/llm-gateways.md,
../../docs/15-production-ai-systems/model-routing.md,
../../docs/15-production-ai-systems/fallback-systems.md, and
../../docs/15-production-ai-systems/cost-tracking.md for the full
production discussion of each of these pieces.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from providers import GenerationResult, ProviderAdapter, ProviderUnavailableError


class AllProvidersFailedError(Exception):
    """Raised when every provider in the priority list failed. Carries the
    per-provider errors so the caller (and logs) can see exactly why."""

    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__(f"all providers failed: {errors}")


# --- Routing with fallback --------------------------------------------------

async def route(
    prompt: str,
    *,
    providers: list[ProviderAdapter],
    max_tokens: int = 500,
    timeout_seconds: float = 5.0,
) -> GenerationResult:
    """Try each provider in `providers`, in priority order, falling back to
    the next one if a provider raises `ProviderUnavailableError` (a missing
    key, a timeout, a non-2xx response). Returns the first successful
    result; raises `AllProvidersFailedError` if every provider fails.

    This is intentionally a simple sequential fallback — no circuit
    breaker, no health-check-based skip-ahead. See
    ../../docs/06-production-reliability/circuit-breakers.md and
    ../../docs/15-production-ai-systems/fallback-systems.md for how a
    production gateway avoids repeatedly retrying a provider it already
    knows is down.
    """
    errors: dict[str, str] = {}

    for provider in providers:
        try:
            return await provider.generate(prompt, max_tokens=max_tokens, timeout_seconds=timeout_seconds)
        except ProviderUnavailableError as exc:
            errors[provider.name] = str(exc)
            continue

    raise AllProvidersFailedError(errors)


# --- Token-bucket rate limiter ----------------------------------------------

@dataclass
class TokenBucketRateLimiter:
    """A simple in-memory, per-process token-bucket rate limiter.

    `capacity` tokens refill continuously at `refill_rate` tokens/second.
    Each request consumes one token; if none are available, the caller is
    rate-limited. This is fine for a single-process demo. A real deployment
    needs a *shared* limiter (e.g. Redis-backed) so the limit applies
    across all gateway instances, not per-process — see
    ../../docs/06-production-reliability/rate-limiting.md.
    """

    capacity: float
    refill_rate: float  # tokens per second
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self._tokens = self.capacity
        self._last_refill = time.monotonic()

    async def allow(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last_refill = now

            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False


# --- Cost tracking -----------------------------------------------------------

# Illustrative pricing table, USD per 1,000 tokens. Keep this current in a
# real system — providers change prices, and a stale table silently
# produces wrong cost reports. See
# ../../docs/15-production-ai-systems/cost-tracking.md.
PRICING_TABLE: dict[tuple[str, str], dict[str, float]] = {
    ("provider_a", "provider-a-balanced-v1"): {"input_per_1k": 0.003, "output_per_1k": 0.015},
    ("provider_b", "provider-b-fast-v1"): {"input_per_1k": 0.0005, "output_per_1k": 0.0015},
    ("flaky_test_provider", "flaky-test-v1"): {"input_per_1k": 0.0, "output_per_1k": 0.0},
}

DEFAULT_PRICING = {"input_per_1k": 0.001, "output_per_1k": 0.002}


def compute_cost_usd(result: GenerationResult) -> float:
    pricing = PRICING_TABLE.get((result.provider, result.model), DEFAULT_PRICING)
    input_cost = (result.input_tokens / 1000) * pricing["input_per_1k"]
    output_cost = (result.output_tokens / 1000) * pricing["output_per_1k"]
    return round(input_cost + output_cost, 6)
