"""Tests for the pgvector retriever (issue #81).

The retriever must use an async ``psycopg`` connection with the async cursor
API. A synchronous ``psycopg.connect`` cannot be driven by ``await
cur.execute(...)`` and crashes on the first query. These tests mock the
``psycopg`` async surface so no real Postgres is required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openagent_eval.exceptions.provider import ProviderConnectionError
from openagent_eval.providers.embedders.base import Embedder
from openagent_eval.providers.retrievers.pgvector import PGVectorRetriever


class _FakeEmbedder(Embedder):
    name = "fake"
    description = "fake embedder for tests"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


def _make_psycopg_mock() -> MagicMock:
    """Build a fake ``psycopg`` module exposing an async connection.

    ``AsyncConnection.connect`` is a coroutine returning a connection whose
    ``cursor()`` is a *synchronous* method that returns an async context
    manager (matching real ``psycopg`` async behaviour).
    """
    cursor = AsyncMock()
    cursor.__aenter__.return_value = cursor
    cursor.fetchall.return_value = [("doc text", 0.95)]

    conn = AsyncMock()
    conn.cursor = MagicMock(return_value=cursor)

    psycopg = MagicMock()
    psycopg.AsyncConnection.connect = AsyncMock(return_value=conn)
    # A sync connect must NOT exist on the fake; the retriever must not call it.
    return psycopg


def _build_retriever() -> PGVectorRetriever:
    return PGVectorRetriever(
        table="docs",
        embedder=_FakeEmbedder(),
        dsn="postgresql://localhost/test",
    )


class TestPGVectorAsyncConnection:
    async def test_retrieve_uses_async_connection(self):
        psycopg = _make_psycopg_mock()

        with patch.dict("sys.modules", {"psycopg": psycopg}):
            retriever = _build_retriever()
            docs = await retriever.retrieve("hello", k=3)

        # Async connection was opened (not the sync blocking connect).
        psycopg.AsyncConnection.connect.assert_awaited_once()
        # The async cursor API was driven via await.
        cursor = psycopg.AsyncConnection.connect.return_value.cursor.return_value
        cursor.execute.assert_awaited_once()
        cursor.fetchall.assert_awaited_once()
        assert len(docs) == 1
        assert docs[0].content == "doc text"
        assert docs[0].score == 0.95

    async def test_connection_is_lazy_and_cached(self):
        psycopg = _make_psycopg_mock()

        with patch.dict("sys.modules", {"psycopg": psycopg}):
            retriever = _build_retriever()
            # No connection before first retrieve.
            assert retriever._conn is None
            await retriever.retrieve("q1")
            await retriever.retrieve("q2")

        # Opened exactly once and reused across calls.
        psycopg.AsyncConnection.connect.assert_awaited_once()
        assert retriever._conn is not None

    async def test_connection_failure_raises_typed_error(self):
        psycopg = MagicMock()
        psycopg.AsyncConnection.connect = AsyncMock(
            side_effect=RuntimeError("connection refused")
        )

        with patch.dict("sys.modules", {"psycopg": psycopg}):
            retriever = _build_retriever()
            with pytest.raises(ProviderConnectionError, match="Failed to connect"):
                await retriever.retrieve("q")

    async def test_close_terminates_connection(self):
        psycopg = _make_psycopg_mock()

        with patch.dict("sys.modules", {"psycopg": psycopg}):
            retriever = _build_retriever()
            await retriever.retrieve("q")
            assert retriever._conn is not None
            await retriever.close()
            assert retriever._conn is None
            psycopg.AsyncConnection.connect.return_value.close.assert_awaited_once()
