"""Main evaluation engine for OpenAgent Eval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openagent_eval.config.models import Config
from openagent_eval.core.executor import Executor
from openagent_eval.core.pipeline import Pipeline, PipelineResult
from openagent_eval.core.registry import Registry
from openagent_eval.exceptions.metric import MetricNotFoundError
from openagent_eval.metrics import METRIC_REGISTRY, get_metric
from openagent_eval.metrics.base import BaseMetric
from openagent_eval.providers.factory import get_llm_provider, get_retriever


@dataclass
class EvaluationReport:
    """Complete evaluation report."""

    config: Config
    result: PipelineResult
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class Engine:
    """Main evaluation engine that orchestrates the entire evaluation.

    The engine coordinates:
    - Provider construction (LLM + retriever) from configuration
    - Metric resolution from the metric registry
    - Pipeline execution (with optional parallelism via the Executor)
    - Report generation
    """

    def __init__(
        self,
        config: Config,
        retriever: Any | None = None,
        llm: Any | None = None,
        metrics: list[tuple[str, BaseMetric]] | None = None,
    ) -> None:
        """Initialize the engine.

        Args:
            config: The evaluation configuration.
            retriever: Optional injected ``Retriever`` (overrides config).
            llm: Optional injected ``LLMProvider`` (overrides config).
            metrics: Optional list of ``(name, metric)`` tuples (overrides config).
        """
        self.config = config
        self.registry = Registry()
        self.executor = Executor(
            max_workers=config.max_workers,
            timeout=config.timeout,
        )
        self._retriever = retriever if retriever is not None else self._build_retriever()
        self._llm = llm if llm is not None else self._build_llm()
        self._metrics = metrics if metrics is not None else self._build_metrics()
        self.pipeline = Pipeline(
            config,
            retriever=self._retriever,
            llm=self._llm,
            metrics=self._metrics,
            executor=self.executor,
        )

    async def run(self, dataset: list[dict[str, Any]]) -> EvaluationReport:
        """Run the evaluation engine.

        Args:
            dataset: List of dataset items to evaluate.

        Returns:
            EvaluationReport with results and summary.
        """
        result = await self.pipeline.execute(dataset)

        summary = {
            "total_items": len(dataset),
            "successful_evaluations": len(result.results),
            "failed_evaluations": len(result.errors),
            "metrics_summary": result.summary.get("metrics", {}),
            "total_tokens": result.summary.get("total_tokens", 0),
            "average_latency_ms": result.summary.get("average_latency_ms"),
        }

        return EvaluationReport(
            config=self.config,
            result=result,
            summary=summary,
            metadata={
                "version": "0.1.0",
                "engine": "openagent-eval",
                "llm_provider": getattr(self._llm, "name", None),
                "retriever_provider": getattr(self._retriever, "name", None),
            },
        )

    def shutdown(self) -> None:
        """Shutdown the engine and clean up resources."""
        self.executor.shutdown()

    # ------------------------------------------------------------------ #
    # Construction helpers                                                #
    # ------------------------------------------------------------------ #

    def _build_retriever(self) -> Any | None:
        """Build the retriever from configuration."""
        try:
            return get_retriever(self.config.retriever)
        except Exception as e:  # pragma: no cover - depends on installed deps
            # A missing retriever (e.g. chromadb not installed) should not
            # crash generation-only evaluations; surface a clear warning.
            import logging

            logging.getLogger(__name__).warning(
                "Retriever unavailable (%s); retrieval metrics will be skipped.", e
            )
            return None

    def _build_llm(self) -> Any | None:
        """Build the LLM provider from configuration."""
        try:
            return get_llm_provider(self.config.llm)
        except Exception as e:  # pragma: no cover - depends on installed deps
            import logging

            logging.getLogger(__name__).warning(
                "LLM provider unavailable (%s); answers will be empty.", e
            )
            return None

    def _build_metrics(self) -> list[tuple[str, BaseMetric]]:
        """Resolve and instantiate all configured metrics from the registry."""
        names: list[str] = []
        names.extend(self.config.metrics.retrieval)
        names.extend(self.config.metrics.generation)
        names.extend(self.config.metrics.performance)
        names.extend(self.config.metrics.cost)

        resolved: list[tuple[str, BaseMetric]] = []
        for name in names:
            try:
                metric_cls = get_metric(name)
            except KeyError as e:
                raise MetricNotFoundError(
                    metric_name=name,
                    available_metrics=list(METRIC_REGISTRY.keys()),
                ) from e
            resolved.append((name, metric_cls()))
        return resolved
