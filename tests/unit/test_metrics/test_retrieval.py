"""Tests for retrieval metrics."""

from __future__ import annotations

import pytest

from openagent_eval.metrics.retrieval import (
    ContextPrecision,
    ContextRecall,
    HitRate,
    MRR,
    NDCG,
    PrecisionAtK,
    RecallAtK,
)


class TestContextPrecision:
    """Tests for ContextPrecision metric."""

    def setup_method(self):
        self.metric = ContextPrecision()

    def test_perfect_precision(self):
        """All retrieved contexts are relevant."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx2"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 1.0

    def test_zero_precision(self):
        """No retrieved contexts are relevant."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx_b"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 0.0

    def test_partial_precision(self):
        """Some retrieved contexts are relevant."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx_a"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 0.5

    def test_no_retrieved_contexts(self):
        """No contexts retrieved returns 0."""
        result = self.metric.evaluate(
            retrieved_contexts=[],
            ground_truth_contexts=["ctx1"],
        )
        assert result.score == 0.0

    def test_no_ground_truth(self):
        """No ground truth returns 0."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1"],
            ground_truth_contexts=[],
        )
        assert result.score == 0.0


class TestContextRecall:
    """Tests for ContextRecall metric."""

    def setup_method(self):
        self.metric = ContextRecall()

    def test_perfect_recall(self):
        """All ground truth contexts retrieved."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx2", "ctx3"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 1.0

    def test_zero_recall(self):
        """No ground truth contexts retrieved."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx_b"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 0.0

    def test_partial_recall(self):
        """Some ground truth contexts retrieved."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx_a"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 0.5

    def test_no_ground_truth(self):
        """No ground truth returns 0."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1"],
            ground_truth_contexts=[],
        )
        assert result.score == 0.0

    def test_no_retrieved(self):
        """No retrieved contexts returns 0."""
        result = self.metric.evaluate(
            retrieved_contexts=[],
            ground_truth_contexts=["ctx1"],
        )
        assert result.score == 0.0


class TestRecallAtK:
    """Tests for RecallAtK metric."""

    def setup_method(self):
        self.metric = RecallAtK()

    def test_hit_in_top_k(self):
        """Relevant context found in top-K."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx1", "ctx_b"],
            ground_truth_contexts=["ctx1"],
            k=2,
        )
        assert result.score == 1.0
        assert result.metadata["found"] is True

    def test_miss_in_top_k(self):
        """No relevant context in top-K."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx_b", "ctx1"],
            ground_truth_contexts=["ctx1"],
            k=2,
        )
        assert result.score == 0.0
        assert result.metadata["found"] is False

    def test_default_k(self):
        """Default K uses all retrieved contexts."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1"],
            ground_truth_contexts=["ctx1"],
        )
        assert result.score == 1.0


class TestPrecisionAtK:
    """Tests for PrecisionAtK metric."""

    def setup_method(self):
        self.metric = PrecisionAtK()

    def test_perfect_precision_at_k(self):
        """All top-K contexts are relevant."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx2"],
            ground_truth_contexts=["ctx1", "ctx2"],
            k=2,
        )
        assert result.score == 1.0

    def test_partial_precision_at_k(self):
        """Some top-K contexts are relevant."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx_a"],
            ground_truth_contexts=["ctx1", "ctx2"],
            k=2,
        )
        assert result.score == 0.5

    def test_k_zero(self):
        """K=0 returns 0."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1"],
            ground_truth_contexts=["ctx1"],
            k=0,
        )
        assert result.score == 0.0


class TestHitRate:
    """Tests for HitRate metric."""

    def setup_method(self):
        self.metric = HitRate()

    def test_hit(self):
        """At least one relevant context found."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx1"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 1.0
        assert result.metadata["hit"] is True

    def test_miss(self):
        """No relevant context found."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx_b"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 0.0
        assert result.metadata["hit"] is False


class TestMRR:
    """Tests for MRR metric."""

    def setup_method(self):
        self.metric = MRR()

    def test_first_rank(self):
        """Relevant context at rank 1."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx_a"],
            ground_truth_contexts=["ctx1"],
        )
        assert result.score == 1.0

    def test_second_rank(self):
        """Relevant context at rank 2."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx1"],
            ground_truth_contexts=["ctx1"],
        )
        assert result.score == 0.5

    def test_third_rank(self):
        """Relevant context at rank 3."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx_b", "ctx1"],
            ground_truth_contexts=["ctx1"],
        )
        assert pytest.approx(result.score) == 1.0 / 3.0

    def test_no_relevant(self):
        """No relevant context found."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx_b"],
            ground_truth_contexts=["ctx1"],
        )
        assert result.score == 0.0


class TestNDCG:
    """Tests for NDCG metric."""

    def setup_method(self):
        self.metric = NDCG()

    def test_perfect_ranking(self):
        """All relevant contexts at top positions."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx2"],
            ground_truth_contexts=["ctx1", "ctx2"],
        )
        assert result.score == 1.0

    def test_imperfect_ranking(self):
        """Relevant context not at top position with multiple relevant docs."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx1", "ctx2"],
            ground_truth_contexts=["ctx1", "ctx2"],
            k=3,
        )
        # 2 relevant in top-3 but ctx_a (irrelevant) is at position 1
        # Ideal would have ctx1, ctx2 at positions 1,2
        assert 0.0 < result.score < 1.0

    def test_no_relevant(self):
        """No relevant contexts."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx_b"],
            ground_truth_contexts=["ctx1"],
        )
        assert result.score == 0.0
