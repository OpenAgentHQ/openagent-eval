"""Mean Reciprocal Rank (MRR) metric.

Measures the reciprocal rank of the first relevant context in the retrieved results.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class MRR(BaseMetric):
    """Mean Reciprocal Rank - reciprocal rank of first relevant result.

    MRR = 1 / rank_of_first_relevant_context

    A score of 1.0 means the first retrieved context is relevant.
    A score of 0.5 means the second retrieved context is relevant.
    """

    name = "mrr"
    description = "Reciprocal rank of the first relevant context in retrieval"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate MRR.

        Args:
            retrieved_contexts: List of retrieved context strings (ordered by relevance).
            ground_truth_contexts: List of ground truth context strings.

        Returns:
            MetricResult with MRR score.
        """
        retrieved = kwargs.get("retrieved_contexts", [])
        ground_truth = kwargs.get("ground_truth_contexts", [])

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth contexts provided",
                metadata={"first_relevant_rank": None},
            )

        if not retrieved:
            return MetricResult(
                score=0.0,
                reason="No contexts retrieved",
                metadata={"first_relevant_rank": None},
            )

        ground_truth_set = set(ground_truth)
        for rank, ctx in enumerate(retrieved, start=1):
            if ctx in ground_truth_set:
                score = 1.0 / rank
                return MetricResult(
                    score=score,
                    reason=f"First relevant context at rank {rank}",
                    metadata={"first_relevant_rank": rank},
                )

        return MetricResult(
            score=0.0,
            reason="No relevant context found in retrieval",
            metadata={"first_relevant_rank": None},
        )
