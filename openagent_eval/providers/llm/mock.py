"""Mock LLM provider for dry-run and testing.

This adapter implements the ``LLMProvider`` interface without making any
network calls. It is selected when ``llm.provider: mock`` is configured, which
lets the full evaluation pipeline run end-to-end in CI or locally without API
keys (per the project's local-first, no-secrets-required goal).
"""

from __future__ import annotations

import time
from typing import Any

from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.models import LLMResponse, TokenUsage


class MockLLMProvider(LLMProvider):
    """Deterministic, offline LLM provider.

    ``generate`` returns the item's ``ground_truth`` when supplied (so that
    generation metrics such as faithfulness / semantic similarity score well in
    tests), otherwise a deterministic echo of the prompt. Token usage and
    latency are approximated locally.
    """

    name: str = "mock"
    description: str = "Deterministic offline LLM provider for dry-run and testing"

    def __init__(
        self,
        config: Any | None = None,
        model: str = "mock-model",
        temperature: float = 0.0,
        **_: Any,
    ) -> None:
        """Initialize the mock provider.

        Args:
            config: Optional LLMConfig (only ``model``/``temperature`` are read).
            model: Model identifier to report.
            temperature: Sampling temperature to report.
        """
        self._model = getattr(config, "model", model) or model
        self._temperature = getattr(config, "temperature", temperature) or temperature

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Return a deterministic answer without calling any API.

        Args:
            prompt: The input prompt.
            **kwargs: May include ``ground_truth`` to echo a known answer.

        Returns:
            The ground truth when available, else a deterministic echo.
        """
        ground_truth = kwargs.get("ground_truth")
        if ground_truth:
            return str(ground_truth)
        return f"[mock-answer] {prompt.strip()[:200]}"

    async def get_token_count(self, text: str) -> int:
        """Approximate token count by whitespace splitting."""
        return len(text.split())

    async def generate_with_usage(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response with approximated token usage and latency.

        Args:
            prompt: The input prompt.
            **kwargs: Forwarded to ``generate`` (e.g. ``ground_truth``).

        Returns:
            An ``LLMResponse`` with local approximations.
        """
        start = time.monotonic()
        content = await self.generate(prompt, **kwargs)
        latency_ms = (time.monotonic() - start) * 1000

        prompt_tokens = len(prompt.split())
        completion_tokens = len(content.split())
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        return LLMResponse(
            content=content,
            model=self._model,
            usage=usage,
            provider=self.name,
            latency_ms=latency_ms,
        )
