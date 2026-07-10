"""Context Precision metric.

Measures the proportion of retrieved contexts that are relevant to the ground truth.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.metrics.retrieval._normalize import normalize_context


class ContextPrecision(BaseMetric):
    """Measures precision of retrieved contexts against ground truth.

    Context Precision = |relevant contexts in retrieval| / |total retrieved contexts|

    A score of 1.0 means all retrieved contexts are relevant.
    """

    name = "context_precision"
    description = "Proportion of retrieved contexts that are relevant to ground truth"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate context precision.

        Args:
            retrieved_contexts: List of retrieved context strings.
            ground_truth_contexts: List of ground truth context strings.

        Returns:
            MetricResult with precision score.
        """
        retrieved = [normalize_context(c) for c in kwargs.get("retrieved_contexts", [])]
        ground_truth = [normalize_context(c) for c in kwargs.get("ground_truth_contexts", [])]

        if not retrieved:
            return MetricResult(
                score=0.0,
                reason="No contexts retrieved",
                metadata={"retrieved_count": 0, "relevant_count": 0},
            )

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth contexts provided",
                metadata={"retrieved_count": len(retrieved), "relevant_count": 0},
            )

        ground_truth_set = set(ground_truth)
        relevant_count = sum(
            1 for ctx in retrieved if ctx in ground_truth_set
        )
        score = relevant_count / len(retrieved)

        return MetricResult(
            score=score,
            reason=f"{relevant_count}/{len(retrieved)} contexts are relevant",
            metadata={
                "retrieved_count": len(retrieved),
                "relevant_count": relevant_count,
            },
        )
