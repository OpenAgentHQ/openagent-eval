"""Synthetic data generator — the orchestrator for test case generation.

Combines QuestionGenerator and AdversarialTestCaseGenerator to produce
comprehensive synthetic datasets from document corpora.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from openagent_eval.exceptions.synthesis import SynthesisExecutionError
from openagent_eval.synthesis.adversarial import AdversarialTestCaseGenerator
from openagent_eval.synthesis.models import (
    SyntheticDataset,
    TestCase,
    TestCaseType,
)
from openagent_eval.synthesis.question_gen import QuestionGenerator

if TYPE_CHECKING:
    from openagent_eval.providers.base.llm import LLMProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default chunking parameters
# ---------------------------------------------------------------------------

DEFAULT_CHUNK_SIZE = 2000  # characters
DEFAULT_CHUNK_OVERLAP = 200  # characters


def _chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks.

    Args:
        text: The text to chunk.
        chunk_size: Maximum chunk size in characters.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        List of text chunks.
    """
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - chunk_overlap

    return chunks


def _read_corpus(corpus_path: str | Path) -> list[tuple[str, str]]:
    """Read all text files from a corpus directory.

    Args:
        corpus_path: Path to the corpus directory.

    Returns:
        List of (filename, content) tuples.

    Raises:
        SynthesisExecutionError: If the path doesn't exist, can't be read,
            or any files fail to read.
    """
    path = Path(corpus_path)
    if not path.exists():
        raise SynthesisExecutionError(
            message=f"Corpus path does not exist: {path}",
            details={"path": str(path)},
        )

    if path.is_file():
        try:
            content = path.read_text(encoding="utf-8")
            return [(path.name, content)]
        except Exception as e:
            raise SynthesisExecutionError(
                message=f"Failed to read corpus file: {path}",
                original_error=e,
                details={"path": str(path)},
            )

    documents: list[tuple[str, str]] = []
    failed_files: list[dict[str, str]] = []

    for file_path in sorted(path.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in {
            ".txt",
            ".md",
            ".rst",
            ".html",
            ".json",
            ".jsonl",
        }:
            try:
                content = file_path.read_text(encoding="utf-8")
                documents.append((str(file_path.relative_to(path)), content))
            except Exception as e:
                failed_files.append(
                    {"file": str(file_path.relative_to(path)), "error": str(e)}
                )
                logger.warning("Failed to read %s: %s", file_path, e)

    if failed_files:
        raise SynthesisExecutionError(
            message=f"Failed to read {len(failed_files)} file(s) from corpus",
            details={"failed_files": failed_files, "corpus_path": str(path)},
        )

    return documents


class SyntheticDataGenerator:
    """Orchestrates synthetic test data generation from a document corpus.

    Reads documents, chunks them, and uses LLM-based generators to produce
    both standard and adversarial test cases for RAG evaluation.

    Usage::

        generator = SyntheticDataGenerator(llm_provider=openai_provider)
        dataset = await generator.generate(
            corpus_path="./knowledge_base/",
            count=100,
            adversarial=True,
        )

        # Or with a single document
        dataset = await generator.generate_from_text(
            text="Your document content here...",
            count=10,
        )
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        max_concurrent: int = 5,
    ) -> None:
        """Initialize the synthetic data generator.

        Args:
            llm_provider: LLM provider for question generation.
            chunk_size: Maximum chunk size in characters.
            chunk_overlap: Overlap between consecutive chunks.
            max_concurrent: Maximum concurrent LLM calls.
        """
        self._llm = llm_provider
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._max_concurrent = max_concurrent
        self._question_gen = QuestionGenerator(llm_provider)
        self._adversarial_gen = AdversarialTestCaseGenerator(llm_provider)

    async def generate(
        self,
        corpus_path: str | Path,
        count: int = 100,
        adversarial: bool = False,
        adversarial_count_per_chunk: int = 1,
        adversarial_types: list[TestCaseType] | None = None,
    ) -> SyntheticDataset:
        """Generate synthetic test cases from a document corpus.

        Args:
            corpus_path: Path to the corpus directory or file.
            count: Total number of standard test cases to generate.
            adversarial: Whether to also generate adversarial test cases.
            adversarial_count_per_chunk: Number of adversarial cases per chunk per type.
            adversarial_types: Specific adversarial types to generate (None = all types).

        Returns:
            SyntheticDataset with all generated test cases.
        """
        documents = _read_corpus(corpus_path)
        if not documents:
            raise SynthesisExecutionError(
                message="No readable documents found in corpus",
                details={"corpus_path": str(corpus_path)},
            )

        # Chunk all documents
        all_chunks: list[tuple[str, int, str]] = []
        for filename, content in documents:
            chunks = _chunk_text(content, self._chunk_size, self._chunk_overlap)
            for idx, chunk in enumerate(chunks):
                all_chunks.append((filename, idx, chunk))

        if not all_chunks:
            raise SynthesisExecutionError(
                message="No content chunks produced from corpus",
                details={"document_count": len(documents)},
            )

        # Calculate standard questions per chunk
        questions_per_chunk = max(1, count // len(all_chunks))
        remaining = count - (questions_per_chunk * len(all_chunks))

        # Generate standard test cases
        all_test_cases: list[TestCase] = []

        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def _generate_standard(
            filename: str,
            chunk_idx: int,
            chunk: str,
            num_questions: int,
        ) -> list[TestCase]:
            async with semaphore:
                return await self._question_gen.generate(
                    context=chunk,
                    count=num_questions,
                    source_document=filename,
                    chunk_index=chunk_idx,
                )

        # Build tasks for standard generation
        tasks: list[asyncio.Task[list[TestCase]]] = []
        for i, (filename, chunk_idx, chunk) in enumerate(all_chunks):
            n = questions_per_chunk + (1 if i < remaining else 0)
            if n > 0:
                task = asyncio.create_task(
                    _generate_standard(filename, chunk_idx, chunk, n)
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Standard generation failed: %s", result)
                continue
            all_test_cases.extend(result)

        # Generate adversarial test cases if requested
        if adversarial:
            adv_tasks: list[asyncio.Task[list[TestCase]]] = []

            async def _generate_adversarial(
                filename: str,
                chunk_idx: int,
                chunk: str,
            ) -> list[TestCase]:
                async with semaphore:
                    return await self._adversarial_gen.generate_all_types(
                        context=chunk,
                        count_per_type=adversarial_count_per_chunk,
                        source_document=filename,
                        chunk_index=chunk_idx,
                    )

            for filename, chunk_idx, chunk in all_chunks:
                task = asyncio.create_task(
                    _generate_adversarial(filename, chunk_idx, chunk)
                )
                adv_tasks.append(task)

            adv_results = await asyncio.gather(*adv_tasks, return_exceptions=True)

            for result in adv_results:
                if isinstance(result, Exception):
                    logger.warning("Adversarial generation failed: %s", result)
                    continue
                all_test_cases.extend(result)

        # Filter adversarial types if specified
        if adversarial_types and adversarial:
            type_values = {t.value for t in adversarial_types}
            all_test_cases = [
                tc
                for tc in all_test_cases
                if tc.test_type == TestCaseType.STANDARD
                or tc.test_type.value in type_values
            ]

        return SyntheticDataset(
            test_cases=all_test_cases,
            metadata={
                "corpus_path": str(corpus_path),
                "document_count": len(documents),
                "chunk_count": len(all_chunks),
                "requested_count": count,
                "adversarial": adversarial,
            },
        )

    async def generate_from_text(
        self,
        text: str,
        count: int = 10,
        adversarial: bool = False,
        adversarial_count_per_type: int = 1,
        adversarial_types: list[TestCaseType] | None = None,
        source_name: str = "inline_text",
    ) -> SyntheticDataset:
        """Generate synthetic test cases from raw text.

        This is a convenience method for generating test cases from a string
        without needing to create files on disk.

        Args:
            text: The document text to generate from.
            count: Number of standard test cases to generate.
            adversarial: Whether to also generate adversarial test cases.
            adversarial_count_per_type: Number of adversarial cases per type.
            adversarial_types: Specific adversarial types to generate (None = all).
            source_name: Identifier for the source text.

        Returns:
            SyntheticDataset with all generated test cases.
        """
        chunks = _chunk_text(text, self._chunk_size, self._chunk_overlap)
        if not chunks:
            raise SynthesisExecutionError(
                message="No content chunks produced from text",
                details={"text_length": len(text)},
            )

        questions_per_chunk = max(1, count // len(chunks))
        remaining = count - (questions_per_chunk * len(chunks))

        all_test_cases: list[TestCase] = []
        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def _gen(chunk: str, idx: int, n: int) -> list[TestCase]:
            async with semaphore:
                return await self._question_gen.generate(
                    context=chunk,
                    count=n,
                    source_document=source_name,
                    chunk_index=idx,
                )

        tasks = []
        for i, chunk in enumerate(chunks):
            n = questions_per_chunk + (1 if i < remaining else 0)
            if n > 0:
                tasks.append(asyncio.create_task(_gen(chunk, i, n)))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Standard generation failed: %s", result)
                continue
            all_test_cases.extend(result)

        if adversarial:
            adv_tasks = []

            async def _gen_adv(chunk: str, idx: int) -> list[TestCase]:
                async with semaphore:
                    return await self._adversarial_gen.generate_all_types(
                        context=chunk,
                        count_per_type=adversarial_count_per_type,
                        source_document=source_name,
                        chunk_index=idx,
                    )

            for i, chunk in enumerate(chunks):
                adv_tasks.append(asyncio.create_task(_gen_adv(chunk, i)))

            adv_results = await asyncio.gather(*adv_tasks, return_exceptions=True)
            for result in adv_results:
                if isinstance(result, Exception):
                    logger.warning("Adversarial generation failed: %s", result)
                    continue
                all_test_cases.extend(result)

        if adversarial_types and adversarial:
            type_values = {t.value for t in adversarial_types}
            all_test_cases = [
                tc
                for tc in all_test_cases
                if tc.test_type == TestCaseType.STANDARD
                or tc.test_type.value in type_values
            ]

        return SyntheticDataset(
            test_cases=all_test_cases,
            metadata={
                "source_name": source_name,
                "chunk_count": len(chunks),
                "requested_count": count,
                "adversarial": adversarial,
            },
        )
