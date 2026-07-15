"""Base report generator interface.

This module defines the abstract ReportGenerator interface that all report
formats must implement, along with shared data models for report generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openagent_eval.core.pipeline import PipelineResult


@dataclass(frozen=True)
class ReportConfig:
    """Configuration for report generation.

    Attributes:
        output_dir: Directory to write report files.
        include_examples: Whether to include example evaluations.
        max_examples: Maximum number of examples to include.
        title: Report title.
    """

    output_dir: str = "./reports"
    include_examples: bool = True
    max_examples: int = 10
    title: str = "OpenAgent Eval Report"


@dataclass
class FailureInfo:
    """Information about a failed evaluation item.

    Attributes:
        item: The original dataset item that failed.
        error: Error message.
        error_type: Exception class name.
        metric_scores: Metric scores computed before failure (if any).
    """

    item: dict[str, Any]
    error: str
    error_type: str
    metric_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class ExperimentComparison:
    """Side-by-side comparison of two experiment results.

    Attributes:
        baseline_name: Name/label for the baseline experiment.
        experiment_name: Name/label for the experiment being compared.
        baseline_results: Results from the baseline.
        experiment_results: Results from the experiment.
        metric_deltas: Per-metric change (experiment - baseline).
    """

    baseline_name: str
    experiment_name: str
    baseline_results: PipelineResult
    experiment_results: PipelineResult
    metric_deltas: dict[str, float] = field(default_factory=dict)


class ReportGenerator(ABC):
    """Abstract base class for all report generators.

    Every report format in OpenAgent Eval must implement this interface.
    The generator receives evaluation results and produces output in a
    specific format (terminal, markdown, HTML, JSON).

    Example:
        ```python
        class CustomReport(ReportGenerator):
            def generate(self, report: EvaluationReport) -> str:
                return f"Score: {report.summary.get('avg_score', 0):.2f}"
        ```
    """

    @abstractmethod
    def generate(self, report: Any) -> str:
        """Generate a report from evaluation results.

        Args:
            report: EvaluationReport containing config, results, and summary.

        Returns:
            Formatted report string.
        """
        ...

    @abstractmethod
    def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
        """Generate a report and write it to a file.

        Args:
            report: EvaluationReport containing config, results, and summary.
            output_path: Path to write the report file.

        Returns:
            Path to the written file.
        """
        ...

    def _ensure_output_dir(self, output_path: Path | str) -> Path:
        """Ensure the output directory exists.

        Args:
            output_path: Target file path.

        Returns:
            Resolved Path object.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _extract_metric_averages(self, result: PipelineResult) -> dict[str, float]:
        """Extract average metric scores from pipeline results.

        Args:
            result: PipelineResult with evaluation results.

        Returns:
            Dictionary of metric name to average score.
        """
        metric_sums: dict[str, float] = {}
        metric_counts: dict[str, int] = {}

        for eval_result in result.results:
            for metric_name, score in eval_result.metrics.items():
                metric_sums[metric_name] = metric_sums.get(metric_name, 0.0) + score
                metric_counts[metric_name] = metric_counts.get(metric_name, 0) + 1

        return {
            name: metric_sums[name] / metric_counts[name]
            for name in metric_sums
            if metric_counts[name] > 0
        }

    def _compute_failure_analysis(self, result: PipelineResult) -> list[FailureInfo]:
        """Analyze failures from pipeline errors.

        Args:
            result: PipelineResult with errors.

        Returns:
            List of FailureInfo objects.
        """
        failures: list[FailureInfo] = []
        for error_entry in result.errors:
            failures.append(
                FailureInfo(
                    item=error_entry.get("item", {}),
                    error=error_entry.get("error", "Unknown error"),
                    error_type=error_entry.get("error_type", "Unknown"),
                )
            )
        return failures
