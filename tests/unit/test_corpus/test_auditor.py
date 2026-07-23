"""Tests for corpus auditor orchestrator."""

from __future__ import annotations

from pathlib import Path

import pytest

from openagent_eval.corpus.auditor import CorpusAuditor
from openagent_eval.exceptions.corpus import (
    CorpusNotFoundError,
    CorpusValidationError,
)


class TestCorpusAuditor:
    """Tests for CorpusAuditor."""

    @pytest.fixture
    def auditor(self):
        """Create a basic auditor."""
        return CorpusAuditor(
            checks=["staleness"],
            staleness_days=365,
        )

    @pytest.fixture
    def temp_corpus(self, tmp_path):
        """Create a temporary corpus directory with test files."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()

        # Create test files
        (corpus_dir / "doc1.txt").write_text("This is document one about Python.")
        (corpus_dir / "doc2.txt").write_text("This is document two about Java.")
        (corpus_dir / "doc3.md").write_text("# Document Three\n\nAbout Rust programming.")

        return corpus_dir

    @pytest.mark.asyncio
    async def test_audit_nonexistent_path(self, auditor):
        """Test auditing a nonexistent path raises error."""
        with pytest.raises(CorpusNotFoundError):
            await auditor.audit("/nonexistent/path")

    @pytest.mark.asyncio
    async def test_audit_empty_directory(self, tmp_path):
        """Test auditing an empty directory raises error."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        auditor = CorpusAuditor(checks=["staleness"])
        with pytest.raises(CorpusValidationError, match="No readable documents"):
            await auditor.audit(str(empty_dir))

    @pytest.mark.asyncio
    async def test_audit_with_files(self, auditor, temp_corpus):
        """Test auditing a directory with files."""
        report = await auditor.audit(str(temp_corpus))

        assert report.total_documents == 3
        assert report.health_score >= 0.0
        assert "staleness" in report.checks_performed

    @pytest.mark.asyncio
    async def test_audit_single_file(self, auditor, tmp_path):
        """Test auditing a single file."""
        single_file = tmp_path / "single.txt"
        single_file.write_text("This is a single document.")

        report = await auditor.audit(str(single_file))

        assert report.total_documents == 1
        assert len(report.checks_performed) > 0

    @pytest.mark.asyncio
    async def test_audit_with_all_checks(self, tmp_path):
        """Test auditing with all checks enabled."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "doc.txt").write_text("Test document content.")

        auditor = CorpusAuditor(checks=None)  # All checks
        report = await auditor.audit(str(corpus_dir))

        assert len(report.checks_performed) > 0

    @pytest.mark.asyncio
    async def test_audit_with_specific_checks(self, temp_corpus):
        """Test auditing with specific checks."""
        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(temp_corpus))

        assert "staleness" in report.checks_performed
        assert "contradiction" not in report.checks_performed
        assert "duplicate" not in report.checks_performed

    @pytest.mark.asyncio
    async def test_max_documents_limit(self, tmp_path):
        """Test max documents limit is respected."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()

        # Create more files than limit
        for i in range(10):
            (corpus_dir / f"doc{i}.txt").write_text(f"Document {i} content.")

        auditor = CorpusAuditor(checks=["staleness"], max_documents=3)
        report = await auditor.audit(str(corpus_dir))

        assert report.total_documents <= 3

    def test_max_documents_cap_across_jsonl_files(self, tmp_path):
        """#224: the cap must apply cumulatively across .jsonl files.

        Two .jsonl files of 3 valid lines each (6 documents available) with
        max_documents=2 must load exactly 2 — the old code only enforced the
        cap in the non-jsonl branch, so it counted per-file and returned 4.
        """
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        for name in ("a", "b"):
            lines = [f'{{"text": "{name}{i}"}}' for i in range(3)]
            (corpus_dir / f"{name}.jsonl").write_text(
                "\n".join(lines), encoding="utf-8"
            )

        auditor = CorpusAuditor(checks=["staleness"], max_documents=2)
        documents = auditor._load_documents(Path(corpus_dir))

        assert len(documents) == 2

    def test_max_documents_cap_across_mixed_directory(self, tmp_path):
        """#224: the cap applies across a mix of .jsonl and .txt files."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        # Sorted rglob visits a.jsonl (3 lines) before b.txt / c.txt.
        (corpus_dir / "a.jsonl").write_text(
            "\n".join(f'{{"text": "a{i}"}}' for i in range(3)),
            encoding="utf-8",
        )
        (corpus_dir / "b.txt").write_text("plain text b", encoding="utf-8")
        (corpus_dir / "c.txt").write_text("plain text c", encoding="utf-8")

        auditor = CorpusAuditor(checks=["staleness"], max_documents=2)
        documents = auditor._load_documents(Path(corpus_dir))

        assert len(documents) == 2

    @pytest.mark.asyncio
    async def test_load_documents_skips_empty_files(self, tmp_path):
        """Test that empty files are skipped."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()

        (corpus_dir / "empty.txt").write_text("")
        (corpus_dir / "whitespace.txt").write_text("   \n  \t  ")
        (corpus_dir / "valid.txt").write_text("Valid content here.")

        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(corpus_dir))

        assert report.total_documents == 1

    @pytest.mark.asyncio
    async def test_load_documents_supported_extensions(self, tmp_path):
        """Test that only supported file extensions are loaded."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()

        (corpus_dir / "doc.txt").write_text("Text file.")
        (corpus_dir / "doc.md").write_text("Markdown file.")
        (corpus_dir / "doc.json").write_text('{"key": "value"}')
        (corpus_dir / "doc.py").write_text("print('hello')")  # Not supported
        (corpus_dir / "doc.bin").write_bytes(b"\x00\x01\x02")  # Not supported

        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(corpus_dir))

        # Should only load .txt, .md, .json
        assert report.total_documents == 3

    @pytest.mark.asyncio
    async def test_health_score_average(self, temp_corpus):
        """Test that health score is average of analyzer scores."""
        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(temp_corpus))

        # Single check = that check's score
        assert 0.0 <= report.health_score <= 1.0

    @pytest.mark.asyncio
    async def test_report_summary(self, temp_corpus):
        """Test that report has a summary."""
        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(temp_corpus))

        assert report.summary
        assert "documents" in report.summary.lower()

    @pytest.mark.asyncio
    async def test_report_metadata(self, temp_corpus):
        """Test that report metadata is populated."""
        auditor = CorpusAuditor(
            checks=["staleness"],
            staleness_days=180,
        )
        report = await auditor.audit(str(temp_corpus))

        assert "staleness_threshold_days" in report.metadata
        assert report.metadata["staleness_threshold_days"] == 180
