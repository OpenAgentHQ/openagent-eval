"""Tests for the synthetic data CLI command."""

from __future__ import annotations

import asyncio

from openagent_eval.cli.commands.synth import _create_provider
from openagent_eval.providers.llm.mock import MockLLMProvider


def test_create_provider_uses_offline_mock_provider() -> None:
    """The mock CLI option must not fall back to a network provider."""
    provider = _create_provider("mock", "synthetic-test-model")

    assert isinstance(provider, MockLLMProvider)

    response = asyncio.run(provider.generate_with_usage("test prompt"))
    assert response.provider == "mock"
    assert response.model == "synthetic-test-model"
