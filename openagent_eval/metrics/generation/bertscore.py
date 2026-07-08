"""BERTScore metric.

Measures semantic similarity using BERT embeddings.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class BERTScore(BaseMetric):
    """BERTScore for semantic answer quality evaluation.

    Uses the bert-score library when available, falls back to
    sentence-transformers cosine similarity.
    """

    name = "bertscore"
    description = "BERTScore measuring semantic similarity with ground truth"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate BERTScore.

        Args:
            answer: The generated answer.
            ground_truth: The expected correct answer.

        Returns:
            MetricResult with BERTScore (F1).
        """
        answer = kwargs.get("answer", "")
        ground_truth = kwargs.get("ground_truth", "")

        if not answer or not ground_truth:
            return MetricResult(
                score=0.0,
                reason="Missing answer or ground truth",
                metadata={"method": "bert_score"},
            )

        try:
            return self._evaluate_with_bertscore(answer, ground_truth)
        except ImportError:
            pass

        # Fallback: sentence-transformers
        try:
            return self._evaluate_with_transformers(answer, ground_truth)
        except ImportError:
            pass

        # Fallback: word overlap (no ML dependencies)
        return self._evaluate_simple(answer, ground_truth)

    def _evaluate_simple(self, answer: str, ground_truth: str) -> MetricResult:
        """Simple word overlap fallback when ML libraries are unavailable."""
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
            reason=f"Jaccard similarity (fallback): {score:.4f}",
            metadata={"method": "word_overlap"},
        )

    def _evaluate_with_bertscore(
        self, answer: str, ground_truth: str
    ) -> MetricResult:
        """Evaluate using bert-score library."""
        from bert_score import score as bert_score

        precision, recall, f1 = bert_score(
            [answer], [ground_truth], lang="en", verbose=False
        )

        return MetricResult(
            score=f1.item(),
            reason=f"BERTScore F1: {f1.item():.4f}",
            metadata={
                "method": "bert_score",
                "precision": precision.item(),
                "recall": recall.item(),
            },
        )

    def _evaluate_with_transformers(
        self, answer: str, ground_truth: str
    ) -> MetricResult:
        """Fallback using sentence-transformers."""
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode([answer, ground_truth])
        similarity = cosine_similarity(
            embeddings[0].reshape(1, -1),
            embeddings[1].reshape(1, -1),
        )[0][0]

        return MetricResult(
            score=float(similarity),
            reason=f"Cosine similarity (fallback): {similarity:.4f}",
            metadata={"method": "sentence_transformers_fallback"},
        )
