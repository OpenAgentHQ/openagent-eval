"""Shared streaming helpers for LLM provider adapters."""

from __future__ import annotations

import inspect
from typing import Any


async def close_async_stream(stream: Any) -> None:
    """Close an async SDK stream or async generator cleanly if supported.

    Supports async generators exposing ``aclose()`` as well as SDK stream
    wrappers such as ``openai.AsyncStream`` and ``groq.AsyncStream`` that expose
    ``close()``. When both attributes are present (for example ``httpx.Response``
    with sync ``close`` and async ``aclose``, or a mock with ``close =
    AsyncMock()``), an async ``close`` coroutine is preferred over a
    non-coroutine ``aclose`` and ``aclose`` is preferred otherwise.

    Args:
        stream: The stream object returned by an SDK call, or ``None``.
    """
    if stream is None:
        return

    aclose = getattr(stream, "aclose", None)
    close = getattr(stream, "close", None)

    if callable(close) and (
        not callable(aclose)
        or (
            inspect.iscoroutinefunction(close)
            and not inspect.iscoroutinefunction(aclose)
        )
    ):
        result = close()
    elif callable(aclose):
        result = aclose()
    else:
        return

    if inspect.isawaitable(result):
        await result
