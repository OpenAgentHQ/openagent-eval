"""JSONL dataset loader.

This module implements the dataset loader for JSONL (JSON Lines) format files.
Each line in the file should be a valid JSON object representing one dataset entry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openagent_eval.datasets.base import BaseDatasetLoader, Dataset, DatasetItem
from openagent_eval.datasets.models import DatasetItemModel
from openagent_eval.exceptions import DatasetValidationError, InvalidDatasetError


class JSONLDatasetLoader(BaseDatasetLoader):
    """Loader for JSONL (JSON Lines) format datasets.

    Expects a file where each line is a valid JSON object:

    ```
    {"question": "What is Python?", "ground_truth": "A programming language."}
    {"question": "What is RAG?", "ground_truth": "Retrieval-Augmented Generation."}
    ```

    Example:
        ```python
        from openagent_eval.datasets import JSONLDatasetLoader
        from pathlib import Path

        loader = JSONLDatasetLoader()
        dataset = loader.load(Path("data/questions.jsonl"))
        ```
    """

    def load(self, path: Path) -> Dataset:
        """Load a dataset from a JSONL file.

        Args:
            path: Path to the JSONL file.

        Returns:
            Loaded Dataset object.

        Raises:
            DatasetNotFoundError: If the file does not exist.
            InvalidDatasetError: If a line contains invalid JSON.
            DatasetValidationError: If the data fails validation.
        """
        self._validate_path(path)

        lines = path.read_text(encoding="utf-8").splitlines()
        return self._parse_lines(lines, path)

    def validate(self, data: Any) -> bool:
        """Validate that the data conforms to the expected JSONL schema.

        Args:
            data: The data to validate (should be a list of dicts).

        Returns:
            True if valid.

        Raises:
            DatasetValidationError: If validation fails.
        """
        if not isinstance(data, list):
            raise DatasetValidationError(
                message="Dataset must be a list of entries",
                validation_errors=["Expected list, got " + type(data).__name__],
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

    def _parse_lines(self, lines: list[str], path: Path) -> Dataset:
        """Parse JSONL lines into a Dataset object.

        Args:
            lines: List of lines from the JSONL file.
            path: Path to the source file (for error reporting).

        Returns:
            Dataset object.

        Raises:
            InvalidDatasetError: If a line contains invalid JSON.
            DatasetValidationError: If validation fails.
        """
        import json

        items: list[DatasetItem] = []
        validation_errors: list[str] = []

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                raw_item = json.loads(line)
            except json.JSONDecodeError as e:
                raise InvalidDatasetError(
                    message=f"Invalid JSON on line {line_num}: {e}",
                    dataset_path=str(path),
                    format="jsonl",
                    line_number=line_num,
                ) from e

            if not isinstance(raw_item, dict):
                validation_errors.append(
                    f"Line {line_num}: Expected dict, got {type(raw_item).__name__}"
                )
                continue

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
                validation_errors.append(f"Line {line_num}: {e}")

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
            metadata={"source": str(path), "format": "jsonl"},
        )
