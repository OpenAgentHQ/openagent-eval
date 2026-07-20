"""CSV dataset loader.

This module implements the dataset loader for CSV format files.
The CSV should have a header row with column names.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from openagent_eval.datasets.base import BaseDatasetLoader, Dataset, DatasetItem
from openagent_eval.datasets.models import DatasetItemModel
from openagent_eval.exceptions import DatasetValidationError, InvalidDatasetError


class CSVDatasetLoader(BaseDatasetLoader):
    """Loader for CSV format datasets.

    Expects a CSV file with a header row. Required column: `question`.
    Optional columns: `ground_truth`, `context`, `metadata`.

    Example CSV:
    ```csv
    question,ground_truth,context
    "What is Python?","Python is a programming language.","Python is a high-level language."
    "What is RAG?","Retrieval-Augmented Generation.","RAG combines retrieval and generation."
    ```

    Example:
        ```python
        from openagent_eval.datasets import CSVDatasetLoader
        from pathlib import Path

        loader = CSVDatasetLoader()
        dataset = loader.load(Path("data/questions.csv"))
        ```
    """

    REQUIRED_COLUMNS = {"question"}
    OPTIONAL_COLUMNS = {"ground_truth", "context", "metadata"}

    def load(self, path: Path) -> Dataset:
        """Load a dataset from a CSV file.

        Args:
            path: Path to the CSV file.

        Returns:
            Loaded Dataset object.

        Raises:
            DatasetNotFoundError: If the file does not exist.
            InvalidDatasetError: If the CSV is malformed.
            DatasetValidationError: If the data fails validation.
        """
        self._validate_path(path)

        try:
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except csv.Error as e:
            raise InvalidDatasetError(
                message=f"Invalid CSV format: {e}",
                dataset_path=str(path),
                data_format="csv",
            ) from e

        return self._parse_rows(rows, path)

    def validate(self, data: Any) -> bool:
        """Validate that the data conforms to the expected CSV schema.

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

        if not data:
            raise DatasetValidationError(
                message="Dataset is empty",
                validation_errors=["No rows found in CSV"],
            )

        errors: list[str] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f"Row {i + 1}: Expected dict, got {type(item).__name__}")
                continue

            if "question" not in item:
                errors.append(f"Row {i + 1}: Missing required column 'question'")
            elif not isinstance(item["question"], str) or not item["question"].strip():
                errors.append(f"Row {i + 1}: 'question' must be a non-empty string")

        if errors:
            raise DatasetValidationError(
                message=f"Dataset validation failed with {len(errors)} error(s)",
                validation_errors=errors,
            )

        return True

    def _parse_rows(self, rows: list[dict[str, str]], path: Path) -> Dataset:
        """Parse CSV rows into a Dataset object.

        Args:
            rows: List of row dictionaries from the CSV reader.
            path: Path to the source file (for error reporting).

        Returns:
            Dataset object.

        Raises:
            DatasetValidationError: If parsing or validation fails.
        """
        # Validate the raw data
        self.validate(rows)

        items: list[DatasetItem] = []
        validation_errors: list[str] = []

        for i, row in enumerate(rows):
            try:
                # Build item data from CSV columns
                item_data: dict[str, Any] = {"question": row.get("question", "").strip()}

                # Add optional fields if present
                if "ground_truth" in row and row["ground_truth"]:
                    item_data["ground_truth"] = row["ground_truth"].strip()
                if "context" in row and row["context"]:
                    item_data["context"] = row["context"].strip()
                if "metadata" in row and row["metadata"]:
                    # Try to parse metadata as JSON. A valid JSON value that is
                    # not an object (e.g. a number, array, or bool) must be kept
                    # rather than crashing the whole row.
                    import json

                    try:
                        parsed = json.loads(row["metadata"])
                        item_data["metadata"] = (
                            parsed if isinstance(parsed, dict) else {"raw": row["metadata"]}
                        )
                    except (json.JSONDecodeError, TypeError):
                        item_data["metadata"] = {"raw": row["metadata"]}

                model = DatasetItemModel(**item_data)
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
                validation_errors.append(f"Row {i + 1}: {e}")

        if validation_errors:
            raise DatasetValidationError(
                message=f"Failed to parse {len(validation_errors)} row(s)",
                dataset_path=str(path),
                validation_errors=validation_errors,
            )

        return Dataset(
            items=items,
            name=path.stem,
            metadata={"source": str(path), "format": "csv"},
        )
