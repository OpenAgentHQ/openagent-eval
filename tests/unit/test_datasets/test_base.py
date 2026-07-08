"""Tests for base dataset models (DatasetItem, Dataset)."""

from __future__ import annotations

import pytest

from openagent_eval.datasets.base import Dataset, DatasetItem


class TestDatasetItem:
    """Tests for DatasetItem dataclass."""

    def test_create_minimal_item(self) -> None:
        """Test creating a minimal item with only question."""
        item = DatasetItem(question="What is Python?")
        assert item.question == "What is Python?"
        assert item.ground_truth is None
        assert item.context is None
        assert item.metadata == {}
        assert item.contexts == []

    def test_create_full_item(self) -> None:
        """Test creating a full item with all fields."""
        item = DatasetItem(
            question="What is Python?",
            ground_truth="Python is a programming language.",
            context="Python is a high-level language.",
            metadata={"id": 1, "source": "docs"},
            contexts=["Context 1", "Context 2"],
        )
        assert item.question == "What is Python?"
        assert item.ground_truth == "Python is a programming language."
        assert item.context == "Python is a high-level language."
        assert item.metadata == {"id": 1, "source": "docs"}
        assert item.contexts == ["Context 1", "Context 2"]

    def test_to_dict_minimal(self) -> None:
        """Test to_dict with minimal item."""
        item = DatasetItem(question="What is Python?")
        d = item.to_dict()
        assert d == {"question": "What is Python?"}

    def test_to_dict_full(self) -> None:
        """Test to_dict with full item."""
        item = DatasetItem(
            question="What is Python?",
            ground_truth="A language.",
            context="Some context.",
            metadata={"id": 1},
        )
        d = item.to_dict()
        assert d["question"] == "What is Python?"
        assert d["ground_truth"] == "A language."
        assert d["context"] == "Some context."
        assert d["metadata"] == {"id": 1}

    def test_to_dict_excludes_none(self) -> None:
        """Test that to_dict excludes None values."""
        item = DatasetItem(question="Q", ground_truth=None, context=None)
        d = item.to_dict()
        assert "ground_truth" not in d
        assert "context" not in d


class TestDataset:
    """Tests for Dataset dataclass."""

    def test_create_empty_dataset(self) -> None:
        """Test creating an empty dataset."""
        dataset = Dataset()
        assert dataset.size == 0
        assert len(dataset) == 0
        assert dataset.items == []
        assert dataset.name is None
        assert dataset.metadata == {}

    def test_create_dataset_with_items(self) -> None:
        """Test creating a dataset with items."""
        items = [
            DatasetItem(question="Q1"),
            DatasetItem(question="Q2"),
        ]
        dataset = Dataset(items=items, name="test")
        assert dataset.size == 2
        assert len(dataset) == 2
        assert dataset.name == "test"

    def test_size_property(self) -> None:
        """Test size property."""
        dataset = Dataset(items=[DatasetItem(question="Q1")])
        assert dataset.size == 1

    def test_has_ground_truth_true(self) -> None:
        """Test has_ground_truth when all items have ground truth."""
        items = [
            DatasetItem(question="Q1", ground_truth="A1"),
            DatasetItem(question="Q2", ground_truth="A2"),
        ]
        dataset = Dataset(items=items)
        assert dataset.has_ground_truth is True

    def test_has_ground_truth_false(self) -> None:
        """Test has_ground_truth when some items lack ground truth."""
        items = [
            DatasetItem(question="Q1", ground_truth="A1"),
            DatasetItem(question="Q2"),
        ]
        dataset = Dataset(items=items)
        assert dataset.has_ground_truth is False

    def test_questions_property(self) -> None:
        """Test questions property."""
        items = [
            DatasetItem(question="Q1"),
            DatasetItem(question="Q2"),
            DatasetItem(question="Q3"),
        ]
        dataset = Dataset(items=items)
        assert dataset.questions == ["Q1", "Q2", "Q3"]

    def test_iter(self) -> None:
        """Test iteration over dataset."""
        items = [DatasetItem(question="Q1"), DatasetItem(question="Q2")]
        dataset = Dataset(items=items)
        collected = [item.question for item in dataset]
        assert collected == ["Q1", "Q2"]

    def test_getitem(self) -> None:
        """Test indexing into dataset."""
        items = [DatasetItem(question="Q1"), DatasetItem(question="Q2")]
        dataset = Dataset(items=items)
        assert dataset[0].question == "Q1"
        assert dataset[1].question == "Q2"

    def test_filter(self) -> None:
        """Test filtering dataset items."""
        items = [
            DatasetItem(question="Q1", ground_truth="A1"),
            DatasetItem(question="Q2"),
            DatasetItem(question="Q3", ground_truth="A3"),
        ]
        dataset = Dataset(items=items)
        filtered = dataset.filter(lambda item: item.ground_truth is not None)
        assert filtered.size == 2
        assert filtered[0].question == "Q1"
        assert filtered[1].question == "Q3"

    def test_filter_preserves_metadata(self) -> None:
        """Test that filter preserves dataset metadata."""
        items = [DatasetItem(question="Q1")]
        dataset = Dataset(items=items, name="test", metadata={"key": "value"})
        filtered = dataset.filter(lambda item: True)
        assert filtered.name == "test"
        assert filtered.metadata == {"key": "value"}

    def test_to_dicts(self) -> None:
        """Test converting dataset to list of dicts."""
        items = [
            DatasetItem(question="Q1", ground_truth="A1"),
            DatasetItem(question="Q2"),
        ]
        dataset = Dataset(items=items)
        dicts = dataset.to_dicts()
        assert len(dicts) == 2
        assert dicts[0]["question"] == "Q1"
        assert dicts[0]["ground_truth"] == "A1"
        assert dicts[1]["question"] == "Q2"
        assert "ground_truth" not in dicts[1]
