"""Tests for ReportGenerator base interface and shared models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from openagent_eval.reports.base import (
    ExperimentComparison,
    FailureInfo,
    ReportConfig,
    ReportGenerator,
)


class TestReportConfig:
    """Tests for ReportConfig dataclass."""

    def test_default_values(self) -> None:
        """ReportConfig has sensible defaults."""
        config = ReportConfig()
        assert config.output_dir == "./reports"
        assert config.include_examples is True
        assert config.max_examples == 10
        assert config.title == "OpenAgent Eval Report"

    def test_custom_values(self) -> None:
        """ReportConfig accepts custom values."""
        config = ReportConfig(
            output_dir="/tmp/reports",
            include_examples=False,
            max_examples=5,
            title="Custom Report",
        )
        assert config.output_dir == "/tmp/reports"
        assert config.include_examples is False
        assert config.max_examples == 5
        assert config.title == "Custom Report"


class TestFailureInfo:
    """Tests for FailureInfo dataclass."""

    def test_creation(self) -> None:
        """FailureInfo can be created with required fields."""
        info = FailureInfo(
            item={"question": "test"},
            error="Something failed",
            error_type="ValueError",
        )
        assert info.item == {"question": "test"}
        assert info.error == "Something failed"
        assert info.error_type == "ValueError"
        assert info.metric_scores == {}

    def test_with_metric_scores(self) -> None:
        """FailureInfo can include metric scores."""
        info = FailureInfo(
            item={"question": "test"},
            error="timeout",
            error_type="TimeoutError",
            metric_scores={"precision": 0.5},
        )
        assert info.metric_scores == {"precision": 0.5}


class TestExperimentComparison:
    """Tests for ExperimentComparison dataclass."""

    def test_creation(self, pipeline_result_with_data: Any) -> None:
        """ExperimentComparison can be created."""
        comp = ExperimentComparison(
            baseline_name="v1",
            experiment_name="v2",
            baseline_results=pipeline_result_with_data,
            experiment_results=pipeline_result_with_data,
        )
        assert comp.baseline_name == "v1"
        assert comp.experiment_name == "v2"
        assert comp.metric_deltas == {}

    def test_with_deltas(self, pipeline_result_with_data: Any) -> None:
        """ExperimentComparison can include metric deltas."""
        comp = ExperimentComparison(
            baseline_name="v1",
            experiment_name="v2",
            baseline_results=pipeline_result_with_data,
            experiment_results=pipeline_result_with_data,
            metric_deltas={"precision": 0.05, "recall": -0.02},
        )
        assert comp.metric_deltas["precision"] == 0.05
        assert comp.metric_deltas["recall"] == -0.02


class TestReportGenerator:
    """Tests for ReportGenerator abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        """ReportGenerator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ReportGenerator()  # type: ignore[abstract]

    def test_concrete_implementation(self, evaluation_report: Any) -> None:
        """A concrete ReportGenerator subclass can be created and used."""

        class ConcreteReport(ReportGenerator):
            def generate(self, report: Any) -> str:
                return "test report"

            def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
                path = Path(output_path)
                path.write_text("test report", encoding="utf-8")
                return path

        report_gen = ConcreteReport()
        result = report_gen.generate(evaluation_report)
        assert result == "test report"

    def test_ensure_output_dir(self, tmp_path: Path) -> None:
        """_ensure_output_dir creates parent directories."""

        class ConcreteReport(ReportGenerator):
            def generate(self, report: Any) -> str:
                return ""

            def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
                return self._ensure_output_dir(output_path)

        report_gen = ConcreteReport()
        target = tmp_path / "subdir" / "report.txt"
        result = report_gen._ensure_output_dir(target)
        assert result.parent.exists()

    def test_extract_metric_averages(self, pipeline_result_with_data: Any) -> None:
        """_extract_metric_averages computes correct averages."""

        class ConcreteReport(ReportGenerator):
            def generate(self, report: Any) -> str:
                return ""

            def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
                return Path(output_path)

        report_gen = ConcreteReport()
        averages = report_gen._extract_metric_averages(pipeline_result_with_data)

        assert "precision" in averages
        assert "recall" in averages
        assert "faithfulness" in averages
        # precision: (0.95 + 0.82 + 0.78) / 3 = 0.85
        assert abs(averages["precision"] - 0.85) < 0.001

    def test_compute_failure_analysis(self, pipeline_result_with_data: Any) -> None:
        """_compute_failure_analysis extracts failure info."""

        class ConcreteReport(ReportGenerator):
            def generate(self, report: Any) -> str:
                return ""

            def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
                return Path(output_path)

        report_gen = ConcreteReport()
        failures = report_gen._compute_failure_analysis(pipeline_result_with_data)

        assert len(failures) == 2
        assert all(isinstance(f, FailureInfo) for f in failures)
        assert failures[0].error_type == "ProviderConnectionError"
        assert failures[1].error_type == "ProviderExecutionError"

    def test_compute_failure_analysis_empty(self, pipeline_result_empty: Any) -> None:
        """_compute_failure_analysis returns empty list for no errors."""

        class ConcreteReport(ReportGenerator):
            def generate(self, report: Any) -> str:
                return ""

            def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
                return Path(output_path)

        report_gen = ConcreteReport()
        failures = report_gen._compute_failure_analysis(pipeline_result_empty)
        assert failures == []
