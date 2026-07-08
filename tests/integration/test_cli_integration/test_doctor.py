"""Tests for oaeval doctor command."""

from __future__ import annotations

from typer.testing import CliRunner

from openagent_eval.cli.main import app


def test_doctor_checks_env(runner: CliRunner) -> None:
    """doctor command verifies environment and dependencies."""
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    # Should display environment status
    assert "Environment Status" in result.output or "Python" in result.output


def test_doctor_verbose(runner: CliRunner) -> None:
    """doctor command shows detailed info with --verbose flag."""
    result = runner.invoke(app, ["doctor", "--verbose"])

    assert result.exit_code == 0
    # Verbose should show more details
    assert "Python" in result.output


def test_doctor_shows_api_keys(runner: CliRunner) -> None:
    """doctor command checks API key availability."""
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    # Should show API key status table
    assert "API Key" in result.output or "OpenAI" in result.output
