"""Answer Relevancy metric.

Measures whether the generated answer addresses the original question.
Uses Ragas answer_relevancy score when available, falls back to NLI-based
scoring, and finally to simple heuristics.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from openagent_eval.metrics.base import BaseMetric, MetricResult


class AnswerRelevancy(BaseMetric):
    """Measures relevancy of answer to the question.

    Answer Relevancy = |question concepts covered by answer| / |total question concepts|

    A score of 1.0 means the answer fully addresses the question.

    Scoring priority:
    1. Ragas (if available) — most accurate
    2. NLI-based (if transformers available) — checks if answer entails question
    3. Simple word overlap — fast fallback
    """

    name = "answer_relevancy"
    description = "Whether the answer addresses the original question"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate answer relevancy.

        Args:
            question: The original question.
            answer: The generated answer.
            contexts: Optional context strings (unused, for API consistency).

        Returns:
            MetricResult with relevancy score.
        """
        question = kwargs.get("question", "")
        answer = kwargs.get("answer", "")

        if not question:
            return MetricResult(
                score=0.0,
                reason="No question provided",
                metadata={"method": "word_overlap"},
            )

        if not answer:
            return MetricResult(
                score=0.0,
                reason="No answer provided",
                metadata={"method": "word_overlap"},
            )

        # Try Ragas if available
        try:
            return self._evaluate_with_ragas(question, answer)
        except ImportError:
            pass

        # Try NLI-based scoring if available
        try:
            return self._evaluate_with_nli(question, answer)
        except (ImportError, Exception) as e:
            logger.debug("NLI scoring unavailable, using simple overlap: {}", e)

        # Fallback: simple word overlap
        return self._evaluate_simple(question, answer)

    @property
    def _ragas_relevancy_metric(self):
        """Lazily import and cache the Ragas answer_relevancy metric (heavy import)."""
        if getattr(self, "_cached_ragas_rel", None) is None:
            from ragas.metrics import answer_relevancy as ragas_relevancy

            self._cached_ragas_rel = ragas_relevancy
        return self._cached_ragas_rel

    def _evaluate_with_ragas(
        self, question: str, answer: str
    ) -> MetricResult:
        """Evaluate using Ragas answer_relevancy."""
        from datasets import Dataset

        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [[]],
            "ground_truth": [""],
        }
        dataset = Dataset.from_dict(data)
        result = self._ragas_relevancy_metric.evaluate(dataset)
        score = result["answer_relevancy"]

        return MetricResult(
            score=score,
            reason=f"Ragas answer relevancy: {score:.4f}",
            metadata={"method": "ragas"},
        )

    def _evaluate_with_nli(
        self, question: str, answer: str
    ) -> MetricResult:
        """Evaluate using NLI: check if answer entails the question.

        For relevancy, we check if the answer is relevant to the question
        by evaluating whether the question's key information is addressed.
        """
        from openagent_eval.metrics.nli import NLIJudge

        judge = NLIJudge()

        # Check if answer is relevant to question
        # Premise: answer, Hypothesis: question (does answer support the question?)
        result = judge.evaluate(premise=answer, hypothesis=question)

        # High entailment means answer is relevant to question
        score = result.entailed_score

        return MetricResult(
            score=score,
            reason=f"NLI relevancy: {result.label.value} (score: {score:.4f})",
            metadata={
                "method": "nli",
                "label": result.label.value,
                "model": judge.model_name,
            },
        )

    def _evaluate_simple(self, question: str, answer: str) -> MetricResult:
        """Simple word overlap fallback."""
        # Remove common stop words and punctuation
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "what", "how", "why", "when", "where", "who", "which",
        }

        import re
        def _normalize(text: str) -> set[str]:
            words = re.findall(r'\b\w+\b', text.lower())
            return set(words) - stop_words

        question_words = _normalize(question)
        answer_words = _normalize(answer)

        if not question_words:
            return MetricResult(
                score=1.0,
                reason="No meaningful question words",
                metadata={"method": "word_overlap"},
            )

        overlap = question_words & answer_words
        score = len(overlap) / len(question_words)

        return MetricResult(
            score=min(score, 1.0),
            reason=f"Word overlap: {len(overlap)}/{len(question_words)} question words in answer",
            metadata={
                "method": "word_overlap",
                "overlap_words": len(overlap),
                "question_words": len(question_words),
            },
        )
