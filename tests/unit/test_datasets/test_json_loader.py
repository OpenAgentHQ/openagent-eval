"""Tests for JSON dataset loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openagent_eval.datasets.json_loader import JSONDatasetLoader
from openagent_eval.exceptions import (
    DatasetNotFoundError,
    DatasetValidationError,
    InvalidDatasetError,
)


class TestJSONDatasetLoader:
    """Tests for JSONDatasetLoader."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.loader = JSONDatasetLoader()

    def test_load_valid_json(self, tmp_path: Path) -> None:
        """Test loading a valid JSON dataset."""
        data = [
            {
                "question": "What is Python?",
                "ground_truth": "Python is a programming language.",
                "context": "Python is a high-level language.",
                "metadata": {"id": 1},
            },
            {
                "question": "What is RAG?",
                "ground_truth": "Retrieval-Augmented Generation.",
                "context": "RAG combines retrieval and generation.",
            },
        ]
        json_path = tmp_path / "test.json"
        json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        dataset = self.loader.load(json_path)

        assert dataset.size == 2
        assert dataset.name == "test"
        assert dataset[0].question == "What is Python?"
        assert dataset[0].ground_truth == "Python is a programming language."
        assert dataset[0].context == "Python is a high-level language."
        assert dataset[0].metadata == {"id": 1}
        assert dataset[1].question == "What is RAG?"

    def test_load_minimal_json(self, tmp_path: Path) -> None:
        """Test loading JSON with minimal fields."""
        data = [{"question": "Q1"}, {"question": "Q2"}]
        json_path = tmp_path / "minimal.json"
        json_path.write_text(json.dumps(data), encoding="utf-8")

        dataset = self.loader.load(json_path)

        assert dataset.size == 2
        assert dataset[0].question == "Q1"
        assert dataset[0].ground_truth is None

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Test loading a non-existent file."""
        json_path = tmp_path / "nonexistent.json"

        with pytest.raises(DatasetNotFoundError):
            self.loader.load(json_path)

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Test loading invalid JSON."""
        json_path = tmp_path / "invalid.json"
        json_path.write_text("not valid json {{{", encoding="utf-8")

        with pytest.raises(InvalidDatasetError) as exc_info:
            self.loader.load(json_path)
        assert "Invalid JSON" in str(exc_info.value)

    def test_load_non_array_json(self, tmp_path: Path) -> None:
        """Test loading JSON that is not an array."""
        json_path = tmp_path / "object.json"
        json_path.write_text(json.dumps({"question": "Q1"}), encoding="utf-8")

        with pytest.raises(DatasetValidationError):
            self.loader.load(json_path)

    def test_load_missing_question_field(self, tmp_path: Path) -> None:
        """Test loading JSON with missing question field."""
        data = [{"ground_truth": "A1"}, {"question": "Q2"}]
        json_path = tmp_path / "missing_q.json"
        json_path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(DatasetValidationError) as exc_info:
            self.loader.load(json_path)
        assert "question" in str(exc_info.value).lower()

    def test_load_empty_question(self, tmp_path: Path) -> None:
        """Test loading JSON with empty question."""
        data = [{"question": ""}, {"question": "Q2"}]
        json_path = tmp_path / "empty_q.json"
        json_path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(DatasetValidationError):
            self.loader.load(json_path)

    def test_validate_valid_data(self) -> None:
        """Test validate with valid data."""
        data = [{"question": "Q1"}, {"question": "Q2"}]
        assert self.loader.validate(data) is True

    def test_validate_not_list(self) -> None:
        """Test validate with non-list data."""
        with pytest.raises(DatasetValidationError):
            self.loader.validate({"question": "Q1"})

    def test_validate_empty_list(self) -> None:
        """Test validate with empty list."""
        # Empty list should pass basic validation (items can be empty)
        # But Pydantic model will reject it
        data: list[dict] = []
        assert self.loader.validate(data) is True

    def test_dataset_metadata(self, tmp_path: Path) -> None:
        """Test that dataset metadata is set correctly."""
        data = [{"question": "Q1"}]
        json_path = tmp_path / "meta.json"
        json_path.write_text(json.dumps(data), encoding="utf-8")

        dataset = self.loader.load(json_path)

        assert dataset.metadata["format"] == "json"
        assert dataset.metadata["source"] == str(json_path)
