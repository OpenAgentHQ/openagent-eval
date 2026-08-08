"""CLI-related exceptions."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class CLIError(OpenAgentEvalError):
    """Base exception for CLI-related errors.

    Attributes:
        message: Human-readable error message.
        command: The CLI command that caused the error.
        details: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        command: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            command: The CLI command that caused the error.
            details: Additional context about the error.
        """
        error_details = details or {}
        if command:
            error_details["command"] = command

        super().__init__(message=message, details=error_details)
        self.command = command


class CommandError(CLIError):
    """Raised when a CLI command fails to execute.

    Attributes:
        exit_code: The exit code to return.
    """

    def __init__(
        self,
        message: str,
        command: str | None = None,
        exit_code: int = 1,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            command: The CLI command that failed.
            exit_code: The exit code to return.
            details: Additional context about the error.
        """
        super().__init__(message=message, command=command, details=details)
        self.exit_code = exit_code


class ValidationError(CLIError):
    """Raised when CLI input validation fails.

    Attributes:
        field: The field that failed validation.
        value: The invalid value.
    """

    def __init__(
        self,
        message: str,
        command: str | None = None,
        field: str | None = None,
        value: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            command: The CLI command where validation failed.
            field: The field that failed validation.
            value: The invalid value.
            details: Additional context about the error.
        """
        error_details = details or {}
        if field is not None:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = value

        super().__init__(message=message, command=command, details=error_details)
        self.field = field
        self.value = value
