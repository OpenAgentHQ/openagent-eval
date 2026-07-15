"""Metric-related exceptions."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class MetricError(OpenAgentEvalError):
    """Base exception for metric-related errors.

    Attributes:
        message: Human-readable error message.
        metric_name: Name of the metric that caused the error.
        details: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        metric_name: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            metric_name: Name of the metric.
            details: Additional context about the error.
        """
        error_details = details or {}
        if metric_name:
            error_details["metric_name"] = metric_name

        super().__init__(message=message, details=error_details)
        self.metric_name = metric_name


class MetricNotFoundError(MetricError):
    """Raised when a requested metric cannot be found."""

    def __init__(
        self,
        metric_name: str,
        available_metrics: list[str] | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            metric_name: Name of the metric that was not found.
            available_metrics: List of available metric names.
            details: Additional context about the error.
        """
        error_details = details or {}
        if available_metrics:
            error_details["available_metrics"] = available_metrics

        message = f"Metric not found: {metric_name}"
        if available_metrics:
            message += f". Available metrics: {', '.join(available_metrics)}"

        super().__init__(message=message, metric_name=metric_name, details=error_details)
        self.available_metrics = available_metrics or []


class MetricExecutionError(MetricError):
    """Raised when a metric fails during execution.

    Attributes:
        original_error: The original exception that caused the failure.
    """

    def __init__(
        self,
        message: str,
        metric_name: str | None = None,
        original_error: Exception | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            metric_name: Name of the metric that failed.
            original_error: The original exception that caused the failure.
            details: Additional context about the error.
        """
        error_details = details or {}
        if original_error:
            error_details["original_error"] = str(original_error)

        super().__init__(message=message, metric_name=metric_name, details=error_details)
        self.original_error = original_error


class MetricTimeoutError(MetricError):
    """Raised when a metric execution times out.

    Attributes:
        timeout_seconds: The timeout duration in seconds.
    """

    def __init__(
        self,
        message: str,
        metric_name: str | None = None,
        timeout_seconds: float | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            metric_name: Name of the metric that timed out.
            timeout_seconds: The timeout duration in seconds.
            details: Additional context about the error.
        """
        error_details = details or {}
        if timeout_seconds is not None:
            error_details["timeout_seconds"] = timeout_seconds

        super().__init__(message=message, metric_name=metric_name, details=error_details)
        self.timeout_seconds = timeout_seconds
