"""
retry.py — PRAMAAN shared retry utilities

Provides:
  with_retry(fn, *args, retries=3, delay=2.0, backoff=2.0, label="")
      → call fn(*args) up to `retries` times with exponential back-off.

  @retryable(retries=3, delay=2.0, backoff=2.0)
      → decorator version for class methods / standalone functions.

Back-off schedule (default: delay=2, backoff=2):
  attempt 1 → immediate
  attempt 2 → 2s wait
  attempt 3 → 4s wait
  attempt 4 → 8s wait  (if retries=4)

Both helpers swallow transient errors and raise on the final failure.
"""

import time
import logging
import functools
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

# Exceptions considered transient (worth retrying)
_TRANSIENT = (
    ConnectionError,
    TimeoutError,
    OSError,          # includes socket errors
)

# Try to import Groq-specific rate-limit exception
try:
    from groq import RateLimitError as GroqRateLimitError
    _TRANSIENT = (*_TRANSIENT, GroqRateLimitError)   # type: ignore[assignment]
except ImportError:
    pass

# Try to import requests exceptions
try:
    import requests.exceptions as _req_exc
    _TRANSIENT = (*_TRANSIENT,                        # type: ignore[assignment]
                  _req_exc.ConnectionError,
                  _req_exc.Timeout,
                  _req_exc.ChunkedEncodingError)
except ImportError:
    pass

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    fn: Callable,
    *args,
    retries: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    label: str = "",
    **kwargs,
) -> Any:
    """
    Call fn(*args, **kwargs) with retry on transient errors.

    Parameters
    ----------
    fn      : callable to invoke
    retries : max additional attempts after the first (total = retries + 1)
    delay   : initial wait in seconds before the second attempt
    backoff : multiplier applied to delay after each failure
    label   : name logged in warnings (e.g. "Groq extraction")
    """
    name = label or getattr(fn, "__name__", str(fn))
    wait = delay
    last_exc: Exception = RuntimeError("No attempts made")

    for attempt in range(1, retries + 2):   # retries+1 total attempts
        try:
            return fn(*args, **kwargs)
        except _TRANSIENT as exc:
            last_exc = exc
            if attempt <= retries:
                logger.warning(
                    "[retry] %s — attempt %d/%d failed (%s). Retrying in %.1fs …",
                    name, attempt, retries + 1, type(exc).__name__, wait,
                )
                time.sleep(wait)
                wait *= backoff
            else:
                logger.error(
                    "[retry] %s — all %d attempts failed. Last error: %s",
                    name, retries + 1, exc,
                )
                raise last_exc
        except Exception as exc:
            # Non-transient error (e.g. JSONDecodeError, ValueError) — don't retry
            logger.error("[retry] %s — non-transient error: %s", name, exc)
            raise


def retryable(
    retries: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    label: str = "",
) -> Callable[[F], F]:
    """
    Decorator: wrap a function with retry logic.

    Usage
    -----
    @retryable(retries=3, delay=1.0)
    def call_external_api(url):
        return requests.get(url, timeout=10)
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return with_retry(
                fn, *args,
                retries=retries,
                delay=delay,
                backoff=backoff,
                label=label or fn.__name__,
                **kwargs,
            )
        return wrapper  # type: ignore[return-value]
    return decorator
