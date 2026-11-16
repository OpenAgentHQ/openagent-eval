"""Plugin-related exceptions."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class PluginError(OpenAgentEvalError):
    """Base exception for plugin-related errors.

    Attributes:
        message: Human-readable error message.
        plugin_name: Name of the plugin that caused the error.
        details: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        plugin_name: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            plugin_name: Name of the plugin.
            details: Additional context about the error.
        """
        error_details = details or {}
        if plugin_name is not None:
            error_details["plugin_name"] = plugin_name

        super().__init__(message=message, details=error_details)
        self.plugin_name = plugin_name


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin cannot be found."""

    def __init__(
        self,
        plugin_name: str,
        available_plugins: list[str] | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            plugin_name: Name of the plugin that was not found.
            available_plugins: List of available plugin names.
            details: Additional context about the error.
        """
        error_details = details or {}
        if available_plugins is not None:
            error_details["available_plugins"] = available_plugins

        message = f"Plugin not found: {plugin_name}"
        if available_plugins:
            message += f". Available plugins: {', '.join(available_plugins)}"

        super().__init__(
            message=message, plugin_name=plugin_name, details=error_details
        )
        self.available_plugins = available_plugins or []


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load.

    Attributes:
        original_error: The original exception that caused the load failure.
    """

    def __init__(
        self,
        message: str,
        plugin_name: str | None = None,
        original_error: Exception | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            plugin_name: Name of the plugin that failed to load.
            original_error: The original exception that caused the failure.
            details: Additional context about the error.
        """
        error_details = details or {}
        if original_error is not None:
            error_details["original_error"] = str(original_error)

        super().__init__(
            message=message, plugin_name=plugin_name, details=error_details
        )
        self.original_error = original_error
