"""Per-model LLM token pricing table and dollar-cost estimation helpers.

All rates in :data:`MODEL_PRICING` are denominated in **USD per 1,000 tokens**
(``prompt_per_1k``, ``completion_per_1k``) so contributors can easily add or
update provider rates as new models are released.
"""

from __future__ import annotations

from dataclasses import dataclass

_ZERO_COST_PROVIDERS = frozenset({"mock", "ollama"})


@dataclass(frozen=True)
class ModelPricing:
    """USD pricing per 1,000 prompt and completion tokens for a model."""

    prompt_per_1k: float
    completion_per_1k: float

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Compute estimated USD cost for the given token counts."""
        safe_prompt = max(0, prompt_tokens)
        safe_completion = max(0, completion_tokens)
        return (safe_prompt / 1000.0) * self.prompt_per_1k + (
            safe_completion / 1000.0
        ) * self.completion_per_1k

    def to_per_1m(self) -> dict[str, float]:
        """Return input/output rates converted to USD per 1M tokens."""
        return {
            "input": self.prompt_per_1k * 1000.0,
            "output": self.completion_per_1k * 1000.0,
        }


# Maintained pricing table: (provider, model) -> USD per 1K tokens.
# Keep keys lowercase; add new models here as providers release updates.
MODEL_PRICING: dict[tuple[str, str], ModelPricing] = {
    # OpenAI (USD per 1K tokens)
    ("openai", "gpt-4.1"): ModelPricing(prompt_per_1k=0.002, completion_per_1k=0.008),
    ("openai", "gpt-4.1-mini"): ModelPricing(
        prompt_per_1k=0.0004, completion_per_1k=0.0016
    ),
    ("openai", "gpt-4.1-nano"): ModelPricing(
        prompt_per_1k=0.0001, completion_per_1k=0.0004
    ),
    ("openai", "gpt-4o"): ModelPricing(prompt_per_1k=0.0025, completion_per_1k=0.01),
    ("openai", "gpt-4o-mini"): ModelPricing(
        prompt_per_1k=0.00015, completion_per_1k=0.0006
    ),
    ("openai", "gpt-4-turbo"): ModelPricing(prompt_per_1k=0.01, completion_per_1k=0.03),
    ("openai", "gpt-4"): ModelPricing(prompt_per_1k=0.03, completion_per_1k=0.06),
    ("openai", "gpt-3.5-turbo"): ModelPricing(
        prompt_per_1k=0.0005, completion_per_1k=0.0015
    ),
    ("openai", "o1"): ModelPricing(prompt_per_1k=0.015, completion_per_1k=0.06),
    ("openai", "o1-mini"): ModelPricing(prompt_per_1k=0.0011, completion_per_1k=0.0044),
    ("openai", "o3"): ModelPricing(prompt_per_1k=0.002, completion_per_1k=0.008),
    ("openai", "o3-mini"): ModelPricing(prompt_per_1k=0.0011, completion_per_1k=0.0044),
    ("openai", "o4-mini"): ModelPricing(prompt_per_1k=0.0011, completion_per_1k=0.0044),
    # Anthropic (USD per 1K tokens)
    ("anthropic", "claude-opus-4-20250514"): ModelPricing(
        prompt_per_1k=0.015, completion_per_1k=0.075
    ),
    ("anthropic", "claude-sonnet-4-20250514"): ModelPricing(
        prompt_per_1k=0.003, completion_per_1k=0.015
    ),
    ("anthropic", "claude-3-5-sonnet-20241022"): ModelPricing(
        prompt_per_1k=0.003, completion_per_1k=0.015
    ),
    ("anthropic", "claude-3-5-sonnet"): ModelPricing(
        prompt_per_1k=0.003, completion_per_1k=0.015
    ),
    ("anthropic", "claude-3-5-haiku-20241022"): ModelPricing(
        prompt_per_1k=0.0008, completion_per_1k=0.004
    ),
    ("anthropic", "claude-3-5-haiku"): ModelPricing(
        prompt_per_1k=0.0008, completion_per_1k=0.004
    ),
    ("anthropic", "claude-3-opus-20240229"): ModelPricing(
        prompt_per_1k=0.015, completion_per_1k=0.075
    ),
    ("anthropic", "claude-3-opus"): ModelPricing(
        prompt_per_1k=0.015, completion_per_1k=0.075
    ),
    ("anthropic", "claude-3-sonnet"): ModelPricing(
        prompt_per_1k=0.003, completion_per_1k=0.015
    ),
    ("anthropic", "claude-3-haiku"): ModelPricing(
        prompt_per_1k=0.00025, completion_per_1k=0.00125
    ),
    # Google Gemini (USD per 1K tokens)
    ("gemini", "gemini-2.5-pro"): ModelPricing(
        prompt_per_1k=0.00125, completion_per_1k=0.01
    ),
    ("gemini", "gemini-2.5-flash"): ModelPricing(
        prompt_per_1k=0.0003, completion_per_1k=0.0025
    ),
    ("gemini", "gemini-2.0-flash"): ModelPricing(
        prompt_per_1k=0.0001, completion_per_1k=0.0004
    ),
    ("gemini", "gemini-2.0-flash-lite"): ModelPricing(
        prompt_per_1k=0.000075, completion_per_1k=0.0003
    ),
    ("gemini", "gemini-1.5-pro"): ModelPricing(
        prompt_per_1k=0.00125, completion_per_1k=0.005
    ),
    ("gemini", "gemini-pro"): ModelPricing(
        prompt_per_1k=0.0005, completion_per_1k=0.0015
    ),
    ("gemini", "gemini-1.5-flash"): ModelPricing(
        prompt_per_1k=0.000075, completion_per_1k=0.0003
    ),
    # Groq (USD per 1K tokens)
    ("groq", "llama-3.3-70b-versatile"): ModelPricing(
        prompt_per_1k=0.00059, completion_per_1k=0.00079
    ),
    ("groq", "llama-3.1-70b-versatile"): ModelPricing(
        prompt_per_1k=0.00059, completion_per_1k=0.00079
    ),
    ("groq", "llama-3-70b"): ModelPricing(
        prompt_per_1k=0.00059, completion_per_1k=0.00079
    ),
    ("groq", "llama-3.1-8b-instant"): ModelPricing(
        prompt_per_1k=0.00005, completion_per_1k=0.00008
    ),
    ("groq", "llama-3-8b"): ModelPricing(
        prompt_per_1k=0.00005, completion_per_1k=0.00008
    ),
    ("groq", "mixtral-8x7b-32768"): ModelPricing(
        prompt_per_1k=0.00024, completion_per_1k=0.00024
    ),
    ("groq", "gemma2-9b-it"): ModelPricing(
        prompt_per_1k=0.0002, completion_per_1k=0.0002
    ),
    # OpenRouter popular routed models (USD per 1K tokens)
    ("openrouter", "openai/gpt-4o"): ModelPricing(
        prompt_per_1k=0.0025, completion_per_1k=0.01
    ),
    ("openrouter", "openai/gpt-4o-mini"): ModelPricing(
        prompt_per_1k=0.00015, completion_per_1k=0.0006
    ),
    ("openrouter", "anthropic/claude-sonnet-4-20250514"): ModelPricing(
        prompt_per_1k=0.003, completion_per_1k=0.015
    ),
    ("openrouter", "anthropic/claude-3.5-sonnet"): ModelPricing(
        prompt_per_1k=0.003, completion_per_1k=0.015
    ),
    ("openrouter", "meta-llama/llama-3.1-70b-instruct"): ModelPricing(
        prompt_per_1k=0.00052, completion_per_1k=0.00075
    ),
}


def get_model_pricing(
    provider: str | None,
    model: str | None,
) -> ModelPricing | None:
    """Look up per-1K token pricing for a ``(provider, model)`` pair.

    Performs case-insensitive lookup, checks longest known prefix matches for
    snapshot-suffixed models (e.g. ``gpt-4o-2024-08-06``), resolves OpenRouter
    ``vendor/model`` identifiers, and returns zero cost for local/mock
    providers (``ollama``, ``mock``).
    """
    norm_provider = (provider or "").strip().lower()
    norm_model = (model or "").strip().lower()

    if norm_provider in _ZERO_COST_PROVIDERS:
        return ModelPricing(prompt_per_1k=0.0, completion_per_1k=0.0)

    if not norm_provider or not norm_model:
        return None

    direct = MODEL_PRICING.get((norm_provider, norm_model))
    if direct is not None:
        return direct

    if norm_provider == "openrouter" and "/" in norm_model:
        routed_vendor, routed_model = norm_model.split("/", 1)
        delegated = get_model_pricing(routed_vendor, routed_model)
        if delegated is not None:
            return delegated

    # Longest-prefix match within the same provider for snapshot/dated model IDs.
    candidates = [
        (known_model, pricing)
        for (known_provider, known_model), pricing in MODEL_PRICING.items()
        if known_provider == norm_provider
        and norm_model.startswith(known_model)
        and (
            len(norm_model) == len(known_model)
            or norm_model[len(known_model)] in ("-", ":", "@")
        )
    ]
    if candidates:
        candidates.sort(key=lambda item: len(item[0]), reverse=True)
        return candidates[0][1]

    return None


def estimate_cost_usd(
    prompt_tokens: int,
    completion_tokens: int,
    provider: str | None = None,
    model: str | None = None,
) -> float:
    """Estimate USD cost for a single generation from usage and pricing table.

    Returns ``0.0`` when tokens are non-positive or the ``(provider, model)``
    pair has no known rate in :data:`MODEL_PRICING`.
    """
    pricing = get_model_pricing(provider, model)
    if pricing is None:
        return 0.0
    return pricing.estimate_cost(prompt_tokens, completion_tokens)


def pricing_as_per_1m_table() -> dict[str, dict[str, dict[str, float]]]:
    """Return :data:`MODEL_PRICING` grouped as ``provider -> model -> per-1M USD``."""
    table: dict[str, dict[str, dict[str, float]]] = {}
    for (provider, model), pricing in MODEL_PRICING.items():
        table.setdefault(provider, {})[model] = pricing.to_per_1m()
    return table
