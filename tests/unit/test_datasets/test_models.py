"""Tests for dataset Pydantic validation models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from openagent_eval.datasets.models import DatasetItemModel, DatasetModel


class TestDatasetItemModel:
    """Tests for DatasetItemModel Pydantic model."""

    def test_valid_minimal_item(self) -> None:
        """Test creating a valid minimal item."""
        model = DatasetItemModel(question="What is Python?")
        assert model.question == "What is Python?"
        assert model.ground_truth is None
        assert model.context is None
        assert model.metadata == {}
        assert model.contexts == []

    def test_valid_full_item(self) -> None:
        """Test creating a valid full item."""
        model = DatasetItemModel(
            question="What is Python?",
            ground_truth="Python is a programming language.",
            context="Python is a high-level language.",
            metadata={"id": 1},
            contexts=["Context 1"],
        )
        assert model.question == "What is Python?"
        assert model.ground_truth == "Python is a programming language."
        assert model.context == "Python is a high-level language."
        assert model.metadata == {"id": 1}
        assert model.contexts == ["Context 1"]

    def test_question_strips_whitespace(self) -> None:
        """Test that question whitespace is stripped."""
        model = DatasetItemModel(question="  What is Python?  ")
        assert model.question == "What is Python?"

    def test_empty_question_raises_error(self) -> None:
        """Test that empty question raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DatasetItemModel(question="")
        assert "question" in str(exc_info.value).lower()

    def test_whitespace_question_raises_error(self) -> None:
        """Test that whitespace-only question raises validation error."""
        with pytest.raises(ValidationError):
            DatasetItemModel(question="   ")

    def test_ground_truth_empty_becomes_none(self) -> None:
        """Test that empty ground_truth becomes None."""
        model = DatasetItemModel(question="Q", ground_truth="  ")
        assert model.ground_truth is None

    def test_context_empty_becomes_none(self) -> None:
        """Test that empty context becomes None."""
        model = DatasetItemModel(question="Q", context="  ")
        assert model.context is None


class TestDatasetModel:
    """Tests for DatasetModel Pydantic model."""

    def test_valid_dataset(self) -> None:
        """Test creating a valid dataset."""
        model = DatasetModel(
            items=[
                DatasetItemModel(question="Q1"),
                DatasetItemModel(question="Q2"),
            ],
            name="test",
        )
        assert len(model.items) == 2
        assert model.name == "test"

    def test_empty_dataset_raises_error(self) -> None:
        """Test that empty dataset raises validation error."""
        with pytest.raises(ValidationError):
            DatasetModel(items=[])

    def test_dataset_with_metadata(self) -> None:
        """Test dataset with metadata."""
        model = DatasetModel(
            items=[DatasetItemModel(question="Q1")],
            metadata={"source": "test"},
        )
        assert model.metadata == {"source": "test"}
