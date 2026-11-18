"""Tests for per-provider token-bucket rate limiting (#354)."""

from __future__ import annotations

import asyncio
import time

import pytest
from pydantic import ValidationError

from openagent_eval.config.models import Config, DatasetConfig, LLMConfig
from openagent_eval.core.engine import Engine
from openagent_eval.core.executor import Executor, TokenBucketRateLimiter
from openagent_eval.core.pipeline import Pipeline
from openagent_eval.providers.llm.mock import MockLLMProvider


class DelayedMockLLM(MockLLMProvider):
    """Mock LLM provider that introduces a fixed per-call async delay."""

    def __init__(self, delay_s: float = 0.01) -> None:
        super().__init__(model="delayed-mock")
        self.delay_s = delay_s
        self.call_timestamps: list[float] = []

    async def generate(self, prompt: str, **kwargs: object) -> str:
        self.call_timestamps.append(time.monotonic())
        await asyncio.sleep(self.delay_s)
        return await super().generate(prompt, **kwargs)


class TestLLMConfigRateLimit:
    """Validation tests for LLMConfig.rate_limit."""

    def test_accepts_none_and_positive_rate_limit(self) -> None:
        assert LLMConfig(provider="mock", model="m").rate_limit is None
        assert LLMConfig(provider="mock", model="m", rate_limit=5.0).rate_limit == 5.0

    @pytest.mark.parametrize("bad_rate", [0.0, -1.0, -0.01])
    def test_rejects_non_positive_rate_limit(self, bad_rate: float) -> None:
        with pytest.raises(ValidationError):
            LLMConfig(provider="mock", model="m", rate_limit=bad_rate)


class TestTokenBucketRateLimiter:
    """Unit tests for TokenBucketRateLimiter."""

    @pytest.mark.parametrize("rate", [0.0, -5.0])
    def test_invalid_rate_raises(self, rate: float) -> None:
        with pytest.raises(ValueError, match="rate must be positive"):
            TokenBucketRateLimiter(rate=rate)

    @pytest.mark.asyncio
    async def test_throttles_sequential_calls_to_configured_rate(self) -> None:
        limiter = TokenBucketRateLimiter(rate=20.0, capacity=1.0)
        start = time.monotonic()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        # First call consumes the initial token; 4 subsequent calls wait >= 4/20s.
        assert elapsed >= 0.16


class TestPipelineAndEngineRateLimiting:
    """End-to-end throttling tests using MockLLMProvider with artificial delay."""

    @pytest.mark.asyncio
    async def test_engine_respects_configured_rate_limit_under_parallel_load(
        self,
    ) -> None:
        dataset = [{"question": f"Q{i}", "ground_truth": f"A{i}"} for i in range(6)]

        unthrottled_cfg = Config(
            dataset=DatasetConfig(path="unused.json"),
            llm=LLMConfig(provider="mock", model="delayed-mock", rate_limit=None),
            parallel=True,
            max_workers=6,
        )
        unthrottled_llm = DelayedMockLLM(delay_s=0.01)
        unthrottled_engine = Engine(
            unthrottled_cfg, retriever=None, llm=unthrottled_llm, metrics=[]
        )
        t0 = time.monotonic()
        unthrottled_report = await unthrottled_engine.run(dataset)
        unthrottled_elapsed = time.monotonic() - t0
        assert len(unthrottled_report.result.results) == 6
        assert unthrottled_elapsed < 0.15

        throttled_cfg = Config(
            dataset=DatasetConfig(path="unused.json"),
            llm=LLMConfig(provider="mock", model="delayed-mock", rate_limit=10.0),
            parallel=True,
            max_workers=6,
        )
        throttled_llm = DelayedMockLLM(delay_s=0.01)
        throttled_engine = Engine(
            throttled_cfg, retriever=None, llm=throttled_llm, metrics=[]
        )
        t1 = time.monotonic()
        throttled_report = await throttled_engine.run(dataset)
        throttled_elapsed = time.monotonic() - t1

        assert throttled_report.summary["successful_evaluations"] == 6
        assert throttled_report.summary["failed_evaluations"] == 0
        # At 10 req/s (capacity=1), 6 calls require at least 5 intervals = 0.50s.
        assert throttled_elapsed >= 0.42
        assert throttled_elapsed > unthrottled_elapsed

    @pytest.mark.asyncio
    async def test_pipeline_standalone_without_executor_applies_rate_limit(
        self,
    ) -> None:
        cfg = Config(
            dataset=DatasetConfig(path="unused.json"),
            llm=LLMConfig(provider="mock", model="delayed-mock", rate_limit=20.0),
            parallel=False,
        )
        llm = DelayedMockLLM(delay_s=0.005)
        pipeline = Pipeline(cfg, retriever=None, llm=llm, metrics=[], executor=None)
        t0 = time.monotonic()
        res = await pipeline.execute(
            [{"question": f"Q{i}", "ground_truth": f"A{i}"} for i in range(4)]
        )
        elapsed = time.monotonic() - t0
        assert len(res.results) == 4
        # 4 calls at 20 req/s => >= 3/20 = 0.15s.
        assert elapsed >= 0.12

    def test_executor_configures_and_returns_rate_limiter(self) -> None:
        executor = Executor(rate_limits={"openai": 2.5})
        assert executor.get_rate_limiter("openai") is not None
        assert executor.get_rate_limiter("anthropic") is None
