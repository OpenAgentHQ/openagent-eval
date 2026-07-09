"""Provider factory for OpenAgent Eval.

Maps provider configuration to concrete adapter instances. This is the single
place that knows how to construct an ``LLMProvider`` or ``Retriever`` from a
``Config`` object, keeping the rest of the pipeline provider-agnostic (D003).

A ``mock`` provider is built in for dry-run / CI usage when no API keys or
external services are available.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.config.models import LLMConfig, RetrieverConfig
from openagent_eval.exceptions.provider import ProviderNotFoundError
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document, LLMResponse, TokenUsage

# --------------------------------------------------------------------------- #
# LLM provider registry                                                       #
# --------------------------------------------------------------------------- #

_LLM_PROVIDERS: dict[str, str] = {
    "openai": "openagent_eval.providers.llm.openai:OpenAIProvider",
    "gemini": "openagent_eval.providers.llm.gemini:GeminiProvider",
    "anthropic": "openagent_eval.providers.llm.anthropic:AnthropicProvider",
    "groq": "openagent_eval.providers.llm.groq:GroqProvider",
    "openrouter": "openagent_eval.providers.llm.openrouter:OpenRouterProvider",
    "ollama": "openagent_eval.providers.llm.ollama:OllamaProvider",
    "mock": "openagent_eval.providers.llm.mock:MockLLMProvider",
}


def _resolve(entry: str) -> type[Any]:
    """Resolve a ``module:Class`` string to a class object."""
    import importlib

    module_path, _, class_name = entry.partition(":")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_llm_provider(config: LLMConfig) -> LLMProvider:
    """Construct an LLM provider from configuration.

    Args:
        config: The LLM configuration.

    Returns:
        An instantiated ``LLMProvider``.

    Raises:
        ProviderNotFoundError: If the provider name is unknown.
    """
    key = (config.provider or "").lower().strip()
    if key not in _LLM_PROVIDERS:
        available = ", ".join(sorted(_LLM_PROVIDERS))
        raise ProviderNotFoundError(
            provider_name=key,
            details={"available_llm_providers": available},
        )
    provider_cls = _resolve(_LLM_PROVIDERS[key])
    return provider_cls(config=config)


# --------------------------------------------------------------------------- #
# Retriever registry                                                         #
# --------------------------------------------------------------------------- #

_RETRIEVER_PROVIDERS: dict[str, str] = {
    "chroma": "openagent_eval.providers.retrievers.chroma:ChromaRetriever",
    "chromadb": "openagent_eval.providers.retrievers.chroma:ChromaRetriever",
    "mock": "openagent_eval.providers.retrievers.mock:MockRetriever",
}


def get_retriever(config: RetrieverConfig) -> Retriever:
    """Construct a retriever from configuration.

    Args:
        config: The retriever configuration.

    Returns:
        An instantiated ``Retriever``.

    Raises:
        ProviderNotFoundError: If the retriever name is unknown.
    """
    key = (config.provider or "").lower().strip()
    if key not in _RETRIEVER_PROVIDERS:
        available = ", ".join(sorted(_RETRIEVER_PROVIDERS))
        raise ProviderNotFoundError(
            provider_name=key,
            details={"available_retrievers": available},
        )
    retriever_cls = _resolve(_RETRIEVER_PROVIDERS[key])
    settings = dict(config.settings or {})
    return retriever_cls(**settings)


__all__ = [
    "Document",
    "LLMProvider",
    "LLMResponse",
    "Retriever",
    "TokenUsage",
    "get_llm_provider",
    "get_retriever",
]
