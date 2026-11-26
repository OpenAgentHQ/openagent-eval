"""Tests for LLMProvider.generate_stream() and native adapter implementations."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.llm import LLMProvider
from openagent_eval.providers.llm._streaming import close_async_stream
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


class _ClosableSDKStream:
    """Minimal SDK stream stand-in exposing ``__aiter__`` and ``async close()``."""

    def __init__(
        self,
        items: list[Any],
        *,
        error_after: int | None = None,
        error: Exception | None = None,
    ) -> None:
        self._items = items
        self._error_after = error_after
        self._error = error
        self.closed = False
        self.close_calls = 0

    def __aiter__(self) -> AsyncIterator[Any]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[Any]:
        for idx, item in enumerate(self._items):
            if self._error_after is not None and idx >= self._error_after:
                assert self._error is not None
                raise self._error
            yield item
        if self._error_after is not None and self._error_after >= len(self._items):
            assert self._error is not None
            raise self._error

    async def close(self) -> None:
        self.closed = True
        self.close_calls += 1


class _ChunkedByteStream(httpx.AsyncByteStream):
    """Streaming httpx byte stream for verifying incremental reads and ResponseNotRead."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks
        self.yielded_count = 0
        self.closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            self.yielded_count += 1
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


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

    @pytest.mark.asyncio
    async def test_generate_stream_closes_stream_on_normal_completion(self):
        pytest.importorskip("openai")
        from openagent_eval.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key-1234567890")
        raw_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
        ]
        sdk_stream = _ClosableSDKStream(raw_chunks)
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(return_value=sdk_stream)

        chunks = await _collect(provider.generate_stream("hi"))
        assert chunks == ["Hello", " world"]
        assert sdk_stream.closed is True
        assert sdk_stream.close_calls == 1

    @pytest.mark.asyncio
    async def test_generate_stream_closes_stream_on_early_break(self):
        pytest.importorskip("openai")
        from openagent_eval.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key-1234567890")
        raw_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="First"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Second"))]),
        ]
        sdk_stream = _ClosableSDKStream(raw_chunks)
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(return_value=sdk_stream)

        received: list[str] = []
        async with contextlib.aclosing(provider.generate_stream("hi")) as stream:
            async for chunk in stream:
                received.append(chunk)
                break

        assert received == ["First"]
        assert sdk_stream.closed is True
        assert sdk_stream.close_calls == 1

    @pytest.mark.asyncio
    async def test_generate_stream_closes_stream_on_midstream_error(self):
        pytest.importorskip("openai")
        from openagent_eval.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="sk-test-key-1234567890")
        raw_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Partial"))]),
        ]
        sdk_stream = _ClosableSDKStream(
            raw_chunks, error_after=1, error=RuntimeError("stream interrupted")
        )
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(return_value=sdk_stream)

        received: list[str] = []
        with pytest.raises(ProviderExecutionError, match="stream interrupted"):
            async for chunk in provider.generate_stream("hi"):
                received.append(chunk)

        assert received == ["Partial"]
        assert sdk_stream.closed is True
        assert sdk_stream.close_calls == 1


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

    @pytest.mark.asyncio
    async def test_generate_stream_exits_context_on_early_break(self):
        anthropic_mod = pytest.importorskip("anthropic")
        from openagent_eval.providers.llm.anthropic import Anthropic

        with patch.object(anthropic_mod, "AsyncAnthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            mock_stream = MagicMock()
            mock_stream.text_stream = _async_iter(["Hello", " Claude"])
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_stream)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_client.messages.stream = MagicMock(return_value=mock_ctx)

            provider = Anthropic(api_key="sk-ant-test-key")
            received: list[str] = []
            async with contextlib.aclosing(provider.generate_stream("Hi")) as stream:
                async for chunk in stream:
                    received.append(chunk)
                    break

            assert received == ["Hello"]
            mock_ctx.__aexit__.assert_awaited_once()


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

    @pytest.mark.asyncio
    async def test_generate_stream_supports_direct_async_iterator(self):
        pytest.importorskip("google.genai")
        from openagent_eval.providers.llm.gemini import Gemini

        with patch("openagent_eval.providers.llm.gemini.genai") as mock_genai_mod:
            mock_client = MagicMock()
            mock_aclient = MagicMock()
            mock_client.aio = mock_aclient
            mock_genai_mod.Client.return_value = mock_client

            async def direct_stream_gen(**_: Any) -> AsyncIterator[Any]:
                yield MagicMock(text="Direct ")
                yield MagicMock(text=None)
                yield MagicMock(text="async gen")

            mock_aclient.models.generate_content_stream = direct_stream_gen

            provider = Gemini(api_key="gemini-test-key")
            chunks = await _collect(provider.generate_stream("Explain"))
            assert chunks == ["Direct ", "async gen"]

    @pytest.mark.asyncio
    async def test_generate_stream_closes_async_generator_on_early_break(self):
        pytest.importorskip("google.genai")
        from openagent_eval.providers.llm.gemini import Gemini

        closed = False

        async def direct_stream_gen(**_: Any) -> AsyncIterator[Any]:
            nonlocal closed
            try:
                yield MagicMock(text="Chunk 1")
                yield MagicMock(text="Chunk 2")
            finally:
                closed = True

        with patch("openagent_eval.providers.llm.gemini.genai") as mock_genai_mod:
            mock_client = MagicMock()
            mock_aclient = MagicMock()
            mock_client.aio = mock_aclient
            mock_genai_mod.Client.return_value = mock_client
            mock_aclient.models.generate_content_stream = direct_stream_gen

            provider = Gemini(api_key="gemini-test-key")
            received: list[str] = []
            async with contextlib.aclosing(
                provider.generate_stream("Explain")
            ) as stream:
                async for chunk in stream:
                    received.append(chunk)
                    break

            assert received == ["Chunk 1"]
            assert closed is True


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

    @pytest.mark.asyncio
    async def test_generate_stream_closes_stream_on_normal_completion(self):
        groq_mod = pytest.importorskip("groq")
        from openagent_eval.providers.llm.groq import Groq

        with patch.object(groq_mod, "AsyncGroq") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            raw_chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Fast "))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Groq"))]),
            ]
            sdk_stream = _ClosableSDKStream(raw_chunks)
            mock_client.chat.completions.create = AsyncMock(return_value=sdk_stream)

            provider = Groq(api_key="gsk-test-key")
            chunks = await _collect(provider.generate_stream("Hello"))
            assert chunks == ["Fast ", "Groq"]
            assert sdk_stream.closed is True
            assert sdk_stream.close_calls == 1

    @pytest.mark.asyncio
    async def test_generate_stream_closes_stream_on_early_break(self):
        groq_mod = pytest.importorskip("groq")
        from openagent_eval.providers.llm.groq import Groq

        with patch.object(groq_mod, "AsyncGroq") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            raw_chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Fast "))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Groq"))]),
            ]
            sdk_stream = _ClosableSDKStream(raw_chunks)
            mock_client.chat.completions.create = AsyncMock(return_value=sdk_stream)

            provider = Groq(api_key="gsk-test-key")
            received: list[str] = []
            async with contextlib.aclosing(provider.generate_stream("Hello")) as stream:
                async for chunk in stream:
                    received.append(chunk)
                    break

            assert received == ["Fast "]
            assert sdk_stream.closed is True
            assert sdk_stream.close_calls == 1

    @pytest.mark.asyncio
    async def test_generate_stream_closes_stream_on_midstream_error(self):
        groq_mod = pytest.importorskip("groq")
        from openagent_eval.providers.llm.groq import Groq

        with patch.object(groq_mod, "AsyncGroq") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            raw_chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Partial"))]),
            ]
            sdk_stream = _ClosableSDKStream(
                raw_chunks, error_after=1, error=RuntimeError("stream broken")
            )
            mock_client.chat.completions.create = AsyncMock(return_value=sdk_stream)

            provider = Groq(api_key="gsk-test-key")
            received: list[str] = []
            with pytest.raises(ProviderExecutionError, match="stream broken"):
                async for chunk in provider.generate_stream("Hello"):
                    received.append(chunk)

            assert received == ["Partial"]
            assert sdk_stream.closed is True
            assert sdk_stream.close_calls == 1


