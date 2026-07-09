"""Recall@K metric.

Measures the fraction of relevant (ground-truth) contexts that appear in the
top-K retrieved results.

Recall@K = |relevant contexts ∩ top-K retrieved| / |relevant contexts|

Unlike Hit Rate (which is binary), Recall@K reflects how much of the relevant
set was recovered. A score of 1.0 means every relevant context is in the top-K.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class RecallAtK(BaseMetric):
    """Fraction of relevant contexts found within the top-K retrieved results."""

    name = "recall_at_k"
    description = "Fraction of relevant contexts recovered in the top-K retrieved results"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate Recall@K.

        Args:
            retrieved_contexts: List of retrieved context strings (ordered).
            ground_truth_contexts: List of ground truth (relevant) context strings.
            k: The K value (optional, defaults to len(retrieved_contexts)).

        Returns:
            MetricResult with the recall@k score in [0, 1].
        """
        retrieved = kwargs.get("retrieved_contexts", [])
        ground_truth = kwargs.get("ground_truth_contexts", [])
        k = kwargs.get("k", len(retrieved))

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth contexts provided",
                metadata={"k": k, "relevant_total": 0, "relevant_in_top_k": 0},
            )

        if not retrieved:
            return MetricResult(
                score=0.0,
                reason="No contexts retrieved",
                metadata={"k": k, "relevant_total": len(ground_truth), "relevant_in_top_k": 0},
            )

        top_k = retrieved[:k]
        retrieved_set = set(top_k)
        relevant_in_top_k = sum(1 for ctx in ground_truth if ctx in retrieved_set)
        score = relevant_in_top_k / len(ground_truth)

        return MetricResult(
            score=score,
            reason=f"{relevant_in_top_k}/{len(ground_truth)} relevant contexts in top-{k}",
            metadata={
                "k": k,
                "relevant_total": len(ground_truth),
                "relevant_in_top_k": relevant_in_top_k,
            },
        )
