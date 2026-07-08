"""Normalized Discounted Cumulative Gain (NDCG) metric.

Measures ranking quality of retrieved contexts.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


def _dcg(relevances: list[int], k: int) -> float:
    """Compute Discounted Cumulative Gain.

    Args:
        relevances: List of relevance scores (1 for relevant, 0 for not).
        k: Number of positions to consider.

    Returns:
        DCG score.
    """
    relevances = relevances[:k]
    return sum(
        rel / (1.0 if i == 0 else _log2(i + 1))
        for i, rel in enumerate(relevances)
    )


def _log2(x: float) -> float:
    """Compute log base 2."""
    import math
    return math.log2(x) if x > 0 else 0.0


def _ndcg(relevances: list[int], ideal_relevances: list[int], k: int) -> float:
    """Compute Normalized Discounted Cumulative Gain.

    Args:
        relevances: Actual relevance scores.
        ideal_relevances: Ideal relevance scores (sorted descending).
        k: Number of positions to consider.

    Returns:
        NDCG score.
    """
    dcg = _dcg(relevances, k)
    ideal_dcg = _dcg(ideal_relevances, k)

    if ideal_dcg == 0:
        return 0.0

    return dcg / ideal_dcg


class NDCG(BaseMetric):
    """Normalized Discounted Cumulative Gain for retrieval ranking.

    NDCG measures how well the retrieved contexts are ranked compared to
    the ideal ranking. A score of 1.0 means perfect ranking.

    The metric considers:
    - Position of relevant contexts (earlier is better)
    - Number of relevant contexts
    - Comparison to ideal ranking
    """

    name = "ndcg"
    description = "Normalized Discounted Cumulative Gain for retrieval ranking quality"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate NDCG.

        Args:
            retrieved_contexts: List of retrieved context strings (ordered).
            ground_truth_contexts: List of ground truth context strings.
            k: Number of positions to evaluate (optional).

        Returns:
            MetricResult with NDCG score.
        """
        retrieved = kwargs.get("retrieved_contexts", [])
        ground_truth = kwargs.get("ground_truth_contexts", [])
        k = kwargs.get("k", len(retrieved))

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth contexts provided",
                metadata={"k": k},
            )

        if not retrieved:
            return MetricResult(
                score=0.0,
                reason="No contexts retrieved",
                metadata={"k": k},
            )

        ground_truth_set = set(ground_truth)
        relevances = [
            1 if ctx in ground_truth_set else 0
            for ctx in retrieved[:k]
        ]

        # Ideal: all relevant contexts first
        ideal_relevances = sorted(relevances, reverse=True)
        # Pad with 1s if we have more ground truth than retrieved
        ideal_relevances.extend(
            [1] * (min(len(ground_truth), k) - len(ideal_relevances))
        )
        ideal_relevances = ideal_relevances[:k]

        score = _ndcg(relevances, ideal_relevances, k)
        relevant_count = sum(relevances)

        return MetricResult(
            score=score,
            reason=f"NDCG@{k} = {score:.4f} ({relevant_count} relevant in top-{k})",
            metadata={
                "k": k,
                "relevant_in_top_k": relevant_count,
                "dcg": _dcg(relevances, k),
            },
        )
