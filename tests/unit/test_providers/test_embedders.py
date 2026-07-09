"""Tests for the embedder abstraction."""

from __future__ import annotations

import pytest

from openagent_eval.providers.embedders.base import Embedder
from openagent_eval.providers.embedders.mock import MockEmbedder


class TestMockEmbedder:
    async def test_embed_returns_fixed_dimension(self):
        emb = MockEmbedder(dimension=16)
        vectors = await emb.embed(["hello", "world"])
        assert len(vectors) == 2
        assert all(len(v) == 16 for v in vectors)

    async def test_deterministic(self):
        emb = MockEmbedder(dimension=16)
        a = await emb.embed(["same text"])
        b = await emb.embed(["same text"])
        assert a == b

    async def test_normalized(self):
        emb = MockEmbedder(dimension=32)
        (vec,) = await emb.embed(["anything"])
        norm = sum(x * x for x in vec) ** 0.5
        assert norm == pytest.approx(1.0, abs=1e-6)

    async def test_embed_query(self):
        emb = MockEmbedder(dimension=8)
        vec = await emb.embed_query("query")
        assert len(vec) == 8

    def test_is_embedder(self):
        assert isinstance(MockEmbedder(), Embedder)


class TestSentenceTransformerEmbedder:
    sentence_transformers = pytest.importorskip(
        "sentence_transformers", reason="sentence-transformers not installed"
    )

    async def test_embed_dimension(self):
        from openagent_eval.providers.embedders.sentence_transformers import (
            SentenceTransformerEmbedder,
        )

        emb = SentenceTransformerEmbedder(model="all-MiniLM-L6-v2")
        assert emb.dimension == 384
        vectors = await emb.embed(["What is RAG?", "Python is a language"])
        assert len(vectors) == 2
        assert len(vectors[0]) == 384
