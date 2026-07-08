"""Token counting and cost estimation metrics.

Tracks token usage and estimated cost across LLM providers.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult


# Cost per 1M tokens by provider and model (USD)
COST_PER_1M_TOKENS: dict[str, dict[str, dict[str, float]]] = {
    "openai": {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    },
    "anthropic": {
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
    },
    "gemini": {
        "gemini-pro": {"input": 0.50, "output": 1.50},
        "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    },
    "groq": {
        "llama-3-70b": {"input": 0.59, "output": 0.79},
        "llama-3-8b": {"input": 0.05, "output": 0.08},
    },
}


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
        """Estimate cost based on provider and model pricing.

        Args:
            provider: LLM provider name.
            model: Model identifier.
            prompt_tokens: Number of prompt tokens.
            completion_tokens: Number of completion tokens.

        Returns:
            Estimated cost in USD.
        """
        provider_costs = COST_PER_1M_TOKENS.get(provider, {})
        model_costs = provider_costs.get(model, {})

        if not model_costs:
            return 0.0

        input_rate = model_costs.get("input", 0.0)
        output_rate = model_costs.get("output", 0.0)

        input_cost = (prompt_tokens / 1_000_000) * input_rate
        output_cost = (completion_tokens / 1_000_000) * output_rate

        return input_cost + output_cost
