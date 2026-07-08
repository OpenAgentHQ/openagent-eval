"""Faithfulness metric.

Measures whether the generated answer is grounded in the provided contexts.
Uses Ragas faithfulness score when available, falls back to simple overlap.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class Faithfulness(BaseMetric):
    """Measures faithfulness of answer to provided contexts.

    Faithfulness = |claims supported by context| / |total claims|

    A score of 1.0 means all claims in the answer are supported by contexts.
    """

    name = "faithfulness"
    description = "Whether the answer is grounded in the provided contexts"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate faithfulness.

        Args:
            answer: The generated answer.
            contexts: List of context strings used for generation.

        Returns:
            MetricResult with faithfulness score.
        """
        answer = kwargs.get("answer", "")
        contexts = kwargs.get("contexts", [])

        if not answer:
            return MetricResult(
                score=0.0,
                reason="No answer provided",
                metadata={"claims_total": 0, "claims_supported": 0},
            )

        if not contexts:
            return MetricResult(
                score=0.0,
                reason="No contexts provided for faithfulness check",
                metadata={"claims_total": 0, "claims_supported": 0},
            )

        # Try Ragas if available
        try:
            return self._evaluate_with_ragas(answer, contexts)
        except ImportError:
            pass

        # Fallback: simple word overlap
        return self._evaluate_simple(answer, contexts)

    def _evaluate_with_ragas(
        self, answer: str, contexts: list[str]
    ) -> MetricResult:
        """Evaluate using Ragas faithfulness."""
        from ragas.metrics import faithfulness as ragas_faithfulness
        from datasets import Dataset

        data = {
            "question": [""],
            "answer": [answer],
            "contexts": [contexts],
            "ground_truth": [""],
        }
        dataset = Dataset.from_dict(data)
        result = ragas_faithfulness.evaluate(dataset)
        score = result["faithfulness"]

        return MetricResult(
            score=score,
            reason=f"Ragas faithfulness: {score:.4f}",
            metadata={"method": "ragas"},
        )

    def _evaluate_simple(
        self, answer: str, contexts: list[str]
    ) -> MetricResult:
        """Simple word overlap fallback."""
        answer_words = set(answer.lower().split())
        context_text = " ".join(contexts).lower()
        context_words = set(context_text.split())

        if not answer_words:
            return MetricResult(
                score=0.0,
                reason="Empty answer",
                metadata={"method": "simple_overlap"},
            )

        overlap = answer_words & context_words
        score = len(overlap) / len(answer_words)

        return MetricResult(
            score=min(score, 1.0),
            reason=f"Word overlap: {len(overlap)}/{len(answer_words)} words found in context",
            metadata={
                "method": "simple_overlap",
                "overlap_words": len(overlap),
                "total_words": len(answer_words),
            },
        )
