"""Tests for generation metrics."""

from __future__ import annotations

import os

import pytest

from openagent_eval.metrics.generation import (
    AnswerRelevancy,
    BERTScore,
    BLEU,
    ExactMatch,
    F1Score,
    Faithfulness,
    HallucinationDetection,
    ROUGE,
    SemanticSimilarity,
)


class TestExactMatch:
    """Tests for ExactMatch metric."""

    def setup_method(self):
        self.metric = ExactMatch()

    def test_exact_match(self):
        """Answer matches ground truth exactly."""
        result = self.metric.evaluate(
            answer="Python is a language",
            ground_truth="Python is a language",
        )
        assert result.score == 1.0

    def test_case_insensitive(self):
        """Match is case-insensitive."""
        result = self.metric.evaluate(
            answer="python is a language",
            ground_truth="Python is a Language",
        )
        assert result.score == 1.0

    def test_no_match(self):
        """Answer does not match ground truth."""
        result = self.metric.evaluate(
            answer="Python is great",
            ground_truth="Python is a language",
        )
        assert result.score == 0.0

    def test_whitespace_trimmed(self):
        """Whitespace is trimmed."""
        result = self.metric.evaluate(
            answer="  Python is a language  ",
            ground_truth="Python is a language",
        )
        assert result.score == 1.0


class TestF1Score:
    """Tests for F1Score metric."""

    def setup_method(self):
        self.metric = F1Score()

    def test_perfect_f1(self):
        """Perfect word overlap."""
        result = self.metric.evaluate(
            answer="Python is a language",
            ground_truth="Python is a language",
        )
        assert result.score == 1.0

    def test_partial_overlap(self):
        """Some words overlap."""
        result = self.metric.evaluate(
            answer="Python is great",
            ground_truth="Python is a language",
        )
        assert 0.0 < result.score < 1.0

    def test_no_overlap(self):
        """No word overlap."""
        result = self.metric.evaluate(
            answer="dogs run fast",
            ground_truth="cats sleep well",
        )
        assert result.score == 0.0

    def test_empty_both(self):
        """Both empty returns 1.0."""
        result = self.metric.evaluate(answer="", ground_truth="")
        assert result.score == 1.0


class TestBLEU:
    """Tests for BLEU metric."""

    def setup_method(self):
        self.metric = BLEU()

    def test_identical(self):
        """Identical text returns high score."""
        result = self.metric.evaluate(
            answer="The cat sat on the mat",
            ground_truth="The cat sat on the mat",
        )
        assert result.score > 0.9

    def test_different(self):
        """Different text returns low score."""
        result = self.metric.evaluate(
            answer="Dogs run fast",
            ground_truth="The cat sat on the mat",
        )
        assert result.score < 0.5

    def test_empty_answer(self):
        """Empty answer returns 0."""
        result = self.metric.evaluate(answer="", ground_truth="Some text")
        assert result.score == 0.0


class TestROUGE:
    """Tests for ROUGE metric."""

    def setup_method(self):
        self.metric = ROUGE()

    def test_identical(self):
        """Identical text returns high score."""
        result = self.metric.evaluate(
            answer="The cat sat on the mat",
            ground_truth="The cat sat on the mat",
        )
        assert result.score > 0.9

    def test_partial_overlap(self):
        """Partial overlap returns moderate score."""
        result = self.metric.evaluate(
            answer="The cat is on the mat",
            ground_truth="The cat sat on the mat",
        )
        assert 0.5 < result.score < 1.0

    def test_no_overlap(self):
        """No overlap returns low score."""
        result = self.metric.evaluate(
            answer="Dogs run fast",
            ground_truth="The cat sat on the mat",
        )
        assert result.score < 0.5


