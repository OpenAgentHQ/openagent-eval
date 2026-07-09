"""Tests for retriever/embedder factory resolution."""

from __future__ import annotations

import pytest

from openagent_eval.config.models import EmbedderConfig, RetrieverConfig
from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderNotFoundError,
)
from openagent_eval.providers.factory import get_embedder, get_retriever


class TestGetEmbedder:
    def test_mock_embedder(self):
        emb = get_embedder(EmbedderConfig(provider="mock", model="mock"))
        assert emb.name == "mock"

    def test_unknown_embedder(self):
        with pytest.raises(ProviderNotFoundError, match="available_embedders"):
            get_embedder(EmbedderConfig(provider="nope"))


class TestGetRetriever:
    def test_memory_with_embedder(self):
        cfg = RetrieverConfig(
            provider="memory",
            settings={"documents": [{"content": "x", "id": "1"}]},
            embedder=EmbedderConfig(provider="mock", model="mock"),
        )
        r = get_retriever(cfg)
        assert r.name == "memory"
        assert r._embedder is not None

    def test_vector_retriever_without_embedder_errors(self):
        cfg = RetrieverConfig(
            provider="memory", settings={"documents": [{"content": "x"}]}
        )
        with pytest.raises(ProviderConnectionError, match="requires an embedder"):
            get_retriever(cfg)

    def test_unknown_retriever(self):
        with pytest.raises(ProviderNotFoundError, match="available_retrievers"):
            get_retriever(RetrieverConfig(provider="does-not-exist"))

    def test_bm25_without_embedder(self):
        # BM25 is lexical and needs no embedder.
        r = get_retriever(RetrieverConfig(provider="bm25", settings={"documents": [{"content": "x"}]}))
        assert r.name == "bm25"
