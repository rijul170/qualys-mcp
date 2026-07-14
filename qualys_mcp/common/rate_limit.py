"""Rate-limit and concurrency awareness for Qualys APIs.

The classic FO API enforces two independent limits, reported via response
headers on every call:

* **Rate limit** — calls per period. Headers: ``X-RateLimit-Limit``,
  ``X-RateLimit-Remaining``, ``X-RateLimit-Window-Sec``,
  ``X-RateLimit-ToWait-Sec``. Exceeding it returns HTTP 409.
* **Concurrency limit** — simultaneous in-flight calls. Headers:
  ``X-Concurrency-Limit-Limit``, ``X-Concurrency-Limit-Running``. Exceeding it
  also returns HTTP 409.

This module extracts those headers and computes a backoff delay so the client
can transparently wait and retry instead of failing a tool call.
"""

from dataclasses import dataclass
from typing import Mapping

from qualys_mcp.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitState:
    """Snapshot of Qualys rate/concurrency headers from one response."""

    limit: int | None = None
    remaining: int | None = None
    window_sec: int | None = None
    to_wait_sec: int | None = None
    concurrency_limit: int | None = None
    concurrency_running: int | None = None

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> "RateLimitState":
        """Build state from a case-insensitive header mapping."""

        def _int(name: str) -> int | None:
            val = headers.get(name)
            try:
                return int(val) if val is not None else None
            except (TypeError, ValueError):
                return None

        return cls(
            limit=_int("X-RateLimit-Limit"),
            remaining=_int("X-RateLimit-Remaining"),
            window_sec=_int("X-RateLimit-Window-Sec"),
            to_wait_sec=_int("X-RateLimit-ToWait-Sec"),
            concurrency_limit=_int("X-Concurrency-Limit-Limit"),
            concurrency_running=_int("X-Concurrency-Limit-Running"),
        )

    def backoff_seconds(self, attempt: int) -> float:
        """Compute how long to wait before retrying a 409.

        Prefers Qualys's own ``X-RateLimit-ToWait-Sec`` hint. Falls back to a
        capped exponential backoff for concurrency contention (which has no
        explicit wait hint).

        Args:
            attempt: 1-based retry attempt number.

        Returns:
            Seconds to sleep before the next attempt.
        """
        if self.to_wait_sec and self.to_wait_sec > 0:
            # Add a small cushion so we clear the window boundary.
            return float(self.to_wait_sec) + 1.0
        # Concurrency contention: exponential backoff, capped at 30s.
        return min(2.0 ** attempt, 30.0)
