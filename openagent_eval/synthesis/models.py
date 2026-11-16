"""Data models for synthetic test data generation.

Defines TestCaseType, TestCase, and SyntheticDataset used by the synthesis
module to represent generated test cases and datasets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class TestCaseType(StrEnum):
    """Type of synthetic test case.

    Attributes:
        STANDARD: Normal question-answer pair generated from document content.
        UNANSWERABLE: Question that cannot be answered from the provided context.
        AMBIGUOUS: Question with multiple valid interpretations.
        MISLEADING: Question that tempts the model to hallucinate.
        MULTI_HOP: Question requiring reasoning across multiple documents.
        COUNTERFACTUAL: Question based on a false premise.
    """

    STANDARD = "standard"
    UNANSWERABLE = "unanswerable"
    AMBIGUOUS = "ambiguous"
    MISLEADING = "misleading"
    MULTI_HOP = "multi_hop"
    COUNTERFACTUAL = "counterfactual"


@dataclass(frozen=True)
class TestCase:
    """A single synthetic test case.

    Attributes:
        question: The generated question.
        ground_truth: The expected answer (empty for unanswerable cases).
        context: The source context used for generation.
        metadata: Additional metadata (source document, generation params, etc.).
        test_type: The type of test case.
        source_document: Path or identifier of the source document.
        chunk_index: Index of the chunk within the source document.
    """

    question: str
    ground_truth: str
    context: str
    metadata: dict[str, object] = field(default_factory=dict)
    test_type: TestCaseType = TestCaseType.STANDARD
    source_document: str = ""
    chunk_index: int = 0

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "question": self.question,
            "ground_truth": self.ground_truth,
            "context": self.context,
            "metadata": self.metadata,
            "test_type": self.test_type.value,
            "source_document": self.source_document,
            "chunk_index": self.chunk_index,
        }


@dataclass
class SyntheticDataset:
    """A collection of synthetic test cases.

    Attributes:
        test_cases: List of generated test cases.
        total_count: Total number of test cases.
        metadata: Dataset-level metadata (generation params, timestamps, etc.).
        type_counts: Breakdown of test case counts by type.
    """

    test_cases: list[TestCase] = field(default_factory=list)
    total_count: int = 0
    metadata: dict[str, object] = field(default_factory=dict)
    type_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Compute derived fields after initialization."""
        if self.total_count == 0:
            self.total_count = len(self.test_cases)
        if not self.type_counts:
            self.type_counts = self._count_by_type()

    def _count_by_type(self) -> dict[str, int]:
        """Count test cases by type."""
        counts: dict[str, int] = {}
        for tc in self.test_cases:
            key = tc.test_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_list(self) -> list[dict[str, object]]:
        """Serialize all test cases to a list of dicts."""
        return [tc.to_dict() for tc in self.test_cases]

    def to_dict(self) -> dict[str, object]:
        """Serialize the full dataset to a dictionary."""
        return {
            "test_cases": self.to_list(),
            "total_count": self.total_count,
            "metadata": self.metadata,
            "type_counts": self.type_counts,
        }
