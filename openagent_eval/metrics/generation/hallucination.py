"""Hallucination Detection metric.

Measures whether the generated answer contains information not present in the contexts.
Uses DeepEval hallucination metric when available, falls back to simple detection.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


class HallucinationDetection(BaseMetric):
    """Detects hallucinated content in generated answers.

    Hallucination Rate = |hallucinated claims| / |total claims|

    A score of 0.0 means no hallucination detected (lower is better).
    A score of 1.0 means all content is hallucinated.
    """

    name = "hallucination"
    description = "Detects information in the answer not present in contexts"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate hallucination.

        Args:
            answer: The generated answer.
            contexts: List of context strings.

        Returns:
            MetricResult with hallucination score (0=no hallucination, 1=all hallucinated).
        """
        answer = kwargs.get("answer", "")
        contexts = kwargs.get("contexts", [])

        if not answer:
            return MetricResult(
                score=0.0,
                reason="No answer to evaluate",
                metadata={"method": "word_coverage"},
            )

        if not contexts:
            return MetricResult(
                score=1.0,
                reason="No contexts provided - cannot verify",
                metadata={"method": "word_coverage"},
            )

        # Try DeepEval if available
        try:
            return self._evaluate_with_deepeval(answer, contexts)
        except (ImportError, Exception) as e:
            # DeepEval may fail if API key is not configured
            pass

        # Fallback: word coverage
        return self._evaluate_simple(answer, contexts)

    def _evaluate_with_deepeval(
        self, answer: str, contexts: list[str]
    ) -> MetricResult:
        """Evaluate using DeepEval hallucination metric."""
        from deepeval.metrics import HallucinationMetric
        from deepeval.test_case import LLMTestCase

        # Build context string for the input field
        context_text = "\n".join(contexts) if contexts else ""

        test_case = LLMTestCase(
            input=context_text,
            actual_output=answer,
            retrieval_context=contexts,
        )
        metric = HallucinationMetric(threshold=0.5)
        metric.measure(test_case)
        score = metric.score

        # Invert so 0 = no hallucination, 1 = all hallucinated
        hallucination_score = 1.0 - score

        return MetricResult(
            score=hallucination_score,
            reason=f"DeepEval hallucination: {hallucination_score:.4f}",
            metadata={"method": "deepeval"},
        )

    def _evaluate_simple(
        self, answer: str, contexts: list[str]
    ) -> MetricResult:
        """Simple word coverage fallback."""
        answer_words = set(answer.lower().split())
        context_text = " ".join(contexts).lower()
        context_words = set(context_text.split())

        if not answer_words:
            return MetricResult(
                score=0.0,
                reason="Empty answer",
                metadata={"method": "word_coverage"},
            )

        unsupported = answer_words - context_words
        score = len(unsupported) / len(answer_words)

        return MetricResult(
            score=min(score, 1.0),
            reason=f"{len(unsupported)}/{len(answer_words)} words not in context",
            metadata={
                "method": "word_coverage",
                "unsupported_words": len(unsupported),
                "total_words": len(answer_words),
            },
        )
