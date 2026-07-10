"""Tests for Gemini LLM provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip tests if google-genai is not installed
pytest.importorskip("google.genai", reason="google-genai not installed")

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_gemini_env(monkeypatch: pytest.MonkeyPatch):
    """Set GEMINI_API_KEY env var."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-api-key-12345")


@pytest.fixture
def mock_genai():
    """Mock google.genai Client while preserving real exception classes."""
    with patch("openagent_eval.providers.llm.gemini.genai") as mock_genai_mod:
        mock_client = MagicMock()
        mock_aclient = AsyncMock()
        mock_client.aio = mock_aclient
        mock_genai_mod.Client.return_value = mock_client
        yield mock_genai_mod, mock_client, mock_aclient


@pytest.fixture
def provider_with_key(mock_genai):
    """Create a Gemini provider with explicit API key."""
    from openagent_eval.providers.llm.gemini import Gemini
    return Gemini(api_key="test-gemini-api-key-12345")


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestGeminiInit:
    """Tests for Gemini initialization."""

    def test_init_with_explicit_api_key(self, mock_genai):
        """Provider initializes with explicit API key."""
        from openagent_eval.providers.llm.gemini import Gemini
        provider = Gemini(api_key="test-gemini-api-key-12345")
        assert provider.name == "gemini"
        assert provider.description == "Google Gemini LLM provider"
        assert provider._model == "gemini-2.5-flash"

    def test_init_from_env_var(self, mock_gemini_env, mock_genai):
        """Provider initializes from GEMINI_API_KEY env var."""
        from openagent_eval.providers.llm.gemini import Gemini
        provider = Gemini()
        assert provider._model == "gemini-2.5-flash"

    def test_init_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch):
        """Provider raises ProviderConnectionError without API key."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        from openagent_eval.providers.llm.gemini import Gemini
        with pytest.raises(ProviderConnectionError, match="API key not provided"):
            Gemini()

    def test_init_with_custom_params(self, mock_genai):
        """Provider initializes with custom parameters."""
        from openagent_eval.providers.llm.gemini import Gemini
        provider = Gemini(
            api_key="test-key",
            model="gemini-2.5-pro",
            temperature=0.5,
            max_tokens=1024,
        )
        assert provider._model == "gemini-2.5-pro"
        assert provider._temperature == 0.5
        assert provider._max_tokens == 1024


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------
class TestGeminiGenerate:
    """Tests for Gemini.generate()."""

    @pytest.mark.asyncio
    async def test_generate_success(self, provider_with_key, mock_genai):
        """generate() returns the generated text on a successful call."""
        _, _, mock_aclient = mock_genai

        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_response.usage_metadata.total_token_count = 30

        mock_aclient.models.generate_content = AsyncMock(return_value=mock_response)

        result = await provider_with_key.generate("Test prompt")
        assert result == "Gemini response"

    async def test_generate_with_usage_success(self, provider_with_key, mock_genai):
        """generate_with_usage() returns an LLMResponse with usage."""
        _, _, mock_aclient = mock_genai

        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_response.usage_metadata.total_token_count = 30

        mock_aclient.models.generate_content = AsyncMock(return_value=mock_response)

        result = await provider_with_key.generate_with_usage("Test prompt")
        assert result.content == "Gemini response"
        assert result.provider == "gemini"
        assert result.usage.total_tokens == 30

    async def test_generate_usage_metadata_none(self, provider_with_key, mock_genai):
        """H8: generate() must not crash when usage_metadata is None."""
        _, _, mock_aclient = mock_genai

        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_response.usage_metadata = None

        mock_aclient.models.generate_content = AsyncMock(return_value=mock_response)

        result = await provider_with_key.generate("Test prompt")
        assert result == "Gemini response"

    @pytest.mark.asyncio
    async def test_generate_with_temperature_override(self, provider_with_key, mock_genai):
        """generate() respects temperature override."""
        _, _, mock_aclient = mock_genai

        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_response.usage_metadata.prompt_token_count = 5
        mock_response.usage_metadata.candidates_token_count = 5
        mock_response.usage_metadata.total_token_count = 10

        mock_aclient.models.generate_content = AsyncMock(return_value=mock_response)

        await provider_with_key.generate("Test", temperature=0.9)
        mock_aclient.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_connection_error(self, provider_with_key, mock_genai):
        """generate() raises ProviderConnectionError on ConnectError."""
        import httpx

        _, _, mock_aclient = mock_genai
        mock_aclient.models.generate_content = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_timeout_error(self, provider_with_key, mock_genai):
        """generate() raises ProviderConnectionError on timeout."""
        import httpx

        _, _, mock_aclient = mock_genai
        mock_aclient.models.generate_content = AsyncMock(
            side_effect=httpx.TimeoutException("timed out")
        )

        with pytest.raises(ProviderConnectionError, match="timed out"):
            await provider_with_key.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_api_error(self, provider_with_key, mock_genai):
        """generate() raises ProviderExecutionError on APIError."""
        from google.genai import errors as genai_errors

        _, _, mock_aclient = mock_genai

        class FakeAPIError(Exception):
            def __init__(self, message="", code=0, status=""):
                super().__init__(message)
                self.message = message
                self.code = code
                self.status = status

        # Temporarily replace the real class in the module's except clause
        # We need the real genai_errors.APIError, so we create a subclass
        # that the except clause can catch
        with patch.object(genai_errors, "APIError", FakeAPIError):
            mock_aclient.models.generate_content = AsyncMock(
                side_effect=FakeAPIError("Invalid request", 400, "BAD_REQUEST")
            )

            with pytest.raises(ProviderExecutionError, match="Gemini API error"):
                await provider_with_key.generate("Test prompt")


# ---------------------------------------------------------------------------
# get_token_count() tests
# ---------------------------------------------------------------------------
class TestGeminiTokenCount:
    """Tests for Gemini.get_token_count()."""

    @pytest.mark.asyncio
    async def test_token_count_success(self, provider_with_key, mock_genai):
        """get_token_count() returns token count."""
        _, _, mock_aclient = mock_genai

        mock_count_response = MagicMock()
        mock_count_response.total_tokens = 5
        mock_aclient.models.count_tokens = AsyncMock(return_value=mock_count_response)

        count = await provider_with_key.get_token_count("Hello, world!")
        assert count == 5

    @pytest.mark.asyncio
    async def test_token_count_connection_error(self, provider_with_key, mock_genai):
        """get_token_count() raises ProviderConnectionError on ConnectError."""
        import httpx

        _, _, mock_aclient = mock_genai
        mock_aclient.models.count_tokens = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )

        with pytest.raises(ProviderConnectionError, match="connect"):
            await provider_with_key.get_token_count("test")

    @pytest.mark.asyncio
    async def test_token_count_api_error(self, provider_with_key, mock_genai):
        """get_token_count() raises ProviderExecutionError on APIError."""
        from google.genai import errors as genai_errors

        _, _, mock_aclient = mock_genai

        class FakeAPIError(Exception):
            def __init__(self, message="", code=0, status=""):
                super().__init__(message)
                self.message = message
                self.code = code
                self.status = status

        with patch.object(genai_errors, "APIError", FakeAPIError):
            mock_aclient.models.count_tokens = AsyncMock(
                side_effect=FakeAPIError("Token count failed", 500, "INTERNAL")
            )

            with pytest.raises(ProviderExecutionError, match="token counting error"):
                await provider_with_key.get_token_count("test")
