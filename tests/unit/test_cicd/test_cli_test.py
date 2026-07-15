"""Unit tests for CLI test command."""

import re

from typer.testing import CliRunner

from openagent_eval.cli.main import app


runner = CliRunner()


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestTestCommand:
    """Tests for oaeval test command."""

    def test_test_command_help(self):
        """Test test command help output."""
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        output = _strip_ansi(result.output)
        assert "Run evaluation as a CI/CD test" in output

    def test_test_command_no_config(self):
        """Test test command without config shows error."""
        result = runner.invoke(app, ["test"])
        assert result.exit_code != 0

    def test_test_command_nonexistent_config(self):
        """Test test command with nonexistent config."""
        result = runner.invoke(app, ["test", "/nonexistent/config.yaml"])
        assert result.exit_code == 2

    def test_test_command_invalid_threshold_format(self):
        """Test test command with invalid threshold format."""
        result = runner.invoke(
            app,
            ["test", "config.yaml", "-t", "invalid_format"],
        )
        assert result.exit_code == 2

    def test_test_command_invalid_threshold_value(self):
        """Test test command with invalid threshold value."""
        result = runner.invoke(
            app,
            ["test", "config.yaml", "-t", "faithfulness:gte:not_a_number"],
        )
        assert result.exit_code == 2

    def test_test_command_invalid_operator(self):
        """Test test command with invalid operator."""
        result = runner.invoke(
            app,
            ["test", "config.yaml", "-t", "faithfulness:invalid:0.8"],
        )
        assert result.exit_code == 2

    def test_test_command_json_output(self):
        """Test test command with --json flag."""
        result = runner.invoke(app, ["test", "--help"])
        output = _strip_ansi(result.output)
        assert "json" in output.lower()

    def test_test_command_timeout_option(self):
        """Test test command with --timeout option."""
        result = runner.invoke(app, ["test", "--help"])
        output = _strip_ansi(result.output)
        assert "timeout" in output.lower()

    def test_test_command_threshold_option(self):
        """Test test command with --threshold option."""
        result = runner.invoke(app, ["test", "--help"])
        output = _strip_ansi(result.output)
        assert "threshold" in output.lower()
        assert "-t" in output
