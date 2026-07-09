"""Pydantic models for configuration validation."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class OutputFormat(str, Enum):
    """Output format for reports."""

    TERMINAL = "terminal"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = Field(..., description="LLM provider name (e.g., openai, gemini, anthropic)")
    model: str = Field(..., description="Model identifier (e.g., gpt-4o)")
    api_key: str | None = Field(None, description="API key (can use environment variable)")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int | None = Field(None, ge=1, description="Maximum tokens to generate")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str | None) -> str | None:
        """Validate API key format."""
        if v is not None and len(v) < 10:
            raise ValueError("API key appears to be invalid (too short)")
        return v


class RetrieverConfig(BaseModel):
    """Retriever configuration."""

    provider: str = Field(..., description="Retriever provider name (e.g., chroma)")
    settings: dict[str, Any] = Field(default_factory=dict, description="Provider-specific settings")


class MetricsConfig(BaseModel):
    """Metrics configuration.

    Metric names must match the keys in ``openagent_eval.metrics.METRIC_REGISTRY``
    (e.g. ``context_precision``, ``context_recall``, ``mrr``, ``faithfulness``,
    ``answer_relevancy``, ``latency``, ``token_count``).
    """

    retrieval: list[str] = Field(
        default_factory=lambda: ["context_precision", "context_recall", "mrr"],
        description="Retrieval metrics to compute",
    )
    generation: list[str] = Field(
        default_factory=lambda: ["faithfulness", "answer_relevancy"],
        description="Generation metrics to compute",
    )
    performance: list[str] = Field(
        default_factory=lambda: ["latency"],
        description="Performance metrics to track",
    )
    cost: list[str] = Field(
        default_factory=lambda: ["token_count"],
        description="Cost metrics to track",
    )


class DatasetConfig(BaseModel):
    """Dataset configuration."""

    path: str = Field(..., description="Path to dataset file")
    format: str | None = Field(None, description="Dataset format (json, jsonl, csv, hf)")
    limit: int | None = Field(None, ge=1, description="Maximum number of items to load")
    shuffle: bool = Field(False, description="Whether to shuffle the dataset")


class ReportConfig(BaseModel):
    """Report configuration."""

    output: OutputFormat = Field(OutputFormat.TERMINAL, description="Output format")
    output_dir: str = Field("./reports", description="Output directory for reports")
    include_examples: bool = Field(True, description="Include examples in reports")
    max_examples: int = Field(10, ge=1, description="Maximum examples to include")


class Config(BaseModel):
    """Main configuration model for OpenAgent Eval."""

    dataset: DatasetConfig = Field(..., description="Dataset configuration")
    llm: LLMConfig = Field(..., description="LLM provider configuration")
    retriever: RetrieverConfig = Field(
        default_factory=lambda: RetrieverConfig(provider="chroma"),
        description="Retriever configuration",
    )
    metrics: MetricsConfig = Field(
        default_factory=MetricsConfig, description="Metrics configuration"
    )
    report: ReportConfig = Field(default_factory=ReportConfig, description="Report configuration")

    # Global settings
    verbose: bool = Field(False, description="Enable verbose output")
    parallel: bool = Field(True, description="Enable parallel evaluation")
    max_workers: int = Field(4, ge=1, description="Maximum parallel workers")
    timeout: float = Field(300.0, ge=1.0, description="Evaluation timeout in seconds")

    model_config = {
        "case_sensitive": False,
        "validate_assignment": True,
    }
