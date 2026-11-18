"""Dollar-cost estimation metric backed by ``openagent_eval.providers.pricing``."""

from __future__ import annotations

from typing import Any

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.providers.pricing import estimate_cost_usd, get_model_pricing


class CostEstimateMetric(BaseMetric):
    """Estimates LLM dollar cost using the maintained per-model pricing table.

    Produces a normalized score in ``[0.0, 1.0]`` against ``max_cost_usd``
    (``1.0`` at ``$0``, decaying linearly to ``0.0`` at ``max_cost_usd``) while
    recording exact ``estimated_cost_usd`` and per-1K rate metadata.
    """

    name = "cost_estimate"
    description = (
        "Estimates dollar cost from token usage and per-model provider pricing"
    )

    def __init__(self, max_cost_usd: float = 0.10) -> None:
        """Initialize the cost-estimate metric.

        Args:
            max_cost_usd: Cost ceiling (in USD) at which the normalized score
                reaches ``0.0``. Must be strictly positive.
        """
        if max_cost_usd <= 0:
            raise ValueError(f"max_cost_usd must be positive, got {max_cost_usd}")
        self.max_cost_usd = max_cost_usd

    def evaluate(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        provider: str = "",
        model: str = "",
        **kwargs: Any,
    ) -> MetricResult:
        """Compute estimated dollar cost and normalized efficiency score."""
        del kwargs  # Accepted for BaseMetric / Pipeline compatibility.
        safe_prompt = max(0, int(prompt_tokens or 0))
        safe_completion = max(0, int(completion_tokens or 0))
        total_tokens = safe_prompt + safe_completion

        pricing = get_model_pricing(provider, model)
        cost_usd = estimate_cost_usd(
            safe_prompt,
            safe_completion,
            provider=provider,
            model=model,
        )
        score = max(0.0, min(1.0, 1.0 - (cost_usd / self.max_cost_usd)))

        if pricing is None:
            reason = (
                f"${cost_usd:.6f} ({total_tokens} tokens; "
                f"no pricing entry for {provider or 'unknown'}/{model or 'unknown'})"
            )
        else:
            reason = (
                f"${cost_usd:.6f} "
                f"({safe_prompt} prompt + {safe_completion} completion tokens)"
            )

        return MetricResult(
            score=score,
            reason=reason,
            metadata={
                "estimated_cost_usd": cost_usd,
                "prompt_tokens": safe_prompt,
                "completion_tokens": safe_completion,
                "total_tokens": total_tokens,
                "provider": provider,
                "model": model,
                "pricing_found": pricing is not None,
                "prompt_per_1k_usd": pricing.prompt_per_1k if pricing else None,
                "completion_per_1k_usd": pricing.completion_per_1k if pricing else None,
            },
        )
