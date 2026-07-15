"""Dataset-related exceptions."""

from __future__ import annotations

from openagent_eval.exceptions.base import OpenAgentEvalError


class DatasetError(OpenAgentEvalError):
    """Base exception for dataset-related errors.

    Attributes:
        message: Human-readable error message.
        dataset_path: Path to the dataset that caused the error.
        details: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        dataset_path: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            dataset_path: Path to the dataset file.
            details: Additional context about the error.
        """
        error_details = details or {}
        if dataset_path:
            error_details["dataset_path"] = dataset_path

        super().__init__(message=message, details=error_details)
        self.dataset_path = dataset_path


class DatasetNotFoundError(DatasetError):
    """Raised when a dataset file cannot be found."""

    def __init__(
        self,
        dataset_path: str,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            dataset_path: Path to the dataset that was not found.
            details: Additional context about the error.
        """
        message = f"Dataset not found: {dataset_path}"
        super().__init__(message=message, dataset_path=dataset_path, details=details)


class InvalidDatasetError(DatasetError):
    """Raised when a dataset has invalid format or structure.

    Attributes:
        format: The detected or expected format of the dataset.
        line_number: The line number where the error occurred (if applicable).
    """

    def __init__(
        self,
        message: str,
        dataset_path: str | None = None,
        frmt: str | None = None,
        line_number: int | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            dataset_path: Path to the invalid dataset.
            format: The detected or expected format.
            line_number: The line number where the error occurred.
            details: Additional context about the error.
        """
        error_details = details or {}
        if frmt:
            error_details["format"] = frmt
        if line_number:
            error_details["line_number"] = line_number

        super().__init__(message=message, dataset_path=dataset_path, details=error_details)
        self.format = frmt
        self.line_number = line_number


class DatasetValidationError(DatasetError):
    """Raised when a dataset fails validation against the expected schema.

    Attributes:
        validation_errors: List of specific validation error messages.
    """

    def __init__(
        self,
        message: str,
        dataset_path: str | None = None,
        validation_errors: list[str] | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            dataset_path: Path to the invalid dataset.
            validation_errors: List of specific validation error messages.
            details: Additional context about the error.
        """
        error_details = details or {}
        if validation_errors:
            error_details["validation_errors"] = validation_errors

        super().__init__(message=message, dataset_path=dataset_path, details=error_details)
        self.validation_errors = validation_errors or []
