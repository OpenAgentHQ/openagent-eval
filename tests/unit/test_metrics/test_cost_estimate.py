"""Tests for providers/pricing.py, CostEstimateMetric, and report cost summaries."""

from __future__ import annotations

import json
from typing import Any

import pytest

from openagent_eval.config.models import (
    Config,
    DatasetConfig,
    LLMConfig,
    MetricsConfig,
    RetrieverConfig,
)
from openagent_eval.core.engine import Engine
from openagent_eval.metrics import METRIC_REGISTRY, CostEstimateMetric, get_metric
from openagent_eval.metrics.cost.tokens import (
    COST_PER_1M_TOKENS as TOKENS_COST_TABLE,
)
from openagent_eval.providers.models import LLMResponse, TokenUsage
from openagent_eval.providers.pricing import (
    MODEL_PRICING,
    ModelPricing,
    estimate_cost_usd,
    get_model_pricing,
)
from openagent_eval.reports.html import HTMLReport
from openagent_eval.reports.json_report import JSONReport
from openagent_eval.reports.markdown import MarkdownReport
from openagent_eval.reports.terminal import TerminalReport


class TestPricingTable:
    """Tests for openagent_eval.providers.pricing."""

    def test_exact_lookup_is_case_insensitive(self) -> None:
        pricing = get_model_pricing("OpenAI", "GPT-4O")
        assert pricing == ModelPricing(prompt_per_1k=0.0025, completion_per_1k=0.01)

    def test_snapshot_suffix_falls_back_to_longest_prefix(self) -> None:
        pricing = get_model_pricing("openai", "gpt-4o-2024-08-06")
        assert pricing == MODEL_PRICING[("openai", "gpt-4o")]

    def test_openrouter_delegates_to_upstream_vendor_pricing(self) -> None:
        pricing = get_model_pricing("openrouter", "openai/gpt-4.1")
        assert pricing == MODEL_PRICING[("openai", "gpt-4.1")]

    def test_local_and_mock_providers_are_zero_cost(self) -> None:
        assert get_model_pricing("ollama", "llama3.2") == ModelPricing(0.0, 0.0)
        assert get_model_pricing("mock", "mock-model") == ModelPricing(0.0, 0.0)

    def test_unknown_provider_or_model_returns_none(self) -> None:
        assert get_model_pricing("custom-cloud", "unknown-1") is None
        assert get_model_pricing("", "gpt-4o") is None

    def test_estimate_cost_usd_calculation_and_clamping(self) -> None:
        # 1,000 prompt tokens * $0.0025/1K + 500 completion tokens * $0.01/1K = $0.0075
        cost = estimate_cost_usd(1000, 500, provider="openai", model="gpt-4o")
        assert cost == pytest.approx(0.0075)
        assert estimate_cost_usd(-50, 0, provider="openai", model="gpt-4o") == 0.0
        assert estimate_cost_usd(1000, 1000, provider="unknown", model="x") == 0.0

    def test_legacy_per_1m_table_is_derived_from_pricing_table(self) -> None:
        assert TOKENS_COST_TABLE["openai"]["gpt-4o"] == {
            "input": 2.50,
            "output": 10.00,
        }


