"""Basic per-client sliding-window rate limiting (in memory, single process)."""

from __future__ import annotations

import threading
import time
from collections import deque

from fastapi import Request

from app.errors import RateLimitError


class RateLimiter:
    def __init__(self, window_seconds: float = 60.0):
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, limit: int) -> None:
        if limit <= 0:
            return
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > self._window:
                hits.popleft()
            if len(hits) >= limit:
                raise RateLimitError("Too many requests. Please wait a minute and try again.")
            hits.append(now)
            if len(self._hits) > 10_000:  # bound memory
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] > self._window]:
                    del self._hits[k]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def client_key(request: Request) -> str:
    # Render (and most PaaS) put the real client IP first in X-Forwarded-For.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
