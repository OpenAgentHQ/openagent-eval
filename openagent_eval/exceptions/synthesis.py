"""Synthesis-related exceptions."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class SynthesisError(OpenAgentEvalError):
    """Base exception for synthesis-related errors.

    Attributes:
        message: Human-readable error message.
        details: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            details: Additional context about the error.
        """
        super().__init__(message=message, details=details)


class SynthesisExecutionError(SynthesisError):
    """Raised when synthesis fails during execution.

    Attributes:
        original_error: The original exception that caused the failure.
    """

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            original_error: The original exception that caused the failure.
            details: Additional context about the error.
        """
        error_details = details or {}
        if original_error is not None:
            error_details["original_error"] = str(original_error)

        super().__init__(message=message, details=error_details)
        self.original_error = original_error
