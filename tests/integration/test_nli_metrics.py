"""Integration tests for NLI-based metrics.

Tests the full pipeline: ClaimExtractor -> EvidenceFinder -> Faithfulness/Relevancy.
Uses mocked NLI pipeline to avoid requiring actual model download.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


from openagent_eval.metrics.generation.faithfulness import Faithfulness
from openagent_eval.metrics.generation.relevancy import AnswerRelevancy
from openagent_eval.metrics.nli import (
    Claim,
    ClaimExtractor,
    EvidenceFinder,
    NLIJudge,
    NLIResult,
    NLILabel,
)
from openagent_eval.metrics.base import MetricResult


# ============================================================
# Mocked NLI Pipeline Fixtures
# ============================================================


def _make_nli_result(entailed: float, neutral: float = 0.0, contradiction: float = 0.0):
    """Helper to create NLI pipeline output."""
    return [[
        {"label": "entailment", "score": entailed},
        {"label": "neutral", "score": neutral},
        {"label": "contradiction", "score": contradiction},
    ]]


# ============================================================
# Faithfulness Integration Tests
# ============================================================


class TestFaithfulnessNLIIntegration:
    """Integration tests for Faithfulness metric with NLI fallback."""

    def test_faithfulness_empty_answer(self):
        metric = Faithfulness()
        result = metric.evaluate(answer="", contexts=["context"])
        assert result.score == 0.0
        assert "No answer" in result.reason

    def test_faithfulness_empty_contexts(self):
        metric = Faithfulness()
        result = metric.evaluate(answer="answer", contexts=[])
        assert result.score == 0.0
        assert "No contexts" in result.reason

    @patch("openagent_eval.metrics.generation.faithfulness.Faithfulness._evaluate_with_ragas")
    def test_faithfulness_fallback_to_simple(self, mock_ragas):
        """When Ragas and NLI unavailable, should use simple overlap."""
        mock_ragas.side_effect = ImportError("No ragas")

        metric = Faithfulness()
        # Mock NLI to also fail
        with patch(
            "openagent_eval.metrics.generation.faithfulness.Faithfulness._evaluate_with_nli",
            side_effect=ImportError("No nli"),
        ):
            result = metric.evaluate(
                answer="The sky is blue and clear today",
                contexts=["The sky is blue and the weather is clear"],
            )
            assert result.score > 0.0
            assert result.metadata["method"] == "simple_overlap"

    @patch("openagent_eval.metrics.generation.faithfulness.Faithfulness._evaluate_with_ragas")
    def test_faithfulness_with_mocked_nli(self, mock_ragas):
        """Test NLI fallback path when Ragas unavailable."""
        mock_ragas.side_effect = ImportError("No ragas")

        with patch(
            "openagent_eval.metrics.nli.NLIJudge"
        ) as MockJudge, patch(
            "openagent_eval.metrics.nli.ClaimExtractor"
        ) as MockExtractor, patch(
            "openagent_eval.metrics.nli.EvidenceFinder"
        ) as MockFinder:
            # Setup mocks
            mock_judge_instance = MagicMock()
            mock_judge_instance._model_name = "test-model"
            MockJudge.return_value = mock_judge_instance

            mock_extractor_instance = MagicMock()
            mock_extractor_instance.extract.return_value = [
                Claim(text="The sky is blue", index=0),
                Claim(text="It is clear", index=1),
            ]
            MockExtractor.return_value = mock_extractor_instance

            mock_finder_instance = MagicMock()
            mock_finder_instance.score_faithfulness.return_value = (
                0.75,
                [
                    MagicMock(nli_result=MagicMock(entailed_score=0.9)),
                    MagicMock(nli_result=MagicMock(entailed_score=0.6)),
                ],
            )
            MockFinder.return_value = mock_finder_instance

            metric = Faithfulness()
            result = metric.evaluate(
                answer="The sky is blue and clear.",
                contexts=["The sky is blue and the weather is clear."],
            )

            assert result.score == 0.75
            assert result.metadata["method"] == "nli"
            assert result.metadata["claims_total"] == 2
            assert result.metadata["claims_supported"] == 2


# ============================================================
# AnswerRelevancy Integration Tests
# ============================================================


class TestAnswerRelevancyNLIIntegration:
    """Integration tests for AnswerRelevancy metric with NLI fallback."""

    def test_relevancy_empty_question(self):
        metric = AnswerRelevancy()
        result = metric.evaluate(question="", answer="answer")
        assert result.score == 0.0
        assert "No question" in result.reason

    def test_relevancy_empty_answer(self):
        metric = AnswerRelevancy()
        result = metric.evaluate(question="question", answer="")
        assert result.score == 0.0
        assert "No answer" in result.reason

    @patch("openagent_eval.metrics.generation.relevancy.AnswerRelevancy._evaluate_with_ragas")
    def test_relevancy_fallback_to_simple(self, mock_ragas):
        """When Ragas and NLI unavailable, should use simple overlap."""
        mock_ragas.side_effect = ImportError("No ragas")

        metric = AnswerRelevancy()
        with patch(
            "openagent_eval.metrics.generation.relevancy.AnswerRelevancy._evaluate_with_nli",
            side_effect=ImportError("No nli"),
        ):
            result = metric.evaluate(
                question="What is Python?",
                answer="Python is a programming language.",
            )
            assert result.score > 0.0
            assert result.metadata["method"] == "word_overlap"

    @patch("openagent_eval.metrics.generation.relevancy.AnswerRelevancy._evaluate_with_ragas")
    def test_relevancy_with_mocked_nli(self, mock_ragas):
        """Test NLI fallback path when Ragas unavailable."""
        mock_ragas.side_effect = ImportError("No ragas")

        with patch(
            "openagent_eval.metrics.nli.NLIJudge"
        ) as MockJudge:
            mock_judge_instance = MagicMock()
            mock_judge_instance._model_name = "test-model"
            mock_judge_instance.evaluate.return_value = NLIResult(
                label=NLILabel.ENTAILMENT,
                score=0.9,
                entailed_score=0.88,
            )
            MockJudge.return_value = mock_judge_instance

            metric = AnswerRelevancy()
            result = metric.evaluate(
                question="What is Python?",
                answer="Python is a programming language created by Guido van Rossum.",
            )

            assert result.score == 0.88
            assert result.metadata["method"] == "nli"
            assert result.metadata["label"] == "entailment"


# ============================================================
# Full Pipeline Integration Tests
# ============================================================


class TestNLIPipelineIntegration:
    """End-to-end integration tests for the NLI scoring pipeline."""

    def test_claim_extractor_to_evidence_finder(self):
        """Test full pipeline: extract claims -> find evidence -> score."""
        # Mock NLI judge
        mock_judge = MagicMock(spec=NLIJudge)
        mock_judge.evaluate.side_effect = [
            # Claim 1 vs Context 1
            NLIResult(label=NLILabel.ENTAILMENT, score=0.95, entailed_score=0.95),
            # Claim 1 vs Context 2
            NLIResult(label=NLILabel.NEUTRAL, score=0.7, entailed_score=0.2),
            # Claim 2 vs Context 1
            NLIResult(label=NLILabel.NEUTRAL, score=0.6, entailed_score=0.3),
            # Claim 2 vs Context 2
            NLIResult(label=NLILabel.ENTAILMENT, score=0.88, entailed_score=0.88),
        ]

        extractor = ClaimExtractor()
        finder = EvidenceFinder(judge=mock_judge)

        # Extract claims
        claims = extractor.extract(
            "Python is open source. It was created in 1991."
        )
        assert len(claims) >= 2

        # Find evidence and score
        contexts = [
            "Python is an open source programming language.",
            "Python was first released in 1991 by Guido van Rossum.",
        ]

        score, matches = finder.score_faithfulness(claims, contexts, threshold=0.5)

        # At least some claims should be supported
        assert score > 0.0
        assert len(matches) >= 2

        # Each match should have evidence
        for match in matches:
            if match is not None:
                assert match.evidence
                assert match.nli_result

    def test_metric_result_format(self):
        """Ensure all NLI-based metrics return proper MetricResult."""
        metric = Faithfulness()
        result = metric.evaluate(answer="test", contexts=["test context"])
        assert isinstance(result, MetricResult)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.reason, str)
        assert isinstance(result.metadata, dict)

    def test_relevancy_metric_result_format(self):
        """Ensure relevancy metric returns proper MetricResult."""
        metric = AnswerRelevancy()
        result = metric.evaluate(question="test question", answer="test answer")
        assert isinstance(result, MetricResult)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.reason, str)
        assert isinstance(result.metadata, dict)
