"""Shared retry/backoff utilities for LLM providers."""

from __future__ import annotations

import asyncio
import functools
import logging
import math
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, overload

import httpx

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderError,
    ProviderNotFoundError,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

RETRYABLE_STATUS_CODES: frozenset[int] = frozenset(
    {408, 409, 429, 500, 502, 503, 504, 529}
)
_MAX_RETRY_AFTER_SECONDS: float = 60.0
NON_RETRYABLE_ERROR_NAMES: frozenset[str] = frozenset(
    {
        "AuthenticationError",
        "BadRequestError",
        "NotFoundError",
        "PermissionDeniedError",
        "UnprocessableEntityError",
    }
)
RETRYABLE_ERROR_NAMES: frozenset[str] = frozenset(
    {
        "APIConnectionError",
        "APITimeoutError",
        "InternalServerError",
        "RateLimitError",
    }
)


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for exponential-backoff retries."""

    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: float = 0.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < 0:
            raise ValueError("max_delay must be non-negative")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be at least 1.0")
        if self.jitter < 0:
            raise ValueError("jitter must be non-negative")

    def compute_delay(self, attempt: int) -> float:
        """Return the sleep duration in seconds after a failed 1-based attempt."""
        delay = min(
            self.base_delay * (self.backoff_factor ** max(0, attempt - 1)),
            self.max_delay,
        )
        if self.jitter > 0:
            delay += random.uniform(0.0, self.jitter)
        return delay


def _extract_status_code(exc: BaseException) -> int | None:
    """Best-effort extraction of an HTTP status code from a provider exception."""
    candidates: list[Any] = [exc]
    if isinstance(exc, ProviderError):
        for key in ("status_code", "code"):
            raw = exc.details.get(key)
            if isinstance(raw, int) and not isinstance(raw, bool):
                return raw
    original = getattr(exc, "original_error", None)
    if original is not None:
        candidates.append(original)

    for candidate in candidates:
        for attr in ("status_code", "code"):
            raw = getattr(candidate, attr, None)
            if isinstance(raw, int) and not isinstance(raw, bool):
                return raw
        response = getattr(candidate, "response", None)
        if response is not None:
            raw = getattr(response, "status_code", None)
            if isinstance(raw, int) and not isinstance(raw, bool):
                return raw
    return None


def is_retryable_error(exc: BaseException) -> bool:
    """Determine whether a provider failure represents a transient error worth retrying."""
    if isinstance(exc, ProviderNotFoundError):
        return False

    status_code = _extract_status_code(exc)
    if status_code is not None:
        return status_code in RETRYABLE_STATUS_CODES

    underlying = getattr(exc, "original_error", None)
    for candidate in (c for c in (exc, underlying) if c is not None):
        if type(candidate).__name__ in NON_RETRYABLE_ERROR_NAMES or isinstance(
            candidate, (ValueError, TypeError)
        ):
            return False

    for candidate in (c for c in (exc, underlying) if c is not None):
        if type(candidate).__name__ in RETRYABLE_ERROR_NAMES or isinstance(
            candidate,
            (
                TimeoutError,
                ConnectionError,
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.RequestError,
            ),
        ):
            return True

    return isinstance(exc, ProviderConnectionError)


def _extract_retry_after(exc: BaseException) -> float | None:
    """Return a valid Retry-After delay in seconds, capped at 60 seconds."""
    candidates: list[Any] = [exc]
    original = getattr(exc, "original_error", None)
    if original is not None:
        candidates.append(original)

    for candidate in candidates:
        response = getattr(candidate, "response", None)
        headers = getattr(response, "headers", None)
        if headers is None or not hasattr(headers, "get"):
            continue

        retry_after_ms = headers.get("retry-after-ms")
        if retry_after_ms is not None:
            try:
                seconds = float(retry_after_ms) / 1000.0
            except (TypeError, ValueError):
                seconds = -1.0
            if math.isfinite(seconds) and seconds > 0:
                return min(seconds, _MAX_RETRY_AFTER_SECONDS)

        retry_after = headers.get("retry-after")
        if retry_after is not None:
            try:
                seconds = float(retry_after)
            except (TypeError, ValueError):
                try:
                    dt = parsedate_to_datetime(str(retry_after))
                except (TypeError, ValueError, IndexError):
                    continue
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                seconds = (dt - datetime.now(UTC)).total_seconds()
            if math.isfinite(seconds) and seconds > 0:
                return min(seconds, _MAX_RETRY_AFTER_SECONDS)
    return None


async def _run_with_retry(
    config: RetryConfig | None,
    func: Callable[P, Coroutine[Any, Any, T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """Internal typed execution loop accepting config before ParamSpec args."""
    retry_config = config or RetryConfig()
    for attempt in range(1, retry_config.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            if attempt >= retry_config.max_attempts or not is_retryable_error(exc):
                raise
            delay = retry_config.compute_delay(attempt)
            retry_after = _extract_retry_after(exc)
            if retry_after is not None:
                delay = max(delay, retry_after)
            logger.warning(
                "Transient provider failure on attempt %d/%d (%s); retrying in %.2fs",
                attempt,
                retry_config.max_attempts,
                exc,
                delay,
            )
            if delay > 0:
                await asyncio.sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover


async def execute_with_retry(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    config: RetryConfig | None = None,
    **kwargs: Any,
) -> T:
    """Invoke an async callable with exponential backoff on transient failures."""
    return await _run_with_retry(config, func, *args, **kwargs)


@overload
def retry_with_backoff(
    func: Callable[P, Coroutine[Any, Any, T]],
    *,
    config: None = None,
) -> Callable[P, Coroutine[Any, Any, T]]: ...


@overload
def retry_with_backoff(
    func: None = None,
    *,
    config: RetryConfig | None = None,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]
]: ...


def retry_with_backoff(
    func: Callable[P, Coroutine[Any, Any, T]] | None = None,
    *,
    config: RetryConfig | None = None,
) -> (
    Callable[P, Coroutine[Any, Any, T]]
    | Callable[
        [Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]
    ]
):
    """Decorate an async LLM provider method with transient-failure retries."""

    def decorator(
        target: Callable[P, Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        @functools.wraps(target)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            effective_config = config
            if effective_config is None and args:
                instance_config = getattr(args[0], "_retry_config", None)
                if isinstance(instance_config, RetryConfig):
                    effective_config = instance_config
            return await _run_with_retry(
                effective_config,
                target,
                *args,
                **kwargs,
            )

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
