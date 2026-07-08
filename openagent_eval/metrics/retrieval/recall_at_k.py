"""Recall@K metric.

Measures whether at least one relevant context appears in the top-K retrieved results.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class RecallAtK(BaseMetric):
    """Measures if relevant context is in top-K results.

    Recall@K = 1 if any ground truth context is in top-K, else 0.

    This is a binary metric per query, typically averaged across queries.
    """

    name = "recall_at_k"
    description = "Binary metric: 1 if any ground truth context is in top-K results"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate Recall@K.

        Args:
            retrieved_contexts: List of retrieved context strings (top-K).
            ground_truth_contexts: List of ground truth context strings.
            k: The K value (optional, defaults to len(retrieved_contexts)).

        Returns:
            MetricResult with binary score.
        """
        retrieved = kwargs.get("retrieved_contexts", [])
        ground_truth = kwargs.get("ground_truth_contexts", [])
        k = kwargs.get("k", len(retrieved))

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth contexts provided",
                metadata={"k": k, "found": False},
            )

        top_k = retrieved[:k]
        retrieved_set = set(top_k)
        found = any(ctx in retrieved_set for ctx in ground_truth)
        score = 1.0 if found else 0.0

        return MetricResult(
            score=score,
            reason=f"{'Found' if found else 'Not found'} relevant context in top-{k}",
            metadata={"k": k, "found": found},
        )
