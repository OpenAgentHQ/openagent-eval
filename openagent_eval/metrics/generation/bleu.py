"""BLEU metric.

Measures n-gram overlap between answer and ground truth using BLEU score.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class BLEU(BaseMetric):
    """BLEU score for answer quality evaluation.

    Uses HuggingFace evaluate library when available, falls back to simple n-gram.
    """

    name = "bleu"
    description = "BLEU score measuring n-gram overlap with ground truth"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate BLEU score.

        Args:
            answer: The generated answer.
            ground_truth: The expected correct answer.

        Returns:
            MetricResult with BLEU score.
        """
        answer = kwargs.get("answer", "")
        ground_truth = kwargs.get("ground_truth", "")

        if not answer or not ground_truth:
            return MetricResult(
                score=0.0,
                reason="Missing answer or ground truth",
                metadata={"method": "evaluate"},
            )

        try:
            return self._evaluate_with_hf(answer, ground_truth)
        except ImportError:
            pass

        # Fallback: simple unigram overlap
        return self._evaluate_simple(answer, ground_truth)

    def _evaluate_with_hf(self, answer: str, ground_truth: str) -> MetricResult:
        """Evaluate using HuggingFace evaluate library."""
        import evaluate

        bleu = evaluate.load("bleu")
        result = bleu.compute(
            predictions=[answer],
            references=[[ground_truth]],
        )
        score = result["bleu"]

        return MetricResult(
            score=score,
            reason=f"BLEU score: {score:.4f}",
            metadata={"method": "evaluate"},
        )

    def _evaluate_simple(self, answer: str, ground_truth: str) -> MetricResult:
        """Simple unigram BLEU fallback."""
        answer_words = answer.lower().split()
        truth_words = ground_truth.lower().split()

        if not answer_words:
            return MetricResult(
                score=0.0,
                reason="Empty answer",
                metadata={"method": "simple_unigram"},
            )

        # Simple unigram precision
        truth_word_counts = {}
        for word in truth_words:
            truth_word_counts[word] = truth_word_counts.get(word, 0) + 1

        matches = 0
        for word in answer_words:
            if truth_word_counts.get(word, 0) > 0:
                matches += 1
                truth_word_counts[word] -= 1

        precision = matches / len(answer_words) if answer_words else 0.0

        # Brevity penalty
        bp = min(1.0, len(answer_words) / len(truth_words)) if truth_words else 0.0
        score = bp * precision

        return MetricResult(
            score=score,
            reason=f"Simple BLEU: {score:.4f}",
            metadata={"method": "simple_unigram", "precision": precision, "bp": bp},
        )
