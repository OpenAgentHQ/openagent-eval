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


class TestCorpusAuditorJsonl:
    """Regression coverage for JSONL loading (issue #57).

    A ``.jsonl`` corpus file is loaded as one ``CorpusDocument`` per
    non-empty, valid JSON line (via ``_load_jsonl_documents``), rather
    than as a single document. These tests lock the merged behavior of
    commit 4e6fbbb so a regression to whole-file loading is caught.
    """

    @pytest.mark.asyncio
    async def test_jsonl_one_document_per_line(self, tmp_path):
        """Each non-empty line of a .jsonl file becomes its own document."""
        jsonl_file = tmp_path / "data.jsonl"
        jsonl_file.write_text(
            '{"id": 1, "text": "first"}\n'
            '{"id": 2, "text": "second"}\n'
            '{"id": 3, "text": "third"}\n'
        )

        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(jsonl_file))

        # Three lines -> three documents (not one whole-file document).
        assert report.total_documents == 3

    def test_jsonl_document_shape(self, tmp_path):
        """Loaded JSONL docs carry per-line content, ids, and metadata."""
        jsonl_file = tmp_path / "data.jsonl"
        jsonl_file.write_text(
            '{"id": 1, "text": "first"}\n'
            '{"id": 2, "text": "second"}\n'
        )

        auditor = CorpusAuditor(checks=["staleness"])
        docs = auditor._load_documents(jsonl_file)

        assert len(docs) == 2
        assert docs[0].content == '{"id": 1, "text": "first"}'
        assert docs[1].content == '{"id": 2, "text": "second"}'
        assert docs[0].doc_id == f"{jsonl_file}:L1"
        assert docs[1].doc_id == f"{jsonl_file}:L2"
        assert docs[0].metadata["extension"] == ".jsonl"
        assert docs[0].metadata["filename"] == "data.jsonl"
        assert docs[0].metadata["line_number"] == 1
        assert docs[1].metadata["line_number"] == 2

    @pytest.mark.asyncio
    async def test_jsonl_skips_empty_and_whitespace_lines(self, tmp_path):
        """Blank and whitespace-only lines are skipped."""
        jsonl_file = tmp_path / "data.jsonl"
        jsonl_file.write_text(
            '{"id": 1}\n'
            "\n"
            "   \n"
            "\t\n"
            '{"id": 2}\n'
        )

        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(jsonl_file))

        # Two valid lines; three blank/whitespace lines dropped.
        assert report.total_documents == 2

    def test_jsonl_skips_malformed_line_silently(self, tmp_path):
        """A line that is not valid JSON is skipped without raising."""
        jsonl_file = tmp_path / "data.jsonl"
        jsonl_file.write_text(
            '{"id": 1}\n'
            "not valid json {\n"
            '{"id": 2}\n'
        )

        auditor = CorpusAuditor(checks=["staleness"])
        # Must not raise; the malformed line is dropped, valid ones kept.
        docs = auditor._load_documents(jsonl_file)

        assert len(docs) == 2
        assert [d.metadata["line_number"] for d in docs] == [1, 3]

    @pytest.mark.asyncio
    async def test_json_file_loads_as_single_document(self, tmp_path):
        """A .json file is still loaded as one document (no routing regression)."""
        json_file = tmp_path / "data.json"
        json_file.write_text('[{"id": 1}, {"id": 2}, {"id": 3}]')

        auditor = CorpusAuditor(checks=["staleness"])
        report = await auditor.audit(str(json_file))

        # Whole .json file -> exactly one document.
        assert report.total_documents == 1

    def test_json_file_document_extension(self, tmp_path):
        """The single .json document keeps its .json extension metadata."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')

        auditor = CorpusAuditor(checks=["staleness"])
        docs = auditor._load_documents(json_file)

        assert len(docs) == 1
        assert docs[0].metadata["extension"] == ".json"

    @pytest.mark.asyncio
    async def test_jsonl_respects_max_documents(self, tmp_path):
        """max_documents caps the number of JSONL lines loaded."""
        jsonl_file = tmp_path / "data.jsonl"
        jsonl_file.write_text("".join(f'{{"id": {i}}}\n' for i in range(10)))

        auditor = CorpusAuditor(checks=["staleness"], max_documents=4)
        report = await auditor.audit(str(jsonl_file))

        assert report.total_documents == 4
