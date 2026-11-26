"""Apply reusable provider contracts to the built-in mock implementations."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.llm.mock import MockLLMProvider
from openagent_eval.providers.retrievers.mock import MockRetriever
from tests.contract.provider_contracts import LLMProviderContract, RetrieverContract


class TestMockLLMProviderContract(LLMProviderContract):
    @pytest.fixture
    def provider(self) -> Iterator[LLMProvider]:
        yield MockLLMProvider()


class TestMockRetrieverContract(RetrieverContract):
    @pytest.fixture
    def retriever(self) -> Iterator[Retriever]:
        yield MockRetriever()
