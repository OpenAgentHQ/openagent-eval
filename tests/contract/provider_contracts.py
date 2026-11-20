"""Reusable contract tests for offline LLM and retriever providers.

Concrete providers can subclass these test classes and override the ``provider``
fixture to run the same public-interface checks without making network calls.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document


class LLMProviderContract:
    """Shared public contract for concrete LLM providers."""

    @pytest.fixture
    def provider(self) -> Iterator[LLMProvider]:
        """Return a configured provider with external clients mocked."""
        raise NotImplementedError

    def test_metadata_is_available(self, provider: LLMProvider) -> None:
        assert isinstance(provider.name, str) and provider.name.strip()
        assert isinstance(provider.description, str) and provider.description.strip()
        assert provider.model_name is None or isinstance(provider.model_name, str)

    def test_valid_inputs_are_accepted(self, provider: LLMProvider) -> None:
        provider.validate_inputs(prompt="contract test")

    async def test_generate_returns_text(self, provider: LLMProvider) -> None:
        result = await provider.generate("contract test")
        assert isinstance(result, str)

    async def test_token_count_is_non_negative(self, provider: LLMProvider) -> None:
        count = await provider.get_token_count("contract test")
        assert isinstance(count, int)
        assert count >= 0


class RetrieverContract:
    """Shared public contract for concrete retrievers."""

    @pytest.fixture
    def retriever(self) -> Iterator[Retriever]:
        """Return a configured retriever backed by local or fake data."""
        raise NotImplementedError

    def test_metadata_is_available(self, retriever: Retriever) -> None:
        assert isinstance(retriever.name, str) and retriever.name.strip()
        assert isinstance(retriever.description, str) and retriever.description.strip()

    def test_valid_inputs_are_accepted(self, retriever: Retriever) -> None:
        retriever.validate_inputs(query="contract test", k=2)

    @pytest.mark.parametrize(
        ("query", "k", "message"),
        [
            (123, 2, "Query must be a string"),
            ("contract test", 0, "k must be positive"),
        ],
    )
    def test_invalid_inputs_raise_value_error(
        self,
        retriever: Retriever,
        query: object,
        k: int,
        message: str,
    ) -> None:
        with pytest.raises(ValueError, match=message):
            retriever.validate_inputs(query=query, k=k)

    async def test_retrieve_returns_documents_within_limit(
        self, retriever: Retriever
    ) -> None:
        documents = await retriever.retrieve("contract test", k=2)
        assert isinstance(documents, list)
        assert len(documents) <= 2
        assert all(isinstance(document, Document) for document in documents)


__all__ = ["LLMProviderContract", "RetrieverContract"]
