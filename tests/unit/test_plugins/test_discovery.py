"""Unit tests for plugin discovery."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from openagent_eval.plugins.discovery import (
    ENTRY_POINT_GROUPS,
    discover_all_plugins,
    discover_plugins,
    get_plugin_info,
)


class TestDiscoverPlugins:
    """Tests for discover_plugins function."""

    def test_discover_plugins_with_valid_group(self) -> None:
        """Test discovering plugins with a valid group name."""
        # This test will discover any built-in plugins
        plugins = discover_plugins("metrics")
        assert isinstance(plugins, dict)

    def test_discover_plugins_with_unknown_group(self) -> None:
        """Test discovering plugins with an unknown group name."""
        plugins = discover_plugins("unknown_group")
        assert plugins == {}

    def test_discover_plugins_returns_dict(self) -> None:
        """Test that discover_plugins returns a dictionary."""
        plugins = discover_plugins("metrics")
        assert isinstance(plugins, dict)

    @patch("openagent_eval.plugins.discovery.importlib.metadata.entry_points")
    def test_discover_plugins_with_mock_entry_points(self, mock_entry_points: MagicMock) -> None:
        """Test plugin discovery with mocked entry points."""
        # Create a mock entry point
        mock_ep = MagicMock()
        mock_ep.name = "test_metric"
        mock_ep.value = "test_module:TestMetric"
        mock_ep.load.return_value = type(
            "TestMetric",
            (),
            {"name": "test_metric", "description": "A test metric"},
        )

        mock_entry_points.return_value = {"openagent_eval.metrics": [mock_ep]}

        plugins = discover_plugins("metrics")
        assert "test_metric" in plugins
        mock_ep.load.assert_called_once()

    @patch("openagent_eval.plugins.discovery.importlib.metadata.entry_points")
    def test_discover_plugins_with_invalid_plugin(self, mock_entry_points: MagicMock) -> None:
        """Test plugin discovery with an invalid plugin (missing attributes)."""
        # Create a mock entry point with missing attributes
        mock_ep = MagicMock()
        mock_ep.name = "invalid_metric"
        mock_ep.value = "test_module:InvalidMetric"
        mock_ep.load.return_value = type(
            "InvalidMetric",
            (),
            {"name": "invalid_metric"},  # Missing description
        )

        mock_entry_points.return_value = {"openagent_eval.metrics": [mock_ep]}

        plugins = discover_plugins("metrics")
        assert "invalid_metric" not in plugins

    @patch("openagent_eval.plugins.discovery.importlib.metadata.entry_points")
    def test_discover_plugins_with_load_error(self, mock_entry_points: MagicMock) -> None:
        """Test plugin discovery when plugin fails to load."""
        mock_ep = MagicMock()
        mock_ep.name = "broken_metric"
        mock_ep.value = "broken_module:BrokenMetric"
        mock_ep.load.side_effect = ImportError("Module not found")

        mock_entry_points.return_value = {"openagent_eval.metrics": [mock_ep]}

        plugins = discover_plugins("metrics")
        assert "broken_metric" not in plugins


class TestDiscoverAllPlugins:
    """Tests for discover_all_plugins function."""

    def test_discover_all_plugins(self) -> None:
        """Test discovering all plugins across all groups."""
        all_plugins = discover_all_plugins()
        assert isinstance(all_plugins, dict)

        # Check that all expected groups are present
        for group_name in ENTRY_POINT_GROUPS:
            assert group_name in all_plugins or all_plugins.get(group_name, {}) == {}

    def test_discover_all_plugins_returns_dict_of_dicts(self) -> None:
        """Test that discover_all_plugins returns a dictionary of dictionaries."""
        all_plugins = discover_all_plugins()
        for _group_name, plugins in all_plugins.items():
            assert isinstance(plugins, dict)


class TestGetPluginInfo:
    """Tests for get_plugin_info function."""

    def test_get_plugin_info(self) -> None:
        """Test getting plugin information."""
        plugin_info = get_plugin_info()
        assert isinstance(plugin_info, dict)

        # Check that all expected groups are present
        for group_name in ENTRY_POINT_GROUPS:
            assert group_name in plugin_info
            assert isinstance(plugin_info[group_name], list)
