"""Provider factory for OpenAgent Eval.

Maps provider configuration to concrete adapter instances. This is the single
place that knows how to construct an ``LLMProvider`` or ``Retriever`` from a
``Config`` object, keeping the rest of the pipeline provider-agnostic (D003).

A ``mock`` provider is built in for dry-run / CI usage when no API keys or
external services are available.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.config.models import (
    EmbedderConfig,
    LLMConfig,
    RetrieverConfig,
)
from openagent_eval.exceptions.provider import ProviderNotFoundError
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.embedders.base import Embedder
from openagent_eval.providers.models import Document, LLMResponse, TokenUsage

# --------------------------------------------------------------------------- #
# LLM provider registry                                                       #
# --------------------------------------------------------------------------- #

_LLM_PROVIDERS: dict[str, str] = {
    "openai": "openagent_eval.providers.llm.openai:OpenAIProvider",
    "gemini": "openagent_eval.providers.llm.gemini:Gemini",
    "anthropic": "openagent_eval.providers.llm.anthropic:Anthropic",
    "groq": "openagent_eval.providers.llm.groq:Groq",
    "openrouter": "openagent_eval.providers.llm.openrouter:OpenRouter",
    "ollama": "openagent_eval.providers.llm.ollama:Ollama",
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
    "memory": "openagent_eval.providers.retrievers.memory:MemoryRetriever",
    "bm25": "openagent_eval.providers.retrievers.bm25:BM25Retriever",
    "http": "openagent_eval.providers.retrievers.http:HttpRetriever",
    "qdrant": "openagent_eval.providers.retrievers.qdrant:QdrantRetriever",
    "pinecone": "openagent_eval.providers.retrievers.pinecone:PineconeRetriever",
    "weaviate": "openagent_eval.providers.retrievers.weaviate:WeaviateRetriever",
    "faiss": "openagent_eval.providers.retrievers.faiss:FAISSRetriever",
    "pgvector": "openagent_eval.providers.retrievers.pgvector:PGVectorRetriever",
    "elasticsearch": "openagent_eval.providers.retrievers.elasticsearch:ElasticsearchRetriever",
    "mock": "openagent_eval.providers.retrievers.mock:MockRetriever",
}


def get_retriever(config: RetrieverConfig) -> Retriever:
    """Construct a retriever from configuration.

    If the retriever configuration declares an ``embedder``, it is built and
    injected so vector retrievers can embed queries/documents locally.

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

    embedder = None
    if config.embedder is not None:
        embedder = get_embedder(config.embedder)
    if embedder is not None:
        settings.setdefault("embedder", embedder)

    return retriever_cls(**settings)


# --------------------------------------------------------------------------- #
# Embedder registry                                                          #
# --------------------------------------------------------------------------- #

_EMBEDDER_PROVIDERS: dict[str, str] = {
    "sentence_transformers": (
        "openagent_eval.providers.embedders.sentence_transformers:"
        "SentenceTransformerEmbedder"
    ),
    "sentence-transformers": (
        "openagent_eval.providers.embedders.sentence_transformers:"
        "SentenceTransformerEmbedder"
    ),
    "mock": "openagent_eval.providers.embedders.mock:MockEmbedder",
}


def get_embedder(config: EmbedderConfig) -> Embedder:
    """Construct an embedder from configuration.

    Args:
        config: The embedder configuration.

    Returns:
        An instantiated ``Embedder``.

    Raises:
        ProviderNotFoundError: If the embedder name is unknown.
    """
    key = (config.provider or "").lower().strip()
    if key not in _EMBEDDER_PROVIDERS:
        available = ", ".join(sorted(_EMBEDDER_PROVIDERS))
        raise ProviderNotFoundError(
            provider_name=key,
            details={"available_embedders": available},
        )
    embedder_cls = _resolve(_EMBEDDER_PROVIDERS[key])
    settings = dict(config.settings or {})
    return embedder_cls(model=config.model, **settings)


__all__ = [
    "Document",
    "LLMProvider",
    "LLMResponse",
    "Retriever",
    "TokenUsage",
    "get_llm_provider",
    "get_retriever",
]
