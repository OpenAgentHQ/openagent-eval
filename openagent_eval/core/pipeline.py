"""Evaluation pipeline for OpenAgent Eval.

The pipeline orchestrates the full RAG evaluation flow:

    Dataset → Question → Retriever → Retrieved Docs → LLM → Answer → Metrics → Reports

It is provider-agnostic: the retriever and LLM are injected (or built from the
``Config`` by the ``Engine``), and metrics are resolved from the metric
registry. Each item is evaluated independently so the loop can run in parallel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openagent_eval.config.models import Config
from openagent_eval.metrics.base import BaseMetric


@dataclass
class EvaluationResult:
    """Result of evaluating a single item."""

    question: str
    answer: str
    ground_truth: str | None = None
    contexts: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of the entire evaluation pipeline."""

    results: list[EvaluationResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)


class Pipeline:
    """Evaluation pipeline that orchestrates the evaluation process."""

    def __init__(
        self,
        config: Config,
        retriever: Any | None = None,
        llm: Any | None = None,
        metrics: list[tuple[str, BaseMetric]] | None = None,
        executor: Any | None = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            config: The evaluation configuration.
            retriever: Optional injected ``Retriever`` (else built by ``Engine``).
            llm: Optional injected ``LLMProvider`` (else built by ``Engine``).
            metrics: Optional list of ``(name, metric)`` tuples (else built by ``Engine``).
            executor: Optional ``Executor`` used for parallel item evaluation.
        """
        self.config = config
        self._retriever = retriever
        self._llm = llm
        self._metrics: list[tuple[str, BaseMetric]] = metrics or []
        self._executor = executor
        self._k = self._resolve_k()

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    async def execute(self, dataset: list[dict[str, Any]]) -> PipelineResult:
        """Execute the evaluation pipeline over a dataset.

        Args:
            dataset: List of dataset items (dicts) to evaluate.

        Returns:
            PipelineResult with evaluation results and summary.
        """
        result = PipelineResult()
        items = list(dataset)

        coroutines = [self._evaluate_item(item, result) for item in items]

        if self.config.parallel and self._executor is not None and len(coroutines) > 1:
            result.results = await self._executor.gather(coroutines)
        else:
            result.results = [await coro for coro in coroutines]

        result.summary = self._compute_summary(result.results, result.errors)
        return result

    # ------------------------------------------------------------------ #
    # Item evaluation                                                     #
    # ------------------------------------------------------------------ #

    async def _evaluate_item(
        self, item: dict[str, Any], result: PipelineResult
    ) -> EvaluationResult:
        """Evaluate a single dataset item end-to-end.

        Retrieval and generation failures are contained per-item: the item is
        still returned (with empty answer/contexts and zeroed metrics) and the
        failure is recorded in ``result.errors`` rather than aborting the run.
        """
        question = item.get("question", "")
        ground_truth = item.get("ground_truth")
        context = item.get("context")
        gt_contexts = item.get("ground_truth_contexts", []) or []

        try:
            # 1. Retrieval
            contexts = await self._retrieve(question, context, gt_contexts)

            # 2. Generation
            answer, token_usage, latency_ms = await self._generate(
                question, contexts, ground_truth
            )

            # 3. Metrics
            metrics, metric_errors = self._run_metrics(
                question, answer, ground_truth, contexts, gt_contexts,
                latency_ms, token_usage,
            )

            return EvaluationResult(
                question=question,
                answer=answer,
                ground_truth=ground_truth,
                contexts=contexts,
                metrics=metrics,
                metadata={
                    "latency_ms": latency_ms,
                    "prompt_tokens": token_usage.prompt_tokens if token_usage else None,
                    "completion_tokens": token_usage.completion_tokens if token_usage else None,
                    "total_tokens": token_usage.total_tokens if token_usage else None,
                    "metric_errors": metric_errors,
                    **item.get("metadata", {}),
                },
            )
        except Exception as e:  # pragma: no cover - defensive boundary
            result.errors.append(
                {
                    "item": {k: v for k, v in item.items() if k != "metadata"},
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return EvaluationResult(
                question=question,
                answer="",
                ground_truth=ground_truth,
                contexts=[],
                metrics={name: 0.0 for name, _ in self._metrics},
                metadata={"failed": True, "error": str(e)},
            )

    # ------------------------------------------------------------------ #
    # Steps                                                               #
    # ------------------------------------------------------------------ #

    async def _retrieve(
        self, question: str, context: str | None, gt_contexts: list[str]
    ) -> list[str]:
        """Retrieve contexts for a question, or fall back to dataset context."""
        if self._retriever is not None:
            try:
                if getattr(self._retriever, "name", None) == "mock":
                    docs = await self._retriever.retrieve(
                        question, k=self._k, ground_truth_contexts=gt_contexts
                    )
                else:
                    docs = await self._retriever.retrieve(question, k=self._k)
                return [doc.content for doc in docs]
            except Exception:
                # Retrieval failure -> fall back to any dataset-provided context.
                if context:
                    return [context]
                return []

        if context:
            return [context]
        return []

    async def _generate(
        self, question: str, contexts: list[str], ground_truth: str | None
    ) -> tuple[str, Any, float | None]:
        """Generate an answer for a question using the configured LLM."""
        prompt = self._build_prompt(question, contexts)
        if self._llm is None:
            return "", None, None

        try:
            response = await self._llm.generate_with_usage(prompt, ground_truth=ground_truth)
            return response.content, response.usage, response.latency_ms
        except Exception:
            # Generation failure -> empty answer; metrics will report accordingly.
            return "", None, None

    def _run_metrics(
        self,
        question: str,
        answer: str,
        ground_truth: str | None,
        contexts: list[str],
        gt_contexts: list[str],
        latency_ms: float | None,
        token_usage: Any | None,
    ) -> tuple[dict[str, float], dict[str, str]]:
        """Run every configured metric and collect scores.

        Returns:
            A tuple of ``(metrics, metric_errors)`` where ``metric_errors`` maps
            metric name -> error message for any metric that raised.
        """
        scores: dict[str, float] = {}
        errors: dict[str, str] = {}

        prompt_tokens = token_usage.prompt_tokens if token_usage else 0
        completion_tokens = token_usage.completion_tokens if token_usage else 0
        provider_name = getattr(self._llm, "name", None)
        model_name = getattr(self._llm, "_model", None) or self.config.llm.model

        for name, metric in self._metrics:
            try:
                result = metric.evaluate(
                    question=question,
                    answer=answer,
                    ground_truth=ground_truth,
                    contexts=contexts,
                    retrieved_contexts=contexts,
                    ground_truth_contexts=gt_contexts,
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    provider=provider_name,
                    model=model_name,
                )
                scores[name] = result.score
            except Exception as e:
                scores[name] = 0.0
                errors[name] = str(e)

        return scores, errors

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _build_prompt(self, question: str, contexts: list[str]) -> str:
        """Build a simple RAG prompt from the question and retrieved contexts."""
        if contexts:
            joined = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(contexts))
            return f"Context:\n{joined}\n\nQuestion: {question}\n\nAnswer:"
        return f"Question: {question}\n\nAnswer:"

    def _resolve_k(self) -> int:
        """Resolve the retrieval ``k`` from retriever settings (default 5)."""
        settings = self.config.retriever.settings if self.config.retriever else {}
        try:
            return int(settings.get("k", 5))
        except (TypeError, ValueError):
            return 5

    def _compute_summary(
        self, results: list[EvaluationResult], errors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Compute summary statistics from evaluation results.

        Args:
            results: List of evaluation results.
            errors: List of per-item errors recorded during execution.

        Returns:
            Summary statistics dictionary.
        """
        if not results:
            return {"total": 0, "errors": len(errors)}

        metric_sums: dict[str, float] = {}
        metric_counts: dict[str, int] = {}

        for result in results:
            for metric_name, score in result.metrics.items():
                metric_sums[metric_name] = metric_sums.get(metric_name, 0.0) + score
                metric_counts[metric_name] = metric_counts.get(metric_name, 0) + 1

        metric_averages = {
            name: metric_sums[name] / metric_counts[name]
            for name in metric_sums
            if metric_counts[name] > 0
        }

        total_tokens = sum(
            (r.metadata.get("total_tokens") or 0) for r in results
        )
        latencies = [
            r.metadata.get("latency_ms")
            for r in results
            if r.metadata.get("latency_ms") is not None
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        return {
            "total": len(results),
            "errors": len(errors),
            "metrics": metric_averages,
            "total_tokens": total_tokens,
            "average_latency_ms": avg_latency,
        }
