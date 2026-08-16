"""ROUGE metric.

Measures overlap between answer and ground truth using ROUGE scores.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class ROUGE(BaseMetric):
    """ROUGE score for answer quality evaluation.

    Uses HuggingFace evaluate library when available, falls back to simple recall.
    """

    name = "rouge"
    description = "ROUGE score measuring overlap with ground truth"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate ROUGE score.

        Args:
            answer: The generated answer.
            ground_truth: The expected correct answer.

        Returns:
            MetricResult with ROUGE score (uses rouge1 by default).
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

        # Fallback: simple unigram recall
        return self._evaluate_simple(answer, ground_truth)

    def _evaluate_with_hf(self, answer: str, ground_truth: str) -> MetricResult:
        """Evaluate using HuggingFace evaluate library."""
        import evaluate

        rouge = evaluate.load("rouge")
        result = rouge.compute(
            predictions=[answer],
            references=[ground_truth],
        )
        score = result["rouge1"]

        return MetricResult(
            score=score,
            reason=f"ROUGE-1 score: {score:.4f}",
            metadata={"method": "evaluate", "rouge1": score},
        )

    def _evaluate_simple(self, answer: str, ground_truth: str) -> MetricResult:
        """Simple unigram recall fallback over word occurrences.

        Overlap is counted per occurrence (not per word type), so a term
        repeated in the reference contributes to the recall denominator
        each time it appears.
        """
        answer_words = answer.lower().split()
        truth_words = ground_truth.lower().split()

        if not truth_words:
            return MetricResult(
                score=0.0,
                reason="Empty ground truth",
                metadata={"method": "simple_recall"},
            )

        answer_counts = Counter(answer_words)
        truth_counts = Counter(truth_words)
        overlap = sum((answer_counts & truth_counts).values())
        recall = overlap / sum(truth_counts.values())

        return MetricResult(
            score=recall,
            reason=f"Simple ROUGE recall: {recall:.4f}",
            metadata={"method": "simple_recall", "overlap": overlap},
        )
