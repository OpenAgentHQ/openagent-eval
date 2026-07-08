"""Tests for CSV dataset loader."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from openagent_eval.datasets.csv_loader import CSVDatasetLoader
from openagent_eval.exceptions import (
    DatasetNotFoundError,
    DatasetValidationError,
)


class TestCSVDatasetLoader:
    """Tests for CSVDatasetLoader."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.loader = CSVDatasetLoader()

    def _write_csv(self, path: Path, rows: list[dict[str, str]]) -> None:
        """Helper to write CSV file."""
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def test_load_valid_csv(self, tmp_path: Path) -> None:
        """Test loading a valid CSV dataset."""
        rows = [
            {"question": "What is Python?", "ground_truth": "A language.", "context": "Some context."},
            {"question": "What is RAG?", "ground_truth": "Retrieval-Augmented Generation.", "context": "RAG info."},
        ]
        csv_path = tmp_path / "test.csv"
        self._write_csv(csv_path, rows)

        dataset = self.loader.load(csv_path)

        assert dataset.size == 2
        assert dataset.name == "test"
        assert dataset[0].question == "What is Python?"
        assert dataset[0].ground_truth == "A language."
        assert dataset[0].context == "Some context."
        assert dataset[1].question == "What is RAG?"

    def test_load_minimal_csv(self, tmp_path: Path) -> None:
        """Test loading CSV with only question column."""
        rows = [{"question": "Q1"}, {"question": "Q2"}]
        csv_path = tmp_path / "minimal.csv"
        self._write_csv(csv_path, rows)

        dataset = self.loader.load(csv_path)

        assert dataset.size == 2
        assert dataset[0].question == "Q1"
        assert dataset[0].ground_truth is None

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Test loading a non-existent file."""
        csv_path = tmp_path / "nonexistent.csv"

        with pytest.raises(DatasetNotFoundError):
            self.loader.load(csv_path)

    def test_load_missing_question_column(self, tmp_path: Path) -> None:
        """Test loading CSV without question column."""
        rows = [{"ground_truth": "A1"}, {"ground_truth": "A2"}]
        csv_path = tmp_path / "no_question.csv"
        self._write_csv(csv_path, rows)

        with pytest.raises(DatasetValidationError):
            self.loader.load(csv_path)

    def test_load_empty_csv(self, tmp_path: Path) -> None:
        """Test loading an empty CSV file."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("", encoding="utf-8")

        with pytest.raises(DatasetValidationError):
            self.loader.load(csv_path)

    def test_load_with_metadata_json(self, tmp_path: Path) -> None:
        """Test loading CSV with JSON metadata."""
        rows = [
            {"question": "Q1", "metadata": '{"id": 1, "source": "docs"}'},
        ]
        csv_path = tmp_path / "metadata.csv"
        self._write_csv(csv_path, rows)

        dataset = self.loader.load(csv_path)

        assert dataset.size == 1
        assert dataset[0].metadata == {"id": 1, "source": "docs"}

    def test_load_with_invalid_metadata(self, tmp_path: Path) -> None:
        """Test loading CSV with invalid JSON metadata."""
        rows = [
            {"question": "Q1", "metadata": "not json"},
        ]
        csv_path = tmp_path / "bad_meta.csv"
        self._write_csv(csv_path, rows)

        dataset = self.loader.load(csv_path)

        # Invalid metadata should be stored as raw string
        assert dataset.size == 1
        assert dataset[0].metadata == {"raw": "not json"}

    def test_validate_valid_data(self) -> None:
        """Test validate with valid data."""
        data = [{"question": "Q1"}, {"question": "Q2"}]
        assert self.loader.validate(data) is True

    def test_validate_not_list(self) -> None:
        """Test validate with non-list data."""
        with pytest.raises(DatasetValidationError):
            self.loader.validate("not a list")

    def test_validate_empty_list(self) -> None:
        """Test validate with empty list."""
        with pytest.raises(DatasetValidationError):
            self.loader.validate([])

    def test_dataset_metadata(self, tmp_path: Path) -> None:
        """Test that dataset metadata is set correctly."""
        rows = [{"question": "Q1"}]
        csv_path = tmp_path / "meta.csv"
        self._write_csv(csv_path, rows)

        dataset = self.loader.load(csv_path)

        assert dataset.metadata["format"] == "csv"
        assert dataset.metadata["source"] == str(csv_path)
