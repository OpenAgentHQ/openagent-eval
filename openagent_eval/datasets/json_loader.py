"""JSON dataset loader.

This module implements the dataset loader for JSON format files.
The expected format is a JSON array of dataset entries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openagent_eval.datasets.base import BaseDatasetLoader, Dataset, DatasetItem
from openagent_eval.datasets.models import DatasetItemModel
from openagent_eval.exceptions import DatasetValidationError, InvalidDatasetError


class JSONDatasetLoader(BaseDatasetLoader):
    """Loader for JSON format datasets.

    Expects a JSON file containing an array of dataset entries:

    ```json
    [
        {
            "question": "What is Python?",
            "ground_truth": "Python is a programming language.",
            "context": "Python is a high-level programming language.",
            "metadata": {"id": 1}
        }
    ]
    ```

    Example:
        ```python
        from openagent_eval.datasets import JSONDatasetLoader
        from pathlib import Path

        loader = JSONDatasetLoader()
        dataset = loader.load(Path("data/questions.json"))
        ```
    """

    def load(self, path: Path) -> Dataset:
        """Load a dataset from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            Loaded Dataset object.

        Raises:
            DatasetNotFoundError: If the file does not exist.
            InvalidDatasetError: If the JSON is malformed.
            DatasetValidationError: If the data fails validation.
        """
        self._validate_path(path)

        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise InvalidDatasetError(
                message=f"Invalid JSON in file: {e}",
                dataset_path=str(path),
                frmt="json",
                line_number=e.lineno,
            ) from e

        # Support both a top-level array and the common {"items": [...]} wrapper.
        if (
            isinstance(raw_data, dict)
            and "items" in raw_data
            and isinstance(raw_data["items"], list)
        ):
            raw_data = raw_data["items"]

        return self._parse_data(raw_data, path)

    def validate(self, data: Any) -> bool:
        """Validate that the data conforms to the expected JSON schema.

        Args:
            data: The data to validate (should be a list of dicts).

        Returns:
            True if valid.

        Raises:
            DatasetValidationError: If validation fails.
        """
        if not isinstance(data, list):
            raise DatasetValidationError(
                message="Dataset must be a JSON array",
                validation_errors=["Expected array, got " + type(data).__name__],
            )

        errors: list[str] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f"Item {i}: Expected dict, got {type(item).__name__}")
                continue

            if "question" not in item:
                errors.append(f"Item {i}: Missing required field 'question'")
            elif not isinstance(item["question"], str) or not item["question"].strip():
                errors.append(f"Item {i}: 'question' must be a non-empty string")

        if errors:
            raise DatasetValidationError(
                message=f"Dataset validation failed with {len(errors)} error(s)",
                validation_errors=errors,
            )

        return True

    def _parse_data(self, raw_data: Any, path: Path) -> Dataset:
        """Parse raw JSON data into a Dataset object.

        Args:
            raw_data: The parsed JSON data.
            path: Path to the source file (for error reporting).

        Returns:
            Dataset object.

        Raises:
            InvalidDatasetError: If the data structure is invalid.
            DatasetValidationError: If validation fails.
        """
        # Validate the raw data
        self.validate(raw_data)

        # Parse each item through Pydantic validation
        items: list[DatasetItem] = []
        validation_errors: list[str] = []

        for i, raw_item in enumerate(raw_data):
            try:
                model = DatasetItemModel(**raw_item)
                items.append(
                    DatasetItem(
                        question=model.question,
                        ground_truth=model.ground_truth,
                        context=model.context,
                        metadata=model.metadata,
                        contexts=model.contexts,
                        ground_truth_contexts=model.ground_truth_contexts,
                    )
                )
            except Exception as e:
                validation_errors.append(f"Item {i}: {e}")

        if validation_errors:
            raise DatasetValidationError(
                message=f"Failed to parse {len(validation_errors)} item(s)",
                dataset_path=str(path),
                validation_errors=validation_errors,
            )

        if not items:
            raise DatasetValidationError(
                message="Dataset is empty (no valid items found)",
                dataset_path=str(path),
                validation_errors=["No valid items in file"],
            )

        return Dataset(
            items=items,
            name=path.stem,
            metadata={"source": str(path), "format": "json"},
        )
