"""Tests for the oaeval diagnose command."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from openagent_eval.cli.context import reset_context
from openagent_eval.cli.main import app
from openagent_eval.diagnosis.models import (
    BlameTarget,
    DiagnosisReport,
    FailureInstance,
    FailureMode,
)

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


@pytest.fixture(autouse=True)
def _reset_cli_context() -> None:
    """Reset the global CLI context before and after every test.

    The CLI context (quiet/json/verbose flags) lives in a module-level
    global, so leaving it dirty between tests can make later tests pass
    or fail depending on run order.
    """
    reset_context()
    yield
    reset_context()


@pytest.fixture
def fake_analyzer(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Replace DiagnosisAnalyzer so no real model or analysis code is executed.

    Yields a holder dict recording every constructed analyzer instance, its
    constructor kwargs, and the DiagnosisReport returned from ``analyze``.
    """
    report = DiagnosisReport(
        total_items=2,
        blame_summary={BlameTarget.RETRIEVAL.value: 1},
        failure_summary={FailureMode.EMPTY_RETRIEVAL.value: 1},
        failures=[
            FailureInstance(
                mode=FailureMode.EMPTY_RETRIEVAL,
                blame=BlameTarget.RETRIEVAL,
                confidence=0.85,
                reason="No contexts were retrieved.",
                question="What is RAG?",
                evidence={"context_count": 0},
            ),
        ],
        chunking_issues=[],
        recommendations=[
            "Check if the retriever is using the correct embedding model."
        ],
        overall_health=0.5,
    )
    holder: dict = {"instances": [], "report": report}

    def factory(**kwargs: object) -> MagicMock:
        instance = MagicMock()
        instance.init_kwargs = kwargs
        instance.analyze = MagicMock(return_value=holder["report"])
        holder["instances"].append(instance)
        return instance

    monkeypatch.setattr(
        "openagent_eval.cli.commands.diagnose.DiagnosisAnalyzer", factory
    )
    return holder


