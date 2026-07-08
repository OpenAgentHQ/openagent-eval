"""F1 Score metric.

Measures word-level F1 score between answer and ground truth.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class F1Score(BaseMetric):
    """Word-level F1 score between answer and ground truth.

    F1 = 2 * (precision * recall) / (precision + recall)

    Where:
    - precision = |common words| / |answer words|
    - recall = |common words| / |ground truth words|
    """

    name = "f1_score"
    description = "Word-level F1 score between answer and ground truth"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate F1 score.

        Args:
            answer: The generated answer.
            ground_truth: The expected correct answer.

        Returns:
            MetricResult with F1 score.
        """
        answer = kwargs.get("answer", "")
        ground_truth = kwargs.get("ground_truth", "")

        if not answer and not ground_truth:
            return MetricResult(
                score=1.0,
                reason="Both empty - trivial match",
                metadata={"precision": 1.0, "recall": 1.0},
            )

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth provided",
                metadata={"precision": 0.0, "recall": 0.0},
            )

        answer_words = set(answer.lower().split())
        truth_words = set(ground_truth.lower().split())

        if not answer_words and not truth_words:
            return MetricResult(
                score=1.0,
                reason="Both empty after normalization",
                metadata={"precision": 1.0, "recall": 1.0},
            )

        common = answer_words & truth_words

        precision = len(common) / len(answer_words) if answer_words else 0.0
        recall = len(common) / len(truth_words) if truth_words else 0.0

        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)

        return MetricResult(
            score=f1,
            reason=f"F1={f1:.4f} (P={precision:.4f}, R={recall:.4f})",
            metadata={"precision": precision, "recall": recall},
        )
