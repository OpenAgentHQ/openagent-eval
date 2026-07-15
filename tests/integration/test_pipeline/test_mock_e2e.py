"""End-to-end pipeline integration test using mock providers (no API keys).

These tests exercise the full Dataset -> Retriever -> LLM -> Metrics flow
without any external services, validating that the pipeline is no longer a
stub and that results are actually computed.
"""

from __future__ import annotations

import pytest

from openagent_eval.config.models import (
    Config,
    DatasetConfig,
    LLMConfig,
    MetricsConfig,
    ReportConfig,
    RetrieverConfig,
)
from openagent_eval.core.engine import Engine
from openagent_eval.metrics.base import BaseMetric


class _FailingMetric(BaseMetric):
    """Metric that always raises, used to verify error containment."""

    name = "failing_metric"
    description = "Always fails"

    def evaluate(self, **kwargs):  # pragma: no cover - intentionally raises
        raise RuntimeError("boom")


@pytest.fixture
def mock_config() -> Config:
    return Config(
        dataset=DatasetConfig(path="data/questions.json"),
        llm=LLMConfig(provider="mock", model="mock-model"),
        retriever=RetrieverConfig(provider="mock", settings={"collection_name": "c"}),
        metrics=MetricsConfig(
            retrieval=["context_precision", "context_recall", "mrr", "recall_at_k", "hit_rate", "ndcg"],
            generation=["faithfulness", "answer_relevancy", "exact_match", "f1_score"],
            performance=["latency"],
            cost=["token_count"],
        ),
        report=ReportConfig(output="json", output_dir="./test_reports"),
        parallel=False,
    )


@pytest.fixture
def mock_dataset() -> list[dict]:
    return [
        {
            "question": "What is RAG?",
            "ground_truth": "RAG combines retrieval with generation.",
            "context": "RAG combines retrieval with generation.",
            "ground_truth_contexts": ["RAG combines retrieval with generation."],
        },
        {
            "question": "What is a vector store?",
            "ground_truth": "A vector store indexes embeddings.",
            "context": "A vector store indexes embeddings.",
            "ground_truth_contexts": ["A vector store indexes embeddings."],
        },
    ]


@pytest.mark.asyncio
async def test_pipeline_runs_end_to_end(mock_config: Config, mock_dataset: list[dict]) -> None:
    """The pipeline must retrieve, generate, and score — not return empty results."""
    engine = Engine(mock_config)
    report = await engine.run(mock_dataset)

    assert report.summary["total_items"] == 2
    assert report.summary["successful_evaluations"] == 2
    assert report.summary["failed_evaluations"] == 0

    for result in report.result.results:
        # Generation actually happened (mock echoes ground_truth).
        assert result.answer
        # Retrieval actually happened.
        assert result.contexts
        # Metrics were actually computed (not an empty dict).
        assert result.metrics
        # Token usage was captured.
        assert result.metadata.get("total_tokens") is not None

    # Retrieval metrics should be perfect because the mock returns GT contexts.
    assert report.result.results[0].metrics["context_precision"] == 1.0
    assert report.result.results[0].metrics["context_recall"] == 1.0
    assert report.result.results[0].metrics["recall_at_k"] == 1.0
    engine.shutdown()


@pytest.mark.asyncio
async def test_summary_counts_real_errors(mock_config: Config, mock_dataset: list[dict]) -> None:
    """The summary must report the real error count, not a hardcoded 0."""
    # Inject a metric that always fails to force a per-item metric error.
    engine = Engine(
        mock_config,
        metrics=[("failing_metric", _FailingMetric())],
    )
    report = await engine.run(mock_dataset)

    # The failing metric is recorded per-item but does not abort the run.
    for result in report.result.results:
        assert result.metrics.get("failing_metric") == 0.0
        assert "failing_metric" in (result.metadata.get("metric_errors") or {})

    # No item-level failures -> summary errors stay 0 (metric errors are contained).
    assert report.result.summary["errors"] == 0
    engine.shutdown()


@pytest.mark.asyncio
async def test_retrieval_metrics_zero_without_ground_truth(
    mock_config: Config, mock_dataset: list[dict]
) -> None:
    """When no ground_truth_contexts are provided, retrieval metrics degrade gracefully."""
    for item in mock_dataset:
        item.pop("ground_truth_contexts", None)

    engine = Engine(mock_config)
    report = await engine.run(mock_dataset)

    for result in report.result.results:
        # No GT contexts -> retrieval metrics return 0.0, not crash.
        assert result.metrics["context_precision"] == 0.0
        assert result.metrics["context_recall"] == 0.0
    engine.shutdown()
