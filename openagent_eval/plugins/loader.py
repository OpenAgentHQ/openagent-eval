"""Plugin loading and registration.

This module handles the loading and registration of discovered plugins
into the central registry.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from openagent_eval.plugins.discovery import discover_all_plugins, discover_plugins


class PluginLoader:
    """Plugin loader that discovers and registers plugins.

    This class manages the loading of plugins from entry points
    and their registration into the central registry.
    """

    def __init__(self, registry: Any) -> None:
        """Initialize the plugin loader.

        Args:
            registry: The central registry to register plugins into.
        """
        self.registry = registry
        self._loaded_plugins: dict[str, dict[str, type[Any]]] = {}

    def load_all_plugins(self) -> dict[str, int]:
        """Load all available plugins.

        Returns:
            Dictionary mapping group names to number of plugins loaded.
        """
        all_plugins = discover_all_plugins()
        load_counts: dict[str, int] = {}

        for group_name, plugins in all_plugins.items():
            count = self._register_plugins(group_name, plugins)
            load_counts[group_name] = count
            self._loaded_plugins[group_name] = plugins

        total = sum(load_counts.values())
        logger.info(f"Loaded {total} plugins across {len(load_counts)} groups")

        return load_counts

    def load_plugins_by_group(self, group_name: str) -> int:
        """Load plugins for a specific group.

        Args:
            group_name: The plugin group to load (e.g., "metrics").

        Returns:
            Number of plugins loaded.
        """
        plugins = discover_plugins(group_name)
        count = self._register_plugins(group_name, plugins)
        self._loaded_plugins[group_name] = plugins

        logger.info(f"Loaded {count} {group_name} plugins")
        return count

    def _register_plugins(
        self, group_name: str, plugins: dict[str, type[Any]]
    ) -> int:
        """Register plugins into the appropriate registry method.

        Args:
            group_name: The plugin group name.
            plugins: Dictionary mapping plugin names to classes.

        Returns:
            Number of plugins successfully registered.
        """
        registered = 0

        for plugin_name, plugin_class in plugins.items():
            try:
                self._register_plugin(group_name, plugin_name, plugin_class)
                registered += 1
            except Exception as e:
                logger.error(f"Failed to register plugin {plugin_name}: {e}")

        return registered

    def _register_plugin(
        self, group_name: str, plugin_name: str, plugin_class: type[Any]
    ) -> None:
        """Register a single plugin.

        Args:
            group_name: The plugin group name.
            plugin_name: The plugin name.
            plugin_class: The plugin class to register.

        Raises:
            ValueError: If the group name is unknown.
        """
        if group_name == "metrics":
            self.registry.register_metric(plugin_name, plugin_class)
        elif group_name == "providers":
            self.registry.register_provider(plugin_name, plugin_class)
        elif group_name == "retrievers":
            self.registry.register_retriever(plugin_name, plugin_class)
        elif group_name == "dataset_loaders":
            self.registry.register_dataset_loader(plugin_name, plugin_class)
        elif group_name == "report_generators":
            self.registry.register_report_generator(plugin_name, plugin_class)
        else:
            raise ValueError(f"Unknown plugin group: {group_name}")

    def get_loaded_plugins(self) -> dict[str, dict[str, type[Any]]]:
        """Get all loaded plugins.

        Returns:
            Dictionary mapping group names to their loaded plugins.
        """
        return self._loaded_plugins.copy()

    def get_plugin_count(self) -> int:
        """Get total number of loaded plugins.

        Returns:
            Total number of loaded plugins.
        """
        return sum(len(plugins) for plugins in self._loaded_plugins.values())
