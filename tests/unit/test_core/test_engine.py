"""Tests for the core module."""

from __future__ import annotations

import pytest

from openagent_eval.config.models import Config
from openagent_eval.core.engine import Engine
from openagent_eval.core.executor import Executor
from openagent_eval.core.pipeline import EvaluationResult, Pipeline, PipelineResult
from openagent_eval.core.registry import Registry
from openagent_eval.exceptions import PluginNotFoundError


class TestRegistry:
    """Tests for the plugin registry."""

    def test_register_metric(self) -> None:
        """Test registering a metric."""
        registry = Registry()

        class FakeMetric:
            name = "fake_metric"

        registry.register_metric("fake_metric", FakeMetric)
        assert "fake_metric" in registry.list_metrics()

    def test_get_metric(self) -> None:
        """Test getting a registered metric."""
        registry = Registry()

        class FakeMetric:
            name = "fake_metric"

        registry.register_metric("fake_metric", FakeMetric)
        metric_class = registry.get_metric("fake_metric")
        assert metric_class is FakeMetric

    def test_get_metric_not_found(self) -> None:
        """Test getting a non-existent metric."""
        registry = Registry()
        with pytest.raises(PluginNotFoundError):
            registry.get_metric("nonexistent")

    def test_register_provider(self) -> None:
        """Test registering a provider."""
        registry = Registry()

        class FakeProvider:
            name = "fake_provider"

        registry.register_provider("fake_provider", FakeProvider)
        assert "fake_provider" in registry.list_providers()

    def test_get_provider_not_found(self) -> None:
        """Test getting a non-existent provider."""
        registry = Registry()
        with pytest.raises(PluginNotFoundError):
            registry.get_provider("nonexistent")


class TestExecutor:
    """Tests for the async executor."""

    def test_init(self) -> None:
        """Test executor initialization."""
        executor = Executor(max_workers=2, timeout=60.0)
        assert executor.max_workers == 2
        assert executor.timeout == 60.0

    @pytest.mark.asyncio
    async def test_execute_parallel(self) -> None:
        """Test parallel execution."""
        executor = Executor(max_workers=2)

        async def fake_task(x: int) -> int:
            return x * 2

        results = await executor.execute_parallel([fake_task, fake_task], 5)
        assert results == [10, 10]

    @pytest.mark.asyncio
    async def test_execute_sequential(self) -> None:
        """Test sequential execution."""
        executor = Executor(max_workers=2)

        async def fake_task(x: int) -> int:
            return x * 2

        results = await executor.execute_sequential([fake_task, fake_task], 5)
        assert results == [10, 10]


class TestPipeline:
    """Tests for the evaluation pipeline."""

    def test_init(self, sample_config: Config) -> None:
        """Test pipeline initialization."""
        pipeline = Pipeline(sample_config)
        assert pipeline.config is sample_config

    @pytest.mark.asyncio
    async def test_execute(self, sample_config: Config, sample_dataset: list[dict]) -> None:
        """Test pipeline execution."""
        pipeline = Pipeline(sample_config)
        result = await pipeline.execute(sample_dataset)
        assert isinstance(result, PipelineResult)
        assert len(result.results) == len(sample_dataset)

    @pytest.mark.asyncio
    async def test_execute_empty_dataset(self, sample_config: Config) -> None:
        """Test pipeline execution with empty dataset."""
        pipeline = Pipeline(sample_config)
        result = await pipeline.execute([])
        assert isinstance(result, PipelineResult)
        assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_item_error_records_error_type(self, sample_config: Config) -> None:
        """C3: per-item failures must record the real exception type under
        'error_type' (not the legacy 'type' key) so reports don't collapse to
        'Unknown'."""
        pipeline = Pipeline(sample_config)

        class BoomError(Exception):
            pass

        async def _boom(*_: object, **__: object) -> object:
            raise BoomError("retrieval failed")

        pipeline._retrieve = _boom  # type: ignore[assignment]

        result = PipelineResult()
        await pipeline._evaluate_item({"question": "q"}, result)

        assert len(result.errors) == 1
        err = result.errors[0]
        assert err["error_type"] == "BoomError"
        assert "type" not in err


class TestEngine:
    """Tests for the evaluation engine."""

    def test_init(self, sample_config: Config) -> None:
        """Test engine initialization."""
        engine = Engine(sample_config)
        assert engine.config is sample_config
        assert isinstance(engine.registry, Registry)
        assert isinstance(engine.executor, Executor)
        assert isinstance(engine.pipeline, Pipeline)

    @pytest.mark.asyncio
    async def test_run(self, sample_config: Config, sample_dataset: list[dict]) -> None:
        """Test engine execution."""
        engine = Engine(sample_config)
        report = await engine.run(sample_dataset)
        assert report.config is sample_config
        assert report.summary["total_items"] == len(sample_dataset)
        engine.shutdown()

    @pytest.mark.asyncio
    async def test_run_summary_counts_success_and_failure(
        self, sample_config: Config, sample_dataset: list[dict], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """H10: successful_evaluations must not double-count failed items.

        Inject a PipelineResult with 2 results and 1 error; the summary must
        report 1 successful and 1 failed (not 2 successful + 1 failed).
        """
        injected = PipelineResult(
            results=[EvaluationResult(question="q", answer="a") for _ in range(2)],
            errors=[{"item": {}, "error": "boom", "error_type": "Boom"}],
        )

        async def _fake_execute(self: Pipeline, dataset: list[dict]) -> PipelineResult:
            return injected

        monkeypatch.setattr(Pipeline, "execute", _fake_execute)

        engine = Engine(sample_config)
        report = await engine.run(sample_dataset)
        assert report.summary["total_items"] == len(sample_dataset)
        assert report.summary["successful_evaluations"] == 1
        assert report.summary["failed_evaluations"] == 1
        engine.shutdown()
