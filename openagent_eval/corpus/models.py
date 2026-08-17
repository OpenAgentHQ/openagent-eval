"""Pydantic models for corpus health auditing."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IssueType(StrEnum):
    """Types of corpus issues that can be detected."""

    CONTRADICTION = "contradiction"
    STALENESS = "staleness"
    DUPLICATE = "duplicate"
    COVERAGE_GAP = "coverage_gap"


class IssueSeverity(StrEnum):
    """Severity levels for corpus issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CorpusIssue(BaseModel):
    """A single issue detected in the corpus.

    Attributes:
        issue_type: Category of the issue.
        severity: How severe the issue is.
        title: Short human-readable title.
        description: Detailed explanation of the issue.
        document_ids: IDs or paths of the documents involved.
        metadata: Additional context (e.g. similarity score, timestamps).
    """

    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    document_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


class AuditReport(BaseModel):
    """Complete report from a corpus audit.

    Attributes:
        corpus_path: Path to the audited corpus.
        total_documents: Number of documents scanned.
        issues: List of detected issues.
        health_score: Overall corpus health (0.0 = unhealthy, 1.0 = perfect).
        checks_performed: Which checks were run.
        timestamp: When the audit was performed.
        summary: High-level summary text.
        metadata: Additional audit metadata.
    """

    corpus_path: str
    total_documents: int
    issues: list[CorpusIssue] = Field(default_factory=list)
    health_score: float = Field(ge=0.0, le=1.0, default=1.0)
    checks_performed: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    @property
    def issues_by_type(self) -> dict[IssueType, list[CorpusIssue]]:
        """Group issues by type."""
        result: dict[IssueType, list[CorpusIssue]] = {}
        for issue in self.issues:
            result.setdefault(issue.issue_type, []).append(issue)
        return result

    @property
    def issues_by_severity(self) -> dict[IssueSeverity, list[CorpusIssue]]:
        """Group issues by severity."""
        result: dict[IssueSeverity, list[CorpusIssue]] = {}
        for issue in self.issues:
            result.setdefault(issue.severity, []).append(issue)
        return result

    @property
    def critical_count(self) -> int:
        """Number of critical issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)

    @property
    def healthy(self) -> bool:
        """Whether the corpus passes health checks (no critical/high issues)."""
        return self.critical_count == 0 and not any(
            i.severity == IssueSeverity.HIGH for i in self.issues
        )


class CorpusDocument(BaseModel):
    """Represents a document in the corpus for auditing.

    Attributes:
        doc_id: Unique identifier (path or hash).
        content: Document text content.
        metadata: Document metadata (timestamps, source, etc.).
    """

    doc_id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