# ---------------------------------------------------------------------------
# Ollama streaming
# ---------------------------------------------------------------------------
class TestOllamaStream:
    """Tests for Ollama.generate_stream()."""

    @pytest.mark.asyncio
    async def test_generate_stream_rejects_eof_after_partial_text(self):
        provider = Ollama()
        async with httpx.AsyncClient(
            base_url="http://localhost:11434",
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, content=b'{"response":"Partial","done":false}\n'
                )
            ),
        ) as client:
            await provider.close()
            provider._client = client
            async with contextlib.aclosing(provider.generate_stream("Hi")) as stream:
                assert await anext(stream) == "Partial"
                with pytest.raises(ProviderExecutionError, match="did not complete"):
                    await anext(stream)

    @pytest.mark.asyncio
    async def test_generate_stream_preserves_status_when_error_body_read_fails(self):
        class UnreadableBody(httpx.AsyncByteStream):
            async def __aiter__(self) -> AsyncIterator[bytes]:
                raise httpx.ReadError("body unavailable")
                yield b""  # pragma: no cover

        provider = Ollama()
        async with httpx.AsyncClient(
            base_url="http://localhost:11434",
            transport=httpx.MockTransport(
                lambda request: httpx.Response(404, stream=UnreadableBody())
            ),
        ) as client:
            await provider.close()
            provider._client = client
            with pytest.raises(
                ProviderExecutionError, match="Ollama API error: 404"
            ) as exc:
                await _collect(provider.generate_stream("Hi"))
        assert exc.value.details["status_code"] == 404
        assert isinstance(exc.value.__cause__, httpx.ReadError)

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

    @pytest.mark.asyncio
    async def test_generate_stream_http_error_reads_body_without_response_not_read(
        self,
    ):
        provider = Ollama(base_url="http://localhost:11434", model="missing-model")
        error_body = b'{"error":"model \'missing-model\' not found"}'

        async def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, stream=_ChunkedByteStream([error_body]))

        await provider.close()
        provider._client = httpx.AsyncClient(
            base_url="http://localhost:11434",
            transport=httpx.MockTransport(handler),
        )
        try:
            with pytest.raises(
                ProviderExecutionError, match="Ollama API error: 404"
            ) as exc:
                await _collect(provider.generate_stream("Hi"))
            assert exc.value.details["status_code"] == 404
            assert exc.value.details["response"] == error_body.decode()
        finally:
            await provider.close()

    @pytest.mark.asyncio
    async def test_generate_stream_2xx_streams_incrementally_without_aread(self):
        provider = Ollama(base_url="http://localhost:11434", model="llama3.2")
        byte_stream = _ChunkedByteStream(
            [
                b'{"model":"llama3.2","response":"First ","done":false}\n',
                b'{"model":"llama3.2","response":"Second","done":false}\n',
                b'{"model":"llama3.2","response":"","done":true}\n',
            ]
        )

        async def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, stream=byte_stream)

        await provider.close()
        provider._client = httpx.AsyncClient(
            base_url="http://localhost:11434",
            transport=httpx.MockTransport(handler),
        )
        try:
            async with contextlib.aclosing(provider.generate_stream("Hi")) as stream:
                first = await anext(stream)
                assert first == "First "
                # Only the first chunk has been pulled from the HTTP byte stream.
                assert byte_stream.yielded_count == 1
                second = await anext(stream)
                assert second == "Second"
        finally:
            await provider.close()

    @pytest.mark.asyncio
    async def test_generate_stream_ndjson_error_raises_before_response(self):
        provider = Ollama()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_lines = lambda: _async_iter(
            [
                '{"error":"model \'missing\' not found","response":"should not yield"}',
            ]
        )
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_stream_ctx)
        provider._client = mock_client

        received: list[str] = []
        with pytest.raises(ProviderExecutionError, match="model 'missing' not found"):
            async for chunk in provider.generate_stream("Hi"):
                received.append(chunk)
        assert received == []

    @pytest.mark.asyncio
    async def test_generate_stream_ndjson_midstream_error_raises(self):
        provider = Ollama()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_lines = lambda: _async_iter(
            [
                '{"model":"llama3.2","response":"Hello ","done":false}',
                '{"error":"context length exceeded"}',
            ]
        )
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_stream_ctx)
        provider._client = mock_client

        received: list[str] = []
        with pytest.raises(ProviderExecutionError, match="context length exceeded"):
            async for chunk in provider.generate_stream("Hi"):
                received.append(chunk)
        assert received == ["Hello "]


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
                'data: {"choices":',
                'data: [{"delta":{"content":"Routed "}}]}',
                "",
                'data: {"choices":[{"delta":{}}]}',
                "",
                'data: {"choices":[{"delta":{"content":"reply"}}]}',
                "",
                "data: [DONE]",
                "",
                'data: {"choices":[{"delta":{"content":"ignored"}}]}',
                "",
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

    @pytest.mark.asyncio
    async def test_generate_stream_sse_error_event_raises_before_choices(self):
        provider = OpenRouter(api_key="sk-or-test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = lambda: _async_iter(
            [
                'data: {"choices":[{"delta":{"content":"Part 1"}}]}',
                "",
                'data: {"error":{"code":503,"message":"Upstream overloaded"},"choices":[{"delta":{"content":"ignored"}}]}',
                "",
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

            received: list[str] = []
            with pytest.raises(
                ProviderExecutionError, match="Upstream overloaded"
            ) as exc:
                async for chunk in provider.generate_stream("Hi"):
                    received.append(chunk)

            assert received == ["Part 1"]
            assert exc.value.details["error"] == {
                "code": 503,
                "message": "Upstream overloaded",
            }

    @pytest.mark.asyncio
    async def test_generate_stream_sse_string_error_raises(self):
        provider = OpenRouter(api_key="sk-or-test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = lambda: _async_iter(
            ['data: {"error":"Rate limited"}', ""]
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

            with pytest.raises(ProviderExecutionError, match="Rate limited"):
                await _collect(provider.generate_stream("Hi"))

    @pytest.mark.asyncio
    async def test_generate_stream_allows_empty_deltas_null_error_and_usage_chunk(self):
        provider = OpenRouter(api_key="sk-or-test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = lambda: _async_iter(
            [
                'data: {"error":null,"choices":[{"delta":{"content":"Valid"}}]}',
                "",
                'data: {"choices":[{"delta":{"content":null}}]}',
                "",
                'data: {"choices":[{"delta":{"content":""}}]}',
                "",
                'data: {"choices":[{"delta":{}}]}',
                "",
                'data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":2,"total_tokens":7}}',
                "",
                "data: [DONE]",
                "",
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
            assert chunks == ["Valid"]


# ---------------------------------------------------------------------------
# Stream closing helper & real SDK AsyncStream closure
# ---------------------------------------------------------------------------
class TestCloseAsyncStream:
    """Tests for close_async_stream() and real SDK AsyncStream early-break closure."""

    @pytest.mark.asyncio
    async def test_close_async_stream_handles_variants(self):
        await close_async_stream(None)
        await close_async_stream(object())

        sync_closed = False

        class SyncCloseOnly:
            def close(self) -> None:
                nonlocal sync_closed
                sync_closed = True

        await close_async_stream(SyncCloseOnly())
        assert sync_closed is True

        class ResponseLike:
            def __init__(self) -> None:
                self.aclose_called = False
                self.close_called = False

            def close(self) -> None:
                self.close_called = True

            async def aclose(self) -> None:
                self.aclose_called = True

        resp_like = ResponseLike()
        await close_async_stream(resp_like)
        assert resp_like.aclose_called is True
        assert resp_like.close_called is False

        mock_stream = MagicMock()
        mock_stream.close = AsyncMock()
        await close_async_stream(mock_stream)
        mock_stream.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_real_openai_async_stream_closes_on_early_break(self):
        openai_mod = pytest.importorskip("openai")
        from openai.types.chat import ChatCompletionChunk

        from openagent_eval.providers.llm.openai import OpenAIProvider

        byte_stream = _ChunkedByteStream(
            [
                b'data: {"id":"1","object":"chat.completion.chunk","created":1,"model":"gpt-4o","choices":[{"index":0,"delta":{"content":"Hi"}}]}\n\n',
                b'data: {"id":"2","object":"chat.completion.chunk","created":1,"model":"gpt-4o","choices":[{"index":0,"delta":{"content":" there"}}]}\n\n',
            ]
        )
        response = httpx.Response(
            200,
            stream=byte_stream,
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        )
        client = openai_mod.AsyncOpenAI(api_key="sk-test-key-1234567890")
        sdk_stream = openai_mod.AsyncStream(
            cast_to=ChatCompletionChunk,
            response=response,
            client=client,
        )
        try:
            provider = OpenAIProvider(api_key="sk-test-key-1234567890")
            provider._client = AsyncMock()
            provider._client.chat.completions.create = AsyncMock(
                return_value=sdk_stream
            )
            async with contextlib.aclosing(provider.generate_stream("Hi")) as stream:
                async for chunk in stream:
                    assert chunk == "Hi"
                    break
            assert byte_stream.closed is True
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_real_groq_async_stream_closes_on_early_break(self):
        groq_mod = pytest.importorskip("groq")
        from groq.types.chat import ChatCompletionChunk

        from openagent_eval.providers.llm.groq import Groq

        byte_stream = _ChunkedByteStream(
            [
                b'data: {"id":"1","object":"chat.completion.chunk","created":1,"model":"llama-3.3-70b-versatile","choices":[{"index":0,"delta":{"content":"Fast"}}]}\n\n',
                b'data: {"id":"2","object":"chat.completion.chunk","created":1,"model":"llama-3.3-70b-versatile","choices":[{"index":0,"delta":{"content":" reply"}}]}\n\n',
            ]
        )
        response = httpx.Response(
            200,
            stream=byte_stream,
            request=httpx.Request(
                "POST", "https://api.groq.com/openai/v1/chat/completions"
            ),
        )
        client = groq_mod.AsyncGroq(api_key="gsk-test-key")
        sdk_stream = groq_mod.AsyncStream(
            cast_to=ChatCompletionChunk,
            response=response,
            client=client,
        )
        try:
            provider = Groq(api_key="gsk-test-key")
            provider.client = AsyncMock()
            provider.client.chat.completions.create = AsyncMock(return_value=sdk_stream)
            async with contextlib.aclosing(provider.generate_stream("Hi")) as stream:
                async for chunk in stream:
                    assert chunk == "Fast"
                    break
            assert byte_stream.closed is True
        finally:
            await client.close()
