import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Retry an async callable with exponential back-off.

    Args:
        fn: Zero-argument async callable to retry.
        attempts: Maximum number of total attempts.
        delay: Initial wait time in seconds between attempts.
        backoff: Multiplier applied to delay after each failure.
        exceptions: Exception types that trigger a retry.

    Returns:
        The return value of ``fn`` on the first successful call.

    Raises:
        The last exception raised by ``fn`` after all attempts are exhausted.
    """
    last_exc: Exception | None = None
    wait = delay

    for attempt in range(attempts):
        try:
            return await fn()
        except exceptions as exc:
            last_exc = exc
            if attempt < attempts - 1:
                await asyncio.sleep(wait)
                wait *= backoff

    raise last_exc  # type: ignore[misc]
