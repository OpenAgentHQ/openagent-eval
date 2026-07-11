"""CI/CD models for OpenAgent Eval."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ThresholdOperator(str, Enum):
    """Comparison operators for threshold evaluation."""

    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    EQ = "eq"  # Equal to
    NEQ = "neq"  # Not equal to


class ThresholdConfig(BaseModel):
    """Configuration for a single metric threshold."""

    metric: str = Field(..., description="Metric name to evaluate")
    operator: ThresholdOperator = Field(
        default=ThresholdOperator.GTE,
        description="Comparison operator",
    )
    value: float = Field(..., description="Threshold value to compare against")
    required: bool = Field(
        default=True,
        description="If True, failure blocks the pipeline",
    )


class GateBehavior(str, Enum):
    """Behavior when a gate fails."""

    FAIL = "fail"  # Fail the test (exit code 1)
    WARN = "warn"  # Warn but pass (exit code 0)
    SKIP = "skip"  # Skip evaluation entirely


class EvaluationGate(BaseModel):
    """A gate that controls whether evaluation passes or fails."""

    name: str = Field(..., description="Name of the gate")
    thresholds: list[ThresholdConfig] = Field(
        default_factory=list,
        description="List of metric thresholds",
    )
    behavior: GateBehavior = Field(
        default=GateBehavior.FAIL,
        description="Behavior when gate fails",
    )


class CICDConfig(BaseModel):
    """CI/CD configuration for OpenAgent Eval."""

    config_path: str | None = Field(
        default=None,
        description="Path to evaluation config file",
    )
    gates: list[EvaluationGate] = Field(
        default_factory=list,
        description="Evaluation gates with thresholds",
    )
    fail_on_error: bool = Field(
        default=True,
        description="Fail pipeline on evaluation errors",
    )
    timeout: int = Field(
        default=300,
        description="Timeout in seconds for evaluation",
    )
    retry_count: int = Field(
        default=0,
        description="Number of retries on failure",
    )
    output_format: str = Field(
        default="json",
        description="Output format for CI/CD (json, terminal)",
    )


class TestStatus(str, Enum):
    """Status of a test result."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestResult(BaseModel):
    """Result of a CI/CD test run."""

    test_name: str = Field(..., description="Name of the test")
    status: TestStatus = Field(..., description="Test status")
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Metric results",
    )
    gate_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Gate evaluation results",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if test failed",
    )
    duration_seconds: float = Field(
        default=0.0,
        description="Test duration in seconds",
    )
