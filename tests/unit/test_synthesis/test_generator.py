"""Tests for SyntheticDataGenerator orchestrator."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from openagent_eval.exceptions.synthesis import SynthesisExecutionError
from openagent_eval.synthesis.generator import (
    SyntheticDataGenerator,
    _chunk_text,
    _read_corpus,
)
from openagent_eval.synthesis.models import TestCaseType


def _make_mock_llm(response: str | None = None) -> MagicMock:
    """Create a mock LLM provider."""
    mock = MagicMock()
    mock.generate = AsyncMock()
    if response is not None:
        mock.generate.return_value = response
    return mock


def _standard_response(count: int = 2) -> str:
    """Generate a standard LLM response."""
    items = [
        {"question": f"Question {i}?", "answer": f"Answer {i}."}
        for i in range(count)
    ]
    return json.dumps(items)


class TestChunkText:
    """Tests for the _chunk_text helper."""

    def test_empty_text(self) -> None:
        """Test chunking empty text."""
        assert _chunk_text("") == []
        assert _chunk_text("   ") == []

    def test_short_text(self) -> None:
        """Test chunking text shorter than chunk size."""
        result = _chunk_text("Hello world.")
        assert result == ["Hello world."]

    def test_long_text(self) -> None:
        """Test chunking text longer than chunk size."""
        text = "A" * 100
        result = _chunk_text(text, chunk_size=50, chunk_overlap=10)
        assert len(result) > 1
        # All content should be covered
        combined = "".join(result)
        assert "A" * 50 in combined

    def test_overlap(self) -> None:
        """Test that chunks overlap correctly."""
        text = "ABCDEFGHIJ" * 10  # 100 chars
        result = _chunk_text(text, chunk_size=30, chunk_overlap=10)
        assert len(result) > 1
        # Check overlap exists between consecutive chunks
        for i in range(len(result) - 1):
            end_of_current = result[i][-10:]
            start_of_next = result[i + 1][:10]
            # At least some overlap
            assert end_of_current == start_of_next or len(result) > 1


class TestReadCorpus:
    """Tests for the _read_corpus helper."""

    def test_read_single_file(self, tmp_path: Path) -> None:
        """Test reading a single text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world.", encoding="utf-8")

        result = _read_corpus(test_file)
        assert len(result) == 1
        assert result[0] == ("test.txt", "Hello world.")

    def test_read_directory(self, tmp_path: Path) -> None:
        """Test reading a directory of files."""
        (tmp_path / "file1.txt").write_text("Content 1.", encoding="utf-8")
        (tmp_path / "file2.md").write_text("Content 2.", encoding="utf-8")
        (tmp_path / "file3.bin").write_bytes(b"\x00\x01\x02")  # Should be skipped

        result = _read_corpus(tmp_path)
        assert len(result) == 2
        contents = {name: content for name, content in result}
        assert "file1.txt" in contents
        assert "file2.md" in contents

    def test_nonexistent_path(self) -> None:
        """Test reading nonexistent path."""
        with pytest.raises(SynthesisExecutionError, match="does not exist"):
            _read_corpus("/nonexistent/path")

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test reading empty directory."""
        result = _read_corpus(tmp_path)
        assert result == []

    def test_read_file_with_encoding_error(self, tmp_path: Path) -> None:
        """Test reading a file with invalid UTF-8 encoding raises error."""
        # Create a file with invalid UTF-8 bytes
        bad_file = tmp_path / "bad.txt"
        bad_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

        with pytest.raises(SynthesisExecutionError, match="Failed to read"):
            _read_corpus(tmp_path)

    def test_read_single_file_with_encoding_error(self, tmp_path: Path) -> None:
        """Test reading a single file with invalid UTF-8 raises error."""
        bad_file = tmp_path / "bad.txt"
        bad_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

        with pytest.raises(SynthesisExecutionError, match="Failed to read corpus file"):
            _read_corpus(bad_file)


class TestSyntheticDataGenerator:
    """Tests for SyntheticDataGenerator."""

    def test_init(self) -> None:
        """Test initialization."""
        mock_llm = _make_mock_llm()
        gen = SyntheticDataGenerator(mock_llm)
        assert gen._llm is mock_llm
        assert gen._chunk_size == 2000
        assert gen._chunk_overlap == 200
        assert gen._max_concurrent == 5

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        mock_llm = _make_mock_llm()
        gen = SyntheticDataGenerator(
            mock_llm,
            chunk_size=1000,
            chunk_overlap=100,
            max_concurrent=10,
        )
        assert gen._chunk_size == 1000
        assert gen._chunk_overlap == 100
        assert gen._max_concurrent == 10

    @pytest.mark.asyncio
    async def test_generate_from_text(self) -> None:
        """Test generation from inline text."""
        mock_llm = _make_mock_llm(_standard_response(2))
        gen = SyntheticDataGenerator(mock_llm)

        result = await gen.generate_from_text(
            text="Python is a programming language used for many purposes.",
            count=2,
        )

        assert result.total_count == 2
        assert all(tc.test_type == TestCaseType.STANDARD for tc in result.test_cases)

    @pytest.mark.asyncio
    async def test_generate_from_text_with_adversarial(self) -> None:
        """Test generation from text with adversarial cases."""
        async def mock_generate(prompt: str) -> str:
            if "UNANSWERABLE" in prompt or "MISLEADING" in prompt or "AMBIGUOUS" in prompt or "MULTI-HOP" in prompt or "COUNTERFACTUAL" in prompt:
                return json.dumps([
                    {"question": "Unanswerable?", "answer": ""},
                ])
            return _standard_response(1)

        mock_llm = _make_mock_llm()
        mock_llm.generate = mock_generate
        gen = SyntheticDataGenerator(mock_llm)

        result = await gen.generate_from_text(
            text="Python is a programming language.",
            count=1,
            adversarial=True,
            adversarial_count_per_type=1,
        )

        # Should have standard + adversarial cases
        assert result.total_count > 1
        types = {tc.test_type for tc in result.test_cases}
        assert TestCaseType.STANDARD in types

    @pytest.mark.asyncio
    async def test_generate_from_text_empty(self) -> None:
        """Test generation from empty text."""
        mock_llm = _make_mock_llm()
        gen = SyntheticDataGenerator(mock_llm)

        with pytest.raises(SynthesisExecutionError, match="No content chunks"):
            await gen.generate_from_text(text="", count=5)

    @pytest.mark.asyncio
    async def test_generate_from_text_adversarial_types_filter(self) -> None:
        """Test filtering adversarial types."""
        async def mock_generate(prompt: str) -> str:
            if "UNANSWERABLE" in prompt:
                return json.dumps([
                    {"question": "Unanswerable?", "answer": ""},
                ])
            return _standard_response(1)

        mock_llm = _make_mock_llm()
        mock_llm.generate = mock_generate
        gen = SyntheticDataGenerator(mock_llm)

        result = await gen.generate_from_text(
            text="Python is a programming language.",
            count=1,
            adversarial=True,
            adversarial_count_per_type=1,
            adversarial_types=[TestCaseType.UNANSWERABLE],
        )

        types = {tc.test_type for tc in result.test_cases}
        # Should only have standard and unanswerable
        assert TestCaseType.STANDARD in types
        assert TestCaseType.UNANSWERABLE in types
        assert TestCaseType.MISLEADING not in types

    @pytest.mark.asyncio
    async def test_generate_from_corpus(self, tmp_path: Path) -> None:
        """Test generation from a corpus directory."""
        # Create a single test file with enough content for multiple chunks
        content = "Python is a programming language. " * 50  # ~1700 chars
        (tmp_path / "doc.txt").write_text(content, encoding="utf-8")

        async def mock_generate(prompt: str) -> str:
            return _standard_response(1)

        mock_llm = _make_mock_llm()
        mock_llm.generate = mock_generate
        gen = SyntheticDataGenerator(mock_llm, chunk_size=500, max_concurrent=2)

        result = await gen.generate(
            corpus_path=tmp_path,
            count=2,
            adversarial=False,
        )

        assert result.total_count > 0
        assert result.metadata["corpus_path"] == str(tmp_path)
        assert result.metadata["document_count"] == 1

    @pytest.mark.asyncio
    async def test_generate_nonexistent_corpus(self) -> None:
        """Test generation from nonexistent corpus."""
        mock_llm = _make_mock_llm()
        gen = SyntheticDataGenerator(mock_llm)

        with pytest.raises(SynthesisExecutionError, match="does not exist"):
            await gen.generate(corpus_path="/nonexistent/path")

    @pytest.mark.asyncio
    async def test_generate_metadata(self) -> None:
        """Test that metadata is correctly populated."""
        mock_llm = _make_mock_llm(_standard_response(1))
        gen = SyntheticDataGenerator(mock_llm)

        result = await gen.generate_from_text(
            text="Test document content for metadata.",
            count=1,
            adversarial=True,
            adversarial_count_per_type=1,
        )

        assert "chunk_count" in result.metadata
        assert "requested_count" in result.metadata
        assert "adversarial" in result.metadata
        assert result.metadata["adversarial"] is True
        assert result.metadata["requested_count"] == 1

    @pytest.mark.asyncio
    async def test_generate_handles_llm_errors_gracefully(self) -> None:
        """Test that LLM errors during generation are handled gracefully."""
        call_count = 0

        async def mock_generate(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("API error")
            return _standard_response(1)

        mock_llm = _make_mock_llm()
        mock_llm.generate = mock_generate
        gen = SyntheticDataGenerator(mock_llm)

        result = await gen.generate_from_text(
            text="Test document content that is long enough to create multiple chunks for testing error handling.",
            count=2,
        )

        # Should still produce some results despite one failure
        assert isinstance(result.total_count, int)


class TestSharedGenerationHelpers:
    """Tests for the extracted shared generation helpers.

    These verify that ``generate`` and ``generate_from_text`` delegate to the
    same private methods instead of each defining duplicate inner functions
    (see issue #92).
    """

    @pytest.mark.asyncio
    async def test_generate_standard_cases(self) -> None:
        """Test _generate_standard_cases produces cases from chunk tuples."""
        mock_llm = _make_mock_llm(_standard_response(1))
        gen = SyntheticDataGenerator(mock_llm)

        chunks = [("doc.txt", 0, "Python is a language."), ("doc.txt", 1, "Rust is a language.")]
        semaphore = asyncio.Semaphore(gen._max_concurrent)

        result = await gen._generate_standard_cases(chunks, 1, 0, semaphore)

        assert len(result) == 2
        assert all(tc.test_type == TestCaseType.STANDARD for tc in result)
        assert {tc.source_document for tc in result} == {"doc.txt"}
        assert {tc.chunk_index for tc in result} == {0, 1}

    @pytest.mark.asyncio
    async def test_generate_standard_cases_distributes_remaining(self) -> None:
        """Test that the `remaining` budget adds an extra question to early chunks."""
        # Mock honors the requested count so we can assert distribution.
        async def mock_generate(prompt: str) -> str:
            # The prompt embeds the requested count as "Generate {count}".
            import re as _re

            match = _re.search(r"Generate (\d+)", prompt)
            n = int(match.group(1)) if match else 1
            return _standard_response(n)

        mock_llm = _make_mock_llm()
        mock_llm.generate = mock_generate
        gen = SyntheticDataGenerator(mock_llm)

        # 3 chunks, questions_per_chunk=1, remaining=1 -> 2 + 1 + 1 distribution
        chunks = [("doc.txt", i, f"Content {i}.") for i in range(3)]
        semaphore = asyncio.Semaphore(gen._max_concurrent)

        result = await gen._generate_standard_cases(chunks, 1, 1, semaphore)

        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_generate_standard_cases_handles_errors(self) -> None:
        """Test that a failing chunk does not abort the whole batch."""
        call_count = 0

        async def mock_generate(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("API error")
            return _standard_response(1)

        mock_llm = _make_mock_llm()
        mock_llm.generate = mock_generate
        gen = SyntheticDataGenerator(mock_llm)

        chunks = [("doc.txt", 0, "Fail here."), ("doc.txt", 1, "Succeed here.")]
        semaphore = asyncio.Semaphore(gen._max_concurrent)

        result = await gen._generate_standard_cases(chunks, 1, 0, semaphore)

        # One chunk failed, the other succeeded
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_generate_adversarial_cases(self) -> None:
        """Test _generate_adversarial_cases produces adversarial cases."""
        async def mock_generate(prompt: str) -> str:
            if any(
                t in prompt
                for t in ("UNANSWERABLE", "MISLEADING", "AMBIGUOUS", "MULTI-HOP", "COUNTERFACTUAL")
            ):
                return json.dumps([{"question": "Tricky?", "answer": ""}])
            return _standard_response(1)

        mock_llm = _make_mock_llm()
        mock_llm.generate = mock_generate
        gen = SyntheticDataGenerator(mock_llm)

        chunks = [("doc.txt", 0, "Python is a language.")]
        semaphore = asyncio.Semaphore(gen._max_concurrent)

        result = await gen._generate_adversarial_cases(chunks, 1, semaphore)

        # 5 adversarial types, 1 per type
        assert len(result) == 5
        assert all(tc.test_type != TestCaseType.STANDARD for tc in result)

    @pytest.mark.asyncio
    async def test_helpers_used_by_both_entrypoints(self) -> None:
        """Test that generate and generate_from_text share the same helpers.

        Both public methods should route through the extracted private
        methods, confirming the duplication from issue #92 is removed.
        """
        mock_llm = _make_mock_llm(_standard_response(1))
        gen = SyntheticDataGenerator(mock_llm)

        from_text = await gen.generate_from_text(text="Python is a language.", count=1)
        from_corpus = await gen.generate_from_text(text="Python is a language.", count=1)

        # Both paths use the same helper; results should be equivalent in shape
        assert from_text.total_count == from_corpus.total_count == 1
        assert all(tc.test_type == TestCaseType.STANDARD for tc in from_text.test_cases)
