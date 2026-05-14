"""Retry decorator with exponential backoff and optional jitter."""
from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable)


def retry_with_backoff(
    max_retries: int = 3,
    backoff_base: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    jitter: bool = True,
) -> Callable[[F], F]:
    """Retry *func* up to *max_retries* times using exponential backoff.

    Each sleep duration is ``backoff_base ** attempt`` seconds, optionally
    multiplied by a uniform random factor in [0.5, 1.5] when *jitter* is True.
    The original exception is chained onto the final RuntimeError raised after
    all retries are exhausted.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        break
                    wait = backoff_base ** attempt
                    if jitter:
                        wait *= 0.5 + random.random()
                    logger.warning(
                        "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                        func.__qualname__,
                        attempt + 1,
                        max_retries,
                        exc,
                        wait,
                    )
                    time.sleep(wait)
            raise RuntimeError(
                f"{func.__qualname__} failed after {max_retries} retries"
            ) from last_exc

        return wrapper  # type: ignore[return-value]

    return decorator
