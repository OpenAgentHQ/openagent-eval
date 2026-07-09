"""Base LLM provider interface.

This module defines the abstract LLMProvider interface that all LLM provider
adapters must implement. Concrete providers (OpenAI, Gemini, Anthropic, etc.)
subclass this interface and provide actual API integrations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base class for all LLM provider adapters.

    Every LLM provider in OpenAgent Eval must implement this interface. The
    provider receives a prompt and returns generated text, along with token
    counting capabilities for cost tracking.

    This interface follows the adapter pattern from hexagonal architecture:
    it is an outbound port that concrete adapters (OpenAI, Gemini, etc.)
    implement to integrate with specific LLM APIs.

    Attributes:
        name: Human-readable name of the provider (e.g., "openai", "gemini").
        description: Brief description of the provider's capabilities.

    Example:
        ```python
        class MyProvider(LLMProvider):
            name = "my_provider"
            description = "A custom LLM provider"

            async def generate(self, prompt: str, **kwargs: Any) -> str:
                # Implementation that calls the LLM API
                return "Generated text"

            async def get_token_count(self, text: str) -> int:
                # Implementation that counts tokens
                return len(text.split())
        ```
    """

    name: str
    description: str

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt to send to the LLM.
            **kwargs: Provider-specific parameters (e.g., temperature,
                max_tokens, model override).

        Returns:
            The generated text response from the LLM.

        Raises:
            ProviderError: If the generation fails due to API errors,
                authentication issues, or other provider-specific problems.
        """
        ...

    @abstractmethod
    async def get_token_count(self, text: str) -> int:
        """Count the number of tokens in the given text.

        This method is used for cost tracking and budget management. The
        implementation should use the provider's tokenization logic when
        available, or fall back to an approximation.

        Args:
            text: The text to count tokens for.

        Returns:
            The number of tokens in the text.

        Raises:
            ProviderError: If token counting fails.
        """
        pass

    def validate_inputs(self, **kwargs: Any) -> None:  # noqa: B027
        """Validate provider inputs before execution.

        Override this method to add custom input validation for specific
        providers. The default implementation does nothing.

        Args:
            **kwargs: Inputs to validate.

        Raises:
            ProviderError: If inputs are invalid.
        """
