"""Precision@K metric.

Measures the proportion of top-K retrieved contexts that are relevant.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.metrics.retrieval._normalize import normalize_context


class PrecisionAtK(BaseMetric):
    """Measures precision of top-K retrieved contexts.

    Precision@K = |relevant contexts in top-K| / K

    A score of 1.0 means all top-K contexts are relevant.
    """

    name = "precision_at_k"
    description = "Proportion of top-K retrieved contexts that are relevant"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate Precision@K.

        Args:
            retrieved_contexts: List of retrieved context strings.
            ground_truth_contexts: List of ground truth context strings.
            k: The K value (optional, defaults to len(retrieved_contexts)).

        Returns:
            MetricResult with precision score.
        """
        retrieved = [normalize_context(c) for c in kwargs.get("retrieved_contexts", [])]
        ground_truth = [normalize_context(c) for c in kwargs.get("ground_truth_contexts", [])]
        k = kwargs.get("k", len(retrieved))

        if k == 0:
            return MetricResult(
                score=0.0,
                reason="K is 0",
                metadata={"k": 0, "relevant_in_top_k": 0},
            )

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth contexts provided",
                metadata={"k": k, "relevant_in_top_k": 0},
            )

        top_k = retrieved[:k]
        ground_truth_set = set(ground_truth)
        relevant_in_top_k = sum(1 for ctx in top_k if ctx in ground_truth_set)
        score = relevant_in_top_k / k

        return MetricResult(
            score=score,
            reason=f"{relevant_in_top_k}/{k} top contexts are relevant",
            metadata={"k": k, "relevant_in_top_k": relevant_in_top_k},
        )
