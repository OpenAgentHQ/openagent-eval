"""Corpus audit exceptions."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class CorpusError(OpenAgentEvalError):
    """Base exception for corpus-related errors.

    Attributes:
        message: Human-readable error message.
        corpus_path: Path to the corpus that caused the error.
        details: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        corpus_path: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            corpus_path: Path to the corpus.
            details: Additional context about the error.
        """
        error_details = details or {}
        if corpus_path is not None:
            error_details["corpus_path"] = corpus_path

        super().__init__(message=message, details=error_details)
        self.corpus_path = corpus_path


class CorpusNotFoundError(CorpusError):
    """Raised when the specified corpus path does not exist."""

    def __init__(
        self,
        corpus_path: str,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            corpus_path: Path to the corpus that was not found.
            details: Additional context about the error.
        """
        message = f"Corpus not found: {corpus_path}"
        super().__init__(message=message, corpus_path=corpus_path, details=details)


class CorpusValidationError(CorpusError):
    """Raised when the corpus fails validation."""

    def __init__(
        self,
        message: str,
        corpus_path: str | None = None,
        validation_errors: list[str] | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            corpus_path: Path to the corpus.
            validation_errors: List of specific validation errors.
            details: Additional context about the error.
        """
        error_details = details or {}
        if validation_errors is not None:
            error_details["validation_errors"] = validation_errors

        super().__init__(message=message, corpus_path=corpus_path, details=error_details)
        self.validation_errors = validation_errors or []


class CorpusAuditError(CorpusError):
    """Raised when the corpus audit process fails."""

    def __init__(
        self,
        message: str,
        corpus_path: str | None = None,
        analyzer_name: str | None = None,
        original_error: Exception | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            corpus_path: Path to the corpus.
            analyzer_name: Name of the analyzer that failed.
            original_error: The original exception that caused the failure.
            details: Additional context about the error.
        """
        error_details = details or {}
        if analyzer_name is not None:
            error_details["analyzer_name"] = analyzer_name
        if original_error is not None:
            error_details["original_error"] = str(original_error)

        super().__init__(message=message, corpus_path=corpus_path, details=error_details)
        self.analyzer_name = analyzer_name
        self.original_error = original_error
