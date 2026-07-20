"""Integration tests for the synthetic data pipeline.

Tests the full flow from text input through generation to output,
verifying that all components work together correctly.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from openagent_eval.synthesis import (
    AdversarialTestCaseGenerator,
    QuestionGenerator,
    SyntheticDataGenerator,
    SyntheticDataset,
    TestCase,
    TestCaseType,
)


def _mock_llm_factory(responses: list[str] | str = "[]") -> MagicMock:
    """Create a mock LLM with configurable responses.

    Args:
        responses: Either a single response string or a list of responses
                   that will be returned in sequence.
    """
    mock = MagicMock()
    mock.generate = AsyncMock()

    if isinstance(responses, str):
        mock.generate.return_value = responses
    else:
        mock.generate.side_effect = responses

    return mock


class TestSynthesisIntegration:
    """Integration tests for the synthesis pipeline."""

    @pytest.mark.asyncio
    async def test_full_standard_generation_flow(self) -> None:
        """Test complete standard generation pipeline."""
        # The generator chunks the text and calls the LLM once per chunk.
        # Short text = 1 chunk = 1 LLM call returning multiple questions.
        llm_response = json.dumps([
            {"question": "What is Python?", "answer": "Python is a programming language."},
            {"question": "Is Python popular?", "answer": "Yes, Python is widely used."},
        ])
        mock_llm = _mock_llm_factory(llm_response)

        generator = SyntheticDataGenerator(mock_llm)

        dataset = await generator.generate_from_text(
            text="Python is a popular programming language. "
            "RAG is a technique that combines retrieval and generation.",
            count=2,
            adversarial=False,
        )

        assert isinstance(dataset, SyntheticDataset)
        assert dataset.total_count == 2
        assert all(tc.test_type == TestCaseType.STANDARD for tc in dataset.test_cases)
        assert all(tc.ground_truth != "" for tc in dataset.test_cases)

    @pytest.mark.asyncio
    async def test_full_adversarial_generation_flow(self) -> None:
        """Test complete adversarial generation pipeline."""
        standard_resp = json.dumps([
            {"question": "What is ML?", "answer": "Machine Learning."},
        ])
        adversarial_resp = json.dumps([
            {"question": "Why did ML fail?", "answer": "The text doesn't mention failure."},
        ])

        responses = [standard_resp] + [adversarial_resp] * 5

        mock_llm = _mock_llm_factory(responses)

        generator = SyntheticDataGenerator(mock_llm)

        dataset = await generator.generate_from_text(
            text="Machine learning enables computers to learn from data.",
            count=1,
            adversarial=True,
            adversarial_count_per_type=1,
        )

        assert isinstance(dataset, SyntheticDataset)
        assert dataset.total_count > 1
        types = {tc.test_type for tc in dataset.test_cases}
        assert TestCaseType.STANDARD in types
        # At least some adversarial types should be present
        adversarial_types = types - {TestCaseType.STANDARD}
        assert len(adversarial_types) > 0

    @pytest.mark.asyncio
    async def test_full_corpus_generation_flow(self, tmp_path: Path) -> None:
        """Test complete corpus-based generation pipeline."""
        # Create test corpus
        (tmp_path / "doc1.txt").write_text(
            "Python was created by Guido van Rossum. It was first released in 1991.",
            encoding="utf-8",
        )
        (tmp_path / "doc2.txt").write_text(
            "Machine learning is a subset of AI. It includes supervised and unsupervised learning.",
            encoding="utf-8",
        )

        standard_resp = json.dumps([
            {"question": "Who created Python?", "answer": "Guido van Rossum."},
        ])
        adversarial_resp = json.dumps([
            {"question": "When was Python created in 2020?", "answer": "Python was created in 1991, not 2020."},
        ])

        responses = [standard_resp] * 2 + [adversarial_resp] * 5

        mock_llm = _mock_llm_factory(responses)

        generator = SyntheticDataGenerator(
            mock_llm,
            chunk_size=100,
            chunk_overlap=20,
        )

        dataset = await generator.generate(
            corpus_path=tmp_path,
            count=2,
            adversarial=True,
            adversarial_count_per_chunk=1,
        )

        assert isinstance(dataset, SyntheticDataset)
        assert dataset.total_count > 0
        assert dataset.metadata["document_count"] == 2

    @pytest.mark.asyncio
    async def test_individual_generators_work_together(self) -> None:
        """Test that QuestionGenerator and AdversarialTestCaseGenerator work together."""
        standard_resp = json.dumps([
            {"question": "What is AI?", "answer": "Artificial Intelligence."},
        ])
        adversarial_resp = json.dumps([
            {"question": "Why did AI fail?", "answer": "The text doesn't mention failure."},
        ])

        mock_llm = _mock_llm_factory([standard_resp, adversarial_resp])

        # Use generators independently
        q_gen = QuestionGenerator(mock_llm)
        a_gen = AdversarialTestCaseGenerator(mock_llm)

        standard_cases = await q_gen.generate(
            context="Artificial Intelligence is transforming technology.",
            count=1,
        )
        adversarial_cases = await a_gen.generate(
            context="Artificial Intelligence is transforming technology.",
            test_type=TestCaseType.MISLEADING,
            count=1,
        )

        # Combine results
        all_cases = standard_cases + adversarial_cases
        dataset = SyntheticDataset(test_cases=all_cases)

        assert dataset.total_count == 2
        assert dataset.type_counts["standard"] == 1
        assert dataset.type_counts["misleading"] == 1

    @pytest.mark.asyncio
    async def test_dataset_serialization_roundtrip(self) -> None:
        """Test that generated datasets can be serialized and deserialized."""
        standard_resp = json.dumps([
            {"question": "What is X?", "answer": "X is Y."},
        ])

        mock_llm = _mock_llm_factory(standard_resp)

        generator = SyntheticDataGenerator(mock_llm)

        dataset = await generator.generate_from_text(
            text="X is a technology that does Y.",
            count=1,
        )

        # Serialize
        serialized = dataset.to_dict()

        # Deserialize
        deserialized = SyntheticDataset(
            test_cases=[
                TestCase(
                    question=tc["question"],
                    ground_truth=tc["ground_truth"],
                    context=tc["context"],
                    test_type=TestCaseType(tc["test_type"]),
                    source_document=tc.get("source_document", ""),
                    chunk_index=tc.get("chunk_index", 0),
                )
                for tc in serialized["test_cases"]
            ],
            metadata=serialized["metadata"],
        )

        assert deserialized.total_count == dataset.total_count
        assert deserialized.test_cases[0].question == dataset.test_cases[0].question

    @pytest.mark.asyncio
    async def test_chunking_produces_multiple_chunks(self) -> None:
        """Test that long text is properly chunked."""
        long_text = "This is a sentence about AI. " * 200  # ~6000 chars

        mock_llm = _mock_llm_factory(json.dumps([
            {"question": "What is this about?", "answer": "AI."},
        ]))

        generator = SyntheticDataGenerator(
            mock_llm,
            chunk_size=1000,
            chunk_overlap=100,
        )

        dataset = await generator.generate_from_text(
            text=long_text,
            count=5,
        )

        # Should have generated questions from multiple chunks
        assert dataset.metadata["chunk_count"] > 1
        assert dataset.total_count > 0

    @pytest.mark.asyncio
    async def test_empty_chunks_are_skipped(self) -> None:
        """Test that empty chunks don't produce test cases."""
        # Text that will produce empty chunks after stripping
        text = "   \n\n   Valid content here.   \n\n   "

        mock_llm = _mock_llm_factory(json.dumps([
            {"question": "What is this?", "answer": "Valid content."},
        ]))

        generator = SyntheticDataGenerator(mock_llm)

        dataset = await generator.generate_from_text(
            text=text,
            count=2,
        )

        # Should still produce results from non-empty chunks
        assert dataset.total_count > 0
