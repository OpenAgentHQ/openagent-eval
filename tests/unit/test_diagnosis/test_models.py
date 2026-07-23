"""Tests for diagnosis data models."""

from __future__ import annotations

import pytest

from openagent_eval.diagnosis.models import (
    BlameResult,
    BlameTarget,
    ChunkingIssue,
    ComponentScores,
    DiagnosisReport,
    FailureInstance,
    FailureMode,
)


class TestFailureMode:
    """Tests for FailureMode enum."""

    def test_has_eight_modes(self) -> None:
        """FailureMode should have exactly 8 failure modes."""
        assert len(FailureMode) == 8

    def test_string_values(self) -> None:
        """FailureMode values should be descriptive strings."""
        assert FailureMode.EMPTY_RETRIEVAL.value == "empty_retrieval"
        assert FailureMode.HALLUCINATION.value == "hallucination"
        assert FailureMode.CHUNKING_SPLIT_INFO_LOST.value == "chunking_split_info_lost"

    def test_is_string_enum(self) -> None:
        """FailureMode should be usable as a string."""
        mode = FailureMode.EMPTY_RETRIEVAL
        assert isinstance(mode, str)
        assert mode == "empty_retrieval"


class TestBlameTarget:
    """Tests for BlameTarget enum."""

    def test_has_six_targets(self) -> None:
        """BlameTarget should have exactly 6 targets."""
        assert len(BlameTarget) == 6

    def test_values(self) -> None:
        """BlameTarget values should be descriptive strings."""
        assert BlameTarget.RETRIEVAL.value == "retrieval"
        assert BlameTarget.GENERATION.value == "generation"
        assert BlameTarget.CHUNKING.value == "chunking"
        assert BlameTarget.DATASET.value == "dataset"
        assert BlameTarget.NONE.value == "none"
        assert BlameTarget.UNKNOWN.value == "unknown"


class TestFailureInstance:
    """Tests for FailureInstance dataclass."""

    def test_creation(self) -> None:
        """FailureInstance should be creatable with required fields."""
        instance = FailureInstance(
            mode=FailureMode.EMPTY_RETRIEVAL,
            blame=BlameTarget.RETRIEVAL,
            confidence=0.9,
            reason="No contexts retrieved.",
        )
        assert instance.mode == FailureMode.EMPTY_RETRIEVAL
        assert instance.blame == BlameTarget.RETRIEVAL
        assert instance.confidence == 0.9
        assert instance.question == ""
        assert instance.evidence == {}

    def test_with_question_and_evidence(self) -> None:
        """FailureInstance should accept optional fields."""
        instance = FailureInstance(
            mode=FailureMode.HALLUCINATION,
            blame=BlameTarget.GENERATION,
            confidence=0.85,
            reason="Low faithfulness.",
            question="What is Python?",
            evidence={"faithfulness": 0.2},
        )
        assert instance.question == "What is Python?"
        assert instance.evidence["faithfulness"] == 0.2

    def test_invalid_confidence_raises(self) -> None:
        """FailureInstance should reject confidence outside 0.0-1.0."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            FailureInstance(
                mode=FailureMode.HALLUCINATION,
                blame=BlameTarget.GENERATION,
                confidence=1.5,
                reason="Bad confidence.",
            )

    def test_negative_confidence_raises(self) -> None:
        """FailureInstance should reject negative confidence."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            FailureInstance(
                mode=FailureMode.HALLUCINATION,
                blame=BlameTarget.GENERATION,
                confidence=-0.1,
                reason="Bad confidence.",
            )

    def test_boundary_confidence(self) -> None:
        """FailureInstance should accept confidence at 0.0 and 1.0."""
        low = FailureInstance(
            mode=FailureMode.HALLUCINATION,
            blame=BlameTarget.GENERATION,
            confidence=0.0,
            reason="Zero confidence.",
        )
        assert low.confidence == 0.0

        high = FailureInstance(
            mode=FailureMode.HALLUCINATION,
            blame=BlameTarget.GENERATION,
            confidence=1.0,
            reason="Max confidence.",
        )
        assert high.confidence == 1.0


class TestComponentScores:
    """Tests for ComponentScores dataclass."""

    def test_defaults(self) -> None:
        """ComponentScores should have sensible defaults."""
        scores = ComponentScores()
        assert scores.question == ""
        assert scores.retrieval_scores == {}
        assert scores.generation_scores == {}
        assert scores.context_count == 0
        assert scores.context_lengths == []
        assert scores.answer_length == 0
        assert scores.latency_ms is None

    def test_with_values(self) -> None:
        """ComponentScores should accept all fields."""
        scores = ComponentScores(
            question="Test question",
            retrieval_scores={"context_precision": 0.9},
            generation_scores={"faithfulness": 0.8},
            context_count=3,
            context_lengths=[100, 200, 150],
            answer_length=250,
            latency_ms=150.5,
        )
        assert scores.context_count == 3
        assert scores.latency_ms == 150.5


class TestBlameResult:
    """Tests for BlameResult dataclass."""

    def test_creation(self) -> None:
        """BlameResult should be creatable."""
        result = BlameResult(
            target=BlameTarget.RETRIEVAL,
            confidence=0.8,
            reason="Low precision.",
        )
        assert result.target == BlameTarget.RETRIEVAL
        assert result.failure_modes == []


class TestChunkingIssue:
    """Tests for ChunkingIssue dataclass."""

    def test_creation(self) -> None:
        """ChunkingIssue should be creatable."""
        issue = ChunkingIssue(
            question="Test?",
            issue_type="overlap",
            description="High overlap detected.",
            affected_contexts=[0, 1],
        )
        assert issue.issue_type == "overlap"
        assert issue.affected_contexts == [0, 1]


class TestDiagnosisReport:
    """Tests for DiagnosisReport dataclass."""

    def test_defaults(self) -> None:
        """DiagnosisReport should have sensible defaults."""
        report = DiagnosisReport()
        assert report.total_items == 0
        assert report.overall_health == 1.0
        assert report.failures == []
        assert report.recommendations == []

    def test_to_dict(self) -> None:
        """DiagnosisReport.to_dict() should produce JSON-serializable dict."""
        report = DiagnosisReport(
            total_items=10,
            blame_summary={"retrieval": 5, "generation": 3},
            failure_summary={"empty_retrieval": 3, "hallucination": 3},
            failures=[
                FailureInstance(
                    mode=FailureMode.EMPTY_RETRIEVAL,
                    blame=BlameTarget.RETRIEVAL,
                    confidence=0.9,
                    reason="No contexts.",
                    question="Q1",
                )
            ],
            chunking_issues=[
                ChunkingIssue(
                    question="Q2",
                    issue_type="overlap",
                    description="Overlap.",
                )
            ],
            recommendations=["Fix retrieval."],
            overall_health=0.7,
        )

        d = report.to_dict()
        assert d["total_items"] == 10
        assert d["overall_health"] == 0.7
        assert len(d["failures"]) == 1
        assert d["failures"][0]["mode"] == "empty_retrieval"
        assert d["failures"][0]["blame"] == "retrieval"
        assert len(d["chunking_issues"]) == 1
        assert d["recommendations"] == ["Fix retrieval."]

    def test_to_dict_empty_report(self) -> None:
        """DiagnosisReport.to_dict() should work for empty report."""
        report = DiagnosisReport()
        d = report.to_dict()
        assert d["total_items"] == 0
        assert d["failures"] == []
        assert d["chunking_issues"] == []
