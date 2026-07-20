"""Diagnosis-specific exceptions for OpenAgent Eval."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class DiagnosisError(OpenAgentEvalError):
    """Base exception for all diagnosis-related errors.

    All diagnosis exceptions inherit from this class for consistent
    error handling in the diagnosis module.
    """

    pass


class DiagnosisExecutionError(DiagnosisError):
    """Raised when diagnosis execution fails.

    This can occur when:
    - Input data is malformed or missing required fields
    - An internal analysis step raises an unexpected error
    - External dependencies (e.g., LLM) fail during analysis
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
        step: str | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            details: Optional dictionary with additional error context.
            step: The diagnosis step that failed (e.g., "blame_attribution").
        """
        error_details = details or {}
        if step is not None:
            error_details["step"] = step

        super().__init__(message, error_details)
        self.step = step


class BlameAttributionError(DiagnosisError):
    """Raised when blame attribution fails.

    This can occur when:
    - Metric scores are missing or invalid
    - All metrics return zero (cannot determine blame)
    - Input format does not match expected ComponentScores structure
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            details: Optional dictionary with additional error context.
        """
        super().__init__(message, details)
