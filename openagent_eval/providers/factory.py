"""Provider factory for OpenAgent Eval.

Maps provider configuration to concrete adapter instances. This is the single
place that knows how to construct an ``LLMProvider`` or ``Retriever`` from a
``Config`` object, keeping the rest of the pipeline provider-agnostic (D003).

A ``mock`` provider is built in for dry-run / CI usage when no API keys or
external services are available.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any

from openagent_eval.exceptions.provider import ProviderError, ProviderNotFoundError
from openagent_eval.plugins.discovery import ENTRY_POINT_GROUPS
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document, LLMResponse, TokenUsage
from openagent_eval.providers.retrievers._validation import (
    validate_retriever_settings,
)

if TYPE_CHECKING:
    from openagent_eval.config.models import (
        EmbedderConfig,
        LLMConfig,
        RetrieverConfig,
    )
    from openagent_eval.providers.embedders.base import Embedder

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


def _retriever_class(key: str) -> type[Retriever]:
    """Load only the selected retriever, preferring installed entry points."""
    entries = entry_points(group=ENTRY_POINT_GROUPS["retrievers"])
    matches = [entry for entry in entries if entry.name.lower() == key]
    if len(matches) > 1:
        raise ProviderError("Multiple installed retrievers use this name", key)
    if matches:
        entry = matches[0]
        try:
            cls = entry.load()
        except Exception as exc:
            raise ProviderError(
                f"Cannot load retriever {entry.value}: {exc}", key
            ) from exc
        if not isinstance(cls, type) or not issubclass(cls, Retriever):
            raise ProviderError(f"{entry.value} must be a Retriever subclass", key)
        return cls
    if key in _RETRIEVER_PROVIDERS:
        return _resolve(_RETRIEVER_PROVIDERS[key])
    available = sorted(set(_RETRIEVER_PROVIDERS) | {entry.name for entry in entries})
    raise ProviderNotFoundError(
        provider_name=key, details={"available_retrievers": ", ".join(available)}
    )


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
    retriever_cls = _retriever_class(key)
    settings = dict(config.settings or {})

    # Catch typos/unknown keys in the free-form settings dict early, before the
    # values reach a provider constructor (which may silently swallow unknown
    # kwargs). Providers opt in by declaring ``SETTINGS_KEYS``.
    allowed_keys = getattr(retriever_cls, "SETTINGS_KEYS", None)
    if allowed_keys is not None:
        unknown = validate_retriever_settings(key, settings, allowed_keys)
        for bad_key in unknown:
            settings.pop(bad_key, None)

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
