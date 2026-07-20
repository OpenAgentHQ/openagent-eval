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

    # --- L19 regression: F1 uses Counter (multiset) not set ---
    def test_repeated_words_counted(self):
        """L19: Repeated words are counted, not deduplicated."""
        result = self.metric.evaluate(
            answer="cat cat cat",
            ground_truth="cat cat",
        )
        # With Counter: overlap=2, answer_len=3, gt_len=2
        # precision=2/3, recall=2/2=1.0, f1=2*(2/3*1)/(2/3+1)=0.8
        # With set: overlap=1, answer_len=1, gt_len=1, f1=1.0 (wrong)
        assert result.score == pytest.approx(0.8)


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
        import sys
        from unittest.mock import MagicMock, patch
        import numpy as np

        if hasattr(self.metric, "_cached_model"):
            delattr(self.metric, "_cached_model")

        mock_st = MagicMock()
        mock_st.return_value.encode.return_value = np.array([[1.0, 0.0], [1.0, 0.0]])
        mock_sklearn = MagicMock()
        mock_sklearn.cosine_similarity.return_value = np.array([[0.8]])

        with patch.dict(sys.modules, {
            "sentence_transformers": mock_st,
            "sklearn": MagicMock(metrics=MagicMock(pairwise=mock_sklearn)),
            "sklearn.metrics": MagicMock(pairwise=mock_sklearn),
            "sklearn.metrics.pairwise": mock_sklearn,
        }):
            result = self.metric.evaluate(
                answer="The car is red",
                ground_truth="The automobile is red",
            )
        assert result.score > 0.7

    def test_different_meaning(self):
        """Different meaning returns lower score."""
        import sys
        from unittest.mock import MagicMock, patch
        import numpy as np

        if hasattr(self.metric, "_cached_model"):
            delattr(self.metric, "_cached_model")

        mock_st = MagicMock()
        mock_st.return_value.encode.return_value = np.array([[1.0, 0.0], [0.0, 1.0]])
        mock_sklearn = MagicMock()
        mock_sklearn.cosine_similarity.return_value = np.array([[0.0]])

        with patch.dict(sys.modules, {
            "sentence_transformers": mock_st,
            "sklearn": MagicMock(metrics=MagicMock(pairwise=mock_sklearn)),
            "sklearn.metrics": MagicMock(pairwise=mock_sklearn),
            "sklearn.metrics.pairwise": mock_sklearn,
        }):
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


# ------------------------------------------------------------------ #
# L22 regression: cosine clamp/rescale for SemanticSimilarity         #
# ------------------------------------------------------------------ #
class TestSimilarityCosineClamp:
    """L22: SemanticSimilarity must clamp/rescale cosine into [0, 1]."""

    def test_negative_cosine_returns_non_negative(self):
        """L22: Even with negative cosine similarity, score must be >= 0."""
        import sys
        from unittest.mock import MagicMock, patch
        import numpy as np

        metric = SemanticSimilarity()
        # Clear any cached model so the lazy import path is taken
        if hasattr(metric, "_cached_model"):
            delattr(metric, "_cached_model")

        # Mock the SentenceTransformer so it returns controlled embeddings
        mock_st = MagicMock()
        mock_st.return_value.encode.return_value = np.array([[1.0, 0.0], [-1.0, 0.0]])
        # Mock cosine_similarity to return -1.0
        mock_sklearn = MagicMock()
        mock_sklearn.cosine_similarity.return_value = np.array([[-1.0]])

        with patch.dict(sys.modules, {
            "sentence_transformers": mock_st,
            "sklearn": MagicMock(metrics=MagicMock(pairwise=mock_sklearn)),
            "sklearn.metrics": MagicMock(pairwise=mock_sklearn),
            "sklearn.metrics.pairwise": mock_sklearn,
        }):
            result = metric.evaluate(answer="a", ground_truth="b")

        assert result.score >= 0.0
        assert result.score <= 1.0

    def test_zero_cosine_returns_half(self):
        """L22: Cosine of 0.0 maps to 0.5 after rescaling."""
        import sys
        from unittest.mock import MagicMock, patch
        import numpy as np

        metric = SemanticSimilarity()
        if hasattr(metric, "_cached_model"):
            delattr(metric, "_cached_model")

        mock_st = MagicMock()
        mock_st.return_value.encode.return_value = np.array([[1.0, 0.0], [0.0, 1.0]])
        mock_sklearn = MagicMock()
        mock_sklearn.cosine_similarity.return_value = np.array([[0.0]])

        with patch.dict(sys.modules, {
            "sentence_transformers": mock_st,
            "sklearn": MagicMock(metrics=MagicMock(pairwise=mock_sklearn)),
            "sklearn.metrics": MagicMock(pairwise=mock_sklearn),
            "sklearn.metrics.pairwise": mock_sklearn,
        }):
            result = metric.evaluate(answer="a", ground_truth="b")

        assert result.score == pytest.approx(0.5)


class TestBERTScoreCosineClamp:
    """L22: BERTScore must clamp F1 into [0, 1]."""

    def test_negative_f1_clamped_to_zero(self):
        """L22: Even if BERTScore returns negative F1, score must be >= 0."""
        from unittest.mock import patch, MagicMock

        metric = BERTScore()
        mock_precision = MagicMock()
        mock_precision.item.return_value = -0.1
        mock_recall = MagicMock()
        mock_recall.item.return_value = -0.2
        mock_f1 = MagicMock()
        mock_f1.item.return_value = -0.15

        # Mock the bert_score module so `from bert_score import score` works.
        mock_bert_score_module = MagicMock()
        mock_bert_score_module.score.return_value = (
            mock_precision,
            mock_recall,
            mock_f1,
        )
        with patch.dict("sys.modules", {"bert_score": mock_bert_score_module}):
            result = metric.evaluate(answer="a", ground_truth="b")
        assert result.score >= 0.0
        assert result.score <= 1.0
