"""Tests for staleness detector."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from openagent_eval.corpus.models import CorpusDocument, IssueSeverity, IssueType
from openagent_eval.corpus.staleness import StalenessDetector


class TestStalenessDetector:
    """Tests for StalenessDetector."""

    @pytest.fixture
    def detector(self):
        """Create a staleness detector with 365-day threshold."""
        return StalenessDetector(staleness_days=365)

    @pytest.fixture
    def recent_doc(self):
        """Create a recently updated document."""
        return CorpusDocument(
            doc_id="recent.txt",
            content="Recently updated content.",
            metadata={"updated_at": datetime.now(timezone.utc).isoformat()},
        )

    @pytest.fixture
    def stale_doc(self):
        """Create a stale document."""
        old_date = datetime.now(timezone.utc) - timedelta(days=500)
        return CorpusDocument(
            doc_id="stale.txt",
            content="Old content.",
            metadata={"updated_at": old_date.isoformat()},
        )

    @pytest.mark.asyncio
    async def test_no_issues_for_recent_documents(self, detector, recent_doc):
        """Test that recent documents don't generate issues."""
        report = await detector.analyze([recent_doc])

        assert len(report.issues) == 0
        assert report.health_score == 1.0

    @pytest.mark.asyncio
    async def test_detects_stale_documents(self, detector, stale_doc):
        """Test that stale documents are detected."""
        report = await detector.analyze([stale_doc])

        assert len(report.issues) == 1
        assert report.issues[0].issue_type == IssueType.STALENESS
        assert report.issues[0].severity in (
            IssueSeverity.MEDIUM,
            IssueSeverity.HIGH,
            IssueSeverity.CRITICAL,
        )
        assert "stale.txt" in report.issues[0].document_ids

    @pytest.mark.asyncio
    async def test_naive_metadata_datetime_is_treated_as_utc(self, detector):
        """Test that naive metadata datetimes do not fail UTC comparisons."""
        doc = CorpusDocument(
            doc_id="naive.txt",
            content="Old content.",
            metadata={"last_modified": datetime(2020, 1, 15)},
        )

        report = await detector.analyze([doc])

        assert len(report.issues) == 1
        assert report.issues[0].metadata["last_updated"].endswith("+00:00")

    @pytest.mark.asyncio
    async def test_health_score_decreases_with_staleness(self, detector, recent_doc, stale_doc):
        """Test health score decreases with more stale documents."""
        # All recent = perfect score
        report = await detector.analyze([recent_doc])
        assert report.health_score == 1.0

        # Mix of recent and stale
        report = await detector.analyze([recent_doc, stale_doc, stale_doc])
        assert report.health_score < 1.0

    @pytest.mark.asyncio
    async def test_empty_corpus(self, detector):
        """Test handling of empty corpus."""
        with pytest.raises(ValueError, match="empty"):
            await detector.analyze([])

    @pytest.mark.asyncio
    async def test_no_metadata_skips_document(self, detector):
        """Test documents without timestamps are skipped."""
        doc = CorpusDocument(
            doc_id="no_date.txt",
            content="Content without any date information.",
        )

        report = await detector.analyze([doc])
        assert len(report.issues) == 0

    @pytest.mark.asyncio
    async def test_content_date_extraction(self, detector):
        """Test extracting dates from document content."""
        doc = CorpusDocument(
            doc_id="content_date.txt",
            content="Last updated: 2020-01-15. This is old content.",
        )

        report = await detector.analyze([doc])
        # Should detect the 2020 date as stale
        assert len(report.issues) == 1

    @pytest.mark.asyncio
    async def test_custom_threshold(self):
        """Test custom staleness threshold."""
        detector = StalenessDetector(staleness_days=30)

        # 60 days old = stale with 30-day threshold
        old_date = datetime.now(timezone.utc) - timedelta(days=60)
        doc = CorpusDocument(
            doc_id="doc.txt",
            content="Content",
            metadata={"updated_at": old_date.isoformat()},
        )

        report = await detector.analyze([doc])
        assert len(report.issues) == 1

    @pytest.mark.asyncio
    async def test_summary_generation(self, detector, recent_doc, stale_doc):
        """Test summary text generation."""
        report = await detector.analyze([recent_doc, stale_doc])
        assert "stale" in report.summary.lower()

    @pytest.mark.asyncio
    async def test_metadata_in_report(self, detector, stale_doc):
        """Test that report metadata is populated."""
        report = await detector.analyze([stale_doc])

        assert "staleness_threshold_days" in report.metadata
        assert "cutoff_date" in report.metadata
        assert report.metadata["staleness_threshold_days"] == 365
