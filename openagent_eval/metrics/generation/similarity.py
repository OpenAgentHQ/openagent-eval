"""Semantic Similarity metric.

Measures semantic similarity between answer and ground truth using embeddings.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class SemanticSimilarity(BaseMetric):
    """Measures semantic similarity using sentence embeddings.

    Uses sentence-transformers to compute cosine similarity between
    answer and ground truth embeddings.

    A score of 1.0 means semantically identical.
    """

    name = "semantic_similarity"
    description = "Semantic similarity between answer and ground truth using embeddings"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate semantic similarity.

        Args:
            answer: The generated answer.
            ground_truth: The expected correct answer.

        Returns:
            MetricResult with similarity score.
        """
        answer = kwargs.get("answer", "")
        ground_truth = kwargs.get("ground_truth", "")

        if not answer or not ground_truth:
            return MetricResult(
                score=0.0,
                reason="Missing answer or ground truth",
                metadata={"method": "sentence_transformers"},
            )

        try:
            return self._evaluate_with_transformers(answer, ground_truth)
        except ImportError:
            pass

        # Fallback: word overlap
        return self._evaluate_simple(answer, ground_truth)

    @property
    def _transformer(self):
        """Lazily load and cache the SentenceTransformer model (heavy load)."""
        if getattr(self, "_cached_model", None) is None:
            from sentence_transformers import SentenceTransformer

            self._cached_model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._cached_model

    def _evaluate_with_transformers(
        self, answer: str, ground_truth: str
    ) -> MetricResult:
        """Evaluate using sentence-transformers."""
        from sklearn.metrics.pairwise import cosine_similarity

        model = self._transformer
        embeddings = model.encode([answer, ground_truth])
        similarity = cosine_similarity(
            embeddings[0].reshape(1, -1),
            embeddings[1].reshape(1, -1),
        )[0][0]

        # Cosine similarity lives in [-1, 1]; rescale to [0, 1] and clamp so it
        # satisfies MetricResult's 0..1 contract (otherwise a negative cosine
        # for dissimilar texts would raise ValueError).
        score = max(0.0, min(1.0, (float(similarity) + 1.0) / 2.0))

        return MetricResult(
            score=score,
            reason=f"Cosine similarity: {similarity:.4f}",
            metadata={"method": "sentence_transformers"},
        )

    def _evaluate_simple(self, answer: str, ground_truth: str) -> MetricResult:
        """Simple word overlap fallback."""
        answer_words = set(answer.lower().split())
        truth_words = set(ground_truth.lower().split())

        if not answer_words or not truth_words:
            return MetricResult(
                score=0.0,
                reason="Empty answer or ground truth",
                metadata={"method": "word_overlap"},
            )

        intersection = answer_words & truth_words
        union = answer_words | truth_words
        score = len(intersection) / len(union) if union else 0.0

        return MetricResult(
            score=score,
            reason=f"Jaccard similarity: {score:.4f}",
            metadata={"method": "word_overlap"},
        )
