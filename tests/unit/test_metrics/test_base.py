"""Tests for BaseMetric interface and MetricResult."""

from __future__ import annotations

import pytest

from openagent_eval.metrics.base import BaseMetric, MetricResult


class TestMetricResult:
    """Tests for MetricResult dataclass."""

    def test_create_with_defaults(self):
        """MetricResult creates with score only."""
        result = MetricResult(score=0.5)
        assert result.score == 0.5
        assert result.reason == ""
        assert result.metadata == {}

    def test_create_with_all_fields(self):
        """MetricResult creates with all fields."""
        result = MetricResult(
            score=0.8,
            reason="Good score",
            metadata={"key": "value"},
        )
        assert result.score == 0.8
        assert result.reason == "Good score"
        assert result.metadata == {"key": "value"}

    def test_score_boundary_zero(self):
        """MetricResult accepts score of 0.0."""
        result = MetricResult(score=0.0)
        assert result.score == 0.0

    def test_score_boundary_one(self):
        """MetricResult accepts score of 1.0."""
        result = MetricResult(score=1.0)
        assert result.score == 1.0

    def test_score_below_zero_raises(self):
        """MetricResult rejects score below 0.0."""
        with pytest.raises(ValueError, match="Score must be between"):
            MetricResult(score=-0.1)

    def test_score_above_one_raises(self):
        """MetricResult rejects score above 1.0."""
        with pytest.raises(ValueError, match="Score must be between"):
            MetricResult(score=1.1)

    def test_frozen_dataclass(self):
        """MetricResult is immutable."""
        result = MetricResult(score=0.5)
        with pytest.raises(AttributeError):
            result.score = 0.8  # type: ignore[misc]


class TestBaseMetric:
    """Tests for BaseMetric ABC."""

    def test_cannot_instantiate_directly(self):
        """BaseMetric cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseMetric()  # type: ignore[abstract]

    def test_subclass_must_implement_evaluate(self):
        """Subclass without evaluate raises TypeError."""

        class IncompleteMetric(BaseMetric):
            name = "incomplete"
            description = "Missing evaluate"

        with pytest.raises(TypeError):
            IncompleteMetric()  # type: ignore[abstract]

    def test_subclass_with_evaluate_works(self):
        """Subclass with evaluate can be instantiated."""

        class ValidMetric(BaseMetric):
            name = "valid"
            description = "A valid metric"

            def evaluate(self, **kwargs):
                return MetricResult(score=0.5)

        metric = ValidMetric()
        assert metric.name == "valid"
        result = metric.evaluate()
        assert result.score == 0.5

    def test_validate_inputs_default(self):
        """validate_inputs does nothing by default."""

        class SimpleMetric(BaseMetric):
            name = "simple"
            description = "Simple metric"

            def evaluate(self, **kwargs):
                return MetricResult(score=1.0)

        metric = SimpleMetric()
        # Should not raise
        metric.validate_inputs(anything="value")
