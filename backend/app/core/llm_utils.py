"""Shared resilience helpers for calls to the Gemini API.

Every direct LLM call in this project should go through
`invoke_with_resilience` instead of calling `.invoke()` directly. That gives
two things uniformly, project-wide:

  1. A client-side sliding-window rate limiter that proactively throttles
     calls to stay under the free-tier RPM cap, instead of firing calls as
     fast as possible and only reacting after Google returns a 429.
  2. Retry with exponential backoff for any 429/503 that slips through
     anyway (e.g. the configured RPM doesn't match your actual quota).
"""

import logging
import threading
import time
from collections import deque
from typing import Any, Callable

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Blocks the calling thread until a new call is allowed within the window."""

    def __init__(self, max_calls: int, period_seconds: float = 60.0):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            while self._calls and now - self._calls[0] > self.period_seconds:
                self._calls.popleft()

            if len(self._calls) >= self.max_calls:
                sleep_for = self.period_seconds - (now - self._calls[0])
                if sleep_for > 0:
                    logger.info("Gemini rate limiter: pausing %.1fs to stay under quota.", sleep_for)
                    time.sleep(sleep_for)
                now = time.monotonic()
                while self._calls and now - self._calls[0] > self.period_seconds:
                    self._calls.popleft()

            self._calls.append(time.monotonic())


_settings = get_settings()
# One shared limiter for the whole process — every caller (agent loop,
# docstring generation, README generation) draws from the same budget,
# because they all hit the same per-model quota on Google's side.
_limiter = SlidingWindowRateLimiter(max_calls=_settings.gemini_requests_per_minute)


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=5, max=65), reraise=True)
def invoke_with_resilience(invoke_fn: Callable[[], Any]) -> Any:
    """
    Runs invoke_fn() with client-side rate limiting plus retry/backoff for
    any 429s that slip through. invoke_fn must be a zero-arg closure, e.g.:

        invoke_with_resilience(lambda: llm.invoke(messages))
    """
    _limiter.acquire()
    return invoke_fn()
