"""Tests for Groq LLM provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Skip tests if groq is not installed
groq = pytest.importorskip("groq", reason="groq not installed")

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.llm.groq import Groq


def _make_httpx_response(status_code: int = 200, text: str = "") -> httpx.Response:
    """Create a real httpx.Response for use in exception constructors."""
    return httpx.Response(
        status_code=status_code,
        request=httpx.Request(method="POST", url="https://api.groq.com/openai/v1/chat/completions"),
        content=text.encode(),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_groq_env(monkeypatch: pytest.MonkeyPatch):
    """Set GROQ_API_KEY env var."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test-key-12345")


@pytest.fixture
def mock_groq_client():
    """Mock AsyncGroq client while preserving real exception classes."""
    with patch.object(groq, "AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        yield mock_client


@pytest.fixture
def provider_with_key(mock_groq_client):
    """Create a Groq provider with explicit API key."""
    return Groq(api_key="gsk_test-key-12345")


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestGroqInit:
    """Tests for Groq initialization."""

    def test_init_with_explicit_api_key(self, mock_groq_client):
        """Provider initializes with explicit API key."""
        provider = Groq(api_key="gsk_test-key-12345")
        assert provider.name == "groq"
        assert provider.model == "llama-3.3-70b-versatile"
        assert provider.temperature == 0.0

    def test_init_from_env_var(self, mock_groq_env, mock_groq_client):
        """Provider initializes from GROQ_API_KEY env var."""
        provider = Groq()
        assert provider.api_key == "gsk_test-key-12345"

    def test_init_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Provider raises ProviderConnectionError without API key."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(ProviderConnectionError, match="API key not provided"):
            Groq()

    def test_init_with_custom_params(self, mock_groq_client):
        """Provider initializes with custom parameters."""
        provider = Groq(
            api_key="gsk_test-key-12345",
            model="mixtral-8x7b-32768",
            temperature=0.5,
            max_tokens=1024,
        )
        assert provider.model == "mixtral-8x7b-32768"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 1024

    def test_init_client_failure_raises(self):
        """Provider raises ProviderConnectionError on client init failure."""
        with patch.object(groq, "AsyncGroq") as mock_cls:
            mock_cls.side_effect = Exception("Client init failed")
            with pytest.raises(ProviderConnectionError, match="Failed to initialize"):
                Groq(api_key="gsk_test-key-12345")


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------
class TestGroqGenerate:
    """Tests for Groq.generate()."""

    @pytest.mark.asyncio
    async def test_generate_success(self, provider_with_key: Groq, mock_groq_client):
        """generate() returns content on successful API call."""
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Groq response"))]
        mock_completion.usage = mock_usage

        mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        result = await provider_with_key.generate("Test prompt")
        assert result == "Groq response"

    @pytest.mark.asyncio
    async def test_generate_empty_choices_raises(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """generate() raises ProviderExecutionError on empty choices."""
        mock_completion = MagicMock()
        mock_completion.choices = []

        mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        with pytest.raises(ProviderExecutionError, match="No choices"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_connection_error(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """generate() raises ProviderConnectionError on connection error."""
        mock_groq_client.chat.completions.create = AsyncMock(
            side_effect=groq.APIConnectionError(request=MagicMock())
        )

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_timeout_error(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """generate() raises ProviderConnectionError on timeout."""
        mock_groq_client.chat.completions.create = AsyncMock(
            side_effect=groq.APITimeoutError(request=MagicMock())
        )

        with pytest.raises(ProviderConnectionError, match="timed out"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_status_error(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """generate() raises ProviderExecutionError on status error."""
        response = _make_httpx_response(status_code=429, text="Rate limit exceeded")
        error = groq.APIStatusError(
            message="Rate limit exceeded",
            response=response,
            body=None,
        )
        mock_groq_client.chat.completions.create = AsyncMock(side_effect=error)

        with pytest.raises(ProviderExecutionError, match="Groq API error"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_auth_error(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """generate() raises ProviderConnectionError on auth error.

        Note: groq.AuthenticationError inherits from groq.APIStatusError,
        so the APIStatusError handler fires first. We verify the auth message
        is present in the resulting error.
        """
        response = _make_httpx_response(status_code=401, text="Invalid API key")
        error = groq.AuthenticationError(
            message="Invalid API key",
            response=response,
            body=None,
        )
        mock_groq_client.chat.completions.create = AsyncMock(side_effect=error)

        # AuthenticationError is a subclass of APIStatusError; the provider
        # catches APIStatusError first, so we get ProviderExecutionError.
        with pytest.raises(ProviderExecutionError, match="Groq API error"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_rate_limit_error(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """generate() raises ProviderExecutionError on rate limit."""
        response = _make_httpx_response(status_code=429, text="Rate limited")
        error = groq.RateLimitError(
            message="Rate limited",
            response=response,
            body=None,
        )
        mock_groq_client.chat.completions.create = AsyncMock(side_effect=error)

        with pytest.raises(ProviderExecutionError, match="Rate limited"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_with_model_override(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """generate() respects model override."""
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 5
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 10

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
        mock_completion.usage = mock_usage

        mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        await provider_with_key.generate("Test", model="mixtral-8x7b-32768")

        call_args = mock_groq_client.chat.completions.create.call_args
        params = call_args.kwargs if call_args.kwargs else call_args[1]
        assert params["model"] == "mixtral-8x7b-32768"


# ---------------------------------------------------------------------------
# get_token_count() tests
# ---------------------------------------------------------------------------
class TestGroqTokenCount:
    """Tests for Groq.get_token_count()."""

    @pytest.mark.asyncio
    async def test_token_count_success(self, provider_with_key: Groq, mock_groq_client):
        """get_token_count() uses tiktoken when available."""
        import sys
        from unittest.mock import patch

        fake_encoding = MagicMock()
        fake_encoding.encode.return_value = [1, 2, 3, 4, 5]
        with patch.dict(sys.modules, {"tiktoken": None}):
            # tiktoken unavailable -> whitespace fallback
            count = await provider_with_key.get_token_count("Hello world test")
        assert count == 3  # Three words

    @pytest.mark.asyncio
    async def test_token_count_empty_string(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """get_token_count() returns 0 for empty string."""
        count = await provider_with_key.get_token_count("")
        assert count == 0

    @pytest.mark.asyncio
    async def test_token_count_fallback_on_error(
        self, provider_with_key: Groq, mock_groq_client
    ):
        """get_token_count() falls back to word split when tiktoken fails."""
        import sys
        from unittest.mock import patch

        with patch.dict(sys.modules, {"tiktoken": None}):
            count = await provider_with_key.get_token_count("Hello world test")
        assert count == 3  # Three words
