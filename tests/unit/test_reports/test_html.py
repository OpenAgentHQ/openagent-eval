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

    def test_generate_respects_max_examples(
        self, evaluation_report_limited: Any
    ) -> None:
        """generate() includes at most config.report.max_examples results."""
        report = HTMLReport()
        captured_context: dict[str, Any] = {}

        def _capture_context(context: dict[str, Any]) -> str:
            captured_context.update(context)
            return "ok"

        report._render_template = _capture_context
        report.generate(evaluation_report_limited)

        assert len(captured_context["results"]) == 2

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

    def test_generate_to_file_replaces_non_html_extension(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() replaces non-.html suffixes with .html."""
        report = HTMLReport()
        output_path = tmp_path / "report.txt"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path == tmp_path / "report.html"
        assert result_path.exists()

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

    def test_generate_ignores_non_numeric_metrics_for_overall_score(
        self, evaluation_report: Any
    ) -> None:
        """generate() computes overall score from numeric metric values only."""
        report = HTMLReport()
        evaluation_report.summary["metrics_summary"] = {
            "precision": 0.8,
            "count": 2,
            "ignored_bool": True,
            "ignored_text": "0.9",
            "ignored_dict": {"value": 1.0},
        }
        captured_context: dict[str, Any] = {}

        def _capture_context(context: dict[str, Any]) -> str:
            captured_context.update(context)
            return "ok"

        report._render_template = _capture_context
        report.generate(evaluation_report)

        assert captured_context["overall_score"] == pytest.approx(1.4)

    def test_load_template_missing_builtin_has_installation_guidance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_load_template() raises a packaging-focused guidance message."""
        report = HTMLReport()
        monkeypatch.setattr(Path, "exists", lambda _: False)

        with pytest.raises(FileNotFoundError) as exc_info:
            report._load_template()

        message = str(exc_info.value)
        assert "openagent_eval/reports/templates/report.html" in message
        assert "Install jinja2" not in message
