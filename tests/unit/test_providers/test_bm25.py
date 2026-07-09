"""Tests for the BM25 retriever."""

from __future__ import annotations

import pytest

rank_bm25 = pytest.importorskip("rank_bm25", reason="rank-bm25 not installed")

from openagent_eval.providers.models import Document
from openagent_eval.providers.retrievers.bm25 import BM25Retriever


DOCS = [
    {"content": "Python is a high-level programming language", "id": "1"},
    {"content": "RAG combines retrieval and generation", "id": "2"},
    {"content": "A vector database stores embeddings", "id": "3"},
]


@pytest.fixture
def retriever() -> BM25Retriever:
    return BM25Retriever(documents=DOCS)


class TestBM25Retrieve:
    async def test_returns_docs(self, retriever: BM25Retriever):
        docs = await retriever.retrieve("programming language", k=2)
        assert len(docs) == 2
        assert all(isinstance(d, Document) for d in docs)

    async def test_scores_normalized(self, retriever: BM25Retriever):
        docs = await retriever.retrieve("vector database", k=3)
        for d in docs:
            assert 0.0 <= d.score <= 1.0

    async def test_empty_corpus(self):
        r = BM25Retriever(documents=[])
        assert await r.retrieve("anything") == []

    async def test_scores_descending(self, retriever: BM25Retriever):
        docs = await retriever.retrieve("retrieval generation RAG", k=3)
        scores = [d.score for d in docs]
        assert scores == sorted(scores, reverse=True)
