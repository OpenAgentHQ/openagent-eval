"""Tests for the Elasticsearch retriever (issue #82).

The retriever must use ``AsyncElasticsearch`` and ``await`` the ``search``
call. A synchronous ``Elasticsearch`` client's ``search()`` blocks the event
loop when driven from an ``async def retrieve()``. These tests mock the
``elasticsearch`` async surface so no real Elasticsearch cluster is required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openagent_eval.exceptions.provider import ProviderConnectionError
from openagent_eval.providers.embedders.base import Embedder
from openagent_eval.providers.retrievers.elasticsearch import ElasticsearchRetriever


class _FakeEmbedder(Embedder):
    name = "fake"
    description = "fake embedder for tests"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


def _make_es_mock(resp: dict | None = None) -> tuple[MagicMock, AsyncMock]:
    """Build a fake ``elasticsearch`` module exposing an async client.

    ``AsyncElasticsearch`` is constructed synchronously (no ``await``, matching
    real ``elasticsearch-py`` behaviour), but its ``search`` method is a
    coroutine that must be ``await``-ed.
    """
    if resp is None:
        resp = {
            "hits": {
                "hits": [
                    {"_score": 5.0, "_source": {"content": "doc text"}, "_id": "1"}
                ]
            }
        }

    client = AsyncMock()
    client.search = AsyncMock(return_value=resp)
    client.close = AsyncMock()

    es_module = MagicMock()
    es_module.AsyncElasticsearch = MagicMock(return_value=client)
    # A sync Elasticsearch must NOT exist on the fake; the retriever must not
    # construct or call it.
    del es_module.Elasticsearch
    return es_module, client


def _build_retriever(**kwargs) -> ElasticsearchRetriever:
    return ElasticsearchRetriever(
        index="docs",
        hosts="http://localhost:9200",
        **kwargs,
    )


class TestElasticsearchAsyncClient:
    async def test_retrieve_uses_async_client_and_awaits_search(self):
        es_module, client = _make_es_mock()

        with patch.dict("sys.modules", {"elasticsearch": es_module}):
            retriever = _build_retriever()
            docs = await retriever.retrieve("hello", k=3)

        # Async client class was used (not a sync blocking client).
        es_module.AsyncElasticsearch.assert_called_once()
        # The search call was awaited, not just invoked synchronously.
        client.search.assert_awaited_once()
        assert len(docs) == 1
        assert docs[0].content == "doc text"
        assert docs[0].id == "1"

    async def test_retrieve_knn_mode_awaits_search(self):
        es_module, client = _make_es_mock()

        with patch.dict("sys.modules", {"elasticsearch": es_module}):
            retriever = _build_retriever(
                mode="knn", embedder=_FakeEmbedder(), vector_field="embedding"
            )
            docs = await retriever.retrieve("hello", k=3)

        client.search.assert_awaited_once()
        _, kwargs = client.search.call_args
        assert kwargs["knn"]["query_vector"] == [0.1, 0.2, 0.3]
        assert len(docs) == 1

    async def test_construction_failure_raises_typed_error(self):
        es_module = MagicMock()
        es_module.AsyncElasticsearch = MagicMock(side_effect=RuntimeError("bad config"))
        del es_module.Elasticsearch

        with (
            patch.dict("sys.modules", {"elasticsearch": es_module}),
            pytest.raises(ProviderConnectionError, match="Failed to connect"),
        ):
            _build_retriever()

    async def test_close_terminates_client(self):
        es_module, client = _make_es_mock()

        with patch.dict("sys.modules", {"elasticsearch": es_module}):
            retriever = _build_retriever()
            await retriever.retrieve("q")
            await retriever.close()

        client.close.assert_awaited_once()
