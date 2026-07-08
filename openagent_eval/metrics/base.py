"""Base metric interface and MetricResult data model.

This module defines the abstract BaseMetric interface that all evaluation metrics
must implement, along with the MetricResult dataclass used to return evaluation
results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MetricResult:
    """Result of a metric evaluation.

    Attributes:
        score: The metric score (typically 0.0 to 1.0).
        reason: Human-readable explanation of the score.
        metadata: Additional context about the evaluation.
    """

    score: float
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate score is within reasonable bounds."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"Score must be between 0.0 and 1.0, got {self.score}"
            )


class BaseMetric(ABC):
    """Abstract base class for all evaluation metrics.

    Every metric in OpenAgent Eval must implement this interface. The metric
    receives evaluation data and returns a MetricResult with a score, reason,
    and optional metadata.

    Example:
        ```python
        class MyMetric(BaseMetric):
            name = "my_metric"
            description = "A custom metric"

            def evaluate(self, **kwargs) -> MetricResult:
                score = compute_score(kwargs)
                return MetricResult(score=score, reason="Computed score")
        ```
    """

    name: str
    description: str

    @abstractmethod
    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate the metric and return a result.

        Args:
            **kwargs: Metric-specific evaluation data.

        Returns:
            MetricResult with score, reason, and metadata.

        Raises:
            MetricExecutionError: If evaluation fails.
            MetricTimeoutError: If evaluation times out.
        """
        ...

    def validate_inputs(self, **kwargs: Any) -> None:
        """Validate metric inputs before evaluation.

        Override this method to add custom input validation.

        Args:
            **kwargs: Inputs to validate.

        Raises:
            ValueError: If inputs are invalid.
        """
