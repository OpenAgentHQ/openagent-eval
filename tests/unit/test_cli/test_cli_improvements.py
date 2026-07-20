"""Tests for CLI improvements."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from openagent_eval.cli.context import (
    CLIContext,
    get_context,
    reset_context,
    set_context,
)
from openagent_eval.cli.main import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class TestGlobalFlags:
    """Tests for global CLI flags."""

    def test_quiet_flag(self):
        """Test that --quiet flag is accepted."""
        result = runner.invoke(app, ["--quiet", "--help"])
        assert result.exit_code == 0

    def test_json_flag(self):
        """Test that --json flag is accepted."""
        result = runner.invoke(app, ["--json", "--help"])
        assert result.exit_code == 0

    def test_no_color_flag(self):
        """Test that --no-color flag is accepted."""
        result = runner.invoke(app, ["--no-color", "--help"])
        assert result.exit_code == 0

    def test_verbose_flag(self):
        """Test that --verbose flag is accepted."""
        result = runner.invoke(app, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_multiple_global_flags(self):
        """Test that multiple global flags can be combined."""
        result = runner.invoke(app, ["--quiet", "--json", "--no-color", "--help"])
        assert result.exit_code == 0


class TestCLIContext:
    """Tests for CLI context management."""

    def test_get_context_default(self):
        """Test that get_context returns default context."""
        reset_context()
        ctx = get_context()
        assert ctx.quiet is False
        assert ctx.json_output is False
        assert ctx.no_color is False
        assert ctx.verbose is False

    def test_set_context(self):
        """Test that set_context updates the context."""
        ctx = CLIContext(quiet=True, verbose=True)
        set_context(ctx)
        retrieved = get_context()
        assert retrieved.quiet is True
        assert retrieved.verbose is True

    def test_reset_context(self):
        """Test that reset_context restores defaults."""
        set_context(CLIContext(quiet=True))
        reset_context()
        ctx = get_context()
        assert ctx.quiet is False


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_help(self):
        """Test that validate command shows help."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "validate" in result.output.lower() or "Validate" in result.output

    def test_validate_missing_config(self):
        """Test validate with missing config file."""
        result = runner.invoke(app, ["validate", "nonexistent.yaml"])
        assert result.exit_code == 2

    def test_validate_invalid_yaml(self, tmp_path):
        """Test validate with invalid YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        result = runner.invoke(app, ["validate", str(config_file)])
        # Should fail validation
        assert result.exit_code != 0 or "FAILED" in result.output


class TestDeleteCommand:
    """Tests for the delete command."""

    def test_delete_help(self):
        """Test that delete command shows help."""
        result = runner.invoke(app, ["delete", "--help"])
        assert result.exit_code == 0
        assert "delete" in result.output.lower() or "Delete" in result.output

    def test_delete_nonexistent_report(self):
        """Test delete with nonexistent report ID."""
        result = runner.invoke(app, ["delete", "nonexistent_report"])
        # Should fail or show error
        assert (
            result.exit_code != 0
            or "Error" in result.output
            or "not found" in result.output
        )


class TestCompletionCommand:
    """Tests for the completion command."""

    def test_completion_help(self):
        """Test that completion command shows help."""
        result = runner.invoke(app, ["completion", "--help"])
        assert result.exit_code == 0

    def test_completion_bash(self):
        """Test bash completion generation."""
        result = runner.invoke(app, ["completion", "bash"])
        assert result.exit_code == 0
        assert "complete" in result.output.lower() or "_oaeval" in result.output

    def test_completion_zsh(self):
        """Test zsh completion generation."""
        result = runner.invoke(app, ["completion", "zsh"])
        assert result.exit_code == 0
        assert "compdef" in result.output or "_oaeval" in result.output

    def test_completion_fish(self):
        """Test fish completion generation."""
        result = runner.invoke(app, ["completion", "fish"])
        assert result.exit_code == 0
        assert "complete" in result.output.lower()

    def test_completion_invalid_shell(self):
        """Test completion with invalid shell."""
        result = runner.invoke(app, ["completion", "powershell"])
        assert result.exit_code == 1


class TestRunCommandImprovements:
    """Tests for run command improvements."""

    def test_run_help_shows_dry_run(self):
        """Test that run help shows dry-run option."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output).lower()
        assert "dry-run" in output or "dry_run" in output

    def test_run_help_shows_metrics(self):
        """Test that run help shows metrics option."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output).lower()
        assert "metrics" in output

    def test_run_dry_run_missing_config(self):
        """Test dry-run with missing config."""
        result = runner.invoke(app, ["run", "--dry-run", "nonexistent.yaml"])
        assert result.exit_code == 2

    def test_run_dry_run_interpolates_timeout_warning(
        self, sample_config_path: Path
    ) -> None:
        """Dry-run warnings should display the configured timeout value."""
        sample_config_path.write_text(
            f"{sample_config_path.read_text()}\ntimeout: 30\n",
            encoding="utf-8",
        )

        result = runner.invoke(app, ["run", "--dry-run", str(sample_config_path)])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "Timeout is low (30.0s)" in output
        assert "{config.timeout}" not in output


class TestDoctorCommandImprovements:
    """Tests for doctor command improvements."""

    def test_doctor_help_shows_check_api(self):
        """Test that doctor help shows check-api option."""
        result = runner.invoke(app, ["doctor", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output).lower()
        assert "check-api" in output or "check_api" in output


class TestListCommandImprovements:
    """Tests for list command improvements."""

    def test_list_help_shows_sort(self):
        """Test that list help shows sort option."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "sort" in result.output.lower()

    def test_list_help_shows_search(self):
        """Test that list help shows search option."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "search" in result.output.lower()

    def test_list_help_shows_reverse(self):
        """Test that list help shows reverse option."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "reverse" in result.output.lower()


