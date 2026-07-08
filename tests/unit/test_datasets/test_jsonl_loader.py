"""Tests for JSONL dataset loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openagent_eval.datasets.jsonl_loader import JSONLDatasetLoader
from openagent_eval.exceptions import (
    DatasetNotFoundError,
    DatasetValidationError,
    InvalidDatasetError,
)


class TestJSONLDatasetLoader:
    """Tests for JSONLDatasetLoader."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.loader = JSONLDatasetLoader()

    def test_load_valid_jsonl(self, tmp_path: Path) -> None:
        """Test loading a valid JSONL dataset."""
        lines = [
            json.dumps({"question": "What is Python?", "ground_truth": "A language."}),
            json.dumps({"question": "What is RAG?", "ground_truth": "Retrieval-Augmented Generation."}),
        ]
        jsonl_path = tmp_path / "test.jsonl"
        jsonl_path.write_text("\n".join(lines), encoding="utf-8")

        dataset = self.loader.load(jsonl_path)

        assert dataset.size == 2
        assert dataset.name == "test"
        assert dataset[0].question == "What is Python?"
        assert dataset[0].ground_truth == "A language."
        assert dataset[1].question == "What is RAG?"

    def test_load_with_blank_lines(self, tmp_path: Path) -> None:
        """Test loading JSONL with blank lines."""
        lines = [
            json.dumps({"question": "Q1"}),
            "",
            "  ",
            json.dumps({"question": "Q2"}),
        ]
        jsonl_path = tmp_path / "blanks.jsonl"
        jsonl_path.write_text("\n".join(lines), encoding="utf-8")

        dataset = self.loader.load(jsonl_path)

        assert dataset.size == 2

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Test loading a non-existent file."""
        jsonl_path = tmp_path / "nonexistent.jsonl"

        with pytest.raises(DatasetNotFoundError):
            self.loader.load(jsonl_path)

    def test_load_invalid_json_line(self, tmp_path: Path) -> None:
        """Test loading JSONL with invalid JSON on a line."""
        lines = [
            json.dumps({"question": "Q1"}),
            "not valid json {{{",
        ]
        jsonl_path = tmp_path / "invalid.jsonl"
        jsonl_path.write_text("\n".join(lines), encoding="utf-8")

        with pytest.raises(InvalidDatasetError) as exc_info:
            self.loader.load(jsonl_path)
        assert "Invalid JSON" in str(exc_info.value)

    def test_load_missing_question(self, tmp_path: Path) -> None:
        """Test loading JSONL with missing question field."""
        lines = [
            json.dumps({"ground_truth": "A1"}),
            json.dumps({"question": "Q2"}),
        ]
        jsonl_path = tmp_path / "missing_q.jsonl"
        jsonl_path.write_text("\n".join(lines), encoding="utf-8")

        with pytest.raises(DatasetValidationError):
            self.loader.load(jsonl_path)

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """Test loading an empty JSONL file."""
        jsonl_path = tmp_path / "empty.jsonl"
        jsonl_path.write_text("", encoding="utf-8")

        with pytest.raises(DatasetValidationError):
            self.loader.load(jsonl_path)

    def test_load_full_item(self, tmp_path: Path) -> None:
        """Test loading JSONL with all fields."""
        data = {
            "question": "What is Python?",
            "ground_truth": "A language.",
            "context": "Some context.",
            "metadata": {"id": 1},
        }
        jsonl_path = tmp_path / "full.jsonl"
        jsonl_path.write_text(json.dumps(data), encoding="utf-8")

        dataset = self.loader.load(jsonl_path)

        assert dataset.size == 1
        assert dataset[0].question == "What is Python?"
        assert dataset[0].ground_truth == "A language."
        assert dataset[0].context == "Some context."
        assert dataset[0].metadata == {"id": 1}

    def test_validate_valid_data(self) -> None:
        """Test validate with valid data."""
        data = [{"question": "Q1"}, {"question": "Q2"}]
        assert self.loader.validate(data) is True

    def test_validate_not_list(self) -> None:
        """Test validate with non-list data."""
        with pytest.raises(DatasetValidationError):
            self.loader.validate("not a list")

    def test_dataset_metadata(self, tmp_path: Path) -> None:
        """Test that dataset metadata is set correctly."""
        lines = [json.dumps({"question": "Q1"})]
        jsonl_path = tmp_path / "meta.jsonl"
        jsonl_path.write_text("\n".join(lines), encoding="utf-8")

        dataset = self.loader.load(jsonl_path)

        assert dataset.metadata["format"] == "jsonl"
        assert dataset.metadata["source"] == str(jsonl_path)
