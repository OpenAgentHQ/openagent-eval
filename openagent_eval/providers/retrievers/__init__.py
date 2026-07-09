"""Retriever provider adapters.

This package contains retriever provider adapters that implement the Retriever
interface. Each adapter integrates with a specific vector database or search
engine (Chroma, Qdrant, Pinecone, Weaviate, FAISS, pgvector, Elasticsearch,
an in-memory vector store, BM25, a generic HTTP endpoint, or a mock).

Imports are lazy so optional dependencies are only required when a given
retriever is actually used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openagent_eval.providers.retrievers.bm25 import BM25Retriever
    from openagent_eval.providers.retrievers.chroma import ChromaRetriever
    from openagent_eval.providers.retrievers.elasticsearch import (
        ElasticsearchRetriever,
    )
    from openagent_eval.providers.retrievers.faiss import FAISSRetriever
    from openagent_eval.providers.retrievers.http import HttpRetriever
    from openagent_eval.providers.retrievers.memory import MemoryRetriever
    from openagent_eval.providers.retrievers.mock import MockRetriever
    from openagent_eval.providers.retrievers.pgvector import PGVectorRetriever
    from openagent_eval.providers.retrievers.pinecone import PineconeRetriever
    from openagent_eval.providers.retrievers.qdrant import QdrantRetriever
    from openagent_eval.providers.retrievers.weaviate import WeaviateRetriever


def __getattr__(name: str):
    """Lazy import of retriever classes to avoid requiring all optional deps."""
    mapping = {
        "ChromaRetriever": "openagent_eval.providers.retrievers.chroma",
        "MemoryRetriever": "openagent_eval.providers.retrievers.memory",
        "BM25Retriever": "openagent_eval.providers.retrievers.bm25",
        "HttpRetriever": "openagent_eval.providers.retrievers.http",
        "QdrantRetriever": "openagent_eval.providers.retrievers.qdrant",
        "PineconeRetriever": "openagent_eval.providers.retrievers.pinecone",
        "WeaviateRetriever": "openagent_eval.providers.retrievers.weaviate",
        "FAISSRetriever": "openagent_eval.providers.retrievers.faiss",
        "PGVectorRetriever": "openagent_eval.providers.retrievers.pgvector",
        "ElasticsearchRetriever": "openagent_eval.providers.retrievers.elasticsearch",
        "MockRetriever": "openagent_eval.providers.retrievers.mock",
    }
    if name in mapping:
        import importlib

        module = importlib.import_module(mapping[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ChromaRetriever",
    "MemoryRetriever",
    "BM25Retriever",
    "HttpRetriever",
    "QdrantRetriever",
    "PineconeRetriever",
    "WeaviateRetriever",
    "FAISSRetriever",
    "PGVectorRetriever",
    "ElasticsearchRetriever",
    "MockRetriever",
]
