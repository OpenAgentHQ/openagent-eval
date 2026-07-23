"""Data models for component diagnosis.

Defines the FailureMode enum, DiagnosisReport, and supporting dataclasses
used to attribute blame when RAG evaluations fail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FailureMode(str, Enum):
    """Enumeration of RAG failure modes.

    Each mode maps to a specific component failure:
    - Retrieval failures: empty_retrieval, low_context_relevance, stale_index, embedding_mismatch
    - Generation failures: hallucination, off_topic_answer
    - Chunking failures: chunking_split_info_lost
    - Context failures: missing_context
    """

    EMPTY_RETRIEVAL = "empty_retrieval"
    LOW_CONTEXT_RELEVANCE = "low_context_relevance"
    MISSING_CONTEXT = "missing_context"
    HALLUCINATION = "hallucination"
    OFF_TOPIC_ANSWER = "off_topic_answer"
    CHUNKING_SPLIT_INFO_LOST = "chunking_split_info_lost"
    STALE_INDEX = "stale_index"
    EMBEDDING_MISMATCH = "embedding_mismatch"


class BlameTarget(str, Enum):
    """Which component is blamed for a failure.

    NONE indicates analysis completed with no failures detected.
    UNKNOWN is reserved for cases where blame could not be determined.
    """

    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    CHUNKING = "chunking"
    DATASET = "dataset"
    NONE = "none"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FailureInstance:
    """A single detected failure.

    Attributes:
        mode: The failure mode detected.
        blame: Which component is responsible.
        confidence: Confidence in this diagnosis (0.0–1.0).
        reason: Human-readable explanation.
        question: The question that triggered the failure.
        evidence: Supporting data for the diagnosis (metric scores, etc.).
    """

    mode: FailureMode
    blame: BlameTarget
    confidence: float
    reason: str
    question: str = ""
    evidence: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


@dataclass
class ComponentScores:
    """Aggregated scores for a single evaluation item, used for blame attribution.

    Attributes:
        question: The original question.
        retrieval_scores: Scores from retrieval metrics (context_precision, context_recall, etc.).
        generation_scores: Scores from generation metrics (faithfulness, relevancy, etc.).
        context_count: Number of retrieved contexts.
        context_lengths: Lengths of retrieved contexts in characters.
        answer_length: Length of the generated answer in characters.
        latency_ms: Total latency in milliseconds.
    """

    question: str = ""
    retrieval_scores: dict[str, float] = field(default_factory=dict)
    generation_scores: dict[str, float] = field(default_factory=dict)
    context_count: int = 0
    context_lengths: list[int] = field(default_factory=list)
    answer_length: int = 0
    latency_ms: float | None = None


@dataclass
class BlameResult:
    """Result of blame attribution for a single item.

    Attributes:
        target: The component blamed.
        confidence: Confidence in the blame (0.0–1.0).
        reason: Explanation of why this component was blamed.
        failure_modes: List of detected failure modes.
    """

    target: BlameTarget
    confidence: float
    reason: str
    failure_modes: list[FailureInstance] = field(default_factory=list)


@dataclass
class ChunkingIssue:
    """A chunking quality issue detected.

    Attributes:
        question: The question that exposed the issue.
        issue_type: Short label (e.g., "split_info", "overlapping_chunks").
        description: Human-readable description.
        affected_contexts: Indices of contexts involved.
    """

    question: str
    issue_type: str
    description: str
    affected_contexts: list[int] = field(default_factory=list)


@dataclass
class DiagnosisReport:
    """Full diagnosis report for an evaluation run.

    Attributes:
        total_items: Total number of items diagnosed.
        blame_summary: Counts per blame target.
        failure_summary: Counts per failure mode.
        failures: All detected failure instances.
        chunking_issues: Detected chunking quality issues.
        recommendations: Actionable recommendations.
        overall_health: Overall health score (0.0–1.0).
    """

    total_items: int = 0
    blame_summary: dict[str, int] = field(default_factory=dict)
    failure_summary: dict[str, int] = field(default_factory=dict)
    failures: list[FailureInstance] = field(default_factory=list)
    chunking_issues: list[ChunkingIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    overall_health: float = 1.0

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "total_items": self.total_items,
            "blame_summary": self.blame_summary,
            "failure_summary": self.failure_summary,
            "failures": [
                {
                    "mode": f.mode.value,
                    "blame": f.blame.value,
                    "confidence": f.confidence,
                    "reason": f.reason,
                    "question": f.question,
                    "evidence": f.evidence,
                }
                for f in self.failures
            ],
            "chunking_issues": [
                {
                    "question": ci.question,
                    "issue_type": ci.issue_type,
                    "description": ci.description,
                    "affected_contexts": ci.affected_contexts,
                }
                for ci in self.chunking_issues
            ],
            "recommendations": self.recommendations,
            "overall_health": self.overall_health,
        }