def _write_report(path: Path, payload: object) -> None:
    """Write ``payload`` as JSON to ``path``."""
    path.write_text(json.dumps(payload), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Argument parsing and help
# --------------------------------------------------------------------------- #


def test_diagnose_help_lists_documented_flags() -> None:
    """Help output exposes the command's public arguments and options."""
    result = runner.invoke(app, ["diagnose", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert "report_path" in output
    for flag in ("--output", "--threshold", "--max-recs", "--verbose"):
        assert flag in output


def test_diagnose_missing_argument_exits_two() -> None:
    """Invoking diagnose without a report path is a usage error (exit 2)."""
    result = runner.invoke(app, ["diagnose"])
    assert result.exit_code == 2
    assert "REPORT_PATH" in result.output or "Missing" in result.output


# --------------------------------------------------------------------------- #
# Input validation errors (exit code 2)
# --------------------------------------------------------------------------- #


def test_diagnose_missing_file_exits_two(tmp_path: Path) -> None:
    """A non-existent report file surfaces as exit code 2."""
    missing = tmp_path / "missing.json"
    result = runner.invoke(app, ["diagnose", str(missing)])
    assert result.exit_code == 2
    assert "not found" in strip_ansi(result.output).lower()


def test_diagnose_non_json_file_exits_two(tmp_path: Path) -> None:
    """A report file that is not JSON surfaces as exit code 2."""
    report = tmp_path / "report.txt"
    report.write_text("not json", encoding="utf-8")
    result = runner.invoke(app, ["diagnose", str(report)])
    assert result.exit_code == 2
    assert "json" in strip_ansi(result.output).lower()


def test_diagnose_invalid_json_exits_two(tmp_path: Path) -> None:
    """Malformed JSON in the report file surfaces as exit code 2."""
    report = tmp_path / "report.json"
    report.write_text("{not valid json", encoding="utf-8")
    result = runner.invoke(app, ["diagnose", str(report)])
    assert result.exit_code == 2
    assert "parse" in strip_ansi(result.output).lower()


# --------------------------------------------------------------------------- #
# Report-loading edge cases
# --------------------------------------------------------------------------- #


def test_diagnose_empty_results_exits_zero(tmp_path: Path) -> None:
    """A report containing an empty list of results exits cleanly with a warning."""
    report = tmp_path / "report.json"
    _write_report(report, [])
    result = runner.invoke(app, ["diagnose", str(report)])
    assert result.exit_code == 0, result.output
    assert "no evaluation results" in strip_ansi(result.output).lower()


def test_diagnose_unsupported_report_format_exits_zero(
    tmp_path: Path,
    fake_analyzer: dict,
) -> None:
    """A JSON payload that is neither a list nor a {results: ...} wrapper yields no results."""
    report = tmp_path / "report.json"
    _write_report(report, {"meta": "data"})
    result = runner.invoke(app, ["diagnose", str(report)])
    assert result.exit_code == 0, result.output
    assert "no evaluation results" in strip_ansi(result.output).lower()
    assert fake_analyzer["instances"] == []


def test_diagnose_pipeline_result_wrapper_is_loaded(
    tmp_path: Path,
    fake_analyzer: dict,
) -> None:
    """A PipelineResult-style wrapper with a 'results' key is unpacked correctly."""
    report = tmp_path / "report.json"
    results = [{"question": "Q1", "answer": "A1"}]
    _write_report(report, {"results": results})
    result = runner.invoke(app, ["diagnose", str(report)])
    assert result.exit_code == 0, result.output
    assert len(fake_analyzer["instances"]) == 1
    assert fake_analyzer["instances"][0].analyze.call_args.args[0] == results


# --------------------------------------------------------------------------- #
# Happy path and output formats
# --------------------------------------------------------------------------- #


def test_diagnose_happy_path_terminal_output(
    tmp_path: Path,
    fake_analyzer: dict,
) -> None:
    """The default terminal output renders the diagnosis report."""
    report = tmp_path / "report.json"
    _write_report(report, [{"question": "Q1", "answer": "A1"}])
    result = runner.invoke(app, ["diagnose", str(report)])
    assert result.exit_code == 0, result.output
    output = strip_ansi(result.output)
    assert "Diagnosis Report" in output
    assert "Items analyzed: 2" in output
    assert "System Health" in output
    assert "Retrieval" in output
    assert "Check if the retriever is using the correct embedding model" in output


def test_diagnose_json_output_format(
    tmp_path: Path,
    fake_analyzer: dict,
) -> None:
    """--output json emits a JSON-serialized DiagnosisReport."""
    report = tmp_path / "report.json"
    _write_report(report, [{"question": "Q1", "answer": "A1"}])
    result = runner.invoke(app, ["diagnose", str(report), "--output", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(strip_ansi(result.output))
    assert payload["total_items"] == 2
    assert payload["blame_summary"] == {BlameTarget.RETRIEVAL.value: 1}
    assert payload["overall_health"] == 0.5


def test_diagnose_global_json_flag_triggers_json_output(
    tmp_path: Path,
    fake_analyzer: dict,
) -> None:
    """The global --json flag forces JSON output even when --output is omitted."""
    report = tmp_path / "report.json"
    _write_report(report, [{"question": "Q1", "answer": "A1"}])
    result = runner.invoke(app, ["--json", "diagnose", str(report)])
    assert result.exit_code == 0, result.output
    payload = json.loads(strip_ansi(result.output))
    assert payload["total_items"] == 2


# --------------------------------------------------------------------------- #
# Option wiring
# --------------------------------------------------------------------------- #


def test_diagnose_threshold_and_max_recs_passed_to_analyzer(
    tmp_path: Path,
    fake_analyzer: dict,
) -> None:
    """--threshold and --max-recs reach the DiagnosisAnalyzer constructor."""
    report = tmp_path / "report.json"
    _write_report(report, [{"question": "Q1", "answer": "A1"}])
    result = runner.invoke(
        app,
        [
            "diagnose",
            str(report),
            "--threshold",
            "0.7",
            "--max-recs",
            "3",
        ],
    )
    assert result.exit_code == 0, result.output
    kwargs = fake_analyzer["instances"][0].init_kwargs
    assert kwargs["blame_threshold"] == 0.7
    assert kwargs["max_recommendations"] == 3


def test_diagnose_verbose_shows_detailed_failures(
    tmp_path: Path,
    fake_analyzer: dict,
) -> None:
    """--verbose includes detailed failure information in terminal output."""
    report = tmp_path / "report.json"
    _write_report(report, [{"question": "Q1", "answer": "A1"}])
    result = runner.invoke(app, ["diagnose", str(report), "--verbose"])
    assert result.exit_code == 0, result.output
    output = strip_ansi(result.output)
    assert "Detailed Failures" in output
    assert "Empty Retrieval" in output
    assert "No contexts were retrieved" in output
    assert "What is RAG?" in output
