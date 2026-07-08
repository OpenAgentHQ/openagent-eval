"""Tests for OpenRouter LLM provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.llm.openrouter import OpenRouter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_openrouter_env(monkeypatch: pytest.MonkeyPatch):
    """Set OPENROUTER_API_KEY env var."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-12345")


@pytest.fixture
def provider_with_key():
    """Create an OpenRouter provider with explicit API key."""
    return OpenRouter(api_key="sk-or-test-key-12345")


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient while preserving real exception classes."""
    with patch.object(httpx, "AsyncClient") as mock_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client
        yield mock_client


def _make_response(
    status_code: int = 200,
    json_data: dict | None = None,
    text: str = "",
) -> MagicMock:
    """Create a mock response with properly configured .json() method."""
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    # Ensure .json() returns a dict, not a coroutine
    response.json = MagicMock(return_value=json_data or {})
    return response


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestOpenRouterInit:
    """Tests for OpenRouter initialization."""

    def test_init_with_explicit_api_key(self):
        """Provider initializes with explicit API key."""
        provider = OpenRouter(api_key="sk-or-test-key-12345")
        assert provider.name == "openrouter"
        assert provider.model == "openai/gpt-4o-mini"
        assert provider.temperature == 0.0
        assert provider.max_tokens is None
        assert provider.base_url == "https://openrouter.ai/api/v1"

    def test_init_from_env_var(self, mock_openrouter_env):
        """Provider initializes from OPENROUTER_API_KEY env var."""
        provider = OpenRouter()
        assert provider.api_key == "sk-or-test-key-12345"

    def test_init_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Provider raises ProviderConnectionError without API key."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(ProviderConnectionError, match="API key not provided"):
            OpenRouter()

    def test_init_with_custom_params(self):
        """Provider initializes with custom parameters."""
        provider = OpenRouter(
            api_key="sk-or-test-key-12345",
            model="anthropic/claude-3-5-sonnet",
            temperature=0.5,
            max_tokens=1024,
            base_url="https://custom.api.com/v1",
        )
        assert provider.model == "anthropic/claude-3-5-sonnet"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 1024
        assert provider.base_url == "https://custom.api.com/v1"

    def test_init_strips_trailing_slash_from_base_url(self):
        """Provider strips trailing slash from base_url."""
        provider = OpenRouter(
            api_key="sk-or-test-key-12345",
            base_url="https://openrouter.ai/api/v1/",
        )
        assert provider.base_url == "https://openrouter.ai/api/v1"


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------
class TestOpenRouterGenerate:
    """Tests for OpenRouter.generate()."""

    @pytest.mark.asyncio
    async def test_generate_success(
        self, provider_with_key: OpenRouter, mock_httpx_client
    ):
        """generate() returns content on successful API call."""
        mock_response = _make_response(
            status_code=200,
            json_data={
                "choices": [{"message": {"content": "OpenRouter response"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            },
            text='{"choices": [...]}',
        )

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        result = await provider_with_key.generate("Test prompt")
        assert result == "OpenRouter response"

    @pytest.mark.asyncio
    async def test_generate_with_max_tokens_override(
        self, provider_with_key: OpenRouter, mock_httpx_client
    ):
        """generate() respects max_tokens override."""
        mock_response = _make_response(
            status_code=200,
            json_data={
                "choices": [{"message": {"content": "ok"}}],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 5,
                    "total_tokens": 10,
                },
            },
            text='{"choices": [...]}',
        )

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        await provider_with_key.generate("Test", max_tokens=256)

        call_args = mock_httpx_client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert payload["max_tokens"] == 256

    @pytest.mark.asyncio
    async def test_generate_http_error(
        self, provider_with_key: OpenRouter, mock_httpx_client
    ):
        """generate() raises ProviderExecutionError on non-200 status."""
        mock_response = _make_response(
            status_code=500,
            json_data={"error": {"message": "Server error"}},
            text='{"error": {"message": "Server error"}}',
        )

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(ProviderExecutionError, match="API error"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_empty_choices_raises(
        self, provider_with_key: OpenRouter, mock_httpx_client
    ):
        """generate() raises ProviderExecutionError on empty choices."""
        mock_response = _make_response(
            status_code=200,
            json_data={"choices": []},
            text='{"choices": []}',
        )

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(ProviderExecutionError, match="No choices"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_connection_error(
        self, provider_with_key: OpenRouter, mock_httpx_client
    ):
        """generate() raises ProviderConnectionError on ConnectError."""
        mock_httpx_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_timeout_error(
        self, provider_with_key: OpenRouter, mock_httpx_client
    ):
        """generate() raises ProviderConnectionError on timeout."""
        mock_httpx_client.post = AsyncMock(
            side_effect=httpx.TimeoutException("timed out")
        )

        with pytest.raises(ProviderConnectionError, match="timed out"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_request_error(
        self, provider_with_key: OpenRouter, mock_httpx_client
    ):
        """generate() raises ProviderConnectionError on RequestError."""
        mock_httpx_client.post = AsyncMock(
            side_effect=httpx.RequestError("network error")
        )

        with pytest.raises(ProviderConnectionError, match="Request"):
            await provider_with_key.generate("Test prompt")


# ---------------------------------------------------------------------------
# get_token_count() tests
# ---------------------------------------------------------------------------
class TestOpenRouterTokenCount:
    """Tests for OpenRouter.get_token_count()."""

    @pytest.mark.asyncio
    async def test_token_count_success(self, provider_with_key: OpenRouter):
        """get_token_count() returns estimated token count."""
        count = await provider_with_key.get_token_count("Hello, world!")
        assert isinstance(count, int)
        assert count > 0

    @pytest.mark.asyncio
    async def test_token_count_empty_string(self, provider_with_key: OpenRouter):
        """get_token_count() returns 0 for empty string."""
        count = await provider_with_key.get_token_count("")
        assert count == 0

    @pytest.mark.asyncio
    async def test_token_count_longer_text(self, provider_with_key: OpenRouter):
        """get_token_count() returns more tokens for longer text."""
        short = await provider_with_key.get_token_count("Hi")
        long = await provider_with_key.get_token_count(
            "This is a much longer sentence for testing token estimation"
        )
        assert long > short
