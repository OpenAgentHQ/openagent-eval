"""Staleness detector using timestamp analysis.

Detects outdated documents by analyzing metadata timestamps
and content freshness signals.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from openagent_eval.corpus.base import BaseCorpusAnalyzer
from openagent_eval.corpus.models import (
    AuditReport,
    CorpusDocument,
    CorpusIssue,
    IssueSeverity,
    IssueType,
)

# Common date patterns in document metadata or content
_DATE_PATTERNS = [
    # ISO 8601 variants
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
    r"\d{4}-\d{2}-\d{2}",
    # US format
    r"\d{1,2}/\d{1,2}/\d{4}",
    # Written format
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}",
]


class StalenessDetector(BaseCorpusAnalyzer):
    """Detects outdated documents using timestamp analysis.

    Checks document metadata for timestamps and flags documents
    that are older than a configurable threshold.

    Attributes:
        name: Identifier for this analyzer.
        description: Human-readable description.
    """

    name = "staleness"
    description = "Detects outdated documents using timestamp analysis"

    def __init__(self, staleness_days: int = 365) -> None:
        """Initialize the staleness detector.

        Args:
            staleness_days: Documents older than this many days are flagged.
        """
        self.staleness_days = staleness_days

    async def analyze(
        self,
        documents: list[CorpusDocument],
        **kwargs: Any,
    ) -> AuditReport:
        """Analyze documents for staleness.

        Args:
            documents: List of corpus documents to analyze.
            **kwargs: Additional configuration.

        Returns:
            AuditReport with detected stale documents.

        Raises:
            CorpusAuditError: If analysis fails.
        """
        self.validate_inputs(documents)

        issues: list[CorpusIssue] = []
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self.staleness_days)

        for doc in documents:
            issue = self._check_document(doc, now, cutoff)
            if issue:
                issues.append(issue)

        health_score = self._compute_health_score(len(documents), len(issues))

        return AuditReport(
            corpus_path="",
            total_documents=len(documents),
            issues=issues,
            health_score=health_score,
            checks_performed=[self.name],
            summary=self._generate_summary(issues, len(documents)),
            metadata={
                "staleness_threshold_days": self.staleness_days,
                "cutoff_date": cutoff.isoformat(),
            },
        )

    def _check_document(
        self,
        doc: CorpusDocument,
        now: datetime,
        cutoff: datetime,
    ) -> CorpusIssue | None:
        """Check a single document for staleness.

        Args:
            doc: Document to check.
            now: Current timestamp.
            cutoff: Staleness cutoff timestamp.

        Returns:
            CorpusIssue if stale, None otherwise.
        """
        # Try to extract timestamp from metadata first
        timestamp = self._extract_timestamp_from_metadata(doc.metadata)

        # Fall back to content-based detection
        if timestamp is None:
            timestamp = self._extract_timestamp_from_content(doc.content)

        if timestamp is None:
            # Cannot determine age — skip (not necessarily stale)
            return None

        if timestamp < cutoff:
            age_days = (now - timestamp).days
            severity = self._compute_severity(age_days)

            return CorpusIssue(
                issue_type=IssueType.STALENESS,
                severity=severity,
                title=f"Document is {age_days} days old",
                description=(
                    f"Document '{doc.doc_id}' was last updated on "
                    f"{timestamp.strftime('%Y-%m-%d')}, which is {age_days} days ago "
                    f"(threshold: {self.staleness_days} days)."
                ),
                document_ids=[doc.doc_id],
                metadata={
                    "last_updated": timestamp.isoformat(),
                    "age_days": age_days,
                    "threshold_days": self.staleness_days,
                },
            )

        return None

    def _extract_timestamp_from_metadata(
        self, metadata: dict[str, Any]
    ) -> datetime | None:
        """Extract timestamp from document metadata.

        Looks for common metadata keys: 'updated_at', 'modified_date',
        'last_modified', 'date', 'timestamp', 'created_at'.

        Args:
            metadata: Document metadata dictionary.

        Returns:
            Parsed datetime or None.
        """
        date_keys = [
            "updated_at", "modified_date", "last_modified",
            "date", "timestamp", "created_at", "publish_date",
            "modified", "updated", "date_modified", "date_updated",
        ]

        for key in date_keys:
            value = metadata.get(key)
            if value is None:
                continue

            if isinstance(value, datetime):
                if value.tzinfo is None:
                    return value.replace(tzinfo=UTC)
                return value

            if isinstance(value, str):
                parsed = self._parse_date_string(value)
                if parsed:
                    return parsed

            if isinstance(value, (int, float)):
                # Assume Unix timestamp
                try:
                    return datetime.fromtimestamp(value, tz=timezone.utc)
                except (OSError, ValueError):
                    continue

        return None

    def _extract_timestamp_from_content(self, content: str) -> datetime | None:
        """Extract timestamp from document content.

        Searches for date patterns in the first 500 characters
        (typically where metadata headers appear).

        Args:
            content: Document text content.

        Returns:
            Parsed datetime or None.
        """
        # Only check first 500 chars for date patterns
        snippet = content[:500]

        for pattern in _DATE_PATTERNS:
            matches = re.findall(pattern, snippet)
            for match in matches:
                parsed = self._parse_date_string(match)
                if parsed:
                    return parsed

        return None

    def _parse_date_string(self, date_str: str) -> datetime | None:
        """Parse a date string into a datetime object.

        Args:
            date_str: Date string to parse.

        Returns:
            Parsed datetime or None.
        """
        # Normalize timezone format: +00:00 -> +0000
        import re

        normalized = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", date_str.strip())

        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%b %d, %Y",
            "%B %d, %Y",
            "%b %d %Y",
            "%B %d %Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(normalized, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        return None

    def _compute_severity(self, age_days: int) -> IssueSeverity:
        """Compute severity based on document age.

        Args:
            age_days: Age of the document in days.

        Returns:
            Appropriate severity level.
        """
        if age_days > self.staleness_days * 3:
            return IssueSeverity.CRITICAL
        elif age_days > self.staleness_days * 2:
            return IssueSeverity.HIGH
        elif age_days > self.staleness_days:
            return IssueSeverity.MEDIUM
        else:
            return IssueSeverity.LOW

    def _compute_health_score(self, num_docs: int, num_issues: int) -> float:
        """Compute health score based on staleness.

        Args:
            num_docs: Number of documents.
            num_issues: Number of stale documents.

        Returns:
            Health score between 0.0 and 1.0.
        """
        if num_docs == 0:
            return 1.0

        ratio = num_issues / num_docs
        return max(1.0 - ratio, 0.0)

    def _generate_summary(self, issues: list[CorpusIssue], num_docs: int) -> str:
        """Generate a human-readable summary.

        Args:
            issues: Detected issues.
            num_docs: Number of documents analyzed.

        Returns:
            Summary string.
        """
        if not issues:
            return f"No stale documents found across {num_docs} documents."

        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
        medium = sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM)

        parts = [f"Found {len(issues)} stale document(s) across {num_docs} documents."]
        if critical:
            parts.append(f"{critical} critical (very old).")
        if high:
            parts.append(f"{high} high.")
        if medium:
            parts.append(f"{medium} medium.")

        return " ".join(parts)
