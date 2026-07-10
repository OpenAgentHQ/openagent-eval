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
        assert result.metadata["relevant_in_top_k"] == 1
        assert result.metadata["relevant_total"] == 1

    def test_miss_in_top_k(self):
        """No relevant context in top-K."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx_a", "ctx_b", "ctx1"],
            ground_truth_contexts=["ctx1"],
            k=2,
        )
        assert result.score == 0.0
        assert result.metadata["relevant_in_top_k"] == 0
        assert result.metadata["relevant_total"] == 1

    def test_partial_recall(self):
        """Recall reflects the fraction of relevant contexts recovered."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx_x"],
            ground_truth_contexts=["ctx1", "ctx2", "ctx3"],
            k=2,
        )
        # 1 of 3 relevant contexts in top-2 -> 1/3
        assert result.score == pytest.approx(1 / 3)
        assert result.metadata["relevant_in_top_k"] == 1
        assert result.metadata["relevant_total"] == 3

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

    def test_ndcg_penalizes_missed_relevant_docs(self):
        """H7: when retrieval misses many relevant docs, NDCG must be < 1.

        k=5, only 1 of 10 relevant docs retrieved. The ideal ranking places 5
        relevant docs in the top-5, so NDCG should be well below 1.0 (the old
        code built the ideal from the retrieved set and reported 1.0).
        """
        ground_truth = [f"r{i}" for i in range(1, 11)]
        result = self.metric.evaluate(
            retrieved_contexts=["r1", "x", "x", "x", "x"],
            ground_truth_contexts=ground_truth,
            k=5,
        )
        assert result.score < 1.0
        assert result.score > 0.0


# ------------------------------------------------------------------ #
# L20 regression: RecallAtK uses distinct ground truth count           #
# ------------------------------------------------------------------ #
class TestRecallAtKRegression:
    """Regression tests for RecallAtK metric."""

    def setup_method(self):
        self.metric = RecallAtK()

    def test_duplicate_ground_truth_uses_distinct_count(self):
        """L20: Duplicate items in ground_truth_contexts should be counted
        once each for the denominator."""
        result = self.metric.evaluate(
            retrieved_contexts=["ctx1", "ctx_x"],
            ground_truth_contexts=["ctx1", "ctx1"],  # duplicate
            k=2,
        )
        # 1 distinct relevant in top-2, 1 distinct relevant total -> 1.0
        # (old code: denominator was len(set(retrieved) & set(gt)) which
        # would be 1/1=1.0 anyway, but the real bug was when gt had dupes
        # and retrieved missed one — denominator was len(retrieved) not
        # len(set(gt)).)
        assert result.score == 1.0
        assert result.metadata["relevant_total"] == 1


# ------------------------------------------------------------------ #
# L21 regression: retrieval metrics normalise whitespace               #
# ------------------------------------------------------------------ #
class TestRetrievalNormalization:
    """L21: Whitespace-normalised matching for retrieval metrics."""

    def test_context_precision_whitespace_insensitive(self):
        """L21: ContextPrecision matches on normalised content."""
        metric = ContextPrecision()
        result = metric.evaluate(
            retrieved_contexts=["  hello   world  "],
            ground_truth_contexts=["hello world"],
        )
        assert result.score == 1.0

    def test_context_recall_whitespace_insensitive(self):
        """L21: ContextRecall matches on normalised content."""
        metric = ContextRecall()
        result = metric.evaluate(
            retrieved_contexts=["hello   world"],
            ground_truth_contexts=["  hello world  "],
        )
        assert result.score == 1.0

    def test_hit_rate_whitespace_insensitive(self):
        """L21: HitRate matches on normalised content."""
        metric = HitRate()
        result = metric.evaluate(
            retrieved_contexts=["doc_a", "  hello  world  "],
            ground_truth_contexts=["hello world"],
        )
        assert result.score == 1.0

    def test_mrr_whitespace_insensitive(self):
        """L21: MRR matches on normalised content."""
        metric = MRR()
        result = metric.evaluate(
            retrieved_contexts=["irrelevant", " hello  world "],
            ground_truth_contexts=["hello world"],
        )
        assert result.score == 0.5
