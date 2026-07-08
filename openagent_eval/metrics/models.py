"""Pydantic models for metric validation.

This module defines Pydantic models used for validating metric inputs
and outputs.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MetricResultModel(BaseModel):
    """Pydantic model for validating metric results.

    Attributes:
        score: The metric score (0.0 to 1.0).
        reason: Human-readable explanation.
        metadata: Additional context about the evaluation.
    """

    score: float = Field(..., ge=0.0, le=1.0, description="Metric score")
    reason: str = Field(default="", description="Explanation of the score")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class RetrievalInput(BaseModel):
    """Input model for retrieval metrics.

    Attributes:
        query: The original query.
        retrieved_contexts: List of retrieved context strings.
        ground_truth_contexts: List of ground truth context strings.
    """

    query: str = Field(..., min_length=1, description="The original query")
    retrieved_contexts: list[str] = Field(
        default_factory=list, description="Retrieved context strings"
    )
    ground_truth_contexts: list[str] = Field(
        default_factory=list, description="Ground truth context strings"
    )


class GenerationInput(BaseModel):
    """Input model for generation metrics.

    Attributes:
        question: The original question.
        answer: The generated answer.
        ground_truth: The expected correct answer.
        contexts: List of context strings used for generation.
    """

    question: str = Field(..., min_length=1, description="The original question")
    answer: str = Field(..., min_length=1, description="The generated answer")
    ground_truth: str | None = Field(None, description="The expected answer")
    contexts: list[str] = Field(
        default_factory=list, description="Context strings used for generation"
    )