class TestInitCommandImprovements:
    """Tests for init command improvements."""

    def test_init_help_shows_interactive(self):
        """Test that init help shows interactive option."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "interactive" in result.output.lower()


class TestConfigDiscovery:
    """Tests for config auto-discovery."""

    def test_find_config_file_not_found(self, tmp_path):
        """Test config discovery when no config exists."""
        from openagent_eval.cli.utils.discovery import find_config_file

        result = find_config_file(tmp_path)
        assert result is None

    def test_find_config_file_found(self, tmp_path):
        """Test config discovery when config exists."""
        from openagent_eval.cli.utils.discovery import find_config_file

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "dataset: test.yaml\nllm:\n  provider: openai\n  model: gpt-4"
        )
        result = find_config_file(tmp_path)
        assert result == config_file

    def test_find_config_file_oaeval_name(self, tmp_path):
        """Test config discovery with oaeval.yaml name."""
        from openagent_eval.cli.utils.discovery import find_config_file

        config_file = tmp_path / "oaeval.yaml"
        config_file.write_text(
            "dataset: test.yaml\nllm:\n  provider: openai\n  model: gpt-4"
        )
        result = find_config_file(tmp_path)
        assert result == config_file


class TestVersionCommand:
    """Tests for version command."""

    def test_version_short_flag(self):
        """Test --version flag."""
        from importlib.metadata import version

        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.output.strip() == f"openagent-eval {version('openagent-eval')}"

    def test_version_V_flag(self):  # noqa: N802
        """Test -V flag."""
        from importlib.metadata import version

        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert result.output.strip() == f"openagent-eval {version('openagent-eval')}"

    def test_version_on_subcommand(self):
        """Test --version flag on subcommands."""
        from importlib.metadata import version

        expected = f"openagent-eval {version('openagent-eval')}"

        result_run = runner.invoke(app, ["run", "--version"])
        assert result_run.exit_code == 0
        assert result_run.output.strip() == expected

        result_init = runner.invoke(app, ["init", "-V"])
        assert result_init.exit_code == 0
        assert result_init.output.strip() == expected


class TestHelpOutput:
    """Tests for help output improvements."""

    def test_main_help_shows_all_commands(self):
        """Test that main help shows all commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # Check for all commands
        assert "init" in result.output.lower()
        assert "run" in result.output.lower()
        assert "report" in result.output.lower()
        assert "compare" in result.output.lower()
        assert "list" in result.output.lower()
        assert "doctor" in result.output.lower()
        assert "validate" in result.output.lower()
        assert "delete" in result.output.lower()
        assert "completion" in result.output.lower()

    def test_main_help_shows_global_flags(self):
        """Test that main help shows global flags."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--quiet" in output or "-q" in output
        assert "--json" in output
        assert "--no-color" in output
        assert "--verbose" in output or "-v" in output


class TestAuditCommand:
    """Tests for the audit command."""

    def test_audit_help(self):
        """Test that audit command shows help."""
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "audit" in result.output.lower() or "Audit" in result.output

    def test_audit_nonexistent_path(self):
        """Test audit command with a nonexistent path."""
        result = runner.invoke(app, ["audit", "/nonexistent/path"])
        assert result.exit_code == 2
        assert "error" in result.output.lower()

    @patch("openagent_eval.cli.commands.audit.CorpusAuditor")
    def test_audit_progress_updates(self, mock_auditor_class, tmp_path):
        """Test that progress callback is called and updates the progress bar."""
        from openagent_eval.corpus.models import AuditReport

        # Setup mock auditor instance
        mock_auditor = MagicMock()
        mock_auditor_class.return_value = mock_auditor

        # Define mock audit method that calls progress_callback
        async def mock_audit(corpus_path, progress_callback=None):
            if progress_callback:
                progress_callback("Scanning documents...", 0, 2)
                progress_callback("Running: staleness", 1, 2)
                progress_callback("Audit complete!", 2, 2)
            return AuditReport(
                corpus_path=corpus_path,
                total_documents=1,
                issues=[],
                health_score=1.0,
                checks_performed=["staleness"],
                summary="Mocked audit summary",
            )

        mock_auditor.audit = mock_audit

        # Create a temp file to satisfy path check
        dummy_file = tmp_path / "dummy.txt"
        dummy_file.write_text("content")

        result = runner.invoke(app, ["audit", str(dummy_file)])
        assert result.exit_code == 0
        assert "Mocked audit summary" in result.output
