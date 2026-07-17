"""Tests for early validation of retriever ``settings`` keys (issue #116)."""

from __future__ import annotations

import logging

import pytest

from openagent_eval.config.models import RetrieverConfig
from openagent_eval.exceptions.provider import ProviderConnectionError
from openagent_eval.providers.factory import get_retriever
from openagent_eval.providers.retrievers._validation import (
    validate_retriever_settings,
)

CHROMA_KEYS = {"collection_name", "persist_directory", "distance_fn"}


class TestValidateRetrieverSettings:
    """Unit tests for the validation helper in isolation."""

    def test_unknown_key_is_reported_and_named(self, caplog):
        with caplog.at_level(logging.WARNING):
            unknown = validate_retriever_settings(
                "chroma", {"collectoin_name": "docs"}, CHROMA_KEYS
            )

        assert unknown == ["collectoin_name"]
        assert "collectoin_name" in caplog.text
        # The suggestion points at the closest real key.
        assert "Did you mean 'collection_name'?" in caplog.text

    def test_all_known_keys_pass(self, caplog):
        with caplog.at_level(logging.WARNING):
            unknown = validate_retriever_settings(
                "chroma",
                {
                    "collection_name": "docs",
                    "persist_directory": "./db",
                    "distance_fn": "cosine",
                },
                CHROMA_KEYS,
            )

        assert unknown == []
        assert "Unknown setting" not in caplog.text

    def test_unknown_key_without_close_match_has_no_suggestion(self, caplog):
        with caplog.at_level(logging.WARNING):
            unknown = validate_retriever_settings("chroma", {"zzzzzz": 1}, CHROMA_KEYS)

        assert unknown == ["zzzzzz"]
        assert "zzzzzz" in caplog.text
        assert "Did you mean" not in caplog.text


class TestFactorySettingsValidation:
    """The factory wires validation into ``get_retriever`` before build."""

    def test_typo_in_qdrant_settings_warns_with_suggestion(self, caplog):
        cfg = RetrieverConfig(
            provider="qdrant",
            settings={"collection_name": "docs", "collectoin_name": "docs"},
        )
        # qdrant still errors (no embedder); validation runs first.
        with (
            caplog.at_level(logging.WARNING),
            pytest.raises(ProviderConnectionError),
        ):
            get_retriever(cfg)

        assert "collectoin_name" in caplog.text
        assert "Did you mean 'collection_name'?" in caplog.text

    def test_known_qdrant_settings_emit_no_unknown_warning(self, caplog):
        cfg = RetrieverConfig(
            provider="qdrant",
            settings={
                "collection_name": "docs",
                "url": "http://localhost:6333",
                "prefer_grpc": True,
                "distance": "Cosine",
            },
        )
        with (
            caplog.at_level(logging.WARNING),
            pytest.raises(ProviderConnectionError),
        ):
            get_retriever(cfg)

        assert "Unknown setting" not in caplog.text

    def test_chroma_declares_expected_settings_keys(self):
        pytest.importorskip("chromadb")
        from openagent_eval.providers.retrievers.chroma import ChromaRetriever

        assert set(ChromaRetriever.SETTINGS_KEYS) == CHROMA_KEYS
