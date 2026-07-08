"""Groq LLM provider adapter.

This module provides an LLM provider adapter for Groq, which offers
high-performance inference for various LLM models through their API.

The adapter uses Groq's official Python SDK and follows the standard
LLMProvider interface for seamless integration with the OpenAgent Eval
evaluation pipeline.
"""

from __future__ import annotations

import os
from typing import Any

import groq

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider


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
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> None:
        """Initialize the Groq provider.

        Args:
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

    async def get_token_count(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Uses Groq's tokenizer API to count tokens accurately. Falls back
        to a simple estimation if the tokenizer API is unavailable.

        Args:
            text: The text to count tokens for.

        Returns:
            Number of tokens in the text.

        Raises:
            ProviderError: If token counting fails.
        """
        if not text:
            return 0

        try:
            # Use Groq's tokenizer API for accurate token counting
            response = await self.client.tokenizer.encode(text=text)
            return len(response.tokens)
        except Exception:
            # Fall back to simple estimation if tokenizer API fails
            # This is a rough approximation; for production, use a proper tokenizer
            tokens = text.split()
            return len(tokens)
