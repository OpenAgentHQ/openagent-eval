"""OpenRouter LLM provider adapter.

This module provides an LLM provider adapter for OpenRouter, which provides
access to multiple LLM models through a unified API interface.

The adapter uses OpenRouter's OpenAI-compatible API endpoint and follows
the standard LLMProvider interface for seamless integration with the
OpenAgent Eval evaluation pipeline.
"""

from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import NoReturn

import httpx

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.models import LLMResponse, TokenUsage


class OpenRouter(LLMProvider):
    """OpenRouter LLM provider adapter.

    Provides access to multiple LLM models through OpenRouter's unified API.
    OpenRouter acts as a gateway to various AI models from different providers,
    including OpenAI, Anthropic, Google, and others.

    This adapter implements the LLMProvider interface and handles:
    - API key authentication via constructor or environment variable
    - OpenAI-compatible API calls to OpenRouter
    - Token usage tracking for cost analysis
    - Proper error handling with provider-specific exceptions

    Attributes:
        name: Provider identifier ("openrouter").
        description: Human-readable provider description.
        api_key: OpenRouter API key for authentication.
        model: Model identifier to use for generation.
        temperature: Temperature parameter for generation (0.0-2.0).
        max_tokens: Maximum tokens to generate in response.

    Example:
        ```python
        import asyncio
        from openagent_eval.providers.llm.openrouter import OpenRouter

        async def main():
            provider = OpenRouter(
                api_key="your-api-key",
                model="openai/gpt-4o-mini",
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

    name: str = "openrouter"
    description: str = "OpenRouter - Unified API gateway for multiple LLM providers"

    def __init__(
        self,
        config: Any | None = None,
        api_key: str | None = None,
        model: str = "openai/gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
    ) -> None:
        """Initialize the OpenRouter provider.

        Args:
            config: Optional LLMConfig (reads api_key, model, temperature, max_tokens).
            api_key: OpenRouter API key. If not provided, falls back to
                OPENROUTER_API_KEY environment variable.
            model: Model identifier for generation. Defaults to "openai/gpt-4o-mini".
            temperature: Temperature for generation (0.0-2.0). Defaults to 0.0.
            max_tokens: Maximum tokens to generate. Defaults to None (model default).
            base_url: OpenRouter API base URL. Defaults to OpenRouter's endpoint.

        Raises:
            ProviderConnectionError: If API key is not provided or found in environment.
        """
        if config is not None:
            config_api_key = getattr(config, "api_key", None)
            api_key = api_key or (
                config_api_key.get_secret_value()
                if config_api_key is not None
                else None
            )
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
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if api_key is None:
                raise ProviderConnectionError(
                    message="OpenRouter API key not provided. Pass api_key parameter or set OPENROUTER_API_KEY environment variable.",
                    provider_name="openrouter",
                )

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url.rstrip("/")

    @property
    def model_name(self) -> str | None:
        """Return the configured OpenRouter model identifier."""
        return self.model

    def _build_payload(
        self, prompt: str, *, stream: bool = False, **kwargs: Any
    ) -> dict[str, Any]:
        """Build OpenRouter chat completion payload."""
        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.temperature),
        }
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        elif self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        if stream:
            payload["stream"] = True
        return payload

    def _build_headers(self) -> dict[str, str]:
        """Build OpenRouter request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/openagent-eval",
            "X-Title": "OpenAgent Eval",
        }

    @staticmethod
    def _extract_error_message(error_payload: Any, fallback: str) -> str:
        """Extract a human-readable message from an OpenRouter error payload."""
        if isinstance(error_payload, dict):
            message = error_payload.get("message")
            if message:
                return str(message)
            return json.dumps(error_payload) if error_payload else fallback
        if error_payload:
            return str(error_payload)
        return fallback

    def _raise_http_error(
        self, status_code: int, raw_body: str, error_data: dict[str, Any]
    ) -> NoReturn:
        """Raise ProviderExecutionError for a non-200 OpenRouter HTTP response."""
        fallback = f"HTTP {status_code}: {raw_body}"
        error_message = self._extract_error_message(
            error_data.get("error"), fallback=fallback
        )
        raise ProviderExecutionError(
            message=f"OpenRouter API error: {error_message}",
            provider_name="openrouter",
            details={
                "status_code": status_code,
                "response": error_data,
            },
        )

    @staticmethod
    def _raise_mapped_httpx_error(exc: Exception) -> NoReturn:
        """Translate httpx transport errors into ProviderConnectionError."""
        if isinstance(exc, httpx.ConnectError):
            raise ProviderConnectionError(
                message=f"Failed to connect to OpenRouter API: {exc!s}",
                provider_name="openrouter",
                original_error=exc,
            ) from exc
        if isinstance(exc, httpx.TimeoutException):
            raise ProviderConnectionError(
                message=f"Request to OpenRouter API timed out: {exc!s}",
                provider_name="openrouter",
                original_error=exc,
            ) from exc
        raise ProviderConnectionError(
            message=f"Request to OpenRouter API failed: {exc!s}",
            provider_name="openrouter",
            original_error=exc,
        ) from exc

    async def generate_with_usage(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response and return it with token usage and latency.

        Sends the prompt to OpenRouter's API and returns an ``LLMResponse``.
        Supports additional generation parameters via kwargs.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Additional generation parameters:
                - temperature (float): Override default temperature.
                - max_tokens (int): Override default max tokens.
                - model (str): Override default model for this request.

        Returns:
            An ``LLMResponse`` with the generated content and usage stats.

        Raises:
            ProviderConnectionError: If the connection to OpenRouter fails.
            ProviderExecutionError: If the API request fails or returns an error.
        """
        payload = self._build_payload(prompt, **kwargs)
        headers = self._build_headers()

        start_time = time.monotonic()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=120.0,
                )

                # Handle HTTP errors
                if response.status_code != 200:
                    error_data: dict[str, Any] = {}
                    if response.text:
                        try:
                            parsed_error = response.json()
                            if isinstance(parsed_error, dict):
                                error_data = parsed_error
                        except ValueError:
                            error_data = {}
                    self._raise_http_error(
                        response.status_code, response.text, error_data
                    )

                # Parse response
                result = response.json()

                # Extract content
                if (
                    not isinstance(result, dict)
                    or "choices" not in result
                    or not isinstance(result["choices"], list)
                    or len(result["choices"]) == 0
                ):
                    raise ProviderExecutionError(
                        message="No choices returned from OpenRouter API",
                        provider_name="openrouter",
                        details={"response": result},
                    )

                first_choice = result["choices"][0]
                message = (
                    first_choice.get("message")
                    if isinstance(first_choice, dict)
                    else None
                )
                content = message.get("content") if isinstance(message, dict) else None
                if not isinstance(content, str):
                    raise ProviderExecutionError(
                        message="Invalid or missing content in OpenRouter API response",
                        provider_name="openrouter",
                        details={"response": result},
                    )

                latency_ms = (time.monotonic() - start_time) * 1000.0
                usage = self._extract_usage(result)
                return LLMResponse(
                    content=content,
                    model=kwargs.get("model", self.model),
                    usage=usage,
                    provider=self.name,
                    latency_ms=latency_ms,
                )

        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            self._raise_mapped_httpx_error(e)

    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        """Stream generated text chunks from OpenRouter's SSE endpoint.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Additional generation parameters (see ``generate_with_usage``).

        Yields:
            Non-empty text delta strings parsed from SSE data frames.

        Raises:
            ProviderConnectionError: If the connection to OpenRouter fails.
            ProviderExecutionError: If the API returns an error status or invalid stream data.
        """
        payload = self._build_payload(prompt, stream=True, **kwargs)
        headers = self._build_headers()

        try:
            async with (
                httpx.AsyncClient() as client,
                client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=120.0,
                ) as response,
            ):
                if response.status_code != 200:
                    raw_body = (await response.aread()).decode(errors="replace")
                    error_data: dict[str, Any] = {}
                    if raw_body:
                        try:
                            parsed_error = json.loads(raw_body)
                            if isinstance(parsed_error, dict):
                                error_data = parsed_error
                        except json.JSONDecodeError:
                            error_data = {}
                    self._raise_http_error(response.status_code, raw_body, error_data)

                data_lines: list[str] = []
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_lines.append(line.removeprefix("data:").removeprefix(" "))
                        continue
                    if line or not data_lines:
                        continue
                    data_str = "\n".join(data_lines).strip()
                    data_lines.clear()
                    if not data_str:
                        continue
                    if data_str == "[DONE]":
                        break
                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError as e:
                        raise ProviderExecutionError(
                            message=f"Failed to parse OpenRouter stream chunk: {e!s}",
                            provider_name="openrouter",
                            original_error=e,
                        ) from e
                    if not isinstance(event, dict):
                        raise ProviderExecutionError(
                            message="Unexpected OpenRouter stream chunk format",
                            provider_name="openrouter",
                            details={"chunk": event},
                        )
                    error_payload = event.get("error")
                    if error_payload:
                        error_message = self._extract_error_message(
                            error_payload,
                            fallback=str(error_payload),
                        )
                        raise ProviderExecutionError(
                            message=f"OpenRouter API error: {error_message}",
                            provider_name="openrouter",
                            details={"error": error_payload, "response": event},
                        )
                    choices = event.get("choices") or []
                    if choices:
                        first_choice = choices[0]
                        delta_obj = (
                            first_choice.get("delta")
                            if isinstance(first_choice, dict)
                            else None
                        )
                        delta = (
                            delta_obj.get("content")
                            if isinstance(delta_obj, dict)
                            else None
                        )
                        if isinstance(delta, str) and delta:
                            yield delta
        except (ProviderConnectionError, ProviderExecutionError):
            raise
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            self._raise_mapped_httpx_error(e)

    def _extract_usage(self, result: dict[str, Any]) -> TokenUsage:
        """Extract token usage from an OpenRouter API response."""
        usage_data = result.get("usage") or {}
        return TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the LLM.

        Sends the prompt to OpenRouter's API and returns the generated text.
        Supports additional generation parameters via kwargs.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Additional generation parameters (see ``generate_with_usage``).

        Returns:
            The generated text response from the LLM.

        Raises:
            ProviderConnectionError: If the connection to OpenRouter fails.
            ProviderExecutionError: If the API request fails or returns an error.
        """
        response = await self.generate_with_usage(prompt, **kwargs)
        return response.content

    async def get_token_count(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Uses a simple estimation based on whitespace splitting since
        OpenRouter doesn't provide a direct tokenization endpoint.
        For production use, consider using tiktoken for more accurate counts.

        Args:
            text: The text to count tokens for.

        Returns:
            Estimated number of tokens in the text.

        Raises:
            ProviderError: If token counting fails.
        """
        if not text:
            return 0

        # Simple estimation: split by whitespace and punctuation
        # This is a rough approximation; for production, use tiktoken
        tokens = text.split()
        return len(tokens)
