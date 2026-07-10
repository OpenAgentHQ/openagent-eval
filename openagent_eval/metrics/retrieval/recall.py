"""Context Recall metric.

Measures the proportion of ground truth contexts that were successfully retrieved.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.metrics.retrieval._normalize import normalize_context


class ContextRecall(BaseMetric):
    """Measures recall of ground truth contexts in retrieval.

    Context Recall = |retrieved contexts matching ground truth| / |total ground truth contexts|

    A score of 1.0 means all ground truth contexts were retrieved.
    """

    name = "context_recall"
    description = "Proportion of ground truth contexts that were retrieved"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate context recall.

        Args:
            retrieved_contexts: List of retrieved context strings.
            ground_truth_contexts: List of ground truth context strings.

        Returns:
            MetricResult with recall score.
        """
        retrieved = [normalize_context(c) for c in kwargs.get("retrieved_contexts", [])]
        ground_truth = [normalize_context(c) for c in kwargs.get("ground_truth_contexts", [])]

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth contexts provided",
                metadata={"ground_truth_count": 0, "retrieved_count": 0},
            )

        if not retrieved:
            return MetricResult(
                score=0.0,
                reason="No contexts retrieved",
                metadata={
                    "ground_truth_count": len(ground_truth),
                    "retrieved_count": 0,
                },
            )

        retrieved_set = set(retrieved)
        matched_count = sum(1 for ctx in ground_truth if ctx in retrieved_set)
        score = matched_count / len(ground_truth)

        return MetricResult(
            score=score,
            reason=f"{matched_count}/{len(ground_truth)} ground truth contexts retrieved",
            metadata={
                "ground_truth_count": len(ground_truth),
                "retrieved_count": matched_count,
            },
        )
