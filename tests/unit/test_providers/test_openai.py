"""Tests for OpenAI LLM provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from openagent_eval.config.models import LLMConfig
from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.llm.openai import OpenAIProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_openai_env(monkeypatch: pytest.MonkeyPatch):
    """Set OPENAI_API_KEY env var."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-1234567890")


@pytest.fixture
def mock_openai_client():
    """Create a mock AsyncOpenAI client."""
    client = AsyncMock()
    return client


@pytest.fixture
def provider_with_key():
    """Create an OpenAIProvider with an explicit API key."""
    return OpenAIProvider(api_key="sk-test-key-1234567890")


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestOpenAIInit:
    """Tests for OpenAIProvider initialization."""

    def test_init_with_explicit_api_key(self):
        """Provider initializes with explicit API key."""
        provider = OpenAIProvider(api_key="sk-test-key-1234567890")
        assert provider.name == "openai"
        assert provider.description == "OpenAI LLM provider (GPT-4o, GPT-4, etc.)"
        assert provider._model == "gpt-4o"
        assert provider._temperature == 0.0
        assert provider._max_tokens is None

    def test_init_from_env_var(self, mock_openai_env):
        """Provider initializes from OPENAI_API_KEY env var."""
        provider = OpenAIProvider()
        assert provider._api_key == "sk-test-key-1234567890"

    def test_init_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Provider raises ProviderConnectionError without API key."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ProviderConnectionError, match="API key not provided"):
            OpenAIProvider()

    def test_init_with_config(self):
        """Provider initializes from LLMConfig."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="sk-config-key-1234567890",
            temperature=0.5,
            max_tokens=512,
        )
        provider = OpenAIProvider(config=config)
        assert provider._model == "gpt-4"
        assert provider._temperature == 0.5
        assert provider._max_tokens == 512

    def test_init_with_custom_params(self):
        """Provider initializes with custom parameters."""
        provider = OpenAIProvider(
            api_key="sk-test-key-1234567890",
            model="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2048,
        )
        assert provider._model == "gpt-4-turbo"
        assert provider._temperature == 0.7
        assert provider._max_tokens == 2048


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------
class TestOpenAIGenerate:
    """Tests for OpenAIProvider.generate()."""

    @pytest.mark.asyncio
    async def test_generate_success(self, provider_with_key: OpenAIProvider):
        """generate() returns content on successful API call."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Hello, world!"))]
        mock_completion.usage = MagicMock(total_tokens=10)

        provider_with_key._client = AsyncMock()
        provider_with_key._client.chat.completions.create = AsyncMock(return_value=mock_completion)

        result = await provider_with_key.generate("Test prompt")
        assert result == "Hello, world!"

    @pytest.mark.asyncio
    async def test_generate_with_system_message(self, provider_with_key: OpenAIProvider):
        """generate() includes system message when provided."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_completion.usage = MagicMock(total_tokens=5)

        provider_with_key._client = AsyncMock()
        provider_with_key._client.chat.completions.create = AsyncMock(return_value=mock_completion)

        result = await provider_with_key.generate(
            "Test prompt",
            system_message="You are a helpful assistant",
        )
        assert result == "Response"

        # Verify messages include system message
        call_args = provider_with_key._client.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_empty_choices_raises(self, provider_with_key: OpenAIProvider):
        """generate() raises ProviderExecutionError on empty choices."""
        mock_completion = MagicMock()
        mock_completion.choices = []

        provider_with_key._client = AsyncMock()
        provider_with_key._client.chat.completions.create = AsyncMock(return_value=mock_completion)

        with pytest.raises(ProviderExecutionError, match="empty choices"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_connection_error(self, provider_with_key: OpenAIProvider):
        """generate() raises ProviderConnectionError on connection failure."""
        provider_with_key._client = AsyncMock()
        provider_with_key._client.chat.completions.create = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_timeout_error(self, provider_with_key: OpenAIProvider):
        """generate() raises ProviderConnectionError on timeout."""
        provider_with_key._client = AsyncMock()
        provider_with_key._client.chat.completions.create = AsyncMock(
            side_effect=Exception("Request timeout")
        )

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_api_error(self, provider_with_key: OpenAIProvider):
        """generate() raises ProviderExecutionError on API error."""
        provider_with_key._client = AsyncMock()
        provider_with_key._client.chat.completions.create = AsyncMock(
            side_effect=Exception("Invalid request")
        )

        with pytest.raises(ProviderExecutionError, match="execution failed"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_with_temperature_override(self, provider_with_key: OpenAIProvider):
        """generate() respects temperature override."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
        mock_completion.usage = MagicMock(total_tokens=5)

        provider_with_key._client = AsyncMock()
        provider_with_key._client.chat.completions.create = AsyncMock(return_value=mock_completion)

        await provider_with_key.generate("Test", temperature=0.9)

        call_args = provider_with_key._client.chat.completions.create.call_args
        params = call_args.kwargs if call_args.kwargs else call_args[1]
        assert params["temperature"] == 0.9

    @pytest.mark.asyncio
    async def test_generate_with_max_tokens_override(self, provider_with_key: OpenAIProvider):
        """generate() respects max_tokens override."""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
        mock_completion.usage = MagicMock(total_tokens=5)

        provider_with_key._client = AsyncMock()
        provider_with_key._client.chat.completions.create = AsyncMock(return_value=mock_completion)

        await provider_with_key.generate("Test", max_tokens=256)

        call_args = provider_with_key._client.chat.completions.create.call_args
        params = call_args.kwargs if call_args.kwargs else call_args[1]
        assert params["max_tokens"] == 256


# ---------------------------------------------------------------------------
# get_token_count() tests
# ---------------------------------------------------------------------------
class TestOpenAITokenCount:
    """Tests for OpenAIProvider.get_token_count()."""

    @pytest.mark.asyncio
    async def test_token_count_success(self, provider_with_key: OpenAIProvider):
        """get_token_count() returns token count."""
        count = await provider_with_key.get_token_count("Hello, world!")
        assert isinstance(count, int)
        assert count > 0

    @pytest.mark.asyncio
    async def test_token_count_empty_string(self, provider_with_key: OpenAIProvider):
        """get_token_count() handles empty string."""
        count = await provider_with_key.get_token_count("")
        assert count == 0

    @pytest.mark.asyncio
    async def test_token_count_longer_text(self, provider_with_key: OpenAIProvider):
        """get_token_count() returns more tokens for longer text."""
        short = await provider_with_key.get_token_count("Hi")
        long = await provider_with_key.get_token_count("This is a much longer sentence for testing purposes")
        assert long > short
