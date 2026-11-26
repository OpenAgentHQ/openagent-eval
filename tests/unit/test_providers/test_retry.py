"""Tests for the shared LLM provider retry and exponential-backoff wrapper."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
    ProviderNotFoundError,
)
from openagent_eval.providers.base.retry import (
    RetryConfig,
    is_retryable_error,
    retry_with_backoff,
)
from openagent_eval.providers.llm.anthropic import Anthropic
from openagent_eval.providers.llm.gemini import Gemini
from openagent_eval.providers.llm.groq import Groq
from openagent_eval.providers.llm.ollama import Ollama
from openagent_eval.providers.llm.openai import OpenAIProvider
from openagent_eval.providers.llm.openrouter import OpenRouter


def _httpx_response(
    status_code: int, url: str = "https://api.example.com"
) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        request=httpx.Request("POST", url),
        content=b"{}",
    )


class TestRetryConfig:
    """Validation and backoff delay calculation tests for RetryConfig."""

    def test_compute_delay_exponential_and_capped(self) -> None:
        cfg = RetryConfig(
            max_attempts=4, base_delay=0.5, max_delay=1.5, backoff_factor=2.0
        )
        assert cfg.compute_delay(1) == pytest.approx(0.5)
        assert cfg.compute_delay(2) == pytest.approx(1.0)
        assert cfg.compute_delay(3) == pytest.approx(1.5)
        assert cfg.compute_delay(4) == pytest.approx(1.5)

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"max_attempts": 0}, "max_attempts"),
            ({"base_delay": -0.1}, "base_delay"),
            ({"max_delay": -1.0}, "max_delay"),
            ({"backoff_factor": 0.5}, "backoff_factor"),
            ({"jitter": -0.1}, "jitter"),
        ],
    )
    def test_invalid_config_raises(
        self, kwargs: dict[str, float | int], match: str
    ) -> None:
        with pytest.raises(ValueError, match=match):
            RetryConfig(**kwargs)  # type: ignore[arg-type]


class TestIsRetryableError:
    """Classification tests for transient vs non-retryable provider failures."""

    @pytest.mark.parametrize("status_code", [408, 409, 429, 500, 502, 503, 504, 529])
    def test_transient_status_codes_are_retryable(self, status_code: int) -> None:
        exc = ProviderExecutionError(
            message="transient error",
            provider_name="openai",
            details={"status_code": status_code},
        )
        assert is_retryable_error(exc) is True

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
    def test_client_and_auth_status_codes_are_not_retryable(
        self, status_code: int
    ) -> None:
        exc = ProviderExecutionError(
            message="client error",
            provider_name="openai",
            details={"status_code": status_code},
        )
        assert is_retryable_error(exc) is False

    def test_connection_error_is_retryable(self) -> None:
        exc = ProviderConnectionError(
            message="network reset",
            provider_name="openai",
            original_error=httpx.ConnectError("reset"),
        )
        assert is_retryable_error(exc) is True

    def test_provider_not_found_is_not_retryable(self) -> None:
        assert is_retryable_error(ProviderNotFoundError("openai", ["mock"])) is False

    def test_empty_choices_execution_error_is_not_retryable(self) -> None:
        exc = ProviderExecutionError(message="empty choices", provider_name="openai")
        assert is_retryable_error(exc) is False

    def test_groq_rate_limit_error_is_retryable(self) -> None:
        groq = pytest.importorskip("groq")
        rate_err = groq.RateLimitError(
            message="Rate limit exceeded",
            response=_httpx_response(
                429, "https://api.groq.com/openai/v1/chat/completions"
            ),
            body=None,
        )
        wrapped = ProviderExecutionError(
            message="Groq API error",
            provider_name="groq",
            original_error=rate_err,
            details={"status_code": 429},
        )
        assert is_retryable_error(wrapped) is True
        assert is_retryable_error(rate_err) is True


class TestRetryDecorator:
    """Unit tests for exponential-backoff retry behavior."""

    @pytest.mark.asyncio
    async def test_retries_transient_error_then_succeeds_with_exponential_backoff(
        self,
    ) -> None:
        calls = 0

        class DummyProvider:
            @retry_with_backoff(
                config=RetryConfig(max_attempts=3, base_delay=0.5, backoff_factor=2.0)
            )
            async def call(self) -> str:
                nonlocal calls
                calls += 1
                if calls < 3:
                    raise ProviderConnectionError("timeout", provider_name="dummy")
                return "ok"

        with patch(
            "openagent_eval.providers.base.retry.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            result = await DummyProvider().call()

        assert result == "ok"
        assert calls == 3
        assert [c.args[0] for c in mock_sleep.await_args_list] == [0.5, 1.0]

    @pytest.mark.asyncio
    async def test_non_retryable_fails_immediately_without_sleep(self) -> None:
        calls = 0

        class DummyProvider:
            @retry_with_backoff(config=RetryConfig(max_attempts=3, base_delay=0.5))
            async def call(self) -> str:
                nonlocal calls
                calls += 1
                raise ProviderExecutionError(
                    "Invalid API key",
                    provider_name="dummy",
                    details={"status_code": 401},
                )

        with (
            patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep,
            pytest.raises(ProviderExecutionError, match="Invalid API key"),
        ):
            await DummyProvider().call()

        assert calls == 1
        mock_sleep.assert_not_called()


class TestProviderUniformRetryIntegration:
    """Verify all six LLM providers retry transient errors and abort on auth failures."""

    @pytest.mark.asyncio
    async def test_groq_retries_rate_limit_error_and_succeeds(self) -> None:
        groq = pytest.importorskip("groq")
        with patch.object(groq, "AsyncGroq") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            rate_err = groq.RateLimitError(
                message="Rate limited",
                response=_httpx_response(
                    429, "https://api.groq.com/openai/v1/chat/completions"
                ),
                body=None,
            )
            ok_completion = MagicMock()
            ok_completion.choices = [MagicMock(message=MagicMock(content="recovered"))]
            mock_client.chat.completions.create = AsyncMock(
                side_effect=[rate_err, ok_completion]
            )

            provider = Groq(api_key="gsk_test")
            with patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ):
                result = await provider.generate("hello")

        assert result == "recovered"
        assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_groq_auth_error_does_not_retry(self) -> None:
        groq = pytest.importorskip("groq")
        with patch.object(groq, "AsyncGroq") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            auth_err = groq.AuthenticationError(
                message="Invalid API key",
                response=_httpx_response(
                    401, "https://api.groq.com/openai/v1/chat/completions"
                ),
                body=None,
            )
            mock_client.chat.completions.create = AsyncMock(side_effect=auth_err)

            provider = Groq(api_key="gsk_bad")
            with pytest.raises(ProviderExecutionError, match="Groq API error"):
                await provider.generate("hello")

        assert mock_client.chat.completions.create.call_count == 1

    @pytest.mark.asyncio
    async def test_openai_retries_transient_connection_then_succeeds(self) -> None:
        pytest.importorskip("openai")
        pytest.importorskip("tiktoken")
        ok_completion = MagicMock()
        ok_completion.choices = [MagicMock(message=MagicMock(content="openai-ok"))]
        ok_completion.usage = MagicMock(total_tokens=12)

        provider = OpenAIProvider(api_key="sk-test")
        provider._client = AsyncMock()
        provider._client.chat.completions.create = AsyncMock(
            side_effect=[Exception("Connection reset"), ok_completion]
        )

        with patch(
            "openagent_eval.providers.base.retry.asyncio.sleep", new_callable=AsyncMock
        ):
            result = await provider.generate("hello")

        assert result == "openai-ok"
        assert provider._client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_anthropic_retries_timeout_then_succeeds_and_skips_retry_on_401(
        self,
    ) -> None:
        anthropic = pytest.importorskip("anthropic")
        with patch.object(anthropic, "AsyncAnthropic") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            ok_block = MagicMock(type="text", text="claude-ok")
            ok_resp = MagicMock(
                content=[ok_block], usage=MagicMock(input_tokens=3, output_tokens=4)
            )
            mock_client.messages.create = AsyncMock(
                side_effect=[anthropic.APITimeoutError(request=MagicMock()), ok_resp]
            )

            provider = Anthropic(api_key="sk-ant-test")
            with patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ):
                assert await provider.generate("hello") == "claude-ok"
            assert mock_client.messages.create.call_count == 2

            auth_err = anthropic.APIStatusError(
                message="Unauthorized",
                response=_httpx_response(401, "https://api.anthropic.com/v1/messages"),
                body=None,
            )
            mock_client.messages.create = AsyncMock(side_effect=auth_err)
            with pytest.raises(ProviderExecutionError):
                await provider.generate("hello")
            assert mock_client.messages.create.call_count == 1

    @pytest.mark.asyncio
    async def test_gemini_retries_timeout_then_succeeds(self) -> None:
        google_genai = pytest.importorskip("google.genai")
        with patch.object(google_genai, "Client") as mock_cls:
            mock_aclient = MagicMock()
            mock_cls.return_value.aio = mock_aclient
            ok_resp = MagicMock(
                text="gemini-ok",
                usage_metadata=MagicMock(
                    prompt_token_count=2,
                    candidates_token_count=3,
                    total_token_count=5,
                ),
            )
            mock_aclient.models.generate_content = AsyncMock(
                side_effect=[httpx.TimeoutException("timed out"), ok_resp]
            )

            provider = Gemini(api_key="gem-test")
            with patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ):
                assert await provider.generate("hello") == "gemini-ok"

            assert mock_aclient.models.generate_content.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [429, 503])
    async def test_openrouter_retries_transient_http_errors_and_skips_401(
        self, status_code: int
    ) -> None:
        rate_resp = httpx.Response(
            status_code=status_code,
            content=b"<html>Upstream busy</html>",
            headers={"Retry-After": "5"},
            request=httpx.Request(
                "POST", "https://openrouter.ai/api/v1/chat/completions"
            ),
        )
        ok_resp = httpx.Response(
            status_code=200,
            json={
                "choices": [{"message": {"content": "or-ok"}}],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 2,
                    "total_tokens": 3,
                },
            },
            request=httpx.Request(
                "POST", "https://openrouter.ai/api/v1/chat/completions"
            ),
        )
        auth_resp = httpx.Response(
            status_code=401,
            json={"error": {"message": "Invalid key"}},
            request=httpx.Request(
                "POST", "https://openrouter.ai/api/v1/chat/completions"
            ),
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=[rate_resp, ok_resp])

        provider = OpenRouter(api_key="or-test")
        with (
            patch(
                "openagent_eval.providers.llm.openrouter.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep,
        ):
            assert await provider.generate("hello") == "or-ok"
        assert mock_client.post.await_count == 2
        mock_sleep.assert_awaited_once_with(5.0)

        mock_client.post = AsyncMock(return_value=auth_resp)
        with (
            patch(
                "openagent_eval.providers.llm.openrouter.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(ProviderExecutionError),
        ):
            await provider.generate("hello")
        assert mock_client.post.await_count == 1

        mock_client.post = AsyncMock(
            return_value=httpx.Response(200, content=b"invalid JSON")
        )
        with (
            patch(
                "openagent_eval.providers.llm.openrouter.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(ValueError),
        ):
            await provider.generate("hello")
        assert mock_client.post.await_count == 1

    @pytest.mark.asyncio
    async def test_ollama_retries_connect_error_then_succeeds(self) -> None:
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.raise_for_status = MagicMock()
        ok_resp.json.return_value = {
            "model": "llama3.2",
            "response": "ollama-ok",
            "done": True,
        }

        provider = Ollama()
        provider._client = AsyncMock()
        provider._client.post = AsyncMock(
            side_effect=[httpx.ConnectError("refused"), ok_resp]
        )

        with patch(
            "openagent_eval.providers.base.retry.asyncio.sleep", new_callable=AsyncMock
        ):
            result = await provider.generate("hello")

        assert result == "ollama-ok"
        assert provider._client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_ollama_usage_retries_503_then_returns_content_and_tokens(
        self,
    ) -> None:
        request_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            if request_count == 1:
                return httpx.Response(503)
            return httpx.Response(
                200,
                json={
                    "model": "llama3.2",
                    "response": "ollama-ok",
                    "done": True,
                    "prompt_eval_count": 3,
                    "eval_count": 5,
                },
            )

        async with Ollama() as provider:
            await provider._client.aclose()
            provider._client = httpx.AsyncClient(
                base_url="http://localhost:11434",
                transport=httpx.MockTransport(handler),
            )
            with patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ):
                result = await provider.generate_with_usage("hello")

        assert request_count == 2
        assert result.content == "ollama-ok"
        assert result.usage is not None
        assert result.usage.prompt_tokens == 3
        assert result.usage.completion_tokens == 5
        assert result.usage.total_tokens == 8


def _make_transport_provider(
    provider_kind: str, http_client: httpx.AsyncClient
) -> tuple[OpenAIProvider | Anthropic | Groq, dict[str, object]]:
    """Construct a real SDK provider swapping only the underlying httpx transport."""
    if provider_kind == "openai":
        pytest.importorskip("openai")
        pytest.importorskip("tiktoken")
        provider = OpenAIProvider(api_key="sk-test-transport")
        provider._client = provider._client.with_options(http_client=http_client)
        ok_body: dict[str, object] = {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ok"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        return provider, ok_body
    if provider_kind == "anthropic":
        pytest.importorskip("anthropic")
        provider_ant = Anthropic(api_key="sk-ant-test-transport")
        provider_ant._client = provider_ant._client.with_options(
            http_client=http_client
        )
        ok_body = {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": "claude-sonnet-4-20250514",
            "content": [{"type": "text", "text": "ok"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
        return provider_ant, ok_body
    pytest.importorskip("groq")
    provider_groq = Groq(api_key="gsk-test-transport")
    provider_groq.client = provider_groq.client.with_options(http_client=http_client)
    ok_body = {
        "id": "chatcmpl-groq-1",
        "object": "chat.completion",
        "created": 0,
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "ok"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    return provider_groq, ok_body


class TestTransportRetryOwnership:
    """Verify at HTTP transport level that shared retries run without SDK multipliers."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("provider_kind", ["openai", "anthropic", "groq"])
    async def test_first_request_success_sends_single_http_request(
        self, provider_kind: str
    ) -> None:
        request_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            return httpx.Response(200, json=ok_body)

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            provider, ok_body = _make_transport_provider(provider_kind, http_client)
            result = await provider.generate("hello")

        assert result == "ok"
        assert request_count == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("provider_kind", ["openai", "anthropic", "groq"])
    @pytest.mark.parametrize("max_attempts", [None, 1], ids=["default", "single"])
    async def test_persistent_429_leaves_retries_to_the_shared_loop(
        self, provider_kind: str, max_attempts: int | None
    ) -> None:
        request_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            return httpx.Response(
                429,
                json={
                    "type": "error",
                    "error": {"type": "rate_limit_error", "message": "rate limited"},
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            provider, _ = _make_transport_provider(provider_kind, http_client)
            if max_attempts is not None:
                provider._retry_config = RetryConfig(max_attempts=max_attempts)
            with (
                patch(
                    "openagent_eval.providers.base.retry.asyncio.sleep",
                    new_callable=AsyncMock,
                ),
                pytest.raises(ProviderExecutionError),
            ):
                await provider.generate("hello")

        assert request_count == (3 if max_attempts is None else max_attempts)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("provider_kind", ["openai", "anthropic", "groq"])
    async def test_409_conflict_retries_once_then_succeeds(
        self, provider_kind: str
    ) -> None:
        request_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            if request_count == 1:
                return httpx.Response(
                    409,
                    json={
                        "type": "error",
                        "error": {"type": "conflict_error", "message": "conflict"},
                    },
                )
            return httpx.Response(200, json=ok_body)

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            provider, ok_body = _make_transport_provider(provider_kind, http_client)
            with patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ):
                result = await provider.generate("hello")

        assert result == "ok"
        assert request_count == 2

    @pytest.mark.asyncio
    async def test_anthropic_token_count_retries_once_through_shared_loop(
        self,
    ) -> None:
        request_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            if request_count == 1:
                return httpx.Response(
                    429,
                    json={
                        "type": "error",
                        "error": {
                            "type": "rate_limit_error",
                            "message": "rate limited",
                        },
                    },
                )
            return httpx.Response(200, json={"input_tokens": 7})

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            provider, _ = _make_transport_provider("anthropic", http_client)
            assert isinstance(provider, Anthropic)
            with patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ):
                count = await provider.get_token_count("hello")

        assert count == 7
        assert request_count == 2

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("retry_after", "retry_after_ms", "expected_delays"),
        [("5", "2500", [5.0, 2.5]), ("120", "120000", [60.0, 60.0])],
    )
    async def test_anthropic_529_overload_and_retry_after_header_honored(
        self, retry_after: str, retry_after_ms: str, expected_delays: list[float]
    ) -> None:
        request_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            if request_count == 1:
                return httpx.Response(
                    529,
                    headers={"retry-after": retry_after},
                    json={
                        "type": "error",
                        "error": {
                            "type": "overloaded_error",
                            "message": "Overloaded",
                        },
                    },
                )
            if request_count == 2:
                return httpx.Response(
                    429,
                    headers={"retry-after-ms": retry_after_ms},
                    json={
                        "type": "error",
                        "error": {
                            "type": "rate_limit_error",
                            "message": "Rate limited",
                        },
                    },
                )
            return httpx.Response(
                200,
                json={
                    "id": "msg_529",
                    "type": "message",
                    "role": "assistant",
                    "model": "claude-sonnet-4-20250514",
                    "content": [{"type": "text", "text": "recovered"}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            provider, _ = _make_transport_provider("anthropic", http_client)
            with patch(
                "openagent_eval.providers.base.retry.asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep:
                result = await provider.generate("hello")

        assert result == "recovered"
        assert request_count == 3
        assert [c.args[0] for c in mock_sleep.await_args_list] == expected_delays
