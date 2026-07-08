"""Tests for HuggingFace dataset loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from openagent_eval.datasets.hf_loader import HFDatasetLoader
from openagent_eval.exceptions import DatasetValidationError, InvalidDatasetError


class TestHFDatasetLoader:
    """Tests for HFDatasetLoader."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.loader = HFDatasetLoader()

    def test_validate_valid_data(self) -> None:
        """Test validate with valid data."""
        data = [{"question": "Q1"}, {"question": "Q2"}]
        assert self.loader.validate(data) is True

    def test_validate_not_list(self) -> None:
        """Test validate with non-list data."""
        with pytest.raises(DatasetValidationError):
            self.loader.validate("not a list")

    def test_validate_missing_question(self) -> None:
        """Test validate with missing question."""
        data = [{"ground_truth": "A1"}]
        with pytest.raises(DatasetValidationError):
            self.loader.validate(data)

    def test_validate_empty_question(self) -> None:
        """Test validate with empty question."""
        data = [{"question": ""}]
        with pytest.raises(DatasetValidationError):
            self.loader.validate(data)

    def test_map_fields_standard(self) -> None:
        """Test field mapping with standard fields."""
        raw = {
            "question": "What is Python?",
            "answer": "A programming language.",
            "context": "Some context.",
        }
        mapped = self.loader._map_fields(raw)
        assert mapped["question"] == "What is Python?"
        assert mapped["ground_truth"] == "A programming language."
        assert mapped["context"] == "Some context."

    def test_map_fields_alternative_names(self) -> None:
        """Test field mapping with alternative field names."""
        raw = {
            "query": "What is RAG?",
            "target": "Retrieval-Augmented Generation.",
            "passage": "RAG info.",
        }
        mapped = self.loader._map_fields(raw)
        assert mapped["question"] == "What is RAG?"
        assert mapped["ground_truth"] == "Retrieval-Augmented Generation."
        assert mapped["context"] == "RAG info."

    def test_map_fields_list_answer(self) -> None:
        """Test field mapping with list of answers."""
        raw = {
            "question": "Q1",
            "answers": [{"text": "Answer 1"}, {"text": "Answer 2"}],
        }
        mapped = self.loader._map_fields(raw)
        assert mapped["ground_truth"] == "Answer 1"

    def test_map_fields_string_list_answer(self) -> None:
        """Test field mapping with list of string answers."""
        raw = {
            "question": "Q1",
            "answers": ["Answer 1", "Answer 2"],
        }
        mapped = self.loader._map_fields(raw)
        assert mapped["ground_truth"] == "Answer 1"

    def test_map_fields_metadata(self) -> None:
        """Test that extra fields become metadata."""
        raw = {
            "question": "Q1",
            "id": 1,
            "source": "docs",
        }
        mapped = self.loader._map_fields(raw)
        assert mapped["question"] == "Q1"
        assert mapped["metadata"]["id"] == 1
        assert mapped["metadata"]["source"] == "docs"

    def test_load_from_hub_with_mock(self) -> None:
        """Test load_from_hub with mocked datasets library."""
        mock_dataset = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]

        mock_datasets = MagicMock()
        mock_datasets.load_dataset.return_value = mock_dataset

        with patch.dict("sys.modules", {"datasets": mock_datasets}):
            dataset = self.loader.load_from_hub("test_dataset", split="train")

            assert dataset.size == 2
            assert dataset[0].question == "Q1"
            assert dataset[0].ground_truth == "A1"
            mock_datasets.load_dataset.assert_called_once_with("test_dataset", split="train")

    def test_load_from_hub_with_limit(self) -> None:
        """Test load_from_hub with limit parameter."""
        mock_dataset = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
            {"question": "Q3", "answer": "A3"},
        ]

        mock_datasets = MagicMock()
        mock_datasets.load_dataset.return_value = mock_dataset

        with patch.dict("sys.modules", {"datasets": mock_datasets}):
            dataset = self.loader.load_from_hub("test_dataset", limit=2)

            assert dataset.size == 2

    def test_load_from_hub_import_error(self) -> None:
        """Test load_from_hub when datasets is not installed."""
        with patch.dict("sys.modules", {"datasets": None}):
            with pytest.raises(InvalidDatasetError) as exc_info:
                self.loader.load_from_hub("test_dataset")
            assert "datasets" in str(exc_info.value).lower()

    def test_load_local_with_mock(self, tmp_path: Path) -> None:
        """Test load from local directory with mocked datasets library."""
        mock_dataset = [
            {"question": "Q1", "answer": "A1"},
        ]

        mock_datasets = MagicMock()
        mock_datasets.load_from_disk.return_value = mock_dataset

        # Create the directory so _validate_path passes
        local_dir = tmp_path / "local_dataset"
        local_dir.mkdir()

        with patch.dict("sys.modules", {"datasets": mock_datasets}):
            dataset = self.loader.load(local_dir)

            assert dataset.size == 1
            mock_datasets.load_from_disk.assert_called_once_with(str(local_dir))
