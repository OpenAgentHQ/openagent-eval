"""Ollama LLM provider adapter.

This module provides an Ollama adapter for local LLM inference using the
Ollama REST API. It implements the LLMProvider interface for token-counting
and text generation via Ollama's local server.

The adapter tracks token usage through Ollama's response metadata
(eval_count, prompt_eval_count) for cost tracking and budget management.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.models import TokenUsage


class OllamaGenerateRequest(BaseModel):
    """Request model for Ollama generate API.

    Attributes:
        model: The model to use for generation.
        prompt: The input prompt.
        stream: Whether to stream the response.
        options: Optional generation parameters.
    """

    model: str = Field(..., description="Model identifier")
    prompt: str = Field(..., description="Input prompt")
    stream: bool = Field(False, description="Enable streaming")
    options: dict[str, Any] = Field(default_factory=dict, description="Generation options")


class OllamaGenerateResponse(BaseModel):
    """Response model from Ollama generate API.

    Attributes:
        model: The model used for generation.
        response: The generated text.
        done: Whether generation is complete.
        eval_count: Number of tokens generated.
        prompt_eval_count: Number of prompt tokens processed.
        eval_duration: Duration of evaluation in nanoseconds.
        prompt_eval_duration: Duration of prompt evaluation in nanoseconds.
    """

    model: str = Field(..., description="Model identifier")
    response: str = Field(..., description="Generated text")
    done: bool = Field(..., description="Whether generation completed")
    eval_count: int = Field(0, description="Number of tokens generated")
    prompt_eval_count: int = Field(0, description="Number of prompt tokens")
    eval_duration: int = Field(0, description="Evaluation duration in nanoseconds")
    prompt_eval_duration: int = Field(0, description="Prompt evaluation duration in nanoseconds")


class Ollama(LLMProvider):
    """Ollama LLM provider for local inference.

    Provides text generation and token counting via Ollama's local REST API.
    Token usage is tracked through Ollama's response metadata for accurate
    cost tracking without requiring external tokenizers.

    Attributes:
        name: Provider identifier ("ollama").
        description: Human-readable provider description.

    Example:
        ```python
        from openagent_eval.providers.llm.ollama import Ollama

        # Initialize provider
        provider = Ollama(
            base_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.7,
            max_tokens=1024,
        )

        # Generate text
        response = await provider.generate("What is RAG?")
        print(response)

        # Count tokens
        token_count = await provider.get_token_count("Hello world")
        print(f"Token count: {token_count}")
        ```
    """

    name: str = "ollama"
    description: str = "Ollama local LLM inference provider"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout: float = 120.0,
    ) -> None:
        """Initialize the Ollama provider.

        Args:
            base_url: Ollama server URL. Defaults to http://localhost:11434.
            model: Model identifier for Ollama. Defaults to "llama3.2".
            temperature: Sampling temperature (0.0-2.0). Defaults to 0.7.
            max_tokens: Maximum tokens to generate. None for unlimited.
            timeout: Request timeout in seconds. Defaults to 120.0.
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            headers={"Content-Type": "application/json"},
        )

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the Ollama model.

        Args:
            prompt: The input prompt to send to Ollama.
            **kwargs: Optional overrides for model, temperature, max_tokens.

        Returns:
            The generated text response from the model.

        Raises:
            ProviderConnectionError: If unable to connect to Ollama server.
            ProviderExecutionError: If the API call fails or returns an error.
        """
        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)

        # Build request payload
        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        request = OllamaGenerateRequest(
            model=model,
            prompt=prompt,
            stream=False,
            options=options,
        )

        try:
            response = await self._client.post(
                "/api/generate",
                content=request.model_dump_json(),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except httpx.ConnectError as e:
            raise ProviderConnectionError(
                message=f"Failed to connect to Ollama server at {self._base_url}",
                provider_name=self.name,
                original_error=e,
            ) from e
        except httpx.HTTPStatusError as e:
            raise ProviderExecutionError(
                message=f"Ollama API error: {e.response.status_code}",
                provider_name=self.name,
                original_error=e,
                details={"status_code": e.response.status_code, "response": e.response.text},
            ) from e
        except Exception as e:
            raise ProviderExecutionError(
                message=f"Unexpected error calling Ollama: {str(e)}",
                provider_name=self.name,
                original_error=e,
            ) from e

        # Parse response
        try:
            data = response.json()
            ollama_response = OllamaGenerateResponse(**data)
        except Exception as e:
            raise ProviderExecutionError(
                message=f"Failed to parse Ollama response: {str(e)}",
                provider_name=self.name,
                original_error=e,
            ) from e

        if not ollama_response.done:
            raise ProviderExecutionError(
                message="Ollama generation did not complete",
                provider_name=self.name,
                details={"model": model},
            )

        return ollama_response.response

    async def get_token_count(self, text: str) -> int:
        """Count tokens using Ollama's tokenizer endpoint.

        Falls back to word-based approximation if the tokenizer endpoint
        is unavailable.

        Args:
            text: The text to count tokens for.

        Returns:
            The estimated number of tokens in the text.
        """
        try:
            response = await self._client.post(
                "/api/tokenize",
                content={"model": self._model, "content": text},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("token_count", 0)
        except Exception:
            # Fallback to word-based approximation
            return len(text.split())

    def generate_with_usage(
        self, prompt: str, **kwargs: Any
    ) -> tuple[str, TokenUsage]:
        """Generate text and return token usage synchronously.

        This is a helper method that generates text and extracts token usage
        from Ollama's response metadata. For async usage, call generate()
        directly.

        Args:
            prompt: The input prompt.
            **kwargs: Optional parameter overrides.

        Returns:
            Tuple of (generated_text, token_usage).

        Note:
            This method is synchronous for convenience. For async contexts,
            use generate() directly and track usage separately.
        """
        # Build request payload
        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        request = OllamaGenerateRequest(
            model=model,
            prompt=prompt,
            stream=False,
            options=options,
        )

        with httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        ) as client:
            try:
                response = client.post(
                    "/api/generate",
                    content=request.model_dump_json(),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
            except httpx.ConnectError as e:
                raise ProviderConnectionError(
                    message=f"Failed to connect to Ollama server at {self._base_url}",
                    provider_name=self.name,
                    original_error=e,
                ) from e
            except httpx.HTTPStatusError as e:
                raise ProviderExecutionError(
                    message=f"Ollama API error: {e.response.status_code}",
                    provider_name=self.name,
                    original_error=e,
                ) from e
            except Exception as e:
                raise ProviderExecutionError(
                    message=f"Unexpected error calling Ollama: {str(e)}",
                    provider_name=self.name,
                    original_error=e,
                ) from e

            data = response.json()
            ollama_response = OllamaGenerateResponse(**data)

        # Extract token usage from Ollama response metadata
        prompt_tokens = ollama_response.prompt_eval_count
        completion_tokens = ollama_response.eval_count
        total_tokens = prompt_tokens + completion_tokens

        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        return ollama_response.response, usage

    async def generate_with_usage_async(
        self, prompt: str, **kwargs: Any
    ) -> tuple[str, TokenUsage]:
        """Generate text and return token usage asynchronously.

        This method generates text and extracts token usage from Ollama's
        response metadata for accurate cost tracking.

        Args:
            prompt: The input prompt.
            **kwargs: Optional parameter overrides.

        Returns:
            Tuple of (generated_text, token_usage).
        """
        model = kwargs.get("model", self._model)
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        request = OllamaGenerateRequest(
            model=model,
            prompt=prompt,
            stream=False,
            options=options,
        )

        try:
            response = await self._client.post(
                "/api/generate",
                content=request.model_dump_json(),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except httpx.ConnectError as e:
            raise ProviderConnectionError(
                message=f"Failed to connect to Ollama server at {self._base_url}",
                provider_name=self.name,
                original_error=e,
            ) from e
        except httpx.HTTPStatusError as e:
            raise ProviderExecutionError(
                message=f"Ollama API error: {e.response.status_code}",
                provider_name=self.name,
                original_error=e,
            ) from e
        except Exception as e:
            raise ProviderExecutionError(
                message=f"Unexpected error calling Ollama: {str(e)}",
                provider_name=self.name,
                original_error=e,
            ) from e

        data = response.json()
        ollama_response = OllamaGenerateResponse(**data)

        # Extract token usage from Ollama response metadata
        prompt_tokens = ollama_response.prompt_eval_count
        completion_tokens = ollama_response.eval_count
        total_tokens = prompt_tokens + completion_tokens

        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        return ollama_response.response, usage

    async def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        await self._client.aclose()

    async def __aenter__(self) -> Ollama:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return (
            f"Ollama(base_url={self._base_url!r}, model={self._model!r}, "
            f"temperature={self._temperature}, max_tokens={self._max_tokens})"
        )
