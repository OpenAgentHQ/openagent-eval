"""Anthropic LLM provider adapter.

This module provides an LLM provider adapter for Anthropic's Claude models.
The adapter uses the official anthropic Python SDK with the async client
and follows the standard LLMProvider interface for seamless integration
with the OpenAgent Eval evaluation pipeline.
"""

from __future__ import annotations

import os
import time
from typing import Any

try:
    import anthropic
except ImportError:
    anthropic = None

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.models import TokenUsage


class Anthropic(LLMProvider):
    """Anthropic LLM provider adapter for Claude models.

    Provides access to Anthropic's Claude models through the official SDK.
    Handles API key authentication, message generation, token counting,
    and error translation into provider-specific exceptions.

    This adapter implements the LLMProvider interface and handles:
    - API key authentication via constructor or environment variable
    - Async message generation via the Anthropic Messages API
    - Token counting via the Anthropic count_tokens endpoint
    - Token usage tracking for cost analysis
    - Proper error handling with provider-specific exceptions

    Attributes:
        name: Provider identifier ("anthropic").
        description: Human-readable provider description.
        api_key: Anthropic API key for authentication.
        model: Model identifier to use for generation.
        temperature: Temperature parameter for generation (0.0-1.0).
        max_tokens: Maximum tokens to generate in response.

    Example:
        ```python
        import asyncio
        from openagent_eval.providers.llm.anthropic import Anthropic

        async def main():
            provider = Anthropic(
                api_key="your-api-key",
                model="claude-sonnet-4-20250514",
                temperature=0.7,
                max_tokens=1000,
            )

            response = await provider.generate("What is RAG?")
            print(response)

            token_count = await provider.get_token_count("Hello, world!")
            print(f"Token count: {token_count}")

        asyncio.run(main())
        ```
    """

    name: str = "anthropic"
    description: str = "Anthropic - Claude large language models"

    def __init__(
        self,
        config: Any | None = None,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> None:
        """Initialize the Anthropic provider.

        Args:
            config: Optional LLMConfig (reads api_key, model, temperature, max_tokens).
            api_key: Anthropic API key. If not provided, falls back to
                ANTHROPIC_API_KEY environment variable.
            model: Model identifier for generation.
                Defaults to "claude-sonnet-4-20250514".
            temperature: Temperature for generation (0.0-1.0). Defaults to 0.0.
            max_tokens: Maximum tokens to generate. The Anthropic Messages API
                requires this field, so it defaults to 4096 (not None).

        Raises:
            ProviderConnectionError: If API key is not provided or found
                in environment.
        """
        if config is not None:
            api_key = api_key or getattr(config, "api_key", None)
            model = getattr(config, "model", model) or model
            temperature = (
                getattr(config, "temperature", temperature)
                if getattr(config, "temperature", None) is not None
                else temperature
            )
            max_tokens = (
                getattr(config, "max_tokens", max_tokens)
                if getattr(config, "max_tokens", None) is not None
                else max_tokens
            )

        if api_key is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key is None:
                raise ProviderConnectionError(
                    message=(
                        "Anthropic API key not provided. Pass api_key parameter "
                        "or set ANTHROPIC_API_KEY environment variable."
                    ),
                    provider_name="anthropic",
                )

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if anthropic is None:
            raise ProviderError(
                message=(
                    "The 'anthropic' package is required for the Anthropic provider. "
                    "Install with: pip install openagent-eval[providers]"
                ),
                provider_name="anthropic",
            )

        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the LLM.

        Sends the prompt to Anthropic's Messages API and returns the
        generated text. Supports additional generation parameters via kwargs.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Additional generation parameters:
                - temperature (float): Override default temperature.
                - max_tokens (int): Override default max tokens.
                - model (str): Override default model for this request.

        Returns:
            The generated text response from the LLM.

        Raises:
            ProviderConnectionError: If the connection to Anthropic fails.
            ProviderExecutionError: If the API request fails or returns
                an error.
        """
        start_time = time.time()

        # Build request parameters
        params: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.temperature),
        }

        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_tokens"]
        elif self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens

        try:
            response = await self._client.messages.create(**params)

            # Extract content from the response
            content_blocks = response.content
            if not content_blocks:
                raise ProviderExecutionError(
                    message="No content returned from Anthropic API",
                    provider_name="anthropic",
                )

            # Concatenate all text blocks
            content = "".join(
                block.text for block in content_blocks if block.type == "text"
            )

            # Track token usage
            usage = TokenUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=(
                    response.usage.input_tokens + response.usage.output_tokens
                ),
            )

            latency_ms = (time.time() - start_time) * 1000

            return content

        except anthropic.APIConnectionError as e:
            raise ProviderConnectionError(
                message=f"Failed to connect to Anthropic API: {e}",
                provider_name="anthropic",
                original_error=e,
            ) from e
        except anthropic.APITimeoutError as e:
            raise ProviderConnectionError(
                message=f"Request to Anthropic API timed out: {e}",
                provider_name="anthropic",
                original_error=e,
            ) from e
        except anthropic.APIStatusError as e:
            raise ProviderExecutionError(
                message=f"Anthropic API error ({e.status_code}): {e.message}",
                provider_name="anthropic",
                original_error=e,
                details={"status_code": e.status_code, "request_id": e.request_id},
            ) from e
        except anthropic.APIError as e:
            raise ProviderExecutionError(
                message=f"Anthropic API error: {e}",
                provider_name="anthropic",
                original_error=e,
            ) from e

    async def get_token_count(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Uses the Anthropic count_tokens endpoint for accurate token counts
        specific to the configured model. Do not use tiktoken for Claude
        models — it undercounts by 15-20%.

        Args:
            text: The text to count tokens for.

        Returns:
            The number of tokens in the text.

        Raises:
            ProviderExecutionError: If the token counting API call fails.
        """
        if not text:
            return 0

        try:
            response = await self._client.messages.count_tokens(
                model=self.model,
                messages=[{"role": "user", "content": text}],
            )
            return response.input_tokens
        except anthropic.APIConnectionError as e:
            raise ProviderConnectionError(
                message=f"Failed to connect to Anthropic token counting API: {e}",
                provider_name="anthropic",
                original_error=e,
            ) from e
        except anthropic.APIStatusError as e:
            raise ProviderExecutionError(
                message=f"Anthropic token counting error ({e.status_code}): {e.message}",
                provider_name="anthropic",
                original_error=e,
                details={"status_code": e.status_code},
            ) from e
        except anthropic.APIError as e:
            raise ProviderExecutionError(
                message=f"Anthropic token counting error: {e}",
                provider_name="anthropic",
                original_error=e,
            ) from e
