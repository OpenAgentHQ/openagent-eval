"""Latency metric.

Tracks and scores latency of evaluation pipeline stages.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class LatencyMetric(BaseMetric):
    """Measures latency of pipeline stages.

    Tracks embedding, retrieval, and LLM latency. Score is normalized
    against a configurable threshold (default 1000ms = score 0.5).

    Score = max(0, 1 - (latency_ms / (2 * threshold_ms)))
    """

    name = "latency"
    description = "Latency measurement for pipeline stages"

    def __init__(self, threshold_ms: float = 1000.0) -> None:
        """Initialize latency metric.

        Args:
            threshold_ms: Reference latency in ms (score 0.5 at this value).
        """
        self.threshold_ms = threshold_ms

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate latency.

        Args:
            latency_ms: Latency in milliseconds.
            stage: Pipeline stage name (e.g., "embedding", "retrieval", "llm").

        Returns:
            MetricResult with latency score.
        """
        latency_ms = kwargs.get("latency_ms", 0.0)
        stage = kwargs.get("stage", "unknown")

        if latency_ms < 0:
            return MetricResult(
                score=0.0,
                reason=f"Invalid latency: {latency_ms}ms",
                metadata={"stage": stage, "latency_ms": latency_ms},
            )

        # Score: 1.0 at 0ms, 0.5 at threshold, 0.0 at 2*threshold
        score = max(0.0, 1.0 - (latency_ms / (2 * self.threshold_ms)))

        return MetricResult(
            score=score,
            reason=f"{stage} latency: {latency_ms:.1f}ms",
            metadata={
                "stage": stage,
                "latency_ms": latency_ms,
                "threshold_ms": self.threshold_ms,
            },
        )
