"""Exact Match metric.

Measures whether the generated answer exactly matches the ground truth.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class ExactMatch(BaseMetric):
    """Binary metric: 1 if answer exactly matches ground truth.

    Comparison is case-insensitive and whitespace-normalized.
    """

    name = "exact_match"
    description = "Binary metric: 1 if answer exactly matches ground truth"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate exact match.

        Args:
            answer: The generated answer.
            ground_truth: The expected correct answer.

        Returns:
            MetricResult with binary score.
        """
        answer = kwargs.get("answer", "")
        ground_truth = kwargs.get("ground_truth", "")

        if not ground_truth:
            return MetricResult(
                score=0.0,
                reason="No ground truth provided",
                metadata={"match": False},
            )

        normalized_answer = answer.strip().lower()
        normalized_truth = ground_truth.strip().lower()
        match = normalized_answer == normalized_truth
        score = 1.0 if match else 0.0

        return MetricResult(
            score=score,
            reason=f"{'Exact match' if match else 'No match'}",
            metadata={"match": match},
        )
