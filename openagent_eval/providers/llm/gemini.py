"""Google Gemini LLM provider adapter.

This module implements the LLMProvider interface for Google's Gemini models
using the google-genai SDK. It provides async generation and token counting
with proper error handling and usage tracking.

Usage:
    ```python
    from openagent_eval.providers.llm.gemini import Gemini

    gemini = Gemini(api_key="your-api-key", model="gemini-2.5-flash")
    response = await gemini.generate("What is RAG?")
    print(response.content)
    print(response.usage.total_tokens)
    ```
"""

from __future__ import annotations

import os
import time
from typing import Any

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.models import LLMResponse, TokenUsage

# google-genai SDK imports (current, non-deprecated SDK)
try:
    from google import genai
    from google.genai import errors as genai_errors
    from google.genai import types
except ImportError as exc:
    raise ImportError(
        "google-genai package is required for Gemini provider. "
        "Install it with: pip install google-genai"
    ) from exc

import httpx


class Gemini(LLMProvider):
    """Google Gemini LLM provider adapter.

    Integrates with Google's Gemini models via the google-genai SDK to provide
    async text generation and token counting for evaluation pipelines.

    This adapter follows the LLMProvider ABC pattern and handles connection
    errors, API execution errors, and token usage tracking.

    Attributes:
        name: Provider identifier ("gemini").
        description: Human-readable provider description.

    Example:
        ```python
        from openagent_eval.providers.llm.gemini import Gemini

        # Basic usage with explicit API key
        gemini = Gemini(
            api_key="your-gemini-api-key",
            model="gemini-2.5-flash",
            temperature=0.3,
            max_tokens=1024,
        )
        response = await gemini.generate("Explain RAG evaluation")
        print(response.content)
        print(f"Tokens used: {response.usage.total_tokens}")

        # API key from GEMINI_API_KEY environment variable
        gemini = Gemini(model="gemini-2.5-flash")
        response = await gemini.generate("Hello")

        # Token counting
        count = await gemini.get_token_count("Hello, world!")
        print(f"Token count: {count}")
        ```
    """

    name: str = "gemini"
    description: str = "Google Gemini LLM provider"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> None:
        """Initialize the Gemini provider.

        Args:
            api_key: Google API key. If not provided, loaded from
                GEMINI_API_KEY environment variable.
            model: Model identifier (e.g., "gemini-2.5-flash").
            temperature: Sampling temperature (0.0 to 1.0). Defaults to 0.0.
            max_tokens: Maximum tokens to generate. None for model default.

        Raises:
            ProviderConnectionError: If API key is not provided and
                GEMINI_API_KEY environment variable is not set.
        """
        resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_api_key:
            raise ProviderConnectionError(
                message="Gemini API key not provided. Pass api_key or set GEMINI_API_KEY env var.",
                provider_name=self.name,
            )

        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

        try:
            self._client = genai.Client(api_key=resolved_api_key)
            self._aclient = self._client.aio
        except Exception as exc:
            raise ProviderConnectionError(
                message=f"Failed to initialize Gemini client: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from the Gemini model.

        Args:
            prompt: The input prompt to send to the model.
            **kwargs: Optional overrides for this call:
                - temperature (float): Override default temperature.
                - max_tokens (int): Override default max_tokens.

        Returns:
            LLMResponse with generated content, usage stats, and metadata.

        Raises:
            ProviderConnectionError: If connection to the API fails.
            ProviderExecutionError: If the API returns an error.
        """
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        start_time = time.monotonic()

        try:
            response = await self._aclient.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
        except httpx.ConnectError as exc:
            raise ProviderConnectionError(
                message=f"Failed to connect to Gemini API: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc
        except httpx.TimeoutException as exc:
            raise ProviderConnectionError(
                message=f"Gemini API request timed out: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc
        except genai_errors.APIError as exc:
            raise ProviderExecutionError(
                message=f"Gemini API error: {exc.message}",
                provider_name=self.name,
                original_error=exc,
                details={"code": exc.code, "status": exc.status},
            ) from exc

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        usage = TokenUsage(
            prompt_tokens=response.usage_metadata.prompt_token_count,
            completion_tokens=response.usage_metadata.candidates_token_count,
            total_tokens=response.usage_metadata.total_token_count,
        )

        return LLMResponse(
            content=response.text,
            model=self._model,
            usage=usage,
            provider=self.name,
            latency_ms=elapsed_ms,
        )

    async def get_token_count(self, text: str) -> int:
        """Count tokens in the given text using the Gemini tokenizer.

        Args:
            text: The text to count tokens for.

        Returns:
            The number of tokens in the text.

        Raises:
            ProviderConnectionError: If connection to the API fails.
            ProviderExecutionError: If token counting fails.
        """
        try:
            response = await self._aclient.models.count_tokens(
                model=self._model,
                contents=text,
            )
            return response.total_tokens
        except httpx.ConnectError as exc:
            raise ProviderConnectionError(
                message=f"Failed to connect to Gemini API for token counting: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc
        except httpx.TimeoutException as exc:
            raise ProviderConnectionError(
                message=f"Gemini API token counting timed out: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc
        except genai_errors.APIError as exc:
            raise ProviderExecutionError(
                message=f"Gemini API token counting error: {exc.message}",
                provider_name=self.name,
                original_error=exc,
                details={"code": exc.code, "status": exc.status},
            ) from exc