class TestCostEstimateMetric:
    """Tests for CostEstimateMetric."""

    def test_registered_in_metric_registry(self) -> None:
        assert "cost_estimate" in METRIC_REGISTRY
        assert get_metric("cost_estimate") is CostEstimateMetric

    def test_invalid_budget_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            CostEstimateMetric(max_cost_usd=0.0)

    def test_known_model_returns_dollar_cost_and_rates(self) -> None:
        metric = CostEstimateMetric(max_cost_usd=1.0)
        result = metric.evaluate(
            prompt_tokens=2000,
            completion_tokens=1000,
            provider="openai",
            model="gpt-4o",
        )
        # 2 * 0.0025 + 1 * 0.01 = 0.015
        assert result.metadata["estimated_cost_usd"] == pytest.approx(0.015)
        assert result.metadata["pricing_found"] is True
        assert result.metadata["prompt_per_1k_usd"] == pytest.approx(0.0025)
        assert result.metadata["completion_per_1k_usd"] == pytest.approx(0.01)
        assert result.score == pytest.approx(0.985)
        assert "$0.015000" in result.reason

    def test_unknown_model_marks_pricing_not_found(self) -> None:
        metric = CostEstimateMetric()
        result = metric.evaluate(
            prompt_tokens=100,
            completion_tokens=50,
            provider="unknown",
            model="mystery",
        )
        assert result.metadata["pricing_found"] is False
        assert result.metadata["estimated_cost_usd"] == 0.0
        assert result.score == 1.0


class _PricedStubLLM:
    name = "openai"
    model_name = "gpt-4o"

    async def generate_with_usage(self, prompt: str, **_: Any) -> LLMResponse:
        del prompt
        return LLMResponse(
            content="Paris",
            model=self.model_name,
            provider=self.name,
            usage=TokenUsage(
                prompt_tokens=1000, completion_tokens=500, total_tokens=1500
            ),
            latency_ms=12.0,
        )


class _StubRetriever:
    name = "mock"

    async def retrieve(self, query: str, **_: Any) -> list[Any]:
        del query
        return []


class TestEndToEndReportDollarCost:
    """Tests that Engine runs propagate dollar cost into all report formats."""

    @pytest.mark.asyncio
    async def test_engine_and_reports_surface_estimated_cost(self) -> None:
        config = Config(
            dataset=DatasetConfig(path="unused.json"),
            llm=LLMConfig(provider="openai", model="gpt-4o"),
            retriever=RetrieverConfig(provider="mock"),
            metrics=MetricsConfig(
                retrieval=[],
                generation=["exact_match"],
                performance=["latency"],
                cost=["token_count", "cost_estimate"],
            ),
        )
        dataset = [
            {
                "question": "Capital of France?",
                "ground_truth": "Paris",
                "context": "Paris is the capital of France.",
            },
            {
                "question": "Capital of France again?",
                "ground_truth": "Paris",
                "context": "Paris is the capital of France.",
            },
        ]

        engine = Engine(
            config,
            retriever=_StubRetriever(),
            llm=_PricedStubLLM(),
        )
        try:
            eval_report = await engine.run(dataset)
        finally:
            engine.shutdown()

        # 2 items * $0.0075/item = $0.0150
        assert eval_report.summary["total_tokens"] == 3000
        assert eval_report.summary["total_estimated_cost_usd"] == pytest.approx(0.015)

        parsed_json = json.loads(JSONReport().generate(eval_report))
        assert parsed_json["summary"]["total_estimated_cost_usd"] == pytest.approx(
            0.015
        )

        md = MarkdownReport().generate(eval_report)
        assert "Estimated Cost (USD)" in md
        assert "$0.0150" in md

        term = TerminalReport().generate(eval_report)
        assert "Estimated cost:" in term
        assert "$0.0150" in term

        html = HTMLReport().generate(eval_report)
        assert "Estimated Cost" in html
        assert "$0.0150" in html

    @pytest.mark.asyncio
    async def test_empty_dataset_reports_zero_estimated_cost(self) -> None:
        config = Config(
            dataset=DatasetConfig(path="unused.json"),
            llm=LLMConfig(provider="mock", model="mock"),
            retriever=RetrieverConfig(provider="mock"),
            metrics=MetricsConfig(retrieval=[], generation=[], performance=[], cost=[]),
        )
        engine = Engine(config, retriever=_StubRetriever(), llm=_PricedStubLLM())
        try:
            eval_report = await engine.run([])
        finally:
            engine.shutdown()
        assert eval_report.summary["total_estimated_cost_usd"] == 0.0
