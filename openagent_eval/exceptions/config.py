"""Configuration-related exceptions."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class ConfigurationError(OpenAgentEvalError):
    """Raised when configuration is invalid or missing.

    Attributes:
        message: Human-readable error message.
        config_path: Path to the configuration file that caused the error.
        field: The specific configuration field that is invalid.
        details: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        config_path: str | None = None,
        field: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            config_path: Path to the configuration file.
            field: The specific configuration field that is invalid.
            details: Additional context about the error.
        """
        error_details = details or {}
        if config_path is not None:
            error_details["config_path"] = config_path
        if field is not None:
            error_details["field"] = field

        super().__init__(message=message, details=error_details)
        self.config_path = config_path
        self.field = field
