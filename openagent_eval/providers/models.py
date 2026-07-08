"""Pydantic models for LLM and document data structures.

This module defines the core data models used throughout the providers layer:
- LLMResponse: Standardized response from any LLM provider
- Document: Document representation for retrieval and evaluation
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class TokenUsage(BaseModel):
    """Token usage statistics for an LLM response.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total tokens used (prompt + completion).
    """

    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")

    @field_validator("prompt_tokens", "completion_tokens", "total_tokens")
    @classmethod
    def validate_non_negative_tokens(cls, v: int) -> int:
        """Ensure token counts are non-negative."""
        if v < 0:
            raise ValueError(f"Token count must be non-negative, got {v}")
        return v

    model_config = {
        "frozen": True,
    }


class LLMResponse(BaseModel):
    """Standardized response from an LLM provider.

    This model provides a consistent interface across different LLM providers,
    normalizing their varying response formats into a unified structure.

    Attributes:
        content: The generated text content from the LLM.
        model: The model identifier used for generation.
        usage: Token usage statistics for the request.
        provider: The LLM provider name (e.g., openai, gemini, anthropic).
        latency_ms: Response latency in milliseconds.
    """

    content: str = Field(..., description="Generated text content from the LLM")
    model: str = Field(..., description="Model identifier used for generation")
    usage: TokenUsage = Field(..., description="Token usage statistics")
    provider: str = Field(..., description="LLM provider name")
    latency_ms: float = Field(..., description="Response latency in milliseconds", ge=0.0)

    @field_validator("model")
    @classmethod
    def validate_model_not_empty(cls, v: str) -> str:
        """Ensure model identifier is not empty."""
        if not v.strip():
            raise ValueError("Model identifier cannot be empty")
        return v.strip()

    @field_validator("provider")
    @classmethod
    def validate_provider_not_empty(cls, v: str) -> str:
        """Ensure provider name is not empty."""
        if not v.strip():
            raise ValueError("Provider name cannot be empty")
        return v.strip().lower()

    model_config = {
        "frozen": True,
    }


class Document(BaseModel):
    """Document representation for retrieval and evaluation.

    Used throughout the retrieval pipeline to represent documents with
    their content, metadata, and optional relevance scoring.

    Attributes:
        content: The document text content.
        metadata: Additional metadata about the document.
        score: Relevance score from retrieval (None if not scored).
        id: Optional document identifier.
    """

    content: str = Field(..., description="Document text content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional document metadata"
    )
    score: float | None = Field(None, description="Relevance score from retrieval")
    id: str | None = Field(None, description="Document identifier")

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: float | None) -> float | None:
        """Validate score is within reasonable bounds if provided."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {v}")
        return v

    model_config = {
        "frozen": True,
    }
