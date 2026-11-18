"""Tests for LLMProvider.generate_stream() and native adapter implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.llm.mock import MockLLMProvider
from openagent_eval.providers.llm.ollama import Ollama
from openagent_eval.providers.llm.openrouter import OpenRouter

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


async def _async_iter(items: list[Any]) -> AsyncIterator[Any]:
    for item in items:
        yield item


async def _collect(stream: AsyncIterator[str]) -> list[str]:
    return [chunk async for chunk in stream]


# ---------------------------------------------------------------------------
# Base class default & Mock provider fallback
# ---------------------------------------------------------------------------
class TestBaseGenerateStreamFallback:
    """Default generate_stream() buffers generate() for backward compatibility."""

    @pytest.mark.asyncio
    async def test_minimal_subclass_inherits_default_generate_stream(self):
        class MinimalProvider(LLMProvider):
            name = "minimal"
            description = "Minimal subclass without streaming override"

            async def generate(self, prompt: str, **kwargs: Any) -> str:
                return f"echo:{prompt}"

            async def get_token_count(self, text: str) -> int:
                return len(text.split())

        provider = MinimalProvider()
        chunks = await _collect(provider.generate_stream("hello"))
        assert chunks == ["echo:hello"]

    @pytest.mark.asyncio
    async def test_mock_provider_generate_stream(self):
        provider = MockLLMProvider()
        assert await _collect(provider.generate_stream("test prompt")) == [
            "[mock-answer] test prompt"
        ]
        assert await _collect(
            provider.generate_stream("test prompt", ground_truth="expected")
        ) == ["expected"]


# ---------------------------------------------------------------------------
# OpenAI streaming
# ---------------------------------------------------------------------------
class TestOpenAIStream:
    """Tests for OpenAIProvider.generate_stream()."""

    @pytest.mark.asyncio
    async def test_generate_stream_yields_deltas_and_passes_stream_flag(self):
        pytest.importorskip("openai")
        from openagent_eval.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key-1234567890")
        raw_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
            MagicMock(choices=[]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
        ]
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(
            return_value=_async_iter(raw_chunks)
        )

        chunks = await _collect(
            provider.generate_stream(
                "Say hello", system_message="Be brief", temperature=0.4, max_tokens=64
            )
        )
        assert chunks == ["Hello", " world"]

        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert call_kwargs["stream"] is True
        assert call_kwargs["temperature"] == 0.4
        assert call_kwargs["max_tokens"] == 64
        assert call_kwargs["messages"][0] == {"role": "system", "content": "Be brief"}

    @pytest.mark.asyncio
    async def test_generate_stream_connection_error(self):
        pytest.importorskip("openai")
        from openagent_eval.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key-1234567890")
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(
            side_effect=Exception("Connection reset")
        )

        with pytest.raises(ProviderConnectionError, match="connect"):
            await _collect(provider.generate_stream("hi"))


# ---------------------------------------------------------------------------
# Anthropic streaming
# ---------------------------------------------------------------------------
class TestAnthropicStream:
    """Tests for Anthropic.generate_stream()."""

    @pytest.mark.asyncio
    async def test_generate_stream_yields_text_stream(self):
        anthropic_mod = pytest.importorskip("anthropic")
        from openagent_eval.providers.llm.anthropic import Anthropic

        with patch.object(anthropic_mod, "AsyncAnthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            mock_stream = MagicMock()
            mock_stream.text_stream = _async_iter(["Hello", "", " Claude"])
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_client.messages.stream = MagicMock(return_value=mock_ctx)

            provider = Anthropic(api_key="sk-ant-test-key")
            chunks = await _collect(provider.generate_stream("Hi", max_tokens=128))
            assert chunks == ["Hello", " Claude"]
            assert mock_client.messages.stream.call_args.kwargs["max_tokens"] == 128

    @pytest.mark.asyncio
    async def test_generate_stream_connection_error(self):
        anthropic_mod = pytest.importorskip("anthropic")
        from openagent_eval.providers.llm.anthropic import Anthropic

        with patch.object(anthropic_mod, "AsyncAnthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(
                side_effect=anthropic_mod.APIConnectionError(request=MagicMock())
            )
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_client.messages.stream = MagicMock(return_value=mock_ctx)

            provider = Anthropic(api_key="sk-ant-test-key")
            with pytest.raises(ProviderConnectionError, match="connect"):
                await _collect(provider.generate_stream("Hi"))


# ---------------------------------------------------------------------------
# Gemini streaming
# ---------------------------------------------------------------------------
class TestGeminiStream:
    """Tests for Gemini.generate_stream()."""

    @pytest.mark.asyncio
    async def test_generate_stream_yields_chunks(self):
        pytest.importorskip("google.genai")
        from openagent_eval.providers.llm.gemini import Gemini

        with patch("openagent_eval.providers.llm.gemini.genai") as mock_genai_mod:
            mock_client = MagicMock()
            mock_aclient = AsyncMock()
            mock_client.aio = mock_aclient
            mock_genai_mod.Client.return_value = mock_client

            raw_chunks = [
                MagicMock(text="Part 1 "),
                MagicMock(text=None),
                MagicMock(text="Part 2"),
            ]
            mock_aclient.models.generate_content_stream = AsyncMock(
                return_value=_async_iter(raw_chunks)
            )

            provider = Gemini(api_key="gemini-test-key")
            chunks = await _collect(provider.generate_stream("Explain"))
            assert chunks == ["Part 1 ", "Part 2"]

    @pytest.mark.asyncio
    async def test_generate_stream_timeout_error(self):
        pytest.importorskip("google.genai")
        from openagent_eval.providers.llm.gemini import Gemini

        with patch("openagent_eval.providers.llm.gemini.genai") as mock_genai_mod:
            mock_client = MagicMock()
            mock_aclient = AsyncMock()
            mock_client.aio = mock_aclient
            mock_genai_mod.Client.return_value = mock_client
            mock_aclient.models.generate_content_stream = AsyncMock(
                side_effect=httpx.TimeoutException("timed out")
            )

            provider = Gemini(api_key="gemini-test-key")
            with pytest.raises(ProviderConnectionError, match="timed out"):
                await _collect(provider.generate_stream("Explain"))


# ---------------------------------------------------------------------------
# Groq streaming
# ---------------------------------------------------------------------------
class TestGroqStream:
    """Tests for Groq.generate_stream()."""

    @pytest.mark.asyncio
    async def test_generate_stream_yields_deltas(self):
        groq_mod = pytest.importorskip("groq")
        from openagent_eval.providers.llm.groq import Groq

        with patch.object(groq_mod, "AsyncGroq") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            raw_chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Fast "))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Groq"))]),
            ]
            mock_client.chat.completions.create = AsyncMock(
                return_value=_async_iter(raw_chunks)
            )

            provider = Groq(api_key="gsk-test-key")
            chunks = await _collect(provider.generate_stream("Hello"))
            assert chunks == ["Fast ", "Groq"]
            assert (
                mock_client.chat.completions.create.call_args.kwargs["stream"] is True
            )

    @pytest.mark.asyncio
    async def test_generate_stream_connection_error(self):
        groq_mod = pytest.importorskip("groq")
        from openagent_eval.providers.llm.groq import Groq

        with patch.object(groq_mod, "AsyncGroq") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                side_effect=groq_mod.APIConnectionError(request=MagicMock())
            )

            provider = Groq(api_key="gsk-test-key")
            with pytest.raises(ProviderConnectionError, match="connect"):
                await _collect(provider.generate_stream("Hello"))


# ---------------------------------------------------------------------------
# Ollama streaming
# ---------------------------------------------------------------------------
class TestOllamaStream:
    """Tests for Ollama.generate_stream()."""

    @pytest.mark.asyncio
    async def test_generate_stream_parses_ndjson(self):
        provider = Ollama(base_url="http://localhost:11434", model="llama3.2")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_lines = lambda: _async_iter(
            [
                '{"model":"llama3.2","response":"Local ","done":false}',
                "",
                '{"model":"llama3.2","response":"stream","done":false}',
                '{"model":"llama3.2","response":"","done":true}',
            ]
        )
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_stream_ctx)
        provider._client = mock_client

        chunks = await _collect(provider.generate_stream("Hi"))
        assert chunks == ["Local ", "stream"]

    @pytest.mark.asyncio
    async def test_generate_stream_invalid_json_raises(self):
        provider = Ollama()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_lines = lambda: _async_iter(["{not-json"])
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_stream_ctx)
        provider._client = mock_client

        with pytest.raises(ProviderExecutionError, match="Failed to parse"):
            await _collect(provider.generate_stream("Hi"))


# ---------------------------------------------------------------------------
# OpenRouter streaming
# ---------------------------------------------------------------------------
class TestOpenRouterStream:
    """Tests for OpenRouter.generate_stream()."""

    @pytest.mark.asyncio
    async def test_generate_stream_parses_sse_events(self):
        provider = OpenRouter(api_key="sk-or-test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = lambda: _async_iter(
            [
                ": keep-alive",
                'data: {"choices":[{"delta":{"content":"Routed "}}]}',
                'data: {"choices":[{"delta":{}}]}',
                'data: {"choices":[{"delta":{"content":"reply"}}]}',
                "data: [DONE]",
                'data: {"choices":[{"delta":{"content":"ignored"}}]}',
            ]
        )
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch.object(httpx, "AsyncClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.stream = MagicMock(return_value=mock_stream_ctx)
            mock_cls.return_value = mock_client

            chunks = await _collect(provider.generate_stream("Hi"))
            assert chunks == ["Routed ", "reply"]
            assert mock_client.stream.call_args.kwargs["json"]["stream"] is True

    @pytest.mark.asyncio
    async def test_generate_stream_http_error_raises(self):
        provider = OpenRouter(api_key="sk-or-test-key")

        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_response.aread = AsyncMock(
            return_value=b'{"error":{"message":"Bad gateway"}}'
        )
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch.object(httpx, "AsyncClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.stream = MagicMock(return_value=mock_stream_ctx)
            mock_cls.return_value = mock_client

            with pytest.raises(ProviderExecutionError, match="Bad gateway"):
                await _collect(provider.generate_stream("Hi"))
