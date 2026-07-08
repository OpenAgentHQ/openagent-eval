"""Tests for Anthropic LLM provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip tests if anthropic is not installed
anthropic = pytest.importorskip("anthropic", reason="anthropic not installed")

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.llm.anthropic import Anthropic


def _make_httpx_response(status_code: int = 200, text: str = "") -> httpx.Response:
    """Create a real httpx.Response for use in exception constructors."""
    return httpx.Response(
        status_code=status_code,
        request=httpx.Request(method="POST", url="https://api.anthropic.com/v1/messages"),
        content=text.encode(),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_anthropic_env(monkeypatch: pytest.MonkeyPatch):
    """Set ANTHROPIC_API_KEY env var."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")


@pytest.fixture
def mock_anthropic_client():
    """Mock AsyncAnthropic client while preserving real exception classes."""
    with patch.object(anthropic, "AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        yield mock_client


@pytest.fixture
def provider_with_key(mock_anthropic_client):
    """Create an Anthropic provider with explicit API key."""
    return Anthropic(api_key="sk-ant-test-key-12345")


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestAnthropicInit:
    """Tests for Anthropic initialization."""

    def test_init_with_explicit_api_key(self, mock_anthropic_client):
        """Provider initializes with explicit API key."""
        provider = Anthropic(api_key="sk-ant-test-key-12345")
        assert provider.name == "anthropic"
        assert provider.model == "claude-sonnet-4-20250514"
        assert provider.temperature == 0.0
        assert provider.max_tokens is None

    def test_init_from_env_var(self, mock_anthropic_env, mock_anthropic_client):
        """Provider initializes from ANTHROPIC_API_KEY env var."""
        provider = Anthropic()
        assert provider.api_key == "sk-ant-test-key-12345"

    def test_init_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Provider raises ProviderConnectionError without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ProviderConnectionError, match="API key not provided"):
            Anthropic()

    def test_init_with_custom_params(self, mock_anthropic_client):
        """Provider initializes with custom parameters."""
        provider = Anthropic(
            api_key="sk-ant-test-key-12345",
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=2048,
        )
        assert provider.model == "claude-3-5-sonnet-20241022"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 2048


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------
class TestAnthropicGenerate:
    """Tests for Anthropic.generate()."""

    @pytest.mark.asyncio
    async def test_generate_success(self, provider_with_key: Anthropic, mock_anthropic_client):
        """generate() returns content on successful API call."""
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Claude response"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20

        mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        result = await provider_with_key.generate("Test prompt")
        assert result == "Claude response"

    @pytest.mark.asyncio
    async def test_generate_with_model_override(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """generate() respects model override."""
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "ok"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 5

        mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        result = await provider_with_key.generate(
            "Test", model="claude-3-5-sonnet-20241022"
        )
        assert result == "ok"

        call_args = mock_anthropic_client.messages.create.call_args
        params = call_args.kwargs if call_args.kwargs else call_args[1]
        assert params["model"] == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_generate_empty_content_raises(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """generate() raises ProviderExecutionError on empty content."""
        mock_response = MagicMock()
        mock_response.content = []

        mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        with pytest.raises(ProviderExecutionError, match="No content"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_connection_error(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """generate() raises ProviderConnectionError on connection error."""
        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=anthropic.APIConnectionError(request=MagicMock())
        )

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_timeout_error(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """generate() raises ProviderConnectionError on timeout."""
        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=anthropic.APITimeoutError(request=MagicMock())
        )

        with pytest.raises(ProviderConnectionError, match="timed out"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_api_status_error(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """generate() raises ProviderExecutionError on API status error."""
        response = _make_httpx_response(status_code=400, text="Bad request")
        error = anthropic.APIStatusError(
            message="Bad request",
            response=response,
            body=None,
        )
        mock_anthropic_client.messages.create = AsyncMock(side_effect=error)

        with pytest.raises(ProviderExecutionError, match="API error"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_generic_api_error(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """generate() raises ProviderExecutionError on generic API error."""
        response = _make_httpx_response(status_code=500, text="Something went wrong")
        error = anthropic.APIError(
            message="Something went wrong",
            request=MagicMock(),
            body=None,
        )
        mock_anthropic_client.messages.create = AsyncMock(side_effect=error)

        with pytest.raises(ProviderExecutionError, match="API error"):
            await provider_with_key.generate("Test prompt")


# ---------------------------------------------------------------------------
# get_token_count() tests
# ---------------------------------------------------------------------------
class TestAnthropicTokenCount:
    """Tests for Anthropic.get_token_count()."""

    @pytest.mark.asyncio
    async def test_token_count_success(self, provider_with_key: Anthropic, mock_anthropic_client):
        """get_token_count() returns token count."""
        mock_count_response = MagicMock()
        mock_count_response.input_tokens = 5
        mock_anthropic_client.messages.count_tokens = AsyncMock(
            return_value=mock_count_response
        )

        count = await provider_with_key.get_token_count("Hello, world!")
        assert count == 5

    @pytest.mark.asyncio
    async def test_token_count_empty_string(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """get_token_count() returns 0 for empty string."""
        count = await provider_with_key.get_token_count("")
        assert count == 0

    @pytest.mark.asyncio
    async def test_token_count_connection_error(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """get_token_count() raises ProviderConnectionError on connection error."""
        mock_anthropic_client.messages.count_tokens = AsyncMock(
            side_effect=anthropic.APIConnectionError(request=MagicMock())
        )

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider_with_key.get_token_count("test")

    @pytest.mark.asyncio
    async def test_token_count_api_error(
        self, provider_with_key: Anthropic, mock_anthropic_client
    ):
        """get_token_count() raises ProviderExecutionError on API error."""
        response = _make_httpx_response(status_code=500, text="Internal error")
        error = anthropic.APIStatusError(
            message="Internal error",
            response=response,
            body=None,
        )
        mock_anthropic_client.messages.count_tokens = AsyncMock(side_effect=error)

        with pytest.raises(ProviderExecutionError, match="token counting error"):
            await provider_with_key.get_token_count("test")
