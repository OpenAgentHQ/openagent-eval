"""Normalized Discounted Cumulative Gain (NDCG) metric.

Measures ranking quality of retrieved contexts.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.metrics.retrieval._normalize import normalize_context


def _dcg(relevances: list[int], k: int) -> float:
    """Compute Discounted Cumulative Gain.

    Args:
        relevances: List of relevance scores (1 for relevant, 0 for not).
        k: Number of positions to consider.

    Returns:
        DCG score.
    """
    relevances = relevances[:k]
    # Standard DCG discount: log2(rank + 1) with 1-indexed rank. With a
    # 0-indexed enumerate() that is log2(i + 2), which gives log2(2) = 1.0 at
    # rank 1 (no special case needed) and a strictly increasing discount for
    # every later position.
    return sum(rel / _log2(i + 2) for i, rel in enumerate(relevances))


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
        retrieved = [normalize_context(c) for c in kwargs.get("retrieved_contexts", [])]
        ground_truth = [normalize_context(c) for c in kwargs.get("ground_truth_contexts", [])]
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

        # Ideal ranking: place every relevant (ground-truth) document first,
        # capped at k. This must be derived from the total number of relevant
        # documents, NOT from what happened to be retrieved — otherwise NDCG is
        # overstated whenever retrieval misses relevant ground-truth docs.
        num_relevant = len(ground_truth_set)
        ideal_relevances = [1] * min(num_relevant, k) + [0] * max(
            0, k - min(num_relevant, k)
        )

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
