"""Unit tests for CLI test command."""

import pytest
from typer.testing import CliRunner

from openagent_eval.cli.main import app


runner = CliRunner()


class TestTestCommand:
    """Tests for oaeval test command."""

    def test_test_command_help(self):
        """Test test command help output."""
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        assert "Run evaluation as a CI/CD test" in result.output

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
        # This would need a valid config, so we just check the flag is accepted
        result = runner.invoke(
            app,
            ["test", "--help"],
        )
        assert "--json" in result.output

    def test_test_command_timeout_option(self):
        """Test test command with --timeout option."""
        result = runner.invoke(
            app,
            ["test", "--help"],
        )
        assert "--timeout" in result.output

    def test_test_command_threshold_option(self):
        """Test test command with --threshold option."""
        result = runner.invoke(
            app,
            ["test", "--help"],
        )
        assert "--threshold" in result.output
        assert "-t" in result.output
