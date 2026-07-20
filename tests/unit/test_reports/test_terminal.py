"""Tests for TerminalReport generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console

from openagent_eval.reports.terminal import TerminalReport


class TestTerminalReport:
    """Tests for TerminalReport generator."""

    def test_generate_returns_string(self, evaluation_report: Any) -> None:
        """generate() returns a non-empty string."""
        report = TerminalReport()
        result = report.generate(evaluation_report)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_contains_summary(self, evaluation_report: Any) -> None:
        """generate() includes summary information."""
        report = TerminalReport()
        result = report.generate(evaluation_report)
        assert "SUMMARY" in result
        assert "Total items" in result
        assert "5" in result  # total_items

    def test_generate_contains_metrics(self, evaluation_report: Any) -> None:
        """generate() includes metrics."""
        report = TerminalReport()
        result = report.generate(evaluation_report)
        assert "METRICS" in result
        assert "precision" in result
        assert "recall" in result

    def test_generate_contains_errors(self, evaluation_report: Any) -> None:
        """generate() includes error breakdown."""
        report = TerminalReport()
        result = report.generate(evaluation_report)
        assert "ERRORS" in result
        assert "ProviderConnectionError" in result

    def test_generate_contains_config(self, evaluation_report: Any) -> None:
        """generate() includes configuration info."""
        report = TerminalReport()
        result = report.generate(evaluation_report)
        assert "CONFIGURATION" in result
        assert "openai" in result
        assert "gpt-4o" in result

    def test_generate_empty_report(self, evaluation_report_empty: Any) -> None:
        """generate() handles empty results."""
        report = TerminalReport()
        result = report.generate(evaluation_report_empty)
        assert "Total items" in result
        assert "0" in result

    def test_generate_to_file(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() writes to a file."""
        report = TerminalReport()
        output_path = tmp_path / "report.txt"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "SUMMARY" in content

    def test_generate_to_file_creates_directory(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() creates parent directories."""
        report = TerminalReport()
        output_path = Path(tmp_path / "subdir" / "report.txt")
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_generate_to_file_defaults_to_txt(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() appends report.txt when no extension is given."""
        report = TerminalReport()
        output_path = tmp_path / "my_report"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.name == "report.txt"
        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "SUMMARY" in content

    def test_generate_to_file_normalizes_wrong_suffix(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() normalizes a non-.txt suffix to .txt."""
        report = TerminalReport()
        output_path = tmp_path / "my_report.log"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.suffix.lower() == ".txt"
        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "SUMMARY" in content

    def test_generate_to_file_keeps_txt_suffix(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() preserves an explicit .txt path."""
        report = TerminalReport()
        output_path = tmp_path / "explicit.txt"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.name == "explicit.txt"
        assert result_path.exists()

    def test_print_report(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """print_report() outputs to console."""
        output_file = tmp_path / "console_output.txt"
        console = Console(file=open(output_file, "w", encoding="utf-8"))  # noqa: SIM115
        report = TerminalReport(console=console)
        # Should not raise
        report.print_report(evaluation_report)

    def test_custom_console(self) -> None:
        """TerminalReport accepts a custom Console."""
        console = Console()
        report = TerminalReport(console=console)
        assert report.console is console

    def test_default_console(self) -> None:
        """TerminalReport creates a default Console."""
        report = TerminalReport()
        assert isinstance(report.console, Console)
