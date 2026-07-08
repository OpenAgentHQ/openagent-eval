"""Tests for performance and cost metrics."""

from __future__ import annotations

import pytest

from openagent_eval.metrics.cost import TokenCountMetric
from openagent_eval.metrics.performance import LatencyMetric


class TestLatencyMetric:
    """Tests for LatencyMetric."""

    def setup_method(self):
        self.metric = LatencyMetric(threshold_ms=1000.0)

    def test_zero_latency(self):
        """Zero latency gives perfect score."""
        result = self.metric.evaluate(latency_ms=0.0, stage="llm")
        assert result.score == 1.0

    def test_at_threshold(self):
        """Latency at threshold gives 0.5."""
        result = self.metric.evaluate(latency_ms=1000.0, stage="llm")
        assert result.score == 0.5

    def test_double_threshold(self):
        """Latency at 2x threshold gives 0."""
        result = self.metric.evaluate(latency_ms=2000.0, stage="llm")
        assert result.score == 0.0

    def test_above_double_threshold(self):
        """Latency above 2x threshold gives 0."""
        result = self.metric.evaluate(latency_ms=5000.0, stage="llm")
        assert result.score == 0.0

    def test_half_threshold(self):
        """Latency at half threshold gives 0.75."""
        result = self.metric.evaluate(latency_ms=500.0, stage="llm")
        assert result.score == 0.75

    def test_custom_threshold(self):
        """Custom threshold works."""
        metric = LatencyMetric(threshold_ms=500.0)
        result = metric.evaluate(latency_ms=500.0, stage="retrieval")
        assert result.score == 0.5

    def test_negative_latency(self):
        """Negative latency returns 0."""
        result = self.metric.evaluate(latency_ms=-100.0, stage="llm")
        assert result.score == 0.0

    def test_metadata(self):
        """Result contains proper metadata."""
        result = self.metric.evaluate(latency_ms=100.0, stage="embedding")
        assert result.metadata["stage"] == "embedding"
        assert result.metadata["latency_ms"] == 100.0


class TestTokenCountMetric:
    """Tests for TokenCountMetric."""

    def setup_method(self):
        self.metric = TokenCountMetric()

    def test_low_token_usage(self):
        """Low token count gives high score."""
        result = self.metric.evaluate(
            prompt_tokens=100,
            completion_tokens=50,
            provider="openai",
            model="gpt-4o",
        )
        assert result.score > 0.9
        assert result.metadata["total_tokens"] == 150

    def test_high_token_usage(self):
        """High token count gives lower score."""
        result = self.metric.evaluate(
            prompt_tokens=5000,
            completion_tokens=5000,
            provider="openai",
            model="gpt-4o",
        )
        assert result.score < 0.6

    def test_cost_estimation_openai(self):
        """Cost estimation works for OpenAI."""
        result = self.metric.evaluate(
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
            provider="openai",
            model="gpt-4o",
        )
        # 1M input @ $2.50 + 1M output @ $10.00 = $12.50
        assert result.metadata["estimated_cost_usd"] == pytest.approx(12.50)

    def test_cost_estimation_anthropic(self):
        """Cost estimation works for Anthropic."""
        result = self.metric.evaluate(
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
            provider="anthropic",
            model="claude-3-opus",
        )
        # 1M input @ $15.00 + 1M output @ $75.00 = $90.00
        assert result.metadata["estimated_cost_usd"] == pytest.approx(90.00)

    def test_unknown_provider(self):
        """Unknown provider gives 0 cost."""
        result = self.metric.evaluate(
            prompt_tokens=1000,
            completion_tokens=1000,
            provider="unknown",
            model="unknown",
        )
        assert result.metadata["estimated_cost_usd"] == 0.0

    def test_zero_tokens(self):
        """Zero tokens gives high score."""
        result = self.metric.evaluate(
            prompt_tokens=0,
            completion_tokens=0,
        )
        assert result.score == 1.0
        assert result.metadata["total_tokens"] == 0

    def test_metadata_fields(self):
        """Result contains all metadata fields."""
        result = self.metric.evaluate(
            prompt_tokens=100,
            completion_tokens=50,
            provider="openai",
            model="gpt-4o",
        )
        assert result.metadata["prompt_tokens"] == 100
        assert result.metadata["completion_tokens"] == 50
        assert result.metadata["provider"] == "openai"
        assert result.metadata["model"] == "gpt-4o"
