"""Integration test for corpus audit pipeline.

Tests the full audit pipeline from document loading through
all analyzers to final report generation.
"""

from __future__ import annotations


import pytest

from openagent_eval.corpus.auditor import CorpusAuditor
from openagent_eval.corpus.models import IssueSeverity, IssueType


class TestCorpusAuditPipeline:
    """Integration tests for the corpus audit pipeline."""

    @pytest.fixture
    def healthy_corpus(self, tmp_path):
        """Create a healthy corpus with recent, unique documents."""
        corpus_dir = tmp_path / "healthy"
        corpus_dir.mkdir()

        (corpus_dir / "python_guide.txt").write_text(
            "Python is a versatile programming language. "
            "It supports object-oriented, functional, and procedural programming paradigms. "
            "Python is widely used in data science, web development, and automation."
        )

        (corpus_dir / "java_guide.txt").write_text(
            "Java is a class-based programming language. "
            "It follows the write once, run anywhere principle. "
            "Java is commonly used in enterprise applications and Android development."
        )

        (corpus_dir / "rust_guide.txt").write_text(
            "Rust is a systems programming language. "
            "It focuses on safety, speed, and concurrency. "
            "Rust is used for system programming, WebAssembly, and command-line tools."
        )

        return corpus_dir

    @pytest.fixture
    def unhealthy_corpus(self, tmp_path):
        """Create a corpus with multiple issues."""
        corpus_dir = tmp_path / "unhealthy"
        corpus_dir.mkdir()

        # Stale document (from 2020)
        (corpus_dir / "old_api.txt").write_text(
            "Last updated: 2020-01-15. "
            "The API endpoint is /api/v1/users. "
            "Authentication uses API keys in the header."
        )

        # Another stale document
        (corpus_dir / "old_api_v2.txt").write_text(
            "Last updated: 2019-06-10. "
            "The API endpoint is /api/v1/users. "
            "Authentication uses API keys in the header."
        )

        # Recent document
        (corpus_dir / "new_guide.txt").write_text(
            "This is a modern guide to using the platform effectively."
        )

        return corpus_dir

    @pytest.mark.asyncio
    async def test_healthy_corpus_passes(self, healthy_corpus):
        """Test that a healthy corpus passes audit."""
        auditor = CorpusAuditor(
            checks=["staleness"],
            staleness_days=365,
        )

        report = await auditor.audit(str(healthy_corpus))

        assert report.total_documents == 3
        assert report.health_score >= 0.8
        assert report.healthy is True
        assert len(report.issues) == 0

    @pytest.mark.asyncio
    async def test_stale_corpus_detected(self, unhealthy_corpus):
        """Test that stale documents are detected."""
        auditor = CorpusAuditor(
            checks=["staleness"],
            staleness_days=365,
        )

        report = await auditor.audit(str(unhealthy_corpus))

        assert report.total_documents == 3
        assert len(report.issues) > 0
        assert any(
            issue.issue_type == IssueType.STALENESS for issue in report.issues
        )

    @pytest.mark.asyncio
    async def test_full_audit_all_checks(self, unhealthy_corpus):
        """Test running all checks on a corpus."""
        auditor = CorpusAuditor(
            checks=None,  # All checks
            staleness_days=365,
        )

        report = await auditor.audit(str(unhealthy_corpus))

        assert report.total_documents == 3
        assert len(report.checks_performed) > 0
        assert report.health_score >= 0.0
        assert report.health_score <= 1.0
        assert report.summary

    @pytest.mark.asyncio
    async def test_audit_report_structure(self, healthy_corpus):
        """Test that audit report has all required fields."""
        auditor = CorpusAuditor(checks=["staleness"])

        report = await auditor.audit(str(healthy_corpus))

        # Required fields
        assert report.corpus_path == str(healthy_corpus)
        assert isinstance(report.total_documents, int)
        assert isinstance(report.issues, list)
        assert isinstance(report.health_score, float)
        assert isinstance(report.checks_performed, list)
        assert isinstance(report.summary, str)
        assert isinstance(report.metadata, dict)

    @pytest.mark.asyncio
    async def test_audit_with_multiple_check_types(self, healthy_corpus):
        """Test running multiple specific checks."""
        auditor = CorpusAuditor(
            checks=["staleness", "duplicate"],
            staleness_days=365,
        )

        report = await auditor.audit(str(healthy_corpus))

        assert "staleness" in report.checks_performed
        assert "duplicate" in report.checks_performed
        assert "contradiction" not in report.checks_performed

    @pytest.mark.asyncio
    async def test_audit_preserves_document_count(self, healthy_corpus):
        """Test that document count is accurate."""
        auditor = CorpusAuditor(checks=["staleness"])

        report = await auditor.audit(str(healthy_corpus))

        # Should match the 3 files we created
        assert report.total_documents == 3

    @pytest.mark.asyncio
    async def test_audit_with_subdirectories(self, tmp_path):
        """Test auditing corpus with nested directories."""
        corpus_dir = tmp_path / "nested"
        corpus_dir.mkdir()

        subdir = corpus_dir / "subdir"
        subdir.mkdir()

        (corpus_dir / "root.txt").write_text("Root level document.")
        (subdir / "nested.txt").write_text("Nested directory document.")

        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(corpus_dir))

        assert report.total_documents == 2

    @pytest.mark.asyncio
    async def test_audit_mixed_file_types(self, tmp_path):
        """Test auditing corpus with different file types."""
        corpus_dir = tmp_path / "mixed"
        corpus_dir.mkdir()

        (corpus_dir / "readme.txt").write_text("Text file content.")
        (corpus_dir / "guide.md").write_text("# Guide\n\nMarkdown content.")
        (corpus_dir / "data.json").write_text('{"key": "value"}')

        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(corpus_dir))

        assert report.total_documents == 3

    @pytest.mark.asyncio
    async def test_health_score_range(self, unhealthy_corpus):
        """Test that health score is always between 0 and 1."""
        auditor = CorpusAuditor(checks=None)

        report = await auditor.audit(str(unhealthy_corpus))

        assert 0.0 <= report.health_score <= 1.0

    @pytest.mark.asyncio
    async def test_issues_have_valid_types(self, unhealthy_corpus):
        """Test that all issues have valid types and severities."""
        auditor = CorpusAuditor(checks=None)

        report = await auditor.audit(str(unhealthy_corpus))

        for issue in report.issues:
            assert isinstance(issue.issue_type, IssueType)
            assert isinstance(issue.severity, IssueSeverity)
            assert issue.title
            assert issue.description