class TestSemanticSimilarity:
    """Tests for SemanticSimilarity metric."""

    def setup_method(self):
        self.metric = SemanticSimilarity()

    def test_identical_meaning(self):
        """Same meaning returns high score."""
        result = self.metric.evaluate(
            answer="The car is red",
            ground_truth="The automobile is red",
        )
        assert result.score > 0.7

    def test_different_meaning(self):
        """Different meaning returns lower score."""
        result = self.metric.evaluate(
            answer="The sky is blue",
            ground_truth="Python is a programming language",
        )
        assert result.score < 0.7

    def test_empty_answer(self):
        """Empty answer returns 0."""
        result = self.metric.evaluate(answer="", ground_truth="Some text")
        assert result.score == 0.0


class TestFaithfulness:
    """Tests for Faithfulness metric."""

    def setup_method(self):
        self.metric = Faithfulness()

    def test_supported_answer(self):
        """Answer supported by context."""
        result = self.metric.evaluate(
            answer="Python is a programming language",
            contexts=["Python is a high-level programming language"],
        )
        assert result.score > 0.5

    def test_unsupported_answer(self):
        """Answer not in context."""
        result = self.metric.evaluate(
            answer="Java is compiled",
            contexts=["Python is a programming language"],
        )
        assert result.score < 0.5

    def test_no_contexts(self):
        """No contexts returns 0."""
        result = self.metric.evaluate(
            answer="Some answer",
            contexts=[],
        )
        assert result.score == 0.0


class TestAnswerRelevancy:
    """Tests for AnswerRelevancy metric."""

    def setup_method(self):
        self.metric = AnswerRelevancy()

    def test_relevant_answer(self):
        """Answer addresses the question."""
        result = self.metric.evaluate(
            question="What is Python?",
            answer="Python is a programming language",
        )
        # "Python" appears in answer, so score > 0
        assert result.score > 0.0

    def test_irrelevant_answer(self):
        """Answer does not address the question."""
        result = self.metric.evaluate(
            question="What is Python?",
            answer="The weather is nice today",
        )
        # Only "is" overlaps (stop word removed), so low score
        assert result.score < 0.5

    def test_empty_question(self):
        """Empty question returns 0."""
        result = self.metric.evaluate(
            question="",
            answer="Some answer",
        )
        assert result.score == 0.0


class TestHallucinationDetection:
    """Tests for HallucinationDetection metric."""

    def setup_method(self):
        self.metric = HallucinationDetection()

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ,
        reason="HallucinationDetection uses DeepEval (OpenAI) and needs OPENAI_API_KEY",
    )
    def test_grounded_answer(self):
        """Answer grounded in context."""
        result = self.metric.evaluate(
            answer="Python is a language",
            contexts=["Python is a programming language"],
        )
        assert result.score < 0.5

    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ,
        reason="HallucinationDetection uses DeepEval (OpenAI) and needs OPENAI_API_KEY",
    )
    def test_hallucinated_answer(self):
        """Answer not in context."""
        result = self.metric.evaluate(
            answer="Python was created in 1800",
            contexts=["Python is a programming language"],
        )
        assert result.score > 0.5

    def test_no_contexts(self):
        """No contexts means cannot verify."""
        result = self.metric.evaluate(
            answer="Some answer",
            contexts=[],
        )
        assert result.score == 1.0


class TestBERTScore:
    """Tests for BERTScore metric."""

    def setup_method(self):
        self.metric = BERTScore()

    def test_identical(self):
        """Identical text returns high score."""
        result = self.metric.evaluate(
            answer="The cat sat on the mat",
            ground_truth="The cat sat on the mat",
        )
        assert result.score > 0.9

    def test_similar_meaning(self):
        """Similar meaning returns moderate-high score."""
        result = self.metric.evaluate(
            answer="The feline sat on the mat",
            ground_truth="The cat sat on the mat",
        )
        assert result.score > 0.5

    def test_different(self):
        """Different content returns lower score."""
        result = self.metric.evaluate(
            answer="Python is a language",
            ground_truth="The cat sat on the mat",
        )
        assert result.score < 0.6
