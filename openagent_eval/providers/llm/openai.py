"""OpenAI LLM provider adapter.

This module provides an OpenAI adapter that implements the LLMProvider interface.
It uses the official openai Python package with async support for non-blocking I/O
and tiktoken for token counting.

Example:
    ```python
    from openagent_eval.providers.llm.openai import OpenAIProvider
    from openagent_eval.config.models import LLMConfig

    # Using configuration
    config = LLMConfig(
        provider="openai",
        model="gpt-4o",
        api_key="sk-...",
        temperature=0.7,
        max_tokens=1024
    )
    provider = OpenAIProvider(config=config)

    # Using environment variable for API key
    provider = OpenAIProvider(model="gpt-4o")

    # Generate response
    async def main():
        response = await provider.generate("What is RAG?")
        print(response)
    ```
"""

from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING, Any

import tiktoken
from openai import AsyncOpenAI

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.models import LLMResponse, TokenUsage

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion

    from openagent_eval.config.models import LLMConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider adapter.

    This adapter integrates with the OpenAI API to provide LLM generation
    capabilities. It supports:
    - Async/await for non-blocking I/O
    - Token counting via tiktoken
    - Automatic API key loading from environment variables
    - Comprehensive error handling with provider-specific exceptions

    Attributes:
        name: Provider identifier ("openai").
        description: Human-readable provider description.
        model: The OpenAI model identifier (e.g., "gpt-4o").
        temperature: Sampling temperature (0.0-2.0).
        max_tokens: Maximum tokens to generate.

    Example:
        ```python
        provider = OpenAIProvider(model="gpt-4o", temperature=0.7)
        response = await provider.generate("Explain quantum computing")
        print(response)
        ```
    """

    name: str = "openai"
    description: str = "OpenAI LLM provider (GPT-4o, GPT-4, etc.)"

    def __init__(
        self,
        config: LLMConfig | None = None,
        api_key: str | None = None,
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> None:
        """Initialize the OpenAI provider.

        Args:
            config: Optional LLMConfig object with provider settings.
            api_key: OpenAI API key. If not provided, loads from OPENAI_API_KEY env var.
            model: Model identifier (default: "gpt-4o").
            temperature: Sampling temperature 0.0-2.0 (default: 0.0).
            max_tokens: Maximum tokens to generate (default: None for model default).

        Raises:
            ProviderConnectionError: If API key is not found or invalid.
        """
        if config:
            self._api_key = config.api_key or os.getenv("OPENAI_API_KEY")
            self._model = config.model
            self._temperature = config.temperature
            self._max_tokens = config.max_tokens
        else:
            self._api_key = api_key or os.getenv("OPENAI_API_KEY")
            self._model = model
            self._temperature = temperature
            self._max_tokens = max_tokens

        if not self._api_key:
            raise ProviderConnectionError(
                message="OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.",
                provider_name=self.name,
            )

        self._client = AsyncOpenAI(api_key=self._api_key)
        self._encoding: tiktoken.Encoding | None = None

    def _get_encoding(self) -> tiktoken.Encoding:
        """Get or create tiktoken encoding for the configured model.

        Returns:
            tiktoken.Encoding instance for token counting.

        Raises:
            ProviderExecutionError: If encoding cannot be loaded.
        """
        if self._encoding is None:
            try:
                self._encoding = tiktoken.encoding_for_model(self._model)
            except KeyError:
                # Fallback to cl100k_base for unknown models
                logger.warning(
                    f"No encoding found for model {self._model}, using cl100k_base"
                )
                self._encoding = tiktoken.get_encoding("cl100k_base")
        return self._encoding

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the OpenAI API.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Additional parameters:
                - temperature (float): Override default temperature.
                - max_tokens (int): Override default max tokens.
                - system_message (str): Optional system message to prepend.

        Returns:
            The generated text response from the LLM.

        Raises:
            ProviderConnectionError: If connection to OpenAI fails.
            ProviderExecutionError: If the API returns an error.
        """
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        system_message = kwargs.get("system_message")

        messages: list[dict[str, str]] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        request_params: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens

        try:
            start_time = time.monotonic()
            completion: ChatCompletion = await self._client.chat.completions.create(
                **request_params
            )
            latency_ms = (time.monotonic() - start_time) * 1000

            if not completion.choices:
                raise ProviderExecutionError(
                    message="OpenAI API returned empty choices",
                    provider_name=self.name,
                )

            content = completion.choices[0].message.content or ""
            usage = completion.usage

            logger.debug(
                f"OpenAI generate completed: {usage.total_tokens if usage else 'unknown'} tokens, "
                f"{latency_ms:.1f}ms"
            )

            return content

        except ProviderConnectionError:
            raise
        except ProviderExecutionError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                raise ProviderConnectionError(
                    message=f"Failed to connect to OpenAI API: {error_msg}",
                    provider_name=self.name,
                    original_error=e,
                ) from e
            raise ProviderExecutionError(
                message=f"OpenAI API execution failed: {error_msg}",
                provider_name=self.name,
                original_error=e,
            ) from e

    async def get_token_count(self, text: str) -> int:
        """Count the number of tokens in the given text using tiktoken.

        Args:
            text: The text to count tokens for.

        Returns:
            The number of tokens in the text.

        Raises:
            ProviderExecutionError: If token counting fails.
        """
        try:
            encoding = self._get_encoding()
            token_count = len(encoding.encode(text))
            return token_count
        except Exception as e:
            raise ProviderExecutionError(
                message=f"Failed to count tokens: {str(e)}",
                provider_name=self.name,
                original_error=e,
            ) from e

    async def generate_with_usage(
        self, prompt: str, **kwargs: Any
    ) -> LLMResponse:
        """Generate a response with detailed token usage information.

        This method extends generate() to return a full LLMResponse object
        with token usage statistics for cost tracking.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Additional parameters (same as generate()).

        Returns:
            LLMResponse with content, model, usage, and latency information.

        Raises:
            ProviderConnectionError: If connection to OpenAI fails.
            ProviderExecutionError: If the API returns an error.
        """
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        system_message = kwargs.get("system_message")

        messages: list[dict[str, str]] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        request_params: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens

        try:
            start_time = time.monotonic()
            completion: ChatCompletion = await self._client.chat.completions.create(
                **request_params
            )
            latency_ms = (time.monotonic() - start_time) * 1000

            if not completion.choices:
                raise ProviderExecutionError(
                    message="OpenAI API returned empty choices",
                    provider_name=self.name,
                )

            content = completion.choices[0].message.content or ""
            usage = completion.usage

            token_usage = TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            )

            logger.debug(
                f"OpenAI generate_with_usage completed: {token_usage.total_tokens} tokens, "
                f"{latency_ms:.1f}ms"
            )

            return LLMResponse(
                content=content,
                model=self._model,
                usage=token_usage,
                provider=self.name,
                latency_ms=latency_ms,
            )

        except ProviderConnectionError:
            raise
        except ProviderExecutionError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                raise ProviderConnectionError(
                    message=f"Failed to connect to OpenAI API: {error_msg}",
                    provider_name=self.name,
                    original_error=e,
                ) from e
            raise ProviderExecutionError(
                message=f"OpenAI API execution failed: {error_msg}",
                provider_name=self.name,
                original_error=e,
            ) from e
