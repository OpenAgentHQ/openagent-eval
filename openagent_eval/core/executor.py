"""Async task executor for OpenAgent Eval."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

from openagent_eval.exceptions import MetricExecutionError

if TYPE_CHECKING:
    from collections.abc import Callable


class Executor:
    """Manages async execution and parallelism for evaluation tasks.

    This class handles parallel evaluation of multiple items,
    managing concurrency limits and error handling.
    """

    def __init__(self, max_workers: int = 4, timeout: float = 300.0) -> None:
        """Initialize the executor.

        Args:
            max_workers: Maximum number of parallel workers.
            timeout: Timeout for individual tasks in seconds.
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_workers)
        self._thread_pool: ThreadPoolExecutor | None = None

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
