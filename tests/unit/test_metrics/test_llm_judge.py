"""Unit tests for the LLM-as-Judge metric.

Regression coverage for issue #71: ``LLMJudgeMetric.evaluate`` must resolve an
async provider's coroutine whether it is called from a plain synchronous
context OR from inside an already-running asyncio event loop. The previous
implementation used ``asyncio.get_event_loop().run_until_complete(...)``, which
raises ``RuntimeError`` when a loop is already running.
"""

from __future__ import annotations

import asyncio

from openagent_eval.metrics.generation.llm_judge import (
    RELEVANCY_CRITERIA,
    LLMJudgeMetric,
)


class _AsyncProvider:
    """Minimal async LLM provider whose ``generate`` returns a coroutine."""

    name = "async_stub"
    description = "async stub provider"

    def __init__(self, reply: str = "0.9") -> None:
        self._reply = reply
        self.calls = 0

    async def generate(self, prompt: str, **kwargs: object) -> str:
        self.calls += 1
        return self._reply

    async def get_token_count(self, text: str) -> int:  # pragma: no cover
        return len(text.split())


class _SyncProvider:
    """Provider whose ``generate`` returns a plain string (not a coroutine)."""

    name = "sync_stub"
    description = "sync stub provider"

    def __init__(self, reply: str = "0.8") -> None:
        self._reply = reply

    def generate(self, prompt: str, **kwargs: object) -> str:
        return self._reply

    async def get_token_count(self, text: str) -> int:  # pragma: no cover
        return len(text.split())


def _judge(provider: object) -> LLMJudgeMetric:
    return LLMJudgeMetric(provider=provider, criteria=RELEVANCY_CRITERIA)


def test_evaluate_async_provider_from_sync_context() -> None:
    """Async provider resolved from a plain sync call (no running loop)."""
    provider = _AsyncProvider(reply="0.9")
    result = _judge(provider).evaluate(
        premise="What color is the sky?",
        hypothesis="The sky is blue.",
    )

    assert provider.calls == 1
    assert result.score == 0.9
    assert "error" not in result.metadata
    assert result.metadata["provider"] == "async_stub"


def test_evaluate_async_provider_inside_running_loop() -> None:
    """Regression for #71: evaluate() must work inside a running event loop.

    Before the fix this raised RuntimeError ("... event loop is already
    running"), which was swallowed by the generic except and returned 0.0.
    """

    async def driver() -> object:
        # We are now inside asyncio.run(...), i.e. a running event loop —
        # exactly the async-pipeline scenario described in issue #71.
        return _judge(_AsyncProvider(reply="0.75")).evaluate(
            premise="What color is the sky?",
            hypothesis="The sky is blue.",
        )

    result = asyncio.run(driver())

    # The coroutine must have been driven to completion, not error out.
    assert result.score == 0.75, result.reason
    assert result.reason.startswith("LLM judge (relevancy)")


def test_evaluate_sync_provider_from_sync_context() -> None:
    """A synchronous provider (non-coroutine generate) still works."""
    result = _judge(_SyncProvider(reply="0.8")).evaluate(
        premise="What color is the sky?",
        hypothesis="The sky is blue.",
    )

    assert result.score == 0.8
    assert result.reason.startswith("LLM judge (relevancy)")


def test_evaluate_missing_inputs_returns_zero() -> None:
    """Missing premise/hypothesis short-circuits to a 0.0 result."""
    result = _judge(_AsyncProvider()).evaluate(premise="", hypothesis="")
    assert result.score == 0.0
    assert result.reason == "Missing premise or hypothesis"
