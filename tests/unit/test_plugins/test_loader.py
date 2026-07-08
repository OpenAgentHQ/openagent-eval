"""Unit tests for plugin loader."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from openagent_eval.plugins.loader import PluginLoader


class TestPluginLoader:
    """Tests for PluginLoader class."""

    def test_init(self) -> None:
        """Test PluginLoader initialization."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)

        assert loader.registry == mock_registry
        assert loader._loaded_plugins == {}

    def test_load_all_plugins(self) -> None:
        """Test loading all plugins."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)

        # Mock discover_all_plugins to return empty dict
        with patch("openagent_eval.plugins.loader.discover_all_plugins", return_value={}):
            load_counts = loader.load_all_plugins()
            assert isinstance(load_counts, dict)
            assert sum(load_counts.values()) == 0

    def test_load_plugins_by_group(self) -> None:
        """Test loading plugins for a specific group."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)

        # Mock discover_plugins to return empty dict
        with patch("openagent_eval.plugins.loader.discover_plugins", return_value={}):
            count = loader.load_plugins_by_group("metrics")
            assert count == 0

    def test_register_plugins_with_metrics(self) -> None:
        """Test registering metric plugins."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)

        # Create a mock plugin class
        mock_plugin_class = type(
            "MockMetric",
            (),
            {"name": "mock_metric", "description": "A mock metric"},
        )

        plugins = {"mock_metric": mock_plugin_class}
        count = loader._register_plugins("metrics", plugins)

        assert count == 1
        mock_registry.register_metric.assert_called_once_with(
            "mock_metric", mock_plugin_class
        )

    def test_register_plugins_with_providers(self) -> None:
        """Test registering provider plugins."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)

        # Create a mock plugin class
        mock_plugin_class = type(
            "MockProvider",
            (),
            {"name": "mock_provider", "description": "A mock provider"},
        )

        plugins = {"mock_provider": mock_plugin_class}
        count = loader._register_plugins("providers", plugins)

        assert count == 1
        mock_registry.register_provider.assert_called_once_with(
            "mock_provider", mock_plugin_class
        )

    def test_register_plugins_with_retrievers(self) -> None:
        """Test registering retriever plugins."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)

        # Create a mock plugin class
        mock_plugin_class = type(
            "MockRetriever",
            (),
            {"name": "mock_retriever", "description": "A mock retriever"},
        )

        plugins = {"mock_retriever": mock_plugin_class}
        count = loader._register_plugins("retrievers", plugins)

        assert count == 1
        mock_registry.register_retriever.assert_called_once_with(
            "mock_retriever", mock_plugin_class
        )

    def test_register_plugins_with_unknown_group(self) -> None:
        """Test registering plugins with an unknown group."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)
        
        mock_plugin_class = type(
            "MockPlugin",
            (),
            {"name": "mock_plugin", "description": "A mock plugin"},
        )
        
        plugins = {"mock_plugin": mock_plugin_class}
        
        # The method catches ValueError and logs an error, so no exception is raised
        count = loader._register_plugins("unknown_group", plugins)
        assert count == 0

    def test_get_loaded_plugins(self) -> None:
        """Test getting loaded plugins."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)
        
        # Manually set loaded plugins
        test_mock = MagicMock()
        loader._loaded_plugins = {"metrics": {"test": test_mock}}
        
        loaded = loader.get_loaded_plugins()
        assert "metrics" in loaded
        assert "test" in loaded["metrics"]
        assert loaded["metrics"]["test"] is test_mock

    def test_get_plugin_count(self) -> None:
        """Test getting plugin count."""
        mock_registry = MagicMock()
        loader = PluginLoader(mock_registry)

        # Manually set loaded plugins
        loader._loaded_plugins = {
            "metrics": {"a": MagicMock(), "b": MagicMock()},
            "providers": {"c": MagicMock()},
        }

        count = loader.get_plugin_count()
        assert count == 3
