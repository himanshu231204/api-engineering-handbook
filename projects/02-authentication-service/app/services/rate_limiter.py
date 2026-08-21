"""A minimal in-memory fixed-window rate limiter.

Good enough for a single-process reference implementation and for tests.
A real deployment behind multiple workers needs a shared store (Redis) --
see docs/06-production-reliability/rate-limiting.md.
"""
from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - self._window_seconds
        hits = [t for t in self._hits[key] if t > window_start]
        if len(hits) >= self._max_requests:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True

    def reset(self) -> None:
        self._hits.clear()
