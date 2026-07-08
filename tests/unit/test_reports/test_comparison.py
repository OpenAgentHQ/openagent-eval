"""Tests for ComparisonReport generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from openagent_eval.core.pipeline import EvaluationResult, PipelineResult
from openagent_eval.reports.base import ExperimentComparison
from openagent_eval.reports.comparison import ComparisonReport


@pytest.fixture
def baseline_result() -> PipelineResult:
    """Create a baseline PipelineResult."""
    results = [
        EvaluationResult(
            question="Q1",
            answer="A1",
            metrics={"precision": 0.70, "recall": 0.65},
        ),
        EvaluationResult(
            question="Q2",
            answer="A2",
            metrics={"precision": 0.80, "recall": 0.75},
        ),
    ]
    return PipelineResult(
        results=results,
        summary={"total": 2, "metrics": {"precision": 0.75, "recall": 0.70}},
        errors=[],
    )


@pytest.fixture
def experiment_result() -> PipelineResult:
    """Create an experiment PipelineResult with improved metrics."""
    results = [
        EvaluationResult(
            question="Q1",
            answer="A1 improved",
            metrics={"precision": 0.85, "recall": 0.80},
        ),
        EvaluationResult(
            question="Q2",
            answer="A2 improved",
            metrics={"precision": 0.90, "recall": 0.85},
        ),
    ]
    return PipelineResult(
        results=results,
        summary={"total": 2, "metrics": {"precision": 0.875, "recall": 0.825}},
        errors=[],
    )


@pytest.fixture
def comparison(
    baseline_result: PipelineResult,
    experiment_result: PipelineResult,
) -> ExperimentComparison:
    """Create an ExperimentComparison."""
    return ExperimentComparison(
        baseline_name="baseline-v1",
        experiment_name="experiment-v2",
        baseline_results=baseline_result,
        experiment_results=experiment_result,
    )


class TestComparisonReport:
    """Tests for ComparisonReport generator."""

    def test_generate_returns_string(self, comparison: Any) -> None:
        """generate() returns a non-empty string."""
        report = ComparisonReport()
        result = report.generate(comparison)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_contains_header(self, comparison: Any) -> None:
        """generate() includes header."""
        report = ComparisonReport()
        result = report.generate(comparison)
        assert "Experiment Comparison Report" in result
        assert "baseline-v1" in result
        assert "experiment-v2" in result

    def test_generate_contains_metric_comparison(
        self, comparison: Any
    ) -> None:
        """generate() includes metric comparison table."""
        report = ComparisonReport()
        result = report.generate(comparison)
        assert "METRIC COMPARISON" in result
        assert "precision" in result
        assert "recall" in result

    def test_generate_shows_deltas(self, comparison: Any) -> None:
        """generate() shows metric deltas."""
        report = ComparisonReport()
        result = report.generate(comparison)
        # Both metrics improved
        assert "+" in result

    def test_generate_contains_summary(self, comparison: Any) -> None:
        """generate() includes summary."""
        report = ComparisonReport()
        result = report.generate(comparison)
        assert "SUMMARY" in result
        assert "Metrics improved" in result
        assert "Metrics regressed" in result

    def test_generate_shows_winner(self, comparison: Any) -> None:
        """generate() identifies the winner."""
        report = ComparisonReport()
        result = report.generate(comparison)
        assert "WINNER" in result
        assert "experiment-v2" in result

    def test_generate_with_regressed_metrics(self) -> None:
        """generate() handles regressed metrics."""
        baseline = PipelineResult(
            results=[
                EvaluationResult(
                    question="Q1", answer="A1", metrics={"f1": 0.90}
                ),
            ],
            summary={"total": 1},
        )
        experiment = PipelineResult(
            results=[
                EvaluationResult(
                    question="Q1", answer="A1", metrics={"f1": 0.70}
                ),
            ],
            summary={"total": 1},
        )
        comparison = ExperimentComparison(
            baseline_name="v1",
            experiment_name="v2",
            baseline_results=baseline,
            experiment_results=experiment,
        )

        report = ComparisonReport()
        result = report.generate(comparison)
        assert "WINNER" in result
        assert "v1" in result  # baseline wins

    def test_generate_with_errors(self) -> None:
        """generate() includes error comparison."""
        baseline = PipelineResult(
            results=[],
            summary={"total": 0},
            errors=[{"error": "e1", "error_type": "Error"}],
        )
        experiment = PipelineResult(
            results=[],
            summary={"total": 0},
            errors=[
                {"error": "e1", "error_type": "Error"},
                {"error": "e2", "error_type": "Error"},
            ],
        )
        comparison = ExperimentComparison(
            baseline_name="v1",
            experiment_name="v2",
            baseline_results=baseline,
            experiment_results=experiment,
        )

        report = ComparisonReport()
        result = report.generate(comparison)
        assert "ERROR COMPARISON" in result
        assert "Baseline errors:  1" in result
        assert "Experiment errors: 2" in result

    def test_generate_wrong_type_raises(self) -> None:
        """generate() raises TypeError for non-ExperimentComparison."""
        report = ComparisonReport()
        with pytest.raises(TypeError, match="ExperimentComparison"):
            report.generate("not a comparison")

    def test_generate_to_file(
        self, comparison: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() writes to a file."""
        report = ComparisonReport()
        output_path = tmp_path / "comparison.txt"
        result_path = report.generate_to_file(comparison, output_path)

        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "Experiment Comparison Report" in content

    def test_generate_to_file_creates_directory(
        self, comparison: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() creates parent directories."""
        report = ComparisonReport()
        output_path = tmp_path / "subdir" / "comparison.txt"
        result_path = report.generate_to_file(comparison, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()
