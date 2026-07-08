"""Plugin management and lifecycle.

This module provides high-level plugin management operations,
including loading, unloading, and querying plugins.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from openagent_eval.plugins.loader import PluginLoader


class PluginManager:
    """Plugin manager for high-level plugin operations.

    This class provides a unified interface for managing plugins,
    including loading, querying, and lifecycle operations.
    """

    def __init__(self, registry: Any) -> None:
        """Initialize the plugin manager.

        Args:
            registry: The central registry for plugin management.
        """
        self.registry = registry
        self.loader = PluginLoader(registry)
        self._initialized = False

    def initialize(self) -> dict[str, int]:
        """Initialize the plugin system by loading all plugins.

        Returns:
            Dictionary mapping group names to number of plugins loaded.
        """
        if self._initialized:
            logger.warning("Plugin system already initialized")
            return {}

        load_counts = self.loader.load_all_plugins()
        self._initialized = True

        logger.info(f"Plugin system initialized with {sum(load_counts.values())} plugins")
        return load_counts

    def reload_plugins(self) -> dict[str, int]:
        """Reload all plugins.

        Returns:
            Dictionary mapping group names to number of plugins loaded.
        """
        logger.info("Reloading plugins...")
        self._initialized = False
        return self.initialize()

    def get_available_plugins(self) -> dict[str, list[str]]:
        """Get list of available plugins by group.

        Returns:
            Dictionary mapping group names to lists of plugin names.
        """
        return {
            "metrics": self.registry.list_metrics(),
            "providers": self.registry.list_providers(),
            "retrievers": self.registry.list_retrievers(),
            "dataset_loaders": self.registry.list_dataset_loaders(),
            "report_generators": self.registry.list_report_generators(),
        }

    def get_plugin_info(self, group_name: str, plugin_name: str) -> dict[str, Any]:
        """Get information about a specific plugin.

        Args:
            group_name: The plugin group name.
            plugin_name: The plugin name.

        Returns:
            Dictionary with plugin information.

        Raises:
            ValueError: If the plugin is not found.
        """
        try:
            if group_name == "metrics":
                plugin_class = self.registry.get_metric(plugin_name)
            elif group_name == "providers":
                plugin_class = self.registry.get_provider(plugin_name)
            elif group_name == "retrievers":
                plugin_class = self.registry.get_retriever(plugin_name)
            elif group_name == "dataset_loaders":
                plugin_class = self.registry.get_dataset_loader(plugin_name)
            elif group_name == "report_generators":
                plugin_class = self.registry.get_report_generator(plugin_name)
            else:
                raise ValueError(f"Unknown plugin group: {group_name}")

            return {
                "name": plugin_name,
                "group": group_name,
                "class": plugin_class,
                "module": plugin_class.__module__,
                "docstring": plugin_class.__doc__,
            }
        except Exception as e:
            logger.error(f"Failed to get plugin info: {e}")
            raise

    def is_initialized(self) -> bool:
        """Check if the plugin system is initialized.

        Returns:
            True if initialized, False otherwise.
        """
        return self._initialized

    def get_plugin_count(self) -> int:
        """Get total number of loaded plugins.

        Returns:
            Total number of loaded plugins.
        """
        return self.loader.get_plugin_count()
