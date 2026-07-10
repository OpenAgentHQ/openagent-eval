"""Tests for Ollama LLM provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.llm.ollama import Ollama


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def provider():
    """Create an Ollama provider with default settings."""
    return Ollama(
        base_url="http://localhost:11434",
        model="llama3.2",
        temperature=0.7,
    )


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "model": "llama3.2",
        "response": "Ollama response",
        "done": True,
        "eval_count": 15,
        "prompt_eval_count": 10,
        "eval_duration": 1000000000,
        "prompt_eval_duration": 500000000,
    }
    return response


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestOllamaInit:
    """Tests for Ollama initialization."""

    def test_init_defaults(self):
        """Provider initializes with default values."""
        provider = Ollama()
        assert provider.name == "ollama"
        assert provider._base_url == "http://localhost:11434"
        assert provider._model == "llama3.2"
        assert provider._temperature == 0.7
        assert provider._max_tokens is None

    def test_init_custom_params(self):
        """Provider initializes with custom parameters."""
        provider = Ollama(
            base_url="http://remote:11434",
            model="mistral",
            temperature=0.3,
            max_tokens=512,
            timeout=60.0,
        )
        assert provider._base_url == "http://remote:11434"
        assert provider._model == "mistral"
        assert provider._temperature == 0.3
        assert provider._max_tokens == 512
        assert provider._timeout == 60.0

    def test_init_strips_trailing_slash(self):
        """Provider strips trailing slash from base_url."""
        provider = Ollama(base_url="http://localhost:11434/")
        assert provider._base_url == "http://localhost:11434"

    def test_repr(self):
        """Provider has a meaningful repr."""
        provider = Ollama(model="mistral")
        repr_str = repr(provider)
        assert "Ollama" in repr_str
        assert "mistral" in repr_str


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------
class TestOllamaGenerate:
    """Tests for Ollama.generate()."""

    @pytest.mark.asyncio
    async def test_generate_success(self, provider: Ollama, mock_httpx_response):
        """generate() returns content on successful API call."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_httpx_response)

        provider._client = mock_client

        result = await provider.generate("Test prompt")
        assert result == "Ollama response"

    @pytest.mark.asyncio
    async def test_generate_with_model_override(self, provider: Ollama, mock_httpx_response):
        """generate() respects model override."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_httpx_response)

        provider._client = mock_client

        result = await provider.generate("Test prompt", model="mistral")
        assert result == "Ollama response"

    @pytest.mark.asyncio
    async def test_generate_not_done_raises(self, provider: Ollama):
        """generate() raises ProviderExecutionError when done=False."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "model": "llama3.2",
            "response": "partial",
            "done": False,
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        with pytest.raises(ProviderExecutionError, match="did not complete"):
            await provider.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_connection_error(self, provider: Ollama):
        """generate() raises ProviderConnectionError on ConnectError."""
        import httpx

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        provider._client = mock_client

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_http_status_error(self, provider: Ollama):
        """generate() raises ProviderExecutionError on HTTP status error."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_http_error = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=mock_http_error)
        provider._client = mock_client

        with pytest.raises(ProviderExecutionError, match="API error"):
            await provider.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_parse_error(self, provider: Ollama):
        """generate() raises ProviderExecutionError on parse failure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"invalid": "response"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        with pytest.raises(ProviderExecutionError, match="Failed to parse"):
            await provider.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_with_max_tokens(self, provider: Ollama, mock_httpx_response):
        """generate() passes max_tokens as num_predict in options."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_httpx_response)
        provider._client = mock_client

        await provider.generate("Test prompt", max_tokens=256)

        call_args = mock_client.post.call_args
        import json

        content = call_args.kwargs.get("content") or call_args[1].get("content")
        payload = json.loads(content)
        assert payload["options"]["num_predict"] == 256


# ---------------------------------------------------------------------------
# get_token_count() tests
# ---------------------------------------------------------------------------
class TestOllamaTokenCount:
    """Tests for Ollama.get_token_count()."""

    @pytest.mark.asyncio
    async def test_token_count_success(self, provider: Ollama):
        """get_token_count() returns the token count from the tokens list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"tokens": [1, 2, 3, 4, 5]}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        count = await provider.get_token_count("Hello, world!")
        assert count == 5
        # The request must be sent as JSON, not raw bytes.
        mock_client.post.assert_called_once()
        _, call_kwargs = mock_client.post.call_args
        assert call_kwargs.get("json") is not None

    @pytest.mark.asyncio
    async def test_token_count_fallback_on_error(self, provider: Ollama):
        """get_token_count() falls back to word split on error."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("API unavailable"))
        provider._client = mock_client

        count = await provider.get_token_count("Hello world test")
        assert count == 3  # Three words


# ---------------------------------------------------------------------------
# Context manager tests
# ---------------------------------------------------------------------------
class TestOllamaContextManager:
    """Tests for Ollama async context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Ollama supports async context manager."""
        provider = Ollama()
        async with provider as ctx:
            assert ctx is provider
        await provider.close()
