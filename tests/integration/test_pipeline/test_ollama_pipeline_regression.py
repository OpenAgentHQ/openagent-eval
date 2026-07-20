"""Regression test for issue #194.

The pipeline awaits ``self._llm.generate_with_usage(...)``. Every LLM provider
exposes ``generate_with_usage`` as an ``async def`` except Ollama, where it was
a plain synchronous ``def`` (the async twin lived under the differently named
``generate_with_usage_async``). Awaiting the synchronous call raised a
``TypeError`` that ``_generate``'s broad ``except Exception`` swallowed, so the
pipeline returned an empty answer for every Ollama generation with no error
surfaced.

This test drives ``Pipeline._generate`` with a real ``Ollama`` provider whose
HTTP client is mocked, and asserts a non-empty answer comes back. Before the
fix it fails (empty string); after the fix it passes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from openagent_eval.core.pipeline import Pipeline
from openagent_eval.providers.llm.ollama import Ollama


def _mock_generate_response() -> MagicMock:
    """A MagicMock mimicking a successful httpx response from /api/generate."""
    response = MagicMock()
    response.raise_for_status = MagicMock(return_value=None)
    response.json.return_value = {
        "model": "llama3.2",
        "response": "Paris is the capital of France.",
        "done": True,
        "prompt_eval_count": 10,
        "eval_count": 15,
    }
    return response


@pytest.mark.asyncio
async def test_pipeline_generate_with_ollama_returns_non_empty_answer() -> None:
    """Pipeline._generate must surface a real answer for the Ollama provider.

    Regression for #194: the awaited ``generate_with_usage`` was synchronous on
    Ollama, so the pipeline silently returned ``("", None, None)``.
    """
    provider = Ollama(model="llama3.2")
    # Mock the async HTTP client so no network call is made.
    provider._client.post = AsyncMock(return_value=_mock_generate_response())

    # Build a Pipeline without a full Config; _generate only needs _llm and
    # _build_prompt, so construct the instance directly and inject the provider.
    pipeline = Pipeline.__new__(Pipeline)
    pipeline._llm = provider

    answer, usage, latency_ms = await pipeline._generate(
        question="What is the capital of France?",
        contexts=["France is a country in Europe. Its capital is Paris."],
        ground_truth="Paris",
    )

    assert answer == "Paris is the capital of France.", (
        "Expected a real Ollama answer; got an empty/incorrect answer, which "
        "means the awaited generate_with_usage was not a coroutine (#194)."
    )
    assert usage is not None
    assert usage.total_tokens == 25
    assert latency_ms is not None and latency_ms >= 0.0
