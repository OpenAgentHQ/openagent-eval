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
