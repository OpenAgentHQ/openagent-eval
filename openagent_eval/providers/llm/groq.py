"""Groq LLM provider adapter.

This module provides an LLM provider adapter for Groq, which offers
high-performance inference for various LLM models through their API.

The adapter uses Groq's official Python SDK and follows the standard
LLMProvider interface for seamless integration with the OpenAgent Eval
evaluation pipeline.
"""

from __future__ import annotations

import os
import time
from typing import Any

try:
    import groq
except ImportError:
    groq = None

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.models import LLMResponse, TokenUsage


class Groq(LLMProvider):
    """Groq LLM provider adapter.

    Provides access to high-performance LLM inference through Groq's API.
    Groq offers fast inference for various models including Llama, Mixtral,
    and Gemma models.

    This adapter implements the LLMProvider interface and handles:
    - API key authentication via constructor or environment variable
    - Groq SDK client initialization and management
    - Token usage tracking for cost analysis
    - Proper error handling with provider-specific exceptions

    Attributes:
        name: Provider identifier ("groq").
        description: Human-readable provider description.
        api_key: Groq API key for authentication.
        model: Model identifier to use for generation.
        temperature: Temperature parameter for generation (0.0-2.0).
        max_tokens: Maximum tokens to generate in response.
        client: Groq AsyncGroq client instance.

    Example:
        ```python
        import asyncio
        from openagent_eval.providers.llm.groq import Groq

        async def main():
            provider = Groq(
                api_key="your-api-key",
                model="llama-3.3-70b-versatile",
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

    name: str = "groq"
    description: str = "Groq - High-performance LLM inference"

    def __init__(
        self,
        config: Any | None = None,
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **_: Any,
    ) -> None:
        """Initialize the Groq provider.

        Args:
            config: Optional LLMConfig (reads api_key, model, temperature, max_tokens).
            api_key: Groq API key. If not provided, falls back to
                GROQ_API_KEY environment variable.
            model: Model identifier for generation. Defaults to
                "llama-3.3-70b-versatile".
            temperature: Temperature for generation (0.0-2.0). Defaults to 0.0.
            max_tokens: Maximum tokens to generate. Defaults to None (model default).

        Raises:
            ProviderConnectionError: If API key is not provided or found
                in environment, or if client initialization fails.
        """
        # Extract from config if provided
        if config is not None:
            api_key = api_key or getattr(config, "api_key", None) or os.environ.get("GROQ_API_KEY")
            model = getattr(config, "model", model) or model
            temperature = getattr(config, "temperature", temperature) if getattr(config, "temperature", None) is not None else temperature
            max_tokens = getattr(config, "max_tokens", max_tokens) if getattr(config, "max_tokens", None) is not None else max_tokens
        else:
            if api_key is None:
                api_key = os.environ.get("GROQ_API_KEY")

        if api_key is None:
            raise ProviderConnectionError(
                message="Groq API key not provided. Pass api_key parameter or set GROQ_API_KEY environment variable.",
                provider_name="groq",
            )

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if groq is None:
            raise ProviderError(
                message=(
                    "The 'groq' package is required for the Groq provider. "
                    "Install with: pip install openagent-eval[providers]"
                ),
                provider_name="groq",
            )

        try:
            self.client = groq.AsyncGroq(api_key=api_key)
        except Exception as e:
            raise ProviderConnectionError(
                message=f"Failed to initialize Groq client: {str(e)}",
                provider_name="groq",
                original_error=e,
            ) from e

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the LLM.

        Sends the prompt to Groq's API and returns the generated text.
        Supports additional generation parameters via kwargs.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Additional generation parameters:
                - temperature (float): Override default temperature.
                - max_tokens (int): Override default max tokens.
                - model (str): Override default model for this request.

        Returns:
            The generated text response from the LLM.

        Raises:
            ProviderConnectionError: If the connection to Groq fails.
            ProviderExecutionError: If the API request fails or returns an error.
        """
        # Build request parameters
        request_params: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.temperature),
        }

        if "max_tokens" in kwargs:
            request_params["max_tokens"] = kwargs["max_tokens"]
        elif self.max_tokens is not None:
            request_params["max_tokens"] = self.max_tokens

        try:
            response = await self.client.chat.completions.create(**request_params)

            # Extract content
            if not response.choices:
                raise ProviderExecutionError(
                    message="No choices returned from Groq API",
                    provider_name="groq",
                    details={"response": response.model_dump()},
                )

            content = response.choices[0].message.content or ""

            return content

        except groq.APIConnectionError as e:
            raise ProviderConnectionError(
                message=f"Failed to connect to Groq API: {str(e)}",
                provider_name="groq",
                original_error=e,
            ) from e
        except groq.APITimeoutError as e:
            raise ProviderConnectionError(
                message=f"Request to Groq API timed out: {str(e)}",
                provider_name="groq",
                original_error=e,
            ) from e
        except groq.APIStatusError as e:
            raise ProviderExecutionError(
                message=f"Groq API error: {str(e)}",
                provider_name="groq",
                original_error=e,
                details={"status_code": e.status_code, "response": str(e.response)},
            ) from e
        except groq.AuthenticationError as e:
            raise ProviderConnectionError(
                message=f"Groq authentication failed: {str(e)}",
                provider_name="groq",
                original_error=e,
            ) from e
        except groq.RateLimitError as e:
            raise ProviderExecutionError(
                message=f"Groq rate limit exceeded: {str(e)}",
                provider_name="groq",
                original_error=e,
            ) from e
        except Exception as e:
            raise ProviderExecutionError(
                message=f"Unexpected error during Groq generation: {str(e)}",
                provider_name="groq",
                original_error=e,
            ) from e

    async def generate_with_usage(
        self, prompt: str, **kwargs: Any
    ) -> LLMResponse:
        """Generate a response with detailed token usage information.

        Extends :meth:`generate` to return a full :class:`LLMResponse` object
        with token usage statistics and latency for cost tracking.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Additional parameters (same as :meth:`generate`, e.g.
                ``temperature``, ``max_tokens``, ``model``).

        Returns:
            LLMResponse with content, model, usage, and latency information.

        Raises:
            ProviderConnectionError: If connection to Groq fails.
            ProviderExecutionError: If the API returns an error.
        """
        request_params: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.temperature),
        }
        if "max_tokens" in kwargs:
            request_params["max_tokens"] = kwargs["max_tokens"]
        elif self.max_tokens is not None:
            request_params["max_tokens"] = self.max_tokens

        try:
            start_time = time.monotonic()
            response = await self.client.chat.completions.create(**request_params)
            latency_ms = (time.monotonic() - start_time) * 1000

            if not response.choices:
                raise ProviderExecutionError(
                    message="No choices returned from Groq API",
                    provider_name="groq",
                    details={"response": response.model_dump()},
                )

            content = response.choices[0].message.content or ""
            usage = response.usage
            token_usage = TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            )
            return LLMResponse(
                content=content,
                model=request_params["model"],
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
                    message=f"Failed to connect to Groq API: {error_msg}",
                    provider_name="groq",
                    original_error=e,
                ) from e
            raise ProviderExecutionError(
                message=f"Groq API execution failed: {error_msg}",
                provider_name="groq",
                original_error=e,
            ) from e

    async def get_token_count(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Uses ``tiktoken`` for accurate token counting when available, falling
        back to a whitespace-based approximation otherwise. (The Groq SDK does
        not expose a tokenizer endpoint, so the previous ``client.tokenizer``
        call was dead code.)

        Args:
            text: The text to count tokens for.

        Returns:
            Number of tokens in the text.
        """
        if not text:
            return 0

        try:
            import tiktoken

            try:
                encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # Fall back to a whitespace-based approximation.
            return len(text.split())
