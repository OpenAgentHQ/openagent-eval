"""Base dataset loader interface and core data models.

This module defines the abstract interface that all dataset loaders must implement,
along with the core Dataset and DatasetItem data models used throughout the framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DatasetItem:
    """A single item in an evaluation dataset.

    Attributes:
        question: The question to evaluate.
        ground_truth: The expected correct answer (optional).
        context: The context provided to the RAG system (optional).
        metadata: Additional metadata about this item.
        contexts: List of retrieved contexts (populated after retrieval).
    """

    question: str
    ground_truth: str | None = None
    context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    contexts: list[str] = field(default_factory=list)
    ground_truth_contexts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format.

        Returns:
            Dictionary representation of the dataset item.
        """
        result: dict[str, Any] = {"question": self.question}
        if self.ground_truth is not None:
            result["ground_truth"] = self.ground_truth
        if self.context is not None:
            result["context"] = self.context
        if self.contexts:
            result["contexts"] = self.contexts
        if self.ground_truth_contexts:
            result["ground_truth_contexts"] = self.ground_truth_contexts
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class Dataset:
    """A collection of dataset items for evaluation.

    Attributes:
        items: List of dataset items.
        name: Optional name for the dataset.
        metadata: Dataset-level metadata.
    """

    items: list[DatasetItem] = field(default_factory=list)
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Return the number of items in the dataset."""
        return len(self.items)

    @property
    def has_ground_truth(self) -> bool:
        """Check if all items have ground truth answers."""
        return len(self.items) > 0 and all(
            item.ground_truth is not None for item in self.items
        )

    @property
    def questions(self) -> list[str]:
        """Return all questions in the dataset."""
        return [item.question for item in self.items]

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, index: int) -> DatasetItem:
        return self.items[index]

    def filter(
        self,
        predicate: Any | None = None,
    ) -> Dataset:
        """Filter dataset items based on a predicate.

        Args:
            predicate: Function that takes a DatasetItem and returns bool.

        Returns:
            New Dataset with filtered items.
        """
        if predicate is None:
            return Dataset(items=list(self.items), name=self.name, metadata=self.metadata)
        filtered = [item for item in self.items if predicate(item)]
        return Dataset(
            items=filtered,
            name=self.name,
            metadata=self.metadata,
        )

    def to_dicts(self) -> list[dict[str, Any]]:
        """Convert all items to dictionary format.

        Returns:
            List of dictionary representations.
        """
        return [item.to_dict() for item in self.items]


class BaseDatasetLoader(ABC):
    """Abstract base class for dataset loaders.

    All dataset loaders must implement this interface. The loader is responsible
    for reading data from a specific format and returning a Dataset object.

    Example:
        ```python
        class MyLoader(BaseDatasetLoader):
            def load(self, path: Path) -> Dataset:
                # Implement loading logic
                ...

            def validate(self, data: Any) -> bool:
                # Implement validation logic
                ...
        ```
    """

    @abstractmethod
    def load(self, path: Path) -> Dataset:
        """Load a dataset from the specified path.

        Args:
            path: Path to the dataset file.

        Returns:
            Loaded Dataset object.

        Raises:
            DatasetNotFoundError: If the file does not exist.
            InvalidDatasetError: If the file format is invalid.
            DatasetValidationError: If the data fails validation.
        """
        ...

    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate that the data conforms to the expected schema.

        Args:
            data: The data to validate.

        Returns:
            True if valid, False otherwise.

        Raises:
            DatasetValidationError: If validation fails with details.
        """
        ...

    def _validate_path(self, path: Path) -> None:
        """Validate that the path exists and is a file.

        Args:
            path: Path to validate.

        Raises:
            DatasetNotFoundError: If the path does not exist
            with a helpful message showing the current working directory.
        """
        import os

        if not path.exists():
            from openagent_eval.exceptions import DatasetNotFoundError

            cwd = os.getcwd()
            raise DatasetNotFoundError(
                dataset_path=str(path),
                details={
                    "tip": (
                        f"Dataset file not found at '{path}'. "
                        f"Checked in: {cwd}. "
                        f"Use an absolute path or verify the path "
                        f"exists relative to your current directory."
                    ),
                },
            )

        if not path.is_file():
            from openagent_eval.exceptions import InvalidDatasetError

            raise InvalidDatasetError(
                message=f"Path is not a file: {path}",
                dataset_path=str(path),
            )
