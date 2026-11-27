"""Tests for local disk LLM response cache and Pipeline/Engine integration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from openagent_eval.config.models import (
    Config,
    DatasetConfig,
    LLMConfig,
    MetricsConfig,
    RetrieverConfig,
)
from openagent_eval.core.cache import ResponseCache
from openagent_eval.core.engine import Engine
from openagent_eval.providers.models import LLMResponse, TokenUsage


class _CountingStubLLM:
    name = "openai"
    model_name = "gpt-4o-mini"

    def __init__(self, delay_seconds: float = 0.02) -> None:
        self.calls = 0
        self.delay_seconds = delay_seconds

    async def generate_with_usage(self, prompt: str, **_: Any) -> LLMResponse:
        del prompt
        self.calls += 1
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)
        return LLMResponse(
            content=f"answer-{self.calls}",
            model=self.model_name,
            provider=self.name,
            usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            latency_ms=self.delay_seconds * 1000.0,
        )


class _StubRetriever:
    name = "mock"

    async def retrieve(self, query: str, **_: Any) -> list[Any]:
        del query
        return []


class TestResponseCacheUnit:
    """Unit tests for ResponseCache."""

    def test_round_trip_and_key_isolation(self, tmp_path: Path) -> None:
        cache = ResponseCache(cache_dir=tmp_path)
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        cache.set("openai", "gpt-4o", "hello", "world", usage=usage, latency_ms=5.0)

        hit = cache.get("openai", "gpt-4o", "hello")
        assert hit is not None
        content, loaded_usage = hit
        assert content == "world"
        assert loaded_usage == usage

        assert cache.get("openai", "gpt-4o-mini", "hello") is None
        assert cache.get("anthropic", "gpt-4o", "hello") is None
        assert cache.get("openai", "gpt-4o", "other") is None

    def test_corrupt_cache_file_returns_none(self, tmp_path: Path) -> None:
        cache = ResponseCache(cache_dir=tmp_path)
        key = cache.build_key("openai", "gpt-4o", "broken")
        (tmp_path / f"{key}.json").write_text("{not valid json", encoding="utf-8")
        assert cache.get("openai", "gpt-4o", "broken") is None

    def test_disabled_cache_never_writes_or_reads(self, tmp_path: Path) -> None:
        target = tmp_path / "disabled"
        cache = ResponseCache(cache_dir=target, enabled=False)
        cache.set("openai", "gpt-4o", "hi", "there")
        assert not target.exists()
        assert cache.get("openai", "gpt-4o", "hi") is None

    def test_clear_deletes_entries(self, tmp_path: Path) -> None:
        cache = ResponseCache(cache_dir=tmp_path)
        cache.set("openai", "gpt-4o", "p1", "a1")
        cache.set("openai", "gpt-4o", "p2", "a2")
        assert cache.clear() == 2
        assert cache.get("openai", "gpt-4o", "p1") is None


class TestPipelineResponseCache:
    """Integration tests for Engine/Pipeline response caching."""

    @pytest.mark.asyncio
    async def test_second_run_hits_cache_with_zero_api_tokens(
        self, tmp_path: Path
    ) -> None:
        dataset = [
            {"question": "Q1?", "ground_truth": "answer-1", "context": "ctx"},
            {"question": "Q2?", "ground_truth": "answer-2", "context": "ctx"},
        ]
        config = Config(
            dataset=DatasetConfig(path="unused.json"),
            llm=LLMConfig(provider="openai", model="gpt-4o-mini"),
            retriever=RetrieverConfig(provider="mock"),
            metrics=MetricsConfig(
                retrieval=[],
                generation=["exact_match"],
                performance=["latency"],
                cost=["token_count"],
            ),
            cache=True,
            cache_dir=str(tmp_path / "cache"),
        )

        llm = _CountingStubLLM(delay_seconds=0.025)
        engine = Engine(config, retriever=_StubRetriever(), llm=llm)
        try:
            first = await engine.run(dataset)
            second = await engine.run(dataset)
        finally:
            engine.shutdown()

        assert llm.calls == 2
        assert first.summary["cache_hits"] == 0
        assert first.summary["cache_misses"] == 2
        assert first.summary["cache_hit_rate"] == 0.0
        assert first.summary["total_tokens"] == 300

        assert second.summary["cache_hits"] == 2
        assert second.summary["cache_misses"] == 0
        assert second.summary["cache_hit_rate"] == pytest.approx(1.0)
        assert second.summary["total_tokens"] == 0
        assert (
            second.summary["average_latency_ms"] < first.summary["average_latency_ms"]
        )
        assert [r.answer for r in second.result.results] == [
            r.answer for r in first.result.results
        ]

    @pytest.mark.asyncio
    async def test_cache_false_disables_caching_completely(
        self, tmp_path: Path
    ) -> None:
        dataset = [{"question": "Q1?", "ground_truth": "answer-1", "context": "ctx"}]
        cache_dir = tmp_path / "no-cache"
        config = Config(
            dataset=DatasetConfig(path="unused.json"),
            llm=LLMConfig(provider="openai", model="gpt-4o-mini"),
            retriever=RetrieverConfig(provider="mock"),
            metrics=MetricsConfig(retrieval=[], generation=[], performance=[], cost=[]),
            cache=False,
            cache_dir=str(cache_dir),
        )

        llm = _CountingStubLLM(delay_seconds=0.0)
        engine = Engine(config, retriever=_StubRetriever(), llm=llm)
        try:
            first = await engine.run(dataset)
            second = await engine.run(dataset)
        finally:
            engine.shutdown()

        assert llm.calls == 2
        assert first.summary["cache_hits"] == 0
        assert second.summary["cache_hits"] == 0
        assert not cache_dir.exists()
