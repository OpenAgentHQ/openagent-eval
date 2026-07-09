"""Shared score-normalization helpers for retriever adapters.

Different vector stores and lexical search engines report relevance in
incompatible scales (cosine distance, L2 distance, inner product, raw BM25
scores, Elasticsearch scores). Every :class:`~openagent_eval.providers.models.Document`
expects ``score`` to be in the ``[0.0, 1.0]`` range (higher = more relevant),
so all retrievers funnel their raw scores through the helpers here.
"""

from __future__ import annotations

from typing import Sequence


def normalize_distance(distance: float, space: str = "cosine") -> float:
    """Normalize a raw distance/similarity into ``[0.0, 1.0]`` (higher = better).

    Args:
        distance: Raw value returned by the backend.
        space: One of ``"cosine"``, ``"l2"``, ``"ip"``/``"dot"``, or
            ``"similarity"`` (already in ``[0, 1]`` and left unchanged).

    Returns:
        A score clamped to ``[0.0, 1.0]`` where 1.0 is most relevant.
    """
    if space in ("similarity", "score"):
        return _clamp(distance)

    if space == "cosine":
        # Chroma/Weaviate cosine distance lives in [0, 2]; map to [0, 1].
        return _clamp(distance / 2.0)

    if space in ("l2", "euclidean"):
        # L2 distance is unbounded and non-negative; clamp directly.
        return _clamp(distance)

    if space in ("ip", "dot", "inner_product"):
        # Inner product can be negative or > 1; clamp directly.
        return _clamp(distance)

    # Unknown space: treat as a raw distance and clamp.
    return _clamp(distance)


def minmax_normalize(scores: Sequence[float]) -> list[float]:
    """Min-max scale a list of raw scores into ``[0.0, 1.0]``.

    Useful for unbounded lexical scores (BM25, Elasticsearch ``_score``).
    A constant list maps to ``1.0`` for every element (perfectly relevant
    relative to itself) to avoid a divide-by-zero.

    Args:
        scores: Raw relevance scores (any scale, any sign).

    Returns:
        Scores scaled into ``[0.0, 1.0]``.
    """
    if not scores:
        return []
    lo = min(scores)
    hi = max(scores)
    if hi == lo:
        return [1.0 for _ in scores]
    return [_clamp((s - lo) / (hi - lo)) for s in scores]


def rank_based_normalize(n: int) -> list[float]:
    """Return normalized scores for the top-``n`` ranked results.

    Rank 1 (most relevant) maps to ``1.0``; rank ``n`` maps to ``1/n``. This
    gives a monotonic, bounded score for engines that only return an ordering
    (no numeric score).

    Args:
        n: Number of ranked results.

    Returns:
        List of ``n`` scores in ``(0.0, 1.0]`` ordered best-first.
    """
    if n <= 0:
        return []
    return [_clamp(1.0 - (i / n)) for i in range(n)]


def _clamp(value: float) -> float:
    """Clamp a float into the ``[0.0, 1.0]`` range."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)
