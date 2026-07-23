"""Regression tests for #72: the hallucination metric must not silently swallow
DeepEval runtime errors.

When ``_evaluate_with_deepeval`` fails at runtime (missing API key, network
error, model init failure, ...) the metric should degrade to the local
word-coverage fallback *and* leave a log trail — matching the visibility that
the sibling Faithfulness / AnswerRelevancy metrics already provide (``logger``
at debug level), instead of the previous bare ``except Exception: pass``.
"""

from __future__ import annotations

import logging

import pytest
from loguru import logger

from openagent_eval.metrics.generation.hallucination import HallucinationDetection


@pytest.fixture
def loguru_caplog(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Bridge loguru output into pytest's ``caplog`` handler.

    loguru does not propagate to the stdlib logging tree that ``caplog``
    listens on, so add a temporary sink that forwards records to the caplog
    handler, filtered by the level caplog is capturing at.
    """
    handler_id = logger.add(
        caplog.handler,
        level=0,
        format="{message}",
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,
    )
    yield caplog
    logger.remove(handler_id)


def _raise_runtime_error(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("OPENAI_API_KEY is not set")


def test_deepeval_runtime_error_is_logged(
    monkeypatch: pytest.MonkeyPatch,
    loguru_caplog: pytest.LogCaptureFixture,
) -> None:
    """A DeepEval runtime failure must be logged, not silently swallowed."""
    monkeypatch.setattr(
        HallucinationDetection,
        "_evaluate_with_deepeval",
        _raise_runtime_error,
    )
    metric = HallucinationDetection()

    with loguru_caplog.at_level(logging.DEBUG):
        result = metric.evaluate(
            answer="Python is a programming language.",
            contexts=["Python is a programming language."],
        )

    # The failure is now visible in the logs (was: except Exception: pass).
    assert "DeepEval hallucination unavailable" in loguru_caplog.text
    assert "OPENAI_API_KEY is not set" in loguru_caplog.text
    # And it still degrades gracefully to the local fallback rather than raising.
    assert result.metadata["method"] == "word_coverage"


def test_deepeval_runtime_error_does_not_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """evaluate() must return a fallback result, never re-raise the failure."""
    monkeypatch.setattr(
        HallucinationDetection,
        "_evaluate_with_deepeval",
        _raise_runtime_error,
    )
    metric = HallucinationDetection()

    result = metric.evaluate(
        answer="The moon is made of green cheese.",
        contexts=["Python is a programming language."],
    )

    assert result.metadata["method"] == "word_coverage"
    assert result.score > 0.0
