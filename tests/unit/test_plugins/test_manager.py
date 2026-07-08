"""Unit tests for plugin manager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from openagent_eval.plugins.manager import PluginManager


class TestPluginManager:
    """Tests for PluginManager class."""

    def test_init(self) -> None:
        """Test PluginManager initialization."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)

        assert manager.registry == mock_registry
        assert manager.loader is not None
        assert manager._initialized is False

    def test_initialize(self) -> None:
        """Test initializing the plugin system."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)

        # Mock load_all_plugins to return empty dict
        with patch.object(manager.loader, "load_all_plugins", return_value={}):
            load_counts = manager.initialize()
            assert isinstance(load_counts, dict)
            assert manager._initialized is True

    def test_initialize_already_initialized(self) -> None:
        """Test initializing when already initialized."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)
        manager._initialized = True

        load_counts = manager.initialize()
        assert load_counts == {}

    def test_reload_plugins(self) -> None:
        """Test reloading plugins."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)

        # Mock load_all_plugins to return empty dict
        with patch.object(manager.loader, "load_all_plugins", return_value={}):
            load_counts = manager.reload_plugins()
            assert isinstance(load_counts, dict)
            assert manager._initialized is True

    def test_get_available_plugins(self) -> None:
        """Test getting available plugins."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)

        # Mock registry methods
        mock_registry.list_metrics.return_value = ["metric1", "metric2"]
        mock_registry.list_providers.return_value = ["provider1"]
        mock_registry.list_retrievers.return_value = []
        mock_registry.list_dataset_loaders.return_value = []
        mock_registry.list_report_generators.return_value = []

        available = manager.get_available_plugins()

        assert available["metrics"] == ["metric1", "metric2"]
        assert available["providers"] == ["provider1"]
        assert available["retrievers"] == []
        assert available["dataset_loaders"] == []
        assert available["report_generators"] == []

    def test_get_plugin_info_for_metric(self) -> None:
        """Test getting plugin info for a metric."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)

        # Create a mock plugin class
        mock_plugin_class = type(
            "MockMetric",
            (),
            {
                "name": "mock_metric",
                "description": "A mock metric",
                "__module__": "test_module",
                "__doc__": "Mock metric docstring",
            },
        )

        mock_registry.get_metric.return_value = mock_plugin_class

        info = manager.get_plugin_info("metrics", "mock_metric")

        assert info["name"] == "mock_metric"
        assert info["group"] == "metrics"
        assert info["class"] == mock_plugin_class
        assert info["module"] == "test_module"
        assert info["docstring"] == "Mock metric docstring"

    def test_get_plugin_info_for_unknown_group(self) -> None:
        """Test getting plugin info for an unknown group."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)

        with pytest.raises(ValueError, match="Unknown plugin group"):
            manager.get_plugin_info("unknown_group", "test_plugin")

    def test_is_initialized(self) -> None:
        """Test checking if initialized."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)

        assert manager.is_initialized() is False

        manager._initialized = True
        assert manager.is_initialized() is True

    def test_get_plugin_count(self) -> None:
        """Test getting plugin count."""
        mock_registry = MagicMock()
        manager = PluginManager(mock_registry)

        # Mock loader's get_plugin_count
        with patch.object(manager.loader, "get_plugin_count", return_value=5):
            count = manager.get_plugin_count()
            assert count == 5
