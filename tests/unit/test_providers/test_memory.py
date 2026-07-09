"""Tests for the in-memory vector retriever."""

from __future__ import annotations

import pytest

from openagent_eval.exceptions.provider import ProviderConnectionError
from openagent_eval.providers.embedders.mock import MockEmbedder
from openagent_eval.providers.models import Document
from openagent_eval.providers.retrievers.memory import MemoryRetriever


DOCS = [
    {"content": "Python is a high-level programming language", "id": "1"},
    {"content": "RAG combines retrieval and generation", "id": "2"},
    {"content": "A vector database stores embeddings", "id": "3"},
]


@pytest.fixture
def retriever() -> MemoryRetriever:
    return MemoryRetriever(documents=DOCS, embedder=MockEmbedder(dimension=32))


class TestMemoryRetrieverInit:
    def test_requires_embedder(self):
        with pytest.raises(ProviderConnectionError, match="requires an embedder"):
            MemoryRetriever(documents=DOCS)

    def test_name(self, retriever: MemoryRetriever):
        assert retriever.name == "memory"


class TestMemoryRetrieve:
    async def test_returns_k_docs(self, retriever: MemoryRetriever):
        docs = await retriever.retrieve("programming language", k=2)
        assert len(docs) == 2
        assert all(isinstance(d, Document) for d in docs)

    async def test_scores_in_range(self, retriever: MemoryRetriever):
        docs = await retriever.retrieve("vector database", k=3)
        for d in docs:
            assert 0.0 <= d.score <= 1.0

    async def test_empty_corpus(self):
        r = MemoryRetriever(documents=[], embedder=MockEmbedder())
        assert await r.retrieve("anything") == []

    async def test_scores_descending(self, retriever: MemoryRetriever):
        docs = await retriever.retrieve("RAG retrieval generation", k=3)
        scores = [d.score for d in docs]
        assert scores == sorted(scores, reverse=True)
