"""Tests for HTMLReport generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from openagent_eval.reports.html import HTMLReport


class TestHTMLReport:
    """Tests for HTMLReport generator."""

    def test_generate_returns_string(self, evaluation_report: Any) -> None:
        """generate() returns a non-empty string."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_is_valid_html(self, evaluation_report: Any) -> None:
        """generate() produces valid HTML."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "</html>" in result
        assert "<head>" in result
        assert "<body>" in result

    def test_generate_contains_title(self, evaluation_report: Any) -> None:
        """generate() includes the report title."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "Test Report" in result

    def test_generate_contains_summary(self, evaluation_report: Any) -> None:
        """generate() includes summary statistics."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "Summary" in result
        assert "5" in result  # total_items
        assert "3" in result  # successful
        assert "2" in result  # failed

    def test_generate_contains_metrics(self, evaluation_report: Any) -> None:
        """generate() includes metrics table."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "Metrics" in result
        assert "precision" in result
        assert "0.8500" in result

    def test_generate_contains_errors(self, evaluation_report: Any) -> None:
        """generate() includes error analysis."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "Error Analysis" in result
        assert "ProviderConnectionError" in result

    def test_generate_contains_results(self, evaluation_report: Any) -> None:
        """generate() includes sample results."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "Sample Results" in result
        assert "What is Python?" in result

    def test_generate_contains_config(self, evaluation_report: Any) -> None:
        """generate() includes configuration."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "Configuration" in result
        assert "openai" in result
        assert "gpt-4o" in result

    def test_generate_contains_footer(self, evaluation_report: Any) -> None:
        """generate() includes footer."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "OpenAgent Eval" in result

    def test_generate_empty_report(self, evaluation_report_empty: Any) -> None:
        """generate() handles empty results."""
        report = HTMLReport()
        result = report.generate(evaluation_report_empty)
        assert "<!DOCTYPE html>" in result
        assert "0" in result

    def test_generate_to_file(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() writes to an HTML file."""
        report = HTMLReport()
        output_path = tmp_path / "report.html"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_generate_to_file_adds_extension(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() appends .html if missing."""
        report = HTMLReport()
        output_path = tmp_path / "report"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        assert str(result_path).endswith(".html")

    def test_generate_to_file_creates_directory(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() creates parent directories."""
        report = HTMLReport()
        output_path = tmp_path / "subdir" / "report.html"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_custom_template_path(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """HTMLReport accepts a custom template path."""
        custom_template = tmp_path / "custom.html"
        custom_template.write_text(
            "<html><body>{{ title }}</body></html>",
            encoding="utf-8",
        )

        report = HTMLReport(template_path=custom_template)
        result = report.generate(evaluation_report)
        assert "Test Report" in result

    def test_css_styles_present(self, evaluation_report: Any) -> None:
        """generate() includes CSS styles."""
        report = HTMLReport()
        result = report.generate(evaluation_report)
        assert "<style>" in result
        assert "var(--primary)" in result
