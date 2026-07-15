"""Tests for corpus models."""

from __future__ import annotations


import pytest

from openagent_eval.corpus.models import (
    AuditReport,
    CorpusDocument,
    CorpusIssue,
    IssueSeverity,
    IssueType,
)


class TestCorpusIssue:
    """Tests for CorpusIssue model."""

    def test_create_basic_issue(self):
        """Test creating a basic corpus issue."""
        issue = CorpusIssue(
            issue_type=IssueType.CONTRADICTION,
            severity=IssueSeverity.HIGH,
            title="Test contradiction",
            description="Two documents disagree",
            document_ids=["doc1.txt", "doc2.txt"],
        )

        assert issue.issue_type == IssueType.CONTRADICTION
        assert issue.severity == IssueSeverity.HIGH
        assert issue.title == "Test contradiction"
        assert len(issue.document_ids) == 2

    def test_issue_is_frozen(self):
        """Test that issues are immutable."""
        issue = CorpusIssue(
            issue_type=IssueType.STALENESS,
            severity=IssueSeverity.LOW,
            title="Test",
            description="Test",
        )

        with pytest.raises(Exception):
            issue.title = "Changed"  # type: ignore

    def test_issue_with_metadata(self):
        """Test issue with custom metadata."""
        issue = CorpusIssue(
            issue_type=IssueType.DUPLICATE,
            severity=IssueSeverity.MEDIUM,
            title="Duplicate found",
            description="Near-duplicate documents",
            metadata={"similarity": 0.95, "is_exact": False},
        )

        assert issue.metadata["similarity"] == 0.95
        assert issue.metadata["is_exact"] is False


class TestAuditReport:
    """Tests for AuditReport model."""

    def test_create_empty_report(self):
        """Test creating an empty audit report."""
        report = AuditReport(
            corpus_path="/test/corpus",
            total_documents=10,
        )

        assert report.health_score == 1.0
        assert len(report.issues) == 0
        assert report.healthy is True

    def test_report_with_issues(self):
        """Test report with issues affects health score."""
        issues = [
            CorpusIssue(
                issue_type=IssueType.CONTRADICTION,
                severity=IssueSeverity.CRITICAL,
                title="Critical issue",
                description="Test",
            ),
        ]

        report = AuditReport(
            corpus_path="/test",
            total_documents=5,
            issues=issues,
            health_score=0.5,
        )

        assert report.healthy is False
        assert report.critical_count == 1

    def test_issues_by_type(self):
        """Test grouping issues by type."""
        issues = [
            CorpusIssue(
                issue_type=IssueType.CONTRADICTION,
                severity=IssueSeverity.HIGH,
                title="C1",
                description="Test",
            ),
            CorpusIssue(
                issue_type=IssueType.STALENESS,
                severity=IssueSeverity.MEDIUM,
                title="S1",
                description="Test",
            ),
            CorpusIssue(
                issue_type=IssueType.CONTRADICTION,
                severity=IssueSeverity.LOW,
                title="C2",
                description="Test",
            ),
        ]

        report = AuditReport(
            corpus_path="/test",
            total_documents=10,
            issues=issues,
        )

        by_type = report.issues_by_type
        assert len(by_type[IssueType.CONTRADICTION]) == 2
        assert len(by_type[IssueType.STALENESS]) == 1

    def test_issues_by_severity(self):
        """Test grouping issues by severity."""
        issues = [
            CorpusIssue(
                issue_type=IssueType.DUPLICATE,
                severity=IssueSeverity.HIGH,
                title="D1",
                description="Test",
            ),
            CorpusIssue(
                issue_type=IssueType.DUPLICATE,
                severity=IssueSeverity.LOW,
                title="D2",
                description="Test",
            ),
        ]

        report = AuditReport(
            corpus_path="/test",
            total_documents=10,
            issues=issues,
        )

        by_severity = report.issues_by_severity
        assert len(by_severity[IssueSeverity.HIGH]) == 1
        assert len(by_severity[IssueSeverity.LOW]) == 1

    def test_healthy_property(self):
        """Test the healthy property logic."""
        # No issues = healthy
        report = AuditReport(corpus_path="/test", total_documents=5)
        assert report.healthy is True

        # Low issues = healthy
        report = AuditReport(
            corpus_path="/test",
            total_documents=5,
            issues=[
                CorpusIssue(
                    issue_type=IssueType.STALENESS,
                    severity=IssueSeverity.LOW,
                    title="T",
                    description="T",
                ),
            ],
        )
        assert report.healthy is True

        # High issues = not healthy
        report = AuditReport(
            corpus_path="/test",
            total_documents=5,
            issues=[
                CorpusIssue(
                    issue_type=IssueType.CONTRADICTION,
                    severity=IssueSeverity.HIGH,
                    title="T",
                    description="T",
                ),
            ],
        )
        assert report.healthy is False

        # Critical issues = not healthy
        report = AuditReport(
            corpus_path="/test",
            total_documents=5,
            issues=[
                CorpusIssue(
                    issue_type=IssueType.DUPLICATE,
                    severity=IssueSeverity.CRITICAL,
                    title="T",
                    description="T",
                ),
            ],
        )
        assert report.healthy is False


class TestCorpusDocument:
    """Tests for CorpusDocument model."""

    def test_create_document(self):
        """Test creating a corpus document."""
        doc = CorpusDocument(
            doc_id="doc1.txt",
            content="This is test content.",
            metadata={"source": "test"},
        )

        assert doc.doc_id == "doc1.txt"
        assert doc.content == "This is test content."
        assert doc.metadata["source"] == "test"

    def test_document_defaults(self):
        """Test document with default metadata."""
        doc = CorpusDocument(
            doc_id="doc1.txt",
            content="Content",
        )

        assert doc.metadata == {}


class TestIssueType:
    """Tests for IssueType enum."""

    def test_all_types_exist(self):
        """Test all expected issue types exist."""
        assert IssueType.CONTRADICTION.value == "contradiction"
        assert IssueType.STALENESS.value == "staleness"
        assert IssueType.DUPLICATE.value == "duplicate"
        assert IssueType.COVERAGE_GAP.value == "coverage_gap"


class TestIssueSeverity:
    """Tests for IssueSeverity enum."""

    def test_severity_order(self):
        """Test severity levels exist."""
        assert IssueSeverity.LOW.value == "low"
        assert IssueSeverity.MEDIUM.value == "medium"
        assert IssueSeverity.HIGH.value == "high"
        assert IssueSeverity.CRITICAL.value == "critical"
