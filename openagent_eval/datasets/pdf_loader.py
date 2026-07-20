"""PDF dataset loader.

This module implements the dataset loader for PDF documents. Text is extracted
from each page using `pypdf` and each page becomes one dataset item where the
extracted text is stored as ``context``.

A PDF is a source document rather than a list of questions, so the required
``question`` field is populated from a configurable template (defaulting to a
generic instruction). This makes the resulting dataset usable for context and
retrieval evaluation.

Requires the optional ``pypdf`` dependency:

    pip install openagent-eval[pdf]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openagent_eval.datasets.base import BaseDatasetLoader, Dataset, DatasetItem
from openagent_eval.datasets.models import DatasetItemModel
from openagent_eval.exceptions import DatasetValidationError, InvalidDatasetError

# Default question used when a PDF page is turned into a dataset item.
DEFAULT_QUESTION_TEMPLATE = "Answer the user's question using the provided context."


class PDFDatasetLoader(BaseDatasetLoader):
    """Loader for PDF documents.

    Extracts text from each page of a PDF and produces one ``DatasetItem`` per
    page. The page text becomes the ``context`` and the ``question`` field is
    filled from ``question_template``.

    Pages that yield no extractable text (e.g. scanned/image-only pages) are
    skipped. If no text can be extracted from any page, loading fails.

    Requires the ``pypdf`` package:

        pip install openagent-eval[pdf]

    Example:
        ```python
        from openagent_eval.datasets import PDFDatasetLoader
        from pathlib import Path

        loader = PDFDatasetLoader()
        dataset = loader.load(Path("docs/manual.pdf"))
        ```
    """

    def __init__(
        self,
        question_template: str | None = None,
    ) -> None:
        """Initialize the loader.

        Args:
            question_template: Template used for the ``question`` field of every
                generated item. Defaults to a generic instruction when ``None``.
        """
        self.question_template = question_template or DEFAULT_QUESTION_TEMPLATE

    def load(self, path: Path) -> Dataset:
        """Load a dataset from a PDF file.

        Args:
            path: Path to the PDF file.

        Returns:
            Loaded Dataset object with one item per extracted page.

        Raises:
            DatasetNotFoundError: If the file does not exist.
            InvalidDatasetError: If ``pypdf`` is missing or the PDF cannot be read.
            DatasetValidationError: If no extractable text is found.
        """
        self._validate_path(path)

        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise InvalidDatasetError(
                message=(
                    "The 'pypdf' package is required for PDF dataset loading. "
                    "Install it with: pip install openagent-eval[pdf]"
                ),
                dataset_path=str(path),
                data_format="pdf",
            ) from e

        try:
            reader = PdfReader(str(path))
        except Exception as e:
            raise InvalidDatasetError(
                message=f"Failed to read PDF: {e}",
                dataset_path=str(path),
                data_format="pdf",
            ) from e

        raw_items = self._extract_raw(reader, path)
        return self._parse_data(raw_items, path)

    def validate(self, data: Any) -> bool:
        """Validate that the data conforms to the expected PDF schema.

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
                validation_errors=["No pages found in PDF"],
            )

        errors: list[str] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f"Item {i}: Expected dict, got {type(item).__name__}")
                continue

            question = item.get("question")
            if not isinstance(question, str) or not question.strip():
                errors.append(f"Item {i}: 'question' must be a non-empty string")

            context = item.get("context")
            if not isinstance(context, str) or not context.strip():
                errors.append(f"Item {i}: 'context' must be a non-empty string")

        if errors:
            raise DatasetValidationError(
                message=f"Dataset validation failed with {len(errors)} error(s)",
                validation_errors=errors,
            )

        return True

    def _extract_raw(self, reader: Any, path: Path) -> list[dict[str, Any]]:
        """Extract raw item dictionaries from a PDF reader.

        Args:
            reader: A ``pypdf.PdfReader`` instance.
            path: Path to the source file (for metadata).

        Returns:
            List of raw item dictionaries (one per non-empty page).

        Raises:
            DatasetValidationError: If no extractable text is found.
        """
        raw_items: list[dict[str, Any]] = []
        skipped = 0

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            text = text.strip()

            if not text:
                skipped += 1
                continue

            raw_items.append(
                {
                    "question": self.question_template,
                    "context": text,
                    "metadata": {
                        "source": str(path),
                        "page": page_num,
                        "format": "pdf",
                    },
                }
            )

        if not raw_items:
            raise DatasetValidationError(
                message="No extractable text found in PDF (all pages empty or image-only).",
                dataset_path=str(path),
                validation_errors=[f"Skipped {skipped} empty page(s)"],
            )

        return raw_items

    def _parse_data(
        self, raw_items: list[dict[str, Any]], path: Path
    ) -> Dataset:
        """Parse raw item dictionaries into a Dataset object.

        Args:
            raw_items: List of raw item dictionaries.
            path: Path to the source file (for error reporting).

        Returns:
            Dataset object.

        Raises:
            DatasetValidationError: If parsing or validation fails.
        """
        self.validate(raw_items)

        items: list[DatasetItem] = []
        validation_errors: list[str] = []

        for i, raw_item in enumerate(raw_items):
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

        return Dataset(
            items=items,
            name=path.stem,
            metadata={
                "source": str(path),
                "format": "pdf",
                "pages": len(items),
            },
        )
