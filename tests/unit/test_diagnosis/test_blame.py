"""Tests for blame attribution."""

from __future__ import annotations

from openagent_eval.diagnosis.blame import (
    BlameAttribution,
    LOW_CONTEXT_PRECISION,
    LOW_CONTEXT_RECALL,
    LOW_FAITHFULNESS,
    LOW_RELEVANCY,
)
from openagent_eval.diagnosis.models import (
    BlameTarget,
    ComponentScores,
    FailureMode,
)


class TestBlameAttribution:
    """Tests for BlameAttribution."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.blamer = BlameAttribution()

    # ------------------------------------------------------------------
    # Healthy cases
    # ------------------------------------------------------------------

    def test_healthy_item_returns_none(self) -> None:
        """An item with good scores should return NONE blame (no failures)."""
        scores = ComponentScores(
            question="What is Python?",
            retrieval_scores={"context_precision": 0.9, "context_recall": 0.85},
            generation_scores={"faithfulness": 0.92, "answer_relevancy": 0.88},
            context_count=3,
            context_lengths=[200, 300, 250],
            answer_length=500,
        )
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.NONE
        assert result.confidence == 1.0
        assert len(result.failure_modes) == 0

    def test_empty_scores_returns_empty_retrieval(self) -> None:
        """An item with no metric scores and no contexts should blame retrieval."""
        scores = ComponentScores(question="Test", context_count=0)
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.RETRIEVAL

    # ------------------------------------------------------------------
    # Retrieval failures
    # ------------------------------------------------------------------

    def test_empty_retrieval(self) -> None:
        """Zero contexts should blame retrieval with high confidence."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={},
            generation_scores={},
            context_count=0,
        )
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.RETRIEVAL
        assert result.confidence >= 0.9
        assert any(
            f.mode == FailureMode.EMPTY_RETRIEVAL for f in result.failure_modes
        )

    def test_low_context_precision(self) -> None:
        """Low context precision should blame retrieval."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={"context_precision": LOW_CONTEXT_PRECISION - 0.1},
            generation_scores={"faithfulness": 0.9},
            context_count=3,
            context_lengths=[100, 100, 100],
            answer_length=200,
        )
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.RETRIEVAL
        assert any(
            f.mode == FailureMode.LOW_CONTEXT_RELEVANCE for f in result.failure_modes
        )

    def test_low_context_recall(self) -> None:
        """Low context recall should blame retrieval for missing context."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={"context_recall": LOW_CONTEXT_RECALL - 0.1},
            generation_scores={"faithfulness": 0.9},
            context_count=2,
            context_lengths=[100, 100],
            answer_length=200,
        )
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.RETRIEVAL
        assert any(
            f.mode == FailureMode.MISSING_CONTEXT for f in result.failure_modes
        )

    # ------------------------------------------------------------------
    # Generation failures
    # ------------------------------------------------------------------

    def test_low_faithfulness(self) -> None:
        """Low faithfulness should blame generation for hallucination."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={"context_precision": 0.8},
            generation_scores={"faithfulness": LOW_FAITHFULNESS - 0.1},
            context_count=3,
            context_lengths=[200, 200, 200],
            answer_length=500,
        )
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.GENERATION
        assert any(
            f.mode == FailureMode.HALLUCINATION for f in result.failure_modes
        )

    def test_low_relevancy(self) -> None:
        """Low relevancy should blame generation for off-topic answer."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={"context_precision": 0.8},
            generation_scores={"answer_relevancy": LOW_RELEVANCY - 0.1},
            context_count=3,
            context_lengths=[200, 200, 200],
            answer_length=500,
        )
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.GENERATION
        assert any(
            f.mode == FailureMode.OFF_TOPIC_ANSWER for f in result.failure_modes
        )

    def test_empty_answer_blames_generation(self) -> None:
        """Empty answer with non-empty contexts should blame generation."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={"context_precision": 0.8},
            generation_scores={},
            context_count=3,
            context_lengths=[200, 200, 200],
            answer_length=5,  # Too short
        )
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.GENERATION

    # ------------------------------------------------------------------
    # Chunking failures
    # ------------------------------------------------------------------

    def test_single_context_with_decent_precision(self) -> None:
        """Single context with good precision may indicate chunking issue."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={"context_precision": 0.8},
            generation_scores={"faithfulness": 0.9},
            context_count=1,
            context_lengths=[500],
            answer_length=300,
        )
        result = self.blamer.analyze(scores)
        # May blame chunking or none depending on thresholds
        assert result.target in (BlameTarget.CHUNKING, BlameTarget.NONE)

    def test_uneven_context_lengths(self) -> None:
        """Highly uneven context lengths should detect chunking issue."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={"context_precision": 0.5},
            generation_scores={"faithfulness": 0.9},
            context_count=3,
            context_lengths=[50, 100, 2000],  # Highly uneven
            answer_length=300,
        )
        result = self.blamer.analyze(scores)
        # Should detect chunking split issue
        chunking_failures = [
            f for f in result.failure_modes
            if f.mode == FailureMode.CHUNKING_SPLIT_INFO_LOST
        ]
        assert len(chunking_failures) > 0

    # ------------------------------------------------------------------
    # Multiple failures
    # ------------------------------------------------------------------

    def test_multiple_retrieval_failures_blame_retrieval(self) -> None:
        """Multiple retrieval failures should still blame retrieval."""
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={
                "context_precision": LOW_CONTEXT_PRECISION - 0.1,
                "context_recall": LOW_CONTEXT_RECALL - 0.1,
            },
            generation_scores={"faithfulness": 0.9},
            context_count=3,
            context_lengths=[200, 200, 200],
            answer_length=500,
        )
        result = self.blamer.analyze(scores)
        assert result.target == BlameTarget.RETRIEVAL
        # Should have both low precision and low recall failures
        assert len(result.failure_modes) >= 2

    def test_mixed_failures_blames_highest_weighted(self) -> None:
        """Mixed failures should blame the component with highest weighted score."""
        # Many retrieval failures + one generation failure
        scores = ComponentScores(
            question="What is AI?",
            retrieval_scores={
                "context_precision": LOW_CONTEXT_PRECISION - 0.1,
                "context_recall": LOW_CONTEXT_RECALL - 0.1,
            },
            generation_scores={
                "faithfulness": LOW_FAITHFULNESS - 0.1,
            },
            context_count=2,
            context_lengths=[200, 200],
            answer_length=500,
        )
        result = self.blamer.analyze(scores)
        # With 2 retrieval failures vs 1 generation, retrieval should be primary
        assert result.target == BlameTarget.RETRIEVAL
