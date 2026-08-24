"""Tests for the CLI main module."""

from __future__ import annotations

from io import StringIO

import pytest
import typer
from rich.console import Console
from typer.testing import CliRunner

from openagent_eval.cli import main
from openagent_eval.cli.main import app

runner = CliRunner()


def test_cli_help():
    """Test that CLI shows help when invoked without arguments."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "OpenAgent Eval" in result.output
    assert "Open-source CLI framework" in result.output


def test_cli_version():
    """Test that CLI shows version when invoked with --version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0


def test_cli_init_help():
    """Test that init command shows help."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "init" in result.output.lower() or "Create" in result.output


def test_cli_run_help():
    """Test that run command shows help."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "run" in result.output.lower() or "Run" in result.output


def test_cli_report_help():
    """Test that report command shows help."""
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0


def test_cli_compare_help():
    """Test that compare command shows help."""
    result = runner.invoke(app, ["compare", "--help"])
    assert result.exit_code == 0


def test_cli_list_help():
    """Test that list command shows help."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0


def test_cli_doctor_help():
    """Test that doctor command shows help."""
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0


def test_all_cli_commands_are_exported():
    """Test that every command is available from the package namespace."""
    from openagent_eval.cli import commands

    expected = {
        "audit_command",
        "compare_command",
        "delete_command",
        "diagnose_command",
        "doctor_command",
        "init_command",
        "list_command",
        "report_command",
        "run_command",
        "synth_command",
        "test_command",
        "validate_command",
    }

    assert set(commands.__all__) == expected
    assert all(hasattr(commands, name) for name in expected)


def test_cli_invalid_command():
    """Test that CLI handles invalid commands gracefully."""
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0


@pytest.mark.parametrize(
    "message",
    ["boom", "dynamic [bold] text", "dynamic [/dim] text"],
)
def test_unexpected_cli_exception_preserves_diagnostic_and_exit_code(
    monkeypatch, message
):
    """Unexpected errors render arbitrary diagnostics and exit through Typer."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, color_system=None)
    monkeypatch.setattr(main, "Console", lambda **kwargs: console)

    with pytest.raises(BaseException) as exc_info:
        main._cli_exception_handler(RuntimeError, RuntimeError(message), None)

    assert isinstance(exc_info.value, typer.Exit)
    assert exc_info.value.exit_code == 1
    rendered = output.getvalue()
    assert "Unexpected error" in rendered
    assert message in rendered
    assert "https://github.com/OpenAgentHQ/openagent-eval/issues" in rendered


# ------------------------------------------------------------------ #
# M18 regression test                                                  #
# ------------------------------------------------------------------ #
def test_resolve_report_id_accepts_file_path(tmp_path):
    """M18: resolve_report_id must accept a direct file path."""
    import json

    from openagent_eval.cli.utils.helpers import resolve_report_id
    from openagent_eval.reports.manager import ReportManager

    report_data = {"report_id": "r1", "scores": {"f1": 0.9}}
    report_file = tmp_path / "my_report.json"
    report_file.write_text(json.dumps(report_data), encoding="utf-8")

    result = resolve_report_id(
        str(report_file),
        output_dir=tmp_path,
        manager=ReportManager(),
    )
    assert result["report_id"] == "r1"
    assert result["scores"]["f1"] == 0.9
