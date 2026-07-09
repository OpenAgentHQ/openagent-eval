"""Pydantic models for dataset validation.

This module defines the Pydantic models used for validating dataset entries
and enforcing the expected schema.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class DatasetItemModel(BaseModel):
    """Pydantic model for validating a single dataset entry.

    This model enforces the schema for dataset items. The `question` field is
    required, while `ground_truth`, `context`, and `metadata` are optional.

    Attributes:
        question: The question to evaluate (required).
        ground_truth: The expected correct answer.
        context: The context provided to the RAG system.
        metadata: Additional metadata about this item.
        contexts: List of retrieved contexts (populated after retrieval).
    """

    question: str = Field(..., min_length=1, description="The question to evaluate")
    ground_truth: str | None = Field(None, description="The expected correct answer")
    context: str | None = Field(None, description="The context provided to the RAG system")
    ground_truth_contexts: list[str] = Field(
        default_factory=list,
        description="Ground-truth relevant contexts for retrieval evaluation",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    contexts: list[str] = Field(default_factory=list, description="Retrieved contexts")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate that the question is not empty or whitespace-only."""
        if not v.strip():
            raise ValueError("Question cannot be empty or whitespace-only")
        return v.strip()

    @field_validator("ground_truth")
    @classmethod
    def validate_ground_truth(cls, v: str | None) -> str | None:
        """Validate ground truth if provided."""
        if v is not None and not v.strip():
            return None
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: str | None) -> str | None:
        """Validate context if provided."""
        if v is not None and not v.strip():
            return None
        return v


class DatasetModel(BaseModel):
    """Pydantic model for validating an entire dataset.

    This model validates a list of dataset entries, ensuring each entry
    conforms to the expected schema.

    Attributes:
        items: List of validated dataset items.
        name: Optional name for the dataset.
        metadata: Dataset-level metadata.
    """

    items: list[DatasetItemModel] = Field(
        default_factory=list,
        description="List of dataset items",
    )
    name: str | None = Field(None, description="Dataset name")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Dataset metadata")

    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, v: list[DatasetItemModel]) -> list[DatasetItemModel]:
        """Validate that the dataset is not empty."""
        if not v:
            raise ValueError("Dataset cannot be empty")
        return v
