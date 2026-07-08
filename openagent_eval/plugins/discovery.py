"""Plugin discovery via Python entry points.

This module handles the discovery of plugins using Python's entry point mechanism.
It discovers plugins for metrics, providers, retrievers, dataset loaders, and
report generators.
"""

from __future__ import annotations

import importlib.metadata
from typing import Any

from loguru import logger

# Entry point group names for each plugin type
ENTRY_POINT_GROUPS = {
    "metrics": "openagent_eval.metrics",
    "providers": "openagent_eval.providers",
    "retrievers": "openagent_eval.retrievers",
    "dataset_loaders": "openagent_eval.dataset_loaders",
    "report_generators": "openagent_eval.report_generators",
}


def discover_plugins(group_name: str) -> dict[str, type[Any]]:
    """Discover plugins for a specific entry point group.

    Args:
        group_name: The entry point group name (e.g., "metrics", "providers").

    Returns:
        Dictionary mapping plugin names to their classes.
    """
    entry_point_group = ENTRY_POINT_GROUPS.get(group_name)
    if not entry_point_group:
        logger.warning(f"Unknown plugin group: {group_name}")
        return {}

    plugins: dict[str, type[Any]] = {}

    try:
        # Get all entry points for the group
        eps = importlib.metadata.entry_points()

        # Handle different Python versions
        if hasattr(eps, "select"):
            # Python 3.12+
            group_eps = eps.select(group=entry_point_group)
        else:
            # Python 3.11
            group_eps = eps.get(entry_point_group, [])

        for ep in group_eps:
            try:
                # Load the entry point to get the class
                plugin_class = ep.load()
                plugin_name = ep.name

                # Validate that the class has required attributes
                if hasattr(plugin_class, "name") and hasattr(plugin_class, "description"):
                    plugins[plugin_name] = plugin_class
                    logger.debug(f"Discovered plugin: {plugin_name} ({ep.value})")
                else:
                    logger.warning(
                        f"Plugin {plugin_name} missing required attributes "
                        f"(name, description): {ep.value}"
                    )
            except Exception as e:
                logger.error(f"Failed to load plugin {ep.name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to discover plugins for group {group_name}: {e}")

    return plugins


def discover_all_plugins() -> dict[str, dict[str, type[Any]]]:
    """Discover all plugins across all groups.

    Returns:
        Dictionary mapping group names to their discovered plugins.
    """
    all_plugins: dict[str, dict[str, type[Any]]] = {}

    for group_name in ENTRY_POINT_GROUPS:
        plugins = discover_plugins(group_name)
        if plugins:
            all_plugins[group_name] = plugins
            logger.info(f"Discovered {len(plugins)} {group_name} plugins")

    return all_plugins


def get_plugin_info() -> dict[str, list[str]]:
    """Get information about available plugins.

    Returns:
        Dictionary mapping group names to lists of plugin names.
    """
    plugin_info: dict[str, list[str]] = {}

    for group_name in ENTRY_POINT_GROUPS:
        plugins = discover_plugins(group_name)
        plugin_info[group_name] = list(plugins.keys())

    return plugin_info
