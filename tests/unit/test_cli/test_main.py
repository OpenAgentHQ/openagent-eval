"""Tests for the CLI main module."""

from __future__ import annotations

from typer.testing import CliRunner

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


def test_cli_invalid_command():
    """Test that CLI handles invalid commands gracefully."""
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0


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
