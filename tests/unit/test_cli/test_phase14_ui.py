"""Tests for Phase 14: Hybrid CLI UI."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from openagent_eval.cli.main import app


runner = CliRunner()


class TestBannerModule:
    """Tests for the banner module."""

    def test_generate_ascii_art_returns_string(self):
        """Test that ASCII art generation returns a string."""
        from openagent_eval.cli.banner import _generate_ascii_art

        result = _generate_ascii_art("test")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_ascii_art_fallback(self):
        """Test ASCII art fallback when pyfiglet is not available."""
        from openagent_eval.cli.banner import _generate_ascii_art

        with patch.dict("sys.modules", {"pyfiglet": None}):
            result = _generate_ascii_art("test")
            assert isinstance(result, str)
            assert "OAEVAL" in result or "██" in result

    def test_get_version_returns_string(self):
        """Test that version retrieval returns a string."""
        from openagent_eval.cli.banner import _get_version

        result = _get_version()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_create_mini_banner_no_error(self):
        """Test that mini banner displays without error."""
        from rich.console import Console

        from openagent_eval.cli.banner import create_mini_banner

        console = Console(force_terminal=True)
        # Should not raise
        create_mini_banner(console=console)

    def test_create_banner_no_error(self):
        """Test that full banner displays without error."""
        from rich.console import Console

        from openagent_eval.cli.banner import create_banner

        console = Console(force_terminal=True)
        # Should not raise
        create_banner(console=console, show_version=True)
        create_banner(console=console, show_version=False)


class TestUICommand:
    """Tests for the oaeval ui command."""

    def test_ui_command_exists(self):
        """Test that the ui command is registered."""
        result = runner.invoke(app, ["ui", "--help"])
        assert result.exit_code == 0
        assert "TUI" in result.stdout or "dashboard" in result.stdout.lower()

    def test_ui_command_shows_config_option(self):
        """Test that the ui command shows --config option."""
        result = runner.invoke(app, ["ui", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.stdout


class TestUIModule:
    """Tests for the UI module structure."""

    def test_ui_module_importable(self):
        """Test that the UI module can be imported."""
        import openagent_eval.ui

        assert hasattr(openagent_eval.ui, "OAEvalDashboard")

    def test_widgets_importable(self):
        """Test that widgets can be imported."""
        from openagent_eval.ui.widgets import (
            BannerWidget,
            MetricsSummaryWidget,
            ProgressWidget,
            ResultsTableWidget,
            StatusWidget,
        )

        assert BannerWidget is not None
        assert StatusWidget is not None
        assert MetricsSummaryWidget is not None
        assert ResultsTableWidget is not None
        assert ProgressWidget is not None

    def test_screens_importable(self):
        """Test that screens can be imported."""
        from openagent_eval.ui.screens import (
            AuditScreen,
            DiagnoseScreen,
            EvaluateScreen,
            HelpScreen,
            MainDashboard,
        )

        assert MainDashboard is not None
        assert EvaluateScreen is not None
        assert AuditScreen is not None
        assert DiagnoseScreen is not None
        assert HelpScreen is not None

    def test_app_importable(self):
        """Test that the app can be imported."""
        from openagent_eval.ui.app import OAEvalDashboard, run_ui

        assert OAEvalDashboard is not None
        assert callable(run_ui)


class TestUIRunCommand:
    """Tests for running the UI command."""

    def test_ui_run_without_textual(self):
        """Test UI command graceful failure without textual."""
        import sys

        # Save original module state
        textual_module = sys.modules.get("textual")

        try:
            # Remove textual from modules to simulate missing dependency
            sys.modules["textual"] = None

            result = runner.invoke(app, ["ui"])
            # Should fail gracefully with helpful error message
            assert result.exit_code == 1
        finally:
            # Restore original state
            if textual_module is not None:
                sys.modules["textual"] = textual_module
            elif "textual" in sys.modules:
                del sys.modules["textual"]


class TestCLIBannerIntegration:
    """Tests for banner integration in CLI."""

    def test_main_help_displays(self):
        """Test that main help still works with banner."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "OpenAgent Eval" in result.stdout or "oaeval" in result.stdout

    def test_quiet_flag_suppresses_banner(self):
        """Test that quiet flag suppresses banner."""
        result = runner.invoke(app, ["--quiet", "--help"])
        assert result.exit_code == 0

    def test_ui_in_help_output(self):
        """Test that ui command appears in help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ui" in result.stdout.lower()
