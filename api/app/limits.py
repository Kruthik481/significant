"""Per-client sliding-window rate limit, kept in memory (the API runs as one instance)."""

import math
import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    def __init__(self, limit: int, window: float = 3600, now: Callable[[], float] = time.monotonic) -> None:
        self.limit = limit
        self.window = window
        self.now = now
        self._log: dict[str, deque[float]] = {}

    def _prune(self, cutoff: float) -> None:
        for key in list(self._log):
            entries = self._log[key]
            while entries and entries[0] <= cutoff:
                entries.popleft()
            if not entries:
                del self._log[key]

    def allow(self, key: str) -> tuple[bool, int]:
        """Returns (allowed, seconds until the next request would be allowed)."""
        now = self.now()
        self._prune(now - self.window)
        entries = self._log.setdefault(key, deque())
        if len(entries) >= self.limit:
            return False, max(1, math.ceil(entries[0] + self.window - now))
        entries.append(now)
        return True, 0
