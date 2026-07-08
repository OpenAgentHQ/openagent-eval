"""Plugin system for OpenAgent Eval.

This module provides the plugin discovery, loading, and management
functionality for extending OpenAgent Eval with custom metrics,
providers, and other components.
"""

from openagent_eval.plugins.discovery import (
    discover_all_plugins,
    discover_plugins,
    get_plugin_info,
)
from openagent_eval.plugins.loader import PluginLoader
from openagent_eval.plugins.manager import PluginManager

__all__ = [
    "discover_all_plugins",
    "discover_plugins",
    "get_plugin_info",
    "PluginLoader",
    "PluginManager",
]
