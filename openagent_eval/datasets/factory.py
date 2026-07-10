"""Factory function for loading datasets based on configuration.

Auto-detects format from file extension if not specified in config.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openagent_eval.config.models import DatasetConfig
from openagent_eval.datasets.base import BaseDatasetLoader
from openagent_eval.datasets.csv_loader import CSVDatasetLoader
from openagent_eval.datasets.json_loader import JSONDatasetLoader
from openagent_eval.datasets.jsonl_loader import JSONLDatasetLoader
from openagent_eval.datasets.pdf_loader import PDFDatasetLoader
from openagent_eval.exceptions.dataset import InvalidDatasetError

# Map of file extensions to loader classes
_LOADER_MAP: dict[str, type[BaseDatasetLoader]] = {
    ".json": JSONDatasetLoader,
    ".jsonl": JSONLDatasetLoader,
    ".csv": CSVDatasetLoader,
    ".pdf": PDFDatasetLoader,
}

# Map of format strings to loader classes
_FORMAT_MAP: dict[str, type[BaseDatasetLoader]] = {
    "json": JSONDatasetLoader,
    "jsonl": JSONLDatasetLoader,
    "csv": CSVDatasetLoader,
    "pdf": PDFDatasetLoader,
}


def _get_loader(config: DatasetConfig) -> BaseDatasetLoader:
    """Get the appropriate loader based on config.

    Format is determined by (in priority order):
    1. Explicit format string in config
    2. File extension

    Args:
        config: Dataset configuration.

    Returns:
        Instantiated DatasetLoader.

    Raises:
        InvalidDatasetError: If format cannot be determined or is unsupported.
    """
    # Try explicit format first
    if config.format is not None:
        format_key = config.format.lower().strip()
        if format_key in _FORMAT_MAP:
            return _FORMAT_MAP[format_key]()
        raise InvalidDatasetError(
            message=f"Unsupported dataset format: '{config.format}'. "
            f"Supported formats: {list(_FORMAT_MAP.keys())}",
            format=config.format,
        )

    # Guard against directory paths, which have no usable extension and
    # would otherwise surface a misleading "set the format field" error.
    path = Path(config.path)
    if path.is_dir():
        raise InvalidDatasetError(
            message=f"Dataset path '{config.path}' is a directory, not a file. "
            f"Point 'path' to a dataset file (e.g. data/sample_questions.json) "
            f"or set the 'format' field explicitly in your config.",
            dataset_path=config.path,
        )

    # Fall back to file extension
    ext = path.suffix.lower()
    if ext in _LOADER_MAP:
        return _LOADER_MAP[ext]()

    raise InvalidDatasetError(
        message=f"Cannot determine dataset format from extension '{ext}'. "
        f"Supported extensions: {list(_LOADER_MAP.keys())}. "
        f"Set the 'format' field explicitly in your config.",
        dataset_path=config.path,
    )


def load_dataset(config: DatasetConfig) -> list[dict[str, Any]]:
    """Load dataset based on configuration.

    Auto-detects format from file extension if not specified.

    Args:
        config: Dataset configuration with path and optional format/limit/shuffle.

    Returns:
        List of dataset items as dictionaries.

    Raises:
        DatasetNotFoundError: If the file does not exist.
        InvalidDatasetError: If format is unsupported or file is malformed.
        DatasetValidationError: If items fail schema validation.

    Example:
        >>> from openagent_eval.config.models import DatasetConfig
        >>> config = DatasetConfig(path="data/questions.json", limit=100)
        >>> items = load_dataset(config)
        >>> print(len(items))
        100
    """
    loader = _get_loader(config)
    path = Path(config.path)

    dataset = loader.load(path=path)

    items = list(dataset.items)

    if config.shuffle:
        import random

        rng = random.Random(42)
        rng.shuffle(items)

    if config.limit is not None:
        items = items[: config.limit]

    return [item.to_dict() for item in items]
