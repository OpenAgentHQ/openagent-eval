"""Tests for the provider factory (LLM registry resolution and config wiring)."""

from __future__ import annotations

from openagent_eval.config.models import LLMConfig
from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.factory import (
    _LLM_PROVIDERS,
    _resolve,
    get_llm_provider,
)

# Expected class name for each registered provider key.
_EXPECTED_CLASSES = {
    "openai": "OpenAIProvider",
    "gemini": "Gemini",
    "anthropic": "Anthropic",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "ollama": "Ollama",
    "mock": "MockLLMProvider",
}


def test_registry_resolves_to_correct_classes() -> None:
    """C1: every registry entry must point at a real, correctly-named class."""
    for key, entry in _LLM_PROVIDERS.items():
        cls = _resolve(entry)
        assert issubclass(cls, LLMProvider)
        assert cls.__name__ == _EXPECTED_CLASSES[key], (
            f"Registry entry for '{key}' resolved to {cls.__name__}, "
            f"expected {_EXPECTED_CLASSES[key]}"
        )


def test_get_llm_provider_accepts_config_for_all_providers() -> None:
    """C2: the factory must be able to construct every provider from an LLMConfig.

    Without API keys the providers raise a provider-specific error (connection
    or missing dependency), but they must NOT raise AttributeError (wrong class
    name) or TypeError (unexpected config kwarg).
    """
    for key in _LLM_PROVIDERS:
        config = LLMConfig(provider=key, model="test-model")
        try:
            provider = get_llm_provider(config)
        except (ProviderConnectionError, ProviderError):
            # Expected when no API key / SDK is available.
            continue
        except (AttributeError, TypeError) as exc:
            raise AssertionError(
                f"get_llm_provider('{key}') raised {type(exc).__name__}: {exc}. "
                "The factory could not resolve or construct the provider."
            ) from exc
        # If it constructed (e.g. mock), it must be a usable LLMProvider.
        assert isinstance(provider, LLMProvider)


def test_mock_provider_constructs_via_factory() -> None:
    """The mock provider should build end-to-end through the factory."""
    config = LLMConfig(provider="mock", model="mock-model")
    provider = get_llm_provider(config)
    assert isinstance(provider, LLMProvider)
    assert provider.name == "mock"
