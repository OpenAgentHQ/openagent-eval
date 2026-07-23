"""Generic LLM-as-Judge metric for custom quality dimensions.

Provides a flexible metric that uses an LLM to evaluate any custom
quality dimension, returning a score based on LLM judgment.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from loguru import logger

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.providers.base.llm import LLMProvider

_JSON_SCORE_INSTRUCTION = (
    'Respond with ONLY a JSON object on a single line: {{"score": <number from 0.0 to 1.0>}}'
)
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
_JSON_OBJECT_RE = re.compile(r"\{[^{}]*\}")
_SCORE_LABEL_RE = re.compile(r"score\s*[:=]\s*(\d+\.?\d*)", re.IGNORECASE)
_BARE_DECIMAL_RE = re.compile(r"^\s*(\d+\.?\d*)\s*$")


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
        f"{_JSON_SCORE_INSTRUCTION}"
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
        f"{_JSON_SCORE_INSTRUCTION}"
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
        f"{_JSON_SCORE_INSTRUCTION}"
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
        text = response.strip()
        if not text:
            logger.warning("LLM judge: empty response, using default score 0.5")
            return 0.5

        for candidate in self._json_score_candidates(text):
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                normalized = {str(key).lower(): value for key, value in payload.items()}
                if "score" in normalized:
                    try:
                        score = float(normalized["score"])
                    except (TypeError, ValueError):
                        logger.warning(
                            "LLM judge: invalid JSON score value in response: {}",
                            response[:200],
                        )
                        continue
                    return self._clamp_normalized_score(score)

        label_match = _SCORE_LABEL_RE.search(text)
        if label_match:
            logger.warning(
                "LLM judge: parsed score from non-JSON labeled response: {}",
                response[:200],
            )
            return self._clamp_normalized_score(float(label_match.group(1)))

        bare_match = _BARE_DECIMAL_RE.match(text)
        if bare_match:
            logger.warning(
                "LLM judge: parsed score from bare numeric response: {}",
                response[:200],
            )
            return self._clamp_normalized_score(float(bare_match.group(1)))

        logger.warning(
            "LLM judge: failed to parse score from response, using default 0.5: {}",
            response[:200],
        )
        return 0.5

    @staticmethod
    def _json_score_candidates(text: str) -> list[str]:
        candidates: list[str] = []
        fence_match = _JSON_FENCE_RE.search(text)
        if fence_match:
            candidates.append(fence_match.group(1))
        obj_match = _JSON_OBJECT_RE.search(text)
        if obj_match:
            candidates.append(obj_match.group())
        candidates.append(text)
        return candidates

    @staticmethod
    def _clamp_normalized_score(score: float) -> float:
        if score > 1.0:
            if score <= 10.0:
                score = score / 10.0
            elif score <= 100.0:
                score = score / 100.0
            else:
                score = min(score / 100.0, 1.0)
        return max(0.0, min(1.0, score))


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
