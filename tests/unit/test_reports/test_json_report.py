"""Tests for JSONReport generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from openagent_eval.reports.json_report import JSONReport


class TestJSONReport:
    """Tests for JSONReport generator."""

    def test_generate_returns_string(self, evaluation_report: Any) -> None:
        """generate() returns a non-empty string."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_is_valid_json(self, evaluation_report: Any) -> None:
        """generate() produces valid JSON."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_generate_contains_metadata(self, evaluation_report: Any) -> None:
        """generate() includes metadata."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        data = json.loads(result)
        assert "metadata" in data
        assert data["metadata"]["engine"] == "openagent-eval"
        assert data["metadata"]["version"] == "0.1.0"
        assert "timestamp" in data["metadata"]

    def test_generate_contains_summary(self, evaluation_report: Any) -> None:
        """generate() includes summary."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        data = json.loads(result)
        assert "summary" in data
        assert data["summary"]["total_items"] == 5
        assert data["summary"]["successful_evaluations"] == 3
        assert data["summary"]["failed_evaluations"] == 2

    def test_generate_contains_metrics(self, evaluation_report: Any) -> None:
        """generate() includes metrics summary."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        data = json.loads(result)
        assert "precision" in data["summary"]["metrics_summary"]
        assert data["summary"]["metrics_summary"]["precision"] == 0.85

    def test_generate_contains_results(self, evaluation_report: Any) -> None:
        """generate() includes individual results."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        data = json.loads(result)
        assert "results" in data
        assert len(data["results"]) == 3
        assert data["results"][0]["question"] == "What is Python?"
        assert "precision" in data["results"][0]["metrics"]

    def test_generate_contains_errors(self, evaluation_report: Any) -> None:
        """generate() includes errors."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        data = json.loads(result)
        assert "errors" in data
        assert len(data["errors"]) == 2

    def test_generate_contains_failure_analysis(
        self, evaluation_report: Any
    ) -> None:
        """generate() includes failure analysis."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        data = json.loads(result)
        assert "failure_analysis" in data
        assert data["failure_analysis"]["total_errors"] == 2
        assert "ProviderConnectionError" in data["failure_analysis"]["error_breakdown"]

    def test_generate_contains_configuration(
        self, evaluation_report: Any
    ) -> None:
        """generate() includes configuration."""
        report = JSONReport()
        result = report.generate(evaluation_report)
        data = json.loads(result)
        assert "configuration" in data
        assert data["configuration"]["dataset"]["path"] == "tests/sample_data/test_dataset.json"
        assert data["configuration"]["llm"]["provider"] == "openai"
        assert data["configuration"]["llm"]["model"] == "gpt-4o"

    def test_generate_empty_report(self, evaluation_report_empty: Any) -> None:
        """generate() handles empty results."""
        report = JSONReport()
        result = report.generate(evaluation_report_empty)
        data = json.loads(result)
        assert data["summary"]["total_items"] == 0
        assert data["results"] == []

    def test_generate_to_file(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() writes to a JSON file."""
        report = JSONReport()
        output_path = tmp_path / "report.json"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        data = json.loads(content)
        assert "metadata" in data

    def test_generate_to_file_adds_extension(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() appends .json if missing."""
        report = JSONReport()
        output_path = tmp_path / "report"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        assert str(result_path).endswith(".json")

    def test_generate_to_file_creates_directory(
        self, evaluation_report: Any, tmp_path: Path
    ) -> None:
        """generate_to_file() creates parent directories."""
        report = JSONReport()
        output_path = tmp_path / "subdir" / "report.json"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_compact_output(self, evaluation_report: Any) -> None:
        """generate_compact() produces single-line JSON."""
        report = JSONReport()
        compact = report.generate_compact(evaluation_report)
        # Compact JSON should not have newlines between items
        assert "\n" not in compact.strip()
        # Should still be valid JSON
        data = json.loads(compact)
        assert "metadata" in data

    def test_custom_indent(self, evaluation_report: Any) -> None:
        """JSONReport accepts custom indent."""
        report = JSONReport(indent=4)
        result = report.generate(evaluation_report)
        # Should have 4-space indentation
        assert '    "metadata"' in result

    def test_sort_keys(self, evaluation_report: Any) -> None:
        """JSONReport can sort keys."""
        report = JSONReport(sort_keys=True)
        result = report.generate(evaluation_report)
        data = json.loads(result)
        keys = list(data.keys())
        assert keys == sorted(keys)
