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
from openagent_eval.metrics.retrieval._normalize import normalize_context


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
        retrieved = [normalize_context(c) for c in kwargs.get("retrieved_contexts", [])]
        ground_truth = [normalize_context(c) for c in kwargs.get("ground_truth_contexts", [])]
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

        if k <= 0:
            return MetricResult(
                score=0.0,
                reason=f"K is {k} (no contexts considered)",
                metadata={"k": k, "relevant_total": len(ground_truth), "relevant_in_top_k": 0},
            )

        top_k = retrieved[:k]
        retrieved_set = set(top_k)
        # Count only *distinct* relevant contexts found, so duplicate gold
        # entries do not inflate the numerator above the denominator.
        relevant_in_top_k = len(set(ground_truth) & retrieved_set)
        # Denominator is the number of *distinct* relevant contexts, so duplicate
        # gold entries cannot make a perfect recall impossible.
        num_relevant = len(set(ground_truth))
        score = relevant_in_top_k / num_relevant if num_relevant else 0.0

        return MetricResult(
            score=score,
            reason=f"{relevant_in_top_k}/{num_relevant} relevant contexts in top-{k}",
            metadata={
                "k": k,
                "relevant_total": num_relevant,
                "relevant_in_top_k": relevant_in_top_k,
            },
        )
