"""Token counting and cost estimation metrics.

Tracks token usage and estimated cost across LLM providers.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.providers.pricing import estimate_cost_usd, pricing_as_per_1m_table

# Cost per 1M tokens derived from the canonical per-1K table in providers/pricing.py.
COST_PER_1M_TOKENS: dict[str, dict[str, dict[str, float]]] = pricing_as_per_1m_table()


class TokenCountMetric(BaseMetric):
    """Counts tokens and estimates cost.

    Tracks prompt tokens, completion tokens, and total tokens.
    Estimates cost based on provider and model pricing.
    """

    name = "token_count"
    description = "Token usage counting and cost estimation"

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Evaluate token usage.

        Args:
            prompt_tokens: Number of prompt/input tokens.
            completion_tokens: Number of completion/output tokens.
            provider: LLM provider name (e.g., "openai").
            model: Model identifier (e.g., "gpt-4o").

        Returns:
            MetricResult with token counts and estimated cost.
        """
        prompt_tokens = kwargs.get("prompt_tokens", 0)
        completion_tokens = kwargs.get("completion_tokens", 0)
        provider = kwargs.get("provider", "unknown")
        model = kwargs.get("model", "unknown")

        total_tokens = prompt_tokens + completion_tokens
        cost = self._estimate_cost(provider, model, prompt_tokens, completion_tokens)

        # Score: 1.0 for low usage, decreases with higher usage
        # Reference: 1000 tokens = score 0.9, 10000 tokens = score 0.5
        score = max(0.0, 1.0 - (total_tokens / 20000))

        return MetricResult(
            score=score,
            reason=f"{total_tokens} tokens (${cost:.4f})",
            metadata={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": cost,
                "provider": provider,
                "model": model,
            },
        )

    def _estimate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate cost based on provider and model pricing."""
        return estimate_cost_usd(
            prompt_tokens,
            completion_tokens,
            provider=provider,
            model=model,
        )
