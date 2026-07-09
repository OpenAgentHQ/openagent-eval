"""Dataset loading and validation module.

This module provides dataset loaders for various formats (JSON, JSONL, CSV, HuggingFace)
and data models for validation.

Usage:
    ```python
    from openagent_eval.datasets import JSONDatasetLoader, Dataset

    loader = JSONDatasetLoader()
    dataset = loader.load(Path("data/questions.json"))
    ```
"""

from openagent_eval.datasets.base import BaseDatasetLoader, Dataset, DatasetItem
from openagent_eval.datasets.csv_loader import CSVDatasetLoader
from openagent_eval.datasets.hf_loader import HFDatasetLoader
from openagent_eval.datasets.json_loader import JSONDatasetLoader
from openagent_eval.datasets.jsonl_loader import JSONLDatasetLoader
from openagent_eval.datasets.models import DatasetItemModel, DatasetModel
from openagent_eval.datasets.pdf_loader import PDFDatasetLoader

__all__ = [
    # Core types
    "BaseDatasetLoader",
    "Dataset",
    "DatasetItem",
    # Pydantic models
    "DatasetItemModel",
    "DatasetModel",
    # Loaders
    "JSONDatasetLoader",
    "JSONLDatasetLoader",
    "CSVDatasetLoader",
    "HFDatasetLoader",
    "PDFDatasetLoader",
]
