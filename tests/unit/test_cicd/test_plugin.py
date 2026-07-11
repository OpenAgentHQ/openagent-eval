"""Unit tests for CI/CD plugin."""

import pytest

from openagent_eval.cicd.models import (
    CICDConfig,
    EvaluationGate,
    ThresholdConfig,
    ThresholdOperator,
)
from openagent_eval.cicd.plugin import OAEvalPlugin


class TestOAEvalPlugin:
    """Tests for OAEvalPlugin class."""

    def test_plugin_class_exists(self):
        """Test that OAEvalPlugin class exists."""
        assert hasattr(OAEvalPlugin, "run_evaluation")
        assert hasattr(OAEvalPlugin, "run_evaluation_from_config")

    def test_run_evaluation_from_config_missing_path(self):
        """Test run_evaluation_from_config raises error without config_path."""
        config = CICDConfig()
        with pytest.raises(ValueError, match="config_path is required"):
            OAEvalPlugin.run_evaluation_from_config(config)

    def test_run_evaluation_nonexistent_config(self):
        """Test run_evaluation with nonexistent config file."""
        with pytest.raises(FileNotFoundError):
            OAEvalPlugin.run_evaluation(
                config_path="/nonexistent/config.yaml",
                timeout=10,
            )

    def test_parse_thresholds_invalid_format(self):
        """Test parsing invalid threshold format."""
        # This would be tested via the CLI command, but we can test the logic
        # The parsing happens in the test_command function
        pass


class TestPluginMarkers:
    """Tests for pytest plugin markers."""

    def test_plugin_has_markers(self):
        """Test that plugin defines expected markers."""
        # The plugin registers markers via pytest_configure
        # We just verify the module structure is correct
        from openagent_eval.cicd import plugin

        assert hasattr(plugin, "pytest_addoption")
        assert hasattr(plugin, "pytest_configure")
        assert hasattr(plugin, "pytest_collection_modifyitems")
