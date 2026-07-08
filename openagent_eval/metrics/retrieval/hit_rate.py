"""Hit Rate metric.

Measures whether at least one relevant context appears in the retrieved results.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class HitRate(BaseMetric):
    """Binary metric: 1 if any retrieved context matches ground truth.

    Hit Rate = 1 if intersection(retrieved, ground_truth) > 0, else 0.

    This is a binary metric per query, typically averaged across queries.
    """

    name = "hit_rate"
    description = "Binary metric: 1 if any retrieved context matches ground truth"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate Hit Rate.

        Args:
            retrieved_contexts: List of retrieved context strings.
            ground_truth_contexts: List of ground truth context strings.

        Returns:
            MetricResult with binary score.
        """
        retrieved = kwargs.get("retrieved_contexts", [])
        ground_truth = kwargs.get("ground_truth_contexts", [])

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth contexts provided",
                metadata={"hit": False},
            )

        if not retrieved:
            return MetricResult(
                score=0.0,
                reason="No contexts retrieved",
                metadata={"hit": False},
            )

        retrieved_set = set(retrieved)
        hit = any(ctx in retrieved_set for ctx in ground_truth)
        score = 1.0 if hit else 0.0

        return MetricResult(
            score=score,
            reason=f"{'Hit' if hit else 'Miss'} - {'found' if hit else 'no'} matching context",
            metadata={"hit": hit},
        )
