"""Provider-related exceptions."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class ProviderError(OpenAgentEvalError):
    """Base exception for provider-related errors.

    Attributes:
        message: Human-readable error message.
        provider_name: Name of the provider that caused the error.
        details: Additional context about the error.
        error_type: Human-readable error type label for standardized formatting.
    """

    error_type: str = "Provider Error"

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            provider_name: Name of the provider.
            details: Additional context about the error.
        """
        error_details = details or {}
        if provider_name:
            error_details["provider_name"] = provider_name

        super().__init__(message=message, details=error_details)
        self.provider_name = provider_name

    def __str__(self) -> str:
        """Return standardized string: [provider] error_type: message (details)."""
        provider_prefix = f"[{self.provider_name}] " if self.provider_name else ""
        base = f"{provider_prefix}{self.error_type}: {self.message}"
        if self.details:
            details_items = {k: v for k, v in self.details.items() if k != "provider_name"}
            if details_items:
                details_str = ", ".join(f"{k}={v}" for k, v in details_items.items())
                return f"{base} ({details_str})"
        return base


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider cannot be found."""

    error_type: str = "Provider Not Found"

    def __init__(
        self,
        provider_name: str,
        available_providers: list[str] | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            provider_name: Name of the provider that was not found.
            available_providers: List of available provider names.
            details: Additional context about the error.
        """
        error_details = details or {}
        if available_providers:
            error_details["available_providers"] = available_providers

        message = f"Provider not found: {provider_name}"
        if available_providers:
            message += f". Available providers: {', '.join(available_providers)}"

        super().__init__(message=message, provider_name=provider_name, details=error_details)
        self.available_providers = available_providers or []


class ProviderConnectionError(ProviderError):
    """Raised when a provider connection fails.

    Attributes:
        original_error: The original exception that caused the connection failure.
    """

    error_type: str = "Connection Error"

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        original_error: Exception | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            provider_name: Name of the provider that failed to connect.
            original_error: The original exception that caused the failure.
            details: Additional context about the error.
        """
        error_details = details or {}
        if original_error:
            error_details["original_error"] = str(original_error)

        super().__init__(message=message, provider_name=provider_name, details=error_details)
        self.original_error = original_error


class ProviderExecutionError(ProviderError):
    """Raised when a provider fails during execution.

    Attributes:
        original_error: The original exception that caused the failure.
    """

    error_type: str = "Execution Error"

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        original_error: Exception | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            provider_name: Name of the provider that failed.
            original_error: The original exception that caused the failure.
            details: Additional context about the error.
        """
        error_details = details or {}
        if original_error:
            error_details["original_error"] = str(original_error)

        super().__init__(message=message, provider_name=provider_name, details=error_details)
        self.original_error = original_error
