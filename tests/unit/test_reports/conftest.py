"""Shared fixtures for report tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from openagent_eval.config.models import (
    Config,
    DatasetConfig,
    LLMConfig,
    MetricsConfig,
    OutputFormat,
    ReportConfig,
    RetrieverConfig,
)
from openagent_eval.core.engine import EvaluationReport
from openagent_eval.core.pipeline import EvaluationResult, PipelineResult


@pytest.fixture
def sample_config() -> Config:
    """Create a sample configuration for testing."""
    return Config(
        dataset=DatasetConfig(path="tests/sample_data/test_dataset.json"),
        llm=LLMConfig(provider="openai", model="gpt-4o"),
        retriever=RetrieverConfig(provider="chroma"),
        metrics=MetricsConfig(
            retrieval=["precision", "recall"],
            generation=["faithfulness"],
        ),
        report=ReportConfig(
            output=OutputFormat.TERMINAL,
            output_dir="./test_reports",
        ),
    )


@pytest.fixture
def pipeline_result_with_data() -> PipelineResult:
    """Create a PipelineResult with sample evaluation data."""
    results = [
        EvaluationResult(
            question="What is Python?",
            answer="Python is a programming language.",
            ground_truth="Python is a high-level programming language.",
            contexts=["Python is a programming language created by Guido van Rossum."],
            metrics={"precision": 0.95, "recall": 0.88, "faithfulness": 0.92},
            metadata={"id": 1},
        ),
        EvaluationResult(
            question="What is RAG?",
            answer="RAG combines retrieval and generation.",
            ground_truth="RAG stands for Retrieval-Augmented Generation.",
            contexts=["RAG is a technique that combines retrieval and generation."],
            metrics={"precision": 0.82, "recall": 0.90, "faithfulness": 0.85},
            metadata={"id": 2},
        ),
        EvaluationResult(
            question="What is an embedding?",
            answer="An embedding is a vector representation.",
            ground_truth="An embedding is a dense vector representation of text.",
            contexts=["Embeddings map text to dense vectors in semantic space."],
            metrics={"precision": 0.78, "recall": 0.75, "faithfulness": 0.80},
            metadata={"id": 3},
        ),
    ]

    errors = [
        {
            "item": {"question": "Failed question"},
            "error": "Connection timeout",
            "error_type": "ProviderConnectionError",
        },
        {
            "item": {"question": "Another failed question"},
            "error": "Invalid response format",
            "error_type": "ProviderExecutionError",
        },
    ]

    summary = {
        "total": 3,
        "errors": 2,
        "metrics": {
            "precision": 0.85,
            "recall": 0.8433,
            "faithfulness": 0.8567,
        },
    }

    return PipelineResult(results=results, summary=summary, errors=errors)


@pytest.fixture
def pipeline_result_empty() -> PipelineResult:
    """Create an empty PipelineResult."""
    return PipelineResult(results=[], summary={"total": 0}, errors=[])


@pytest.fixture
def evaluation_report(
    sample_config: Config,
    pipeline_result_with_data: PipelineResult,
) -> EvaluationReport:
    """Create a complete EvaluationReport for testing."""
    summary = {
        "total_items": 5,
        "successful_evaluations": 3,
        "failed_evaluations": 2,
        "metrics_summary": {
            "precision": 0.85,
            "recall": 0.8433,
            "faithfulness": 0.8567,
        },
    }

    return EvaluationReport(
        config=sample_config,
        result=pipeline_result_with_data,
        summary=summary,
        metadata={
            "version": "0.1.0",
            "engine": "openagent-eval",
            "title": "Test Report",
        },
    )


@pytest.fixture
def evaluation_report_empty(
    sample_config: Config,
    pipeline_result_empty: PipelineResult,
) -> EvaluationReport:
    """Create an empty EvaluationReport for testing."""
    summary = {
        "total_items": 0,
        "successful_evaluations": 0,
        "failed_evaluations": 0,
        "metrics_summary": {},
    }

    return EvaluationReport(
        config=sample_config,
        result=pipeline_result_empty,
        summary=summary,
        metadata={
            "version": "0.1.0",
            "engine": "openagent-eval",
            "title": "Empty Report",
        },
    )
