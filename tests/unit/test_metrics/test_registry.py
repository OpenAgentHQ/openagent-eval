"""Tests for metrics package exports and registry."""

from __future__ import annotations

import pytest

from openagent_eval.metrics import (
    METRIC_REGISTRY,
    BaseMetric,
    get_metric,
    list_metrics,
)


class TestMetricRegistry:
    """Tests for metric registry."""

    def test_registry_has_all_metrics(self):
        """Registry contains all expected metrics."""
        expected = [
            "context_precision",
            "context_recall",
            "recall_at_k",
            "precision_at_k",
            "hit_rate",
            "mrr",
            "ndcg",
            "faithfulness",
            "answer_relevancy",
            "hallucination",
            "semantic_similarity",
            "exact_match",
            "f1_score",
            "bleu",
            "rouge",
            "bertscore",
            "latency",
            "token_count",
        ]
        for name in expected:
            assert name in METRIC_REGISTRY

    def test_registry_values_are_metric_classes(self):
        """All registry values are BaseMetric subclasses."""
        for name, metric_class in METRIC_REGISTRY.items():
            assert issubclass(metric_class, BaseMetric), (
                f"{name} is not a BaseMetric subclass"
            )

    def test_list_metrics_returns_sorted(self):
        """list_metrics returns sorted list."""
        metrics = list_metrics()
        assert metrics == sorted(metrics)
        assert len(metrics) > 0

    def test_get_metric_existing(self):
        """get_metric returns correct class for existing metric."""
        metric_class = get_metric("exact_match")
        assert metric_class is not None
        assert issubclass(metric_class, BaseMetric)

    def test_get_metric_nonexistent(self):
        """get_metric raises KeyError for nonexistent metric."""
        with pytest.raises(KeyError, match="not found"):
            get_metric("nonexistent_metric")

    def test_all_metrics_can_instantiate(self):
        """All metrics in registry can be instantiated."""
        for name, metric_class in METRIC_REGISTRY.items():
            metric = metric_class()
            assert metric.name == name or hasattr(metric, "name")
