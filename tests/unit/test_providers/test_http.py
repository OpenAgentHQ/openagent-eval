"""Tests for the generic HTTP retriever."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from openagent_eval.providers.retrievers.http import HttpRetriever, _dig


class TestDig:
    def test_nested(self):
        obj = {"a": {"b": [{"c": 42}]}}
        assert _dig(obj, "a.b.0.c") == 42

    def test_missing(self):
        assert _dig({"a": 1}, "a.b.c") is None

    def test_none_path(self):
        assert _dig({"x": 1}, None) == {"x": 1}


def _fake_client(payload: dict[str, Any]) -> MagicMock:
    """Build a mock httpx.AsyncClient returning ``payload``."""
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    client = MagicMock()
    client.request = AsyncMock(return_value=response)
    ctx = MagicMock()
    ctx.__aenter__.return_value = client
    ctx.__aexit__.return_value = False
    mock = MagicMock()
    mock.return_value = ctx
    return mock


class TestHttpRetriever:
    async def test_post_mapping(self, monkeypatch: pytest.MonkeyPatch):
        payload = {
            "results": [
                {"content": "doc one", "id": "a", "score": 0.9},
                {"content": "doc two", "id": "b", "score": 0.4},
            ]
        }
        monkeypatch.setattr(
            "openagent_eval.providers.retrievers.http.httpx.AsyncClient",
            _fake_client(payload),
        )
        retriever = HttpRetriever(
            url="http://example.test/search",
            results_path="results",
            content_path="content",
            id_path="id",
            score_path="score",
        )
        docs = await retriever.retrieve("query", k=2)
        assert len(docs) == 2
        assert docs[0].content == "doc one"
        assert docs[0].id == "a"
        assert docs[0].score == pytest.approx(0.9)

    async def test_rank_based_when_no_score(self, monkeypatch: pytest.MonkeyPatch):
        payload = {
            "results": [
                {"content": "first"},
                {"content": "second"},
                {"content": "third"},
            ]
        }
        monkeypatch.setattr(
            "openagent_eval.providers.retrievers.http.httpx.AsyncClient",
            _fake_client(payload),
        )
        retriever = HttpRetriever(
            url="http://example.test/search",
            results_path="results",
        )
        docs = await retriever.retrieve("query", k=3)
        assert [d.content for d in docs] == ["first", "second", "third"]
        # rank-based: best first == 1.0
        assert docs[0].score == 1.0

    def test_requires_url(self):
        with pytest.raises(Exception, match="requires a 'url'"):
            HttpRetriever(url="")
