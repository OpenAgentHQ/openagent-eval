"""Async task executor for OpenAgent Eval."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine

from openagent_eval.exceptions import MetricExecutionError


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
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    async def execute_parallel(
        self,
        tasks: list[Callable[..., Coroutine[Any, Any, Any]]],
        *args: Any,
        **kwargs: Any,
    ) -> list[Any]:
        """Execute multiple tasks in parallel with concurrency limits.

        Args:
            tasks: List of async functions to execute.
            *args: Positional arguments to pass to each task.
            **kwargs: Keyword arguments to pass to each task.

        Returns:
            List of results from each task.

        Raises:
            MetricExecutionError: If a task fails or times out.
        """
        async def _run_with_semaphore(
            task: Callable[..., Coroutine[Any, Any, Any]],
        ) -> Any:
            async with self._semaphore:
                try:
                    return await asyncio.wait_for(
                        task(*args, **kwargs),
                        timeout=self.timeout,
                    )
                except asyncio.TimeoutError:
                    raise MetricExecutionError(
                        message=f"Task timed out after {self.timeout}s",
                        details={"timeout": self.timeout},
                    )
                except Exception as e:
                    raise MetricExecutionError(
                        message=f"Task failed: {e}",
                        original_error=e,
                    ) from e

        coroutines = [_run_with_semaphore(task) for task in tasks]
        return await asyncio.gather(*coroutines)

    async def gather(self, coroutines: list[Any]) -> list[Any]:
        """Run coroutines concurrently with the configured concurrency limit.

        Args:
            coroutines: List of coroutine objects to execute.

        Returns:
            List of results in the same order as ``coroutines``.

        Raises:
            MetricExecutionError: If a coroutine times out.
        """
        async def _run(coro: Any) -> Any:
            async with self._semaphore:
                try:
                    return await asyncio.wait_for(coro, timeout=self.timeout)
                except asyncio.TimeoutError:
                    raise MetricExecutionError(
                        message=f"Task timed out after {self.timeout}s",
                        details={"timeout": self.timeout},
                    ) from None

        return await asyncio.gather(*[_run(c) for c in coroutines])

    async def execute_sequential(
        self,
        tasks: list[Callable[..., Coroutine[Any, Any, Any]]],
        *args: Any,
        **kwargs: Any,
    ) -> list[Any]:
        """Execute tasks sequentially.

        Args:
            tasks: List of async functions to execute.
            *args: Positional arguments to pass to each task.
            **kwargs: Keyword arguments to pass to each task.

        Returns:
            List of results from each task.

        Raises:
            MetricExecutionError: If a task fails.
        """
        results: list[Any] = []
        for task in tasks:
            try:
                result = await asyncio.wait_for(
                    task(*args, **kwargs),
                    timeout=self.timeout,
                )
                results.append(result)
            except asyncio.TimeoutError:
                raise MetricExecutionError(
                    message=f"Task timed out after {self.timeout}s",
                    details={"timeout": self.timeout},
                )
            except Exception as e:
                raise MetricExecutionError(
                    message=f"Task failed: {e}",
                    original_error=e,
                ) from e
        return results

    def run_in_thread(
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
            An awaitable resolving to the result of the function.
        """
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_in_executor(
            self._thread_pool,
            lambda: func(*args, **kwargs),
        )

    def shutdown(self) -> None:
        """Shutdown the executor and clean up resources."""
        self._thread_pool.shutdown(wait=True)
