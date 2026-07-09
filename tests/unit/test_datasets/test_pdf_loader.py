"""Tests for the PDF dataset loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from openagent_eval.datasets.pdf_loader import (
    DEFAULT_QUESTION_TEMPLATE,
    PDFDatasetLoader,
)
from openagent_eval.exceptions import (
    DatasetNotFoundError,
    DatasetValidationError,
    InvalidDatasetError,
)


def _escape(text: str) -> str:
    """Escape text for inclusion in a PDF content stream."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(texts: list[str]) -> bytes:
    """Build a minimal but valid PDF with one page per entry in ``texts``.

    Each page renders its text via a simple text-show operator so that
    ``pypdf`` can extract it. Used to avoid committing a binary fixture.
    """
    n_pages = len(texts)
    page_objs = [3 + i for i in range(n_pages)]
    content_objs = [3 + n_pages + i for i in range(n_pages)]
    font_obj = 3 + 2 * n_pages

    parts: list[bytes] = []
    offsets: dict[int, int] = {}

    def add(obj_num: int, body: str) -> None:
        offsets[obj_num] = sum(len(p) for p in parts)
        parts.append(f"{obj_num} 0 obj\n{body}\nendobj\n".encode())

    add(1, "<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{n} 0 R" for n in page_objs)
    add(2, f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>")

    for i, text in enumerate(texts):
        page_body = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_objs[i]} 0 R "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> >>"
        )
        add(page_objs[i], page_body)
        stream = f"BT /F1 12 Tf 72 720 Td ({_escape(text)}) Tj ET".encode()
        content_body = (
            f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"
        )
        add(content_objs[i], content_body.decode())

    add(font_obj, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    prefix = b"%PDF-1.4\n"
    body = b"".join(parts)
    xref_offset = len(prefix) + len(body)

    xref = b"xref\n0 " + str(font_obj + 1).encode() + b"\n"
    xref += b"0000000000 65535 f \n"
    for obj_num in range(1, font_obj + 1):
        xref += f"{len(prefix) + offsets[obj_num]:010d} 00000 n \n".encode()

    trailer = (
        f"trailer\n<< /Size {font_obj + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode()

    return prefix + body + xref + trailer


class TestPDFDatasetLoader:
    """Tests for PDFDatasetLoader."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.loader = PDFDatasetLoader()

    def _write_pdf(self, path: Path, texts: list[str]) -> None:
        """Helper to write a PDF with the given page texts."""
        path.write_bytes(_build_pdf(texts))

    def test_load_multi_page_pdf(self, tmp_path: Path) -> None:
        """Test loading a multi-page PDF produces one item per page."""
        pdf_path = tmp_path / "doc.pdf"
        self._write_pdf(pdf_path, ["Page one about Python.", "Page two about RAG."])

        dataset = self.loader.load(pdf_path)

        assert dataset.size == 2
        assert dataset.name == "doc"
        assert "Python" in dataset[0].context
        assert "RAG" in dataset[1].context
        assert dataset[0].metadata["page"] == 1
        assert dataset[1].metadata["page"] == 2
        assert dataset.metadata["format"] == "pdf"
        assert dataset.metadata["pages"] == 2

    def test_load_single_page_pdf(self, tmp_path: Path) -> None:
        """Test loading a single-page PDF."""
        pdf_path = tmp_path / "single.pdf"
        self._write_pdf(pdf_path, ["Only page content."])

        dataset = self.loader.load(pdf_path)

        assert dataset.size == 1
        assert dataset[0].context == "Only page content."
        assert dataset[0].question == DEFAULT_QUESTION_TEMPLATE

    def test_load_uses_custom_question_template(self, tmp_path: Path) -> None:
        """Test that a custom question template is applied."""
        loader = PDFDatasetLoader(question_template="Summarize this page.")
        pdf_path = tmp_path / "doc.pdf"
        self._write_pdf(pdf_path, ["Content here."])

        dataset = loader.load(pdf_path)

        assert dataset[0].question == "Summarize this page."

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Test loading a non-existent file raises DatasetNotFoundError."""
        pdf_path = tmp_path / "missing.pdf"

        with pytest.raises(DatasetNotFoundError):
            self.loader.load(pdf_path)

    def test_load_empty_pdf_raises(self, tmp_path: Path) -> None:
        """Test that a PDF with no extractable text raises."""
        pdf_path = tmp_path / "blank.pdf"
        # A PDF with a page that has no text content stream.
        self._write_pdf(pdf_path, [])

        with pytest.raises(DatasetValidationError):
            self.loader.load(pdf_path)

    def test_load_missing_pypdf_raises(self, tmp_path: Path, monkeypatch) -> None:
        """Test that a helpful error is raised when pypdf is missing."""
        import sys

        pdf_path = tmp_path / "doc.pdf"
        self._write_pdf(pdf_path, ["Content."])
        monkeypatch.setitem(sys.modules, "pypdf", None)

        with pytest.raises(InvalidDatasetError, match="pypdf"):
            self.loader.load(pdf_path)

    def test_validate_valid_data(self) -> None:
        """Test validate with valid data."""
        data = [
            {"question": "Q1", "context": "C1"},
            {"question": "Q2", "context": "C2"},
        ]
        assert self.loader.validate(data) is True

    def test_validate_not_list(self) -> None:
        """Test validate with non-list data."""
        with pytest.raises(DatasetValidationError):
            self.loader.validate("not a list")

    def test_validate_empty_list(self) -> None:
        """Test validate with empty list."""
        with pytest.raises(DatasetValidationError):
            self.loader.validate([])

    def test_validate_missing_context(self) -> None:
        """Test validate rejects items without context."""
        data = [{"question": "Q1"}]
        with pytest.raises(DatasetValidationError):
            self.loader.validate(data)

    def test_factory_registration(self) -> None:
        """Test that the PDF loader is registered in the factory maps."""
        from openagent_eval.datasets.factory import _FORMAT_MAP, _LOADER_MAP

        assert ".pdf" in _LOADER_MAP
        assert "pdf" in _FORMAT_MAP
        assert _LOADER_MAP[".pdf"] is PDFDatasetLoader
        assert _FORMAT_MAP["pdf"] is PDFDatasetLoader
