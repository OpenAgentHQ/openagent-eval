"""HuggingFace dataset loader.

This module implements the dataset loader for HuggingFace datasets.
Requires the `datasets` package to be installed.

Note: This loader is optional and requires the `datasets` extra:
    pip install openagent-eval[datasets]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openagent_eval.datasets.base import BaseDatasetLoader, Dataset, DatasetItem
from openagent_eval.datasets.models import DatasetItemModel
from openagent_eval.exceptions import DatasetValidationError, InvalidDatasetError


class HFDatasetLoader(BaseDatasetLoader):
    """Loader for HuggingFace datasets.

    This loader can load datasets from:
    - HuggingFace Hub (e.g., "squad", "natural_questions")
    - Local dataset directories

    Requires the `datasets` package:
        pip install openagent-eval[datasets]

    Example:
        ```python
        from openagent_eval.datasets import HFDatasetLoader

        loader = HFDatasetLoader()
        dataset = loader.load_from_hub("squad", split="train", limit=100)
        ```

    Note:
        The `load()` method is not used for HuggingFace datasets.
        Use `load_from_hub()` or `load_from_disk()` instead.
    """

    def load(self, path: Path) -> Dataset:
        """Load a dataset from a local HuggingFace dataset directory or hub.

        Args:
            path: Path to the local dataset directory, or a HuggingFace Hub
                dataset name (e.g. "squad"). When the path does not exist
                locally it is treated as a hub name and loaded via
                ``load_from_hub``.

        Returns:
            Loaded Dataset object.

        Raises:
            DatasetNotFoundError: If the local directory does not exist and the
                path is not a valid hub identifier.
            InvalidDatasetError: If the dataset format is invalid.
            DatasetValidationError: If the data fails validation.
        """
        # A path that exists locally is a dataset directory on disk.
        if path.exists():
            try:
                from datasets import load_from_disk
            except ImportError as e:
                raise InvalidDatasetError(
                    message=(
                        "The 'datasets' package is required for HuggingFace dataset loading. "
                        "Install it with: pip install openagent-eval[datasets]"
                    ),
                    dataset_path=str(path),
                    format="hf",
                ) from e

            try:
                hf_dataset = load_from_disk(str(path))
            except Exception as e:
                raise InvalidDatasetError(
                    message=f"Failed to load HuggingFace dataset: {e}",
                    dataset_path=str(path),
                    format="hf",
                ) from e

            return self._parse_hf_dataset(hf_dataset, path)

        # Otherwise treat the path as a HuggingFace Hub dataset name.
        return self.load_from_hub(str(path))

    def validate(self, data: Any) -> bool:
        """Validate that the data conforms to the expected schema.

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

    def load_from_hub(
        self,
        dataset_name: str,
        split: str = "train",
        limit: int | None = None,
        **kwargs: Any,
    ) -> Dataset:
        """Load a dataset from the HuggingFace Hub.

        Args:
            dataset_name: Name of the dataset on HuggingFace Hub.
            split: Dataset split to load (default: "train").
            limit: Maximum number of items to load.
            **kwargs: Additional arguments to pass to `datasets.load_dataset`.

        Returns:
            Loaded Dataset object.

        Raises:
            InvalidDatasetError: If the dataset cannot be loaded.
            DatasetValidationError: If the data fails validation.
        """
        try:
            from datasets import load_dataset
        except ImportError as e:
            raise InvalidDatasetError(
                message=(
                    "The 'datasets' package is required for HuggingFace dataset loading. "
                    "Install it with: pip install openagent-eval[datasets]"
                ),
                format="hf",
            ) from e

        try:
            hf_dataset = load_dataset(dataset_name, split=split, **kwargs)
        except Exception as e:
            raise InvalidDatasetError(
                message=f"Failed to load dataset '{dataset_name}': {e}",
                format="hf",
            ) from e

        # Convert to list and apply limit
        data = [dict(item) for item in hf_dataset]
        if limit is not None:
            data = data[:limit]

        return self._parse_data(data, dataset_name)

    def _parse_hf_dataset(self, hf_dataset: Any, path: Path) -> Dataset:
        """Parse a HuggingFace dataset object into our Dataset model.

        Args:
            hf_dataset: The HuggingFace dataset object.
            path: Path or name of the dataset.

        Returns:
            Dataset object.
        """
        data = [dict(item) for item in hf_dataset]
        return self._parse_data(data, str(path))

    def _parse_data(self, data: list[dict[str, Any]], source: str) -> Dataset:
        """Parse a list of dictionaries into a Dataset object.

        Args:
            data: List of raw data dictionaries.
            source: Source identifier (path or dataset name).

        Returns:
            Dataset object.

        Raises:
            DatasetValidationError: If parsing fails.
        """
        # Validate the raw data
        self.validate(data)

        items: list[DatasetItem] = []
        validation_errors: list[str] = []

        for i, raw_item in enumerate(data):
            try:
                # Map common HuggingFace field names to our schema
                mapped = self._map_fields(raw_item)
                model = DatasetItemModel(**mapped)
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
                validation_errors=validation_errors,
            )

        return Dataset(
            items=items,
            name=source,
            metadata={"source": source, "format": "hf"},
        )

    def _map_fields(self, raw_item: dict[str, Any]) -> dict[str, Any]:
        """Map common HuggingFace field names to our schema.

        This handles common variations in field naming across different
        HuggingFace datasets.

        Args:
            raw_item: Raw item from HuggingFace dataset.

        Returns:
            Mapped item with standardized field names.
        """
        mapped: dict[str, Any] = {}

        # Question field mappings
        question_fields = ["question", "query", "input", "prompt"]
        for field in question_fields:
            if field in raw_item and raw_item[field]:
                mapped["question"] = str(raw_item[field])
                break

        # Ground truth field mappings
        ground_truth_fields = ["answer", "answers", "ground_truth", "target", "output", "response"]
        for field in ground_truth_fields:
            if field in raw_item and raw_item[field]:
                value = raw_item[field]
                # Handle list of answers (common in QA datasets)
                if isinstance(value, list):
                    if value:
                        first = value[0]
                        if isinstance(first, dict) and "text" in first:
                            mapped["ground_truth"] = first["text"]
                        elif isinstance(first, str):
                            mapped["ground_truth"] = first
                elif isinstance(value, str):
                    mapped["ground_truth"] = value
                break

        # Context field mappings
        context_fields = ["context", "passage", "document", "paragraph", "text"]
        for field in context_fields:
            if field in raw_item and raw_item[field]:
                mapped["context"] = str(raw_item[field])
                break

        # Metadata - include all other fields
        metadata_fields = set(mapped.keys()) | {"question", "ground_truth", "context"}
        metadata = {k: v for k, v in raw_item.items() if k not in metadata_fields}
        if metadata:
            mapped["metadata"] = metadata

        return mapped
