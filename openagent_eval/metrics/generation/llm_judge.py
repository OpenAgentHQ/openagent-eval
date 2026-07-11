"""Generic LLM-as-Judge metric for custom quality dimensions.

Provides a flexible metric that uses an LLM to evaluate any custom
quality dimension, returning a score based on LLM judgment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.providers.base.llm import LLMProvider


@dataclass(frozen=True)
class JudgeCriteria:
    """Criteria for LLM-as-Judge evaluation.

    Attributes:
        name: Name of the quality dimension.
        description: What this criteria measures.
        scoring_prompt: Template prompt for scoring. Use {premise} and {hypothesis}.
        passing_threshold: Minimum score to consider passing.
    """

    name: str
    description: str
    scoring_prompt: str
    passing_threshold: float = 0.7


# Pre-defined criteria templates
FAITHFULNESS_CRITERIA = JudgeCriteria(
    name="faithfulness",
    description="Whether the answer is supported by the context",
    scoring_prompt=(
        "Rate how well the following answer is supported by the context. "
        "Score from 0.0 (not supported at all) to 1.0 (fully supported).\n\n"
        "Context: {premise}\n\n"
        "Answer: {hypothesis}\n\n"
        "Score:"
    ),
)

RELEVANCY_CRITERIA = JudgeCriteria(
    name="relevancy",
    description="Whether the answer addresses the question",
    scoring_prompt=(
        "Rate how well the following answer addresses the question. "
        "Score from 0.0 (completely irrelevant) to 1.0 (fully addresses the question).\n\n"
        "Question: {premise}\n\n"
        "Answer: {hypothesis}\n\n"
        "Score:"
    ),
)

COMPREHENSIVENESS_CRITERIA = JudgeCriteria(
    name="comprehensiveness",
    description="How comprehensive and thorough the answer is",
    scoring_prompt=(
        "Rate how comprehensive and thorough the following answer is. "
        "Consider whether it covers all important aspects. "
        "Score from 0.0 (very incomplete) to 1.0 (fully comprehensive).\n\n"
        "Topic: {premise}\n\n"
        "Answer: {hypothesis}\n\n"
        "Score:"
    ),
)


class LLMJudgeMetric(BaseMetric):
    """Generic LLM-as-Judge metric for custom quality dimensions.

    Uses an LLM provider to evaluate any custom quality criteria.
    The LLM receives a scoring prompt and returns a numeric score.

    Example:
        ```python
        from openagent_eval.metrics.generation.llm_judge import (
            LLMJudgeMetric, FAITHFULNESS_CRITERIA
        )

        judge = LLMJudgeMetric(
            provider=openai_provider,
            criteria=FAITHFULNESS_CRITERIA,
        )
        result = judge.evaluate(
            premise="The sky is blue.",
            hypothesis="The sky is indeed blue and clear."
        )
        ```
    """

    def __init__(
        self,
        provider: LLMProvider,
        criteria: JudgeCriteria | None = None,
    ) -> None:
        """Initialize the LLM judge metric.

        Args:
            provider: LLM provider for scoring.
            criteria: Scoring criteria. Defaults to faithfulness.
        """
        self._provider = provider
        self._criteria = criteria or FAITHFULNESS_CRITERIA
        self.name = f"llm_judge_{self._criteria.name}"
        self.description = self._criteria.description

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate using LLM judge.

        Args:
            premise: The context or question.
            hypothesis: The answer or text to evaluate.

        Returns:
            MetricResult with LLM-judged score.
        """
        premise = kwargs.get("premise", "")
        hypothesis = kwargs.get("hypothesis", "")

        if not premise or not hypothesis:
            return MetricResult(
                score=0.0,
                reason="Missing premise or hypothesis",
                metadata={"method": "llm_judge", "criteria": self._criteria.name},
            )

        # Build prompt
        prompt = self._criteria.scoring_prompt.format(
            premise=premise, hypothesis=hypothesis
        )

        try:
            import asyncio
            import inspect

            response = self._provider.generate(prompt)
            # Handle both sync and async providers
            if inspect.iscoroutine(response):
                response = asyncio.get_event_loop().run_until_complete(response)
            score = self._parse_score(response)
        except Exception as e:
            logger.error("LLM judge failed: {}", e)
            return MetricResult(
                score=0.0,
                reason=f"LLM judge failed: {e}",
                metadata={"method": "llm_judge", "error": str(e)},
            )

        return MetricResult(
            score=score,
            reason=f"LLM judge ({self._criteria.name}): {score:.4f}",
            metadata={
                "method": "llm_judge",
                "criteria": self._criteria.name,
                "provider": self._provider.name,
            },
        )

    def _parse_score(self, response: str) -> float:
        """Parse numeric score from LLM response text."""
        import re

        # Try to find a decimal number
        match = re.search(r'(\d+\.?\d*)', response.strip())
        if match:
            score = float(match.group(1))
            # Normalize to 0-1 range if needed
            if score > 1.0:
                # Could be percentage (85 -> 0.85) or scale (8.5 -> 0.85)
                if score <= 10.0:
                    score = score / 10.0
                else:
                    score = min(score / 100.0, 1.0)
            return max(0.0, min(1.0, score))

        # Fallback: check for keywords
        response_lower = response.lower()
        if any(word in response_lower for word in ["yes", "true", "fully", "completely", "excellent"]):
            return 1.0
        if any(word in response_lower for word in ["no", "false", "not at all", "poor"]):
            return 0.0

        return 0.5  # Default neutral score


class AsyncLLMJudgeMetric(LLMJudgeMetric):
    """Async version of LLMJudgeMetric for use in async pipelines."""

    async def evaluate_async(self, **kwargs: Any) -> MetricResult:
        """Evaluate asynchronously.

        Args:
            premise: The context or question.
            hypothesis: The answer or text to evaluate.

        Returns:
            MetricResult with LLM-judged score.
        """
        premise = kwargs.get("premise", "")
        hypothesis = kwargs.get("hypothesis", "")

        if not premise or not hypothesis:
            return MetricResult(
                score=0.0,
                reason="Missing premise or hypothesis",
                metadata={"method": "llm_judge", "criteria": self._criteria.name},
            )

        prompt = self._criteria.scoring_prompt.format(
            premise=premise, hypothesis=hypothesis
        )

        try:
            response = await self._provider.generate(prompt)
            score = self._parse_score(response)
        except Exception as e:
            logger.error("Async LLM judge failed: {}", e)
            return MetricResult(
                score=0.0,
                reason=f"LLM judge failed: {e}",
                metadata={"method": "llm_judge", "error": str(e)},
            )

        return MetricResult(
            score=score,
            reason=f"LLM judge ({self._criteria.name}): {score:.4f}",
            metadata={
                "method": "llm_judge",
                "criteria": self._criteria.name,
                "provider": self._provider.name,
            },
        )
