"""Regression test for issue #256.

Verifies that a retriever failure inside ``Pipeline._retrieve`` is no longer
silently swallowed: the dataset-context fallback still applies (behaviour
unchanged), and the failure is logged naming the exception. The degradation
is log-only: it must NOT be recorded in the run's ``errors``, because
engine.py computes ``successful_evaluations`` as ``len(results) -
len(errors)`` and an entry without a paired placeholder result would
mis-count a healthy run as failed (breaking cicd gate metrics).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from openagent_eval.config.models import (
    Config,
    DatasetConfig,
    LLMConfig,
    MetricsConfig,
    ReportConfig,
    RetrieverConfig,
)
from openagent_eval.core.pipeline import Pipeline
from openagent_eval.providers.base.retriever import Retriever

if TYPE_CHECKING:
    from openagent_eval.providers.models import Document


class _FailingRetriever(Retriever):
    """Retriever whose ``retrieve`` always raises, simulating a broken backend."""

    name = "failing"
    description = "Always raises from retrieve()"

    async def retrieve(
        self,
        query: str,
        k: int = 5,
        *,
        ground_truth_contexts: list[str] | None = None,
    ) -> list[Document]:
        raise RuntimeError("vector store unreachable")


@pytest.mark.asyncio
async def test_retrieval_failure_is_visible_and_still_falls_back(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A raising retriever degrades to dataset context and is logged only."""
    from openagent_eval.providers.llm.mock import MockLLMProvider

    config = Config(
        dataset=DatasetConfig(path="data/questions.json"),
        llm=LLMConfig(provider="mock", model="mock-model"),
        retriever=RetrieverConfig(provider="failing"),
        metrics=MetricsConfig(),
        report=ReportConfig(),
        parallel=False,
    )

    pipeline = Pipeline(config, retriever=_FailingRetriever(), llm=MockLLMProvider())

    with caplog.at_level(logging.WARNING, logger="openagent_eval.core.pipeline"):
        result = await pipeline.execute(
            [
                {
                    "question": "What is RAG?",
                    "ground_truth": "RAG is retrieval augmented generation.",
                    "context": "dataset-provided context",
                }
            ]
        )

    # (a) Fallback behaviour is unchanged: the dataset context is still used.
    assert result.results[0].contexts == ["dataset-provided context"]

    # (b) The degradation is log-only: it must NOT appear in result.errors.
    # engine.py computes successful_evaluations as
    # len(results) - len(errors), so an errors entry without a paired
    # placeholder result would mis-count this healthy run as failed and
    # trip cicd gate metrics. This pins that property.
    assert result.errors == []
    assert len(result.results) == 1
    assert len(result.results) - len(result.errors) == 1

    # (c) The failure is logged, naming the exception.
    assert "RuntimeError" in caplog.text
    assert "vector store unreachable" in caplog.text
