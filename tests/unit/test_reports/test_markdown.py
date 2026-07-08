"""Tests for MarkdownReport generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from openagent_eval.reports.markdown import MarkdownReport


class TestMarkdownReport:
    """Tests for MarkdownReport generator."""

    def test_generate_returns_string(self, evaluation_report: Any) -> None:
        """generate() returns a non-empty string."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_is_valid_markdown(self, evaluation_report: Any) -> None:
        """generate() produces valid markdown with headers."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert result.startswith("# ")
        assert "## Summary" in result
        assert "## Metrics" in result

    def test_generate_contains_summary_table(self, evaluation_report: Any) -> None:
        """generate() includes summary table."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert "| Metric | Value |" in result
        assert "| Total Items | 5 |" in result
        assert "| Successful | 3 |" in result
        assert "| Failed | 2 |" in result

    def test_generate_contains_metrics_table(self, evaluation_report: Any) -> None:
        """generate() includes metrics table."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert "| Metric | Average Score |" in result
        assert "precision" in result
        assert "0.8500" in result

    def test_generate_contains_overall_score(self, evaluation_report: Any) -> None:
        """generate() includes overall score."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert "Overall Average Score" in result

    def test_generate_contains_error_analysis(self, evaluation_report: Any) -> None:
        """generate() includes error analysis."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert "## Error Analysis" in result
        assert "ProviderConnectionError" in result

    def test_generate_contains_sample_results(self, evaluation_report: Any) -> None:
        """generate() includes sample results."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert "## Sample Results" in result
        assert "What is Python?" in result

    def test_generate_contains_config(self, evaluation_report: Any) -> None:
        """generate() includes configuration."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert "## Configuration" in result
        assert "```yaml" in result
        assert "openai" in result

    def test_generate_contains_footer(self, evaluation_report: Any) -> None:
        """generate() includes footer."""
        report = MarkdownReport()
        result = report.generate(evaluation_report)
        assert "OpenAgent Eval" in result
        assert "v0.1.0" in result

    def test_generate_empty_report(self, evaluation_report_empty: Any) -> None:
        """generate() handles empty results."""
        report = MarkdownReport()
        result = report.generate(evaluation_report_empty)
        assert "## Summary" in result
        assert "| Total Items | 0 |" in result

    def test_generate_to_file(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() writes to a .md file."""
        report = MarkdownReport()
        output_path = tmp_path / "report.md"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "## Summary" in content

    def test_generate_to_file_adds_extension(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() appends .md if missing."""
        report = MarkdownReport()
        output_path = tmp_path / "report"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        assert str(result_path).endswith(".md")

    def test_generate_to_file_creates_directory(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() creates parent directories."""
        report = MarkdownReport()
        output_path = tmp_path / "subdir" / "report.md"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()
