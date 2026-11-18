"""Async task executor for OpenAgent Eval."""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

from openagent_eval.exceptions import MetricExecutionError

if TYPE_CHECKING:
    from collections.abc import Callable


class TokenBucketRateLimiter:
    """Async token-bucket rate limiter measuring throughput in requests per second."""

    def __init__(self, rate: float, capacity: float = 1.0) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity < 1.0:
            raise ValueError("capacity must be at least 1.0")
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        """Wait until ``tokens`` are available in the bucket, then consume them."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("requested tokens exceed bucket capacity")

        async with self._lock:
            now = time.monotonic()
            elapsed = max(0.0, now - self._last_refill)
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_refill = now

            if self._tokens < tokens:
                wait_seconds = (tokens - self._tokens) / self.rate
                await asyncio.sleep(wait_seconds)
                now = time.monotonic()
                elapsed = max(0.0, now - self._last_refill)
                self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
                self._last_refill = now

            self._tokens = max(0.0, self._tokens - tokens)


class Executor:
    """Manages async execution and parallelism for evaluation tasks.

    This class handles parallel evaluation of multiple items,
    managing concurrency limits and error handling.
    """

    def __init__(
        self,
        max_workers: int = 4,
        timeout: float = 300.0,
        rate_limits: dict[str, float] | None = None,
    ) -> None:
        """Initialize the executor.

        Args:
            max_workers: Maximum number of parallel workers.
            timeout: Timeout for individual tasks in seconds.
            rate_limits: Optional per-provider request-per-second caps.
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_workers)
        self._thread_pool: ThreadPoolExecutor | None = None
        self._rate_limiters: dict[str, TokenBucketRateLimiter] = {}
        if rate_limits:
            for provider, rate in rate_limits.items():
                self.configure_rate_limit(provider, rate)

    def configure_rate_limit(
        self, provider: str, rate: float, capacity: float = 1.0
    ) -> TokenBucketRateLimiter:
        """Register or replace a per-provider token-bucket rate limiter."""
        limiter = TokenBucketRateLimiter(rate=rate, capacity=capacity)
        self._rate_limiters[provider] = limiter
        return limiter

    def get_rate_limiter(self, provider: str) -> TokenBucketRateLimiter | None:
        """Return the configured rate limiter for ``provider``, if any."""
        return self._rate_limiters.get(provider)

    async def gather(self, coroutines: list[Any]) -> list[Any]:
        """Run coroutines concurrently with the configured concurrency limit.

        Args:
            coroutines: List of coroutine objects to execute.

        Returns:
            List of results in the same order as ``coroutines``.

        Raises:
            MetricExecutionError: If a coroutine times out. The first
                failure cancels the remaining coroutines.
        """

        async def _run(coro: Any) -> Any:
            async with self._semaphore:
                try:
                    return await asyncio.wait_for(coro, timeout=self.timeout)
                except TimeoutError:
                    raise MetricExecutionError(
                        message=f"Task timed out after {self.timeout}s",
                        details={"timeout": self.timeout},
                    ) from None

        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(_run(c)) for c in coroutines]
        except* Exception as eg:
            # TaskGroup cancels the remaining tasks and bundles the
            # failures; re-raise the first one to preserve the public
            # error contract (e.g. MetricExecutionError on timeout).
            raise eg.exceptions[0] from None

        return [t.result() for t in tasks]

    async def run_in_thread(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run a synchronous function in a thread pool.

        Args:
            func: The synchronous function to run.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            The result of the function.
        """
        if self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._thread_pool,
            lambda: func(*args, **kwargs),
        )

    def shutdown(self) -> None:
        """Shutdown the executor and clean up resources."""
        if self._thread_pool is not None:
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None
