"""Question generator — generates questions from document chunks.

Uses an LLM provider to create question-answer pairs from text content,
producing standard test cases for RAG evaluation.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from openagent_eval.exceptions.synthesis import SynthesisExecutionError
from openagent_eval.synthesis.models import TestCase, TestCaseType

if TYPE_CHECKING:
    from openagent_eval.providers.base.llm import LLMProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_QUESTION_GENERATION_PROMPT = """\
You are a test case generator for a RAG (Retrieval-Augmented Generation) evaluation system.

Given the following document chunk, generate {count} diverse question-answer pairs.
Each question should be answerable ONLY from the provided context.

Return a JSON array of objects with "question" and "answer" keys.
Example:
[
  {{"question": "What is X?", "answer": "X is Y."}},
  {{"question": "How does Z work?", "answer": "Z works by..."}}
]

Rules:
- Questions should be specific and factual
- Answers must be directly supported by the context
- Vary question difficulty (easy, medium, hard)
- Use different question types (what, how, why, when, who)
- Do NOT include questions that require external knowledge

Document chunk:
\"\"\"
{context}
\"\"\"

Generate {count} question-answer pairs as a JSON array:"""


class QuestionGenerator:
    """Generates question-answer pairs from document chunks.

    Uses an LLM provider to create standard test cases for RAG evaluation.
    Each question is designed to be answerable from the provided context.

    Usage::

        generator = QuestionGenerator(llm_provider=openai_provider)
        test_cases = await generator.generate(
            context="The quick brown fox jumps over the lazy dog.",
            count=3,
            source_document="example.txt",
            chunk_index=0,
        )
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the question generator.

        Args:
            llm_provider: LLM provider for question generation.
        """
        self._llm = llm_provider

    async def generate(
        self,
        context: str,
        count: int = 3,
        source_document: str = "",
        chunk_index: int = 0,
    ) -> list[TestCase]:
        """Generate question-answer pairs from a document chunk.

        Args:
            context: The document chunk text.
            count: Number of questions to generate.
            source_document: Path or identifier of the source document.
            chunk_index: Index of the chunk within the source document.

        Returns:
            List of TestCase instances with questions and ground truth answers.

        Raises:
            SynthesisExecutionError: If generation or parsing fails.
        """
        if not context.strip():
            logger.warning("Empty context provided, skipping question generation")
            return []

        prompt = _QUESTION_GENERATION_PROMPT.format(
            count=count,
            context=context.strip(),
        )

        try:
            raw_response = await self._llm.generate(prompt)
        except Exception as e:
            raise SynthesisExecutionError(
                message=f"LLM generation failed: {e}",
                original_error=e,
                details={"source_document": source_document, "chunk_index": chunk_index},
            ) from e

        return self._parse_response(
            raw_response,
            context=context,
            source_document=source_document,
            chunk_index=chunk_index,
        )

    def _parse_response(
        self,
        raw_response: str,
        context: str,
        source_document: str,
        chunk_index: int,
    ) -> list[TestCase]:
        """Parse the LLM response into TestCase instances.

        Args:
            raw_response: Raw text response from the LLM.
            context: The original document chunk.
            source_document: Source document identifier.
            chunk_index: Chunk index.

        Returns:
            List of parsed TestCase instances.

        Raises:
            SynthesisExecutionError: If parsing fails.
        """
        try:
            import re as _re

            # Extract JSON from response (handle markdown code blocks)
            text = raw_response.strip()
            if text.startswith("```"):
                # Remove markdown code fence
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            # Try to find JSON array in the response
            # Look for the first [ and last ] to extract the JSON array
            start_idx = text.find("[")
            end_idx = text.rfind("]")
            if start_idx != -1 and end_idx > start_idx:
                text = text[start_idx : end_idx + 1]

            # Fix common JSON issues from LLM output
            # Remove trailing commas before ] or }
            text = _re.sub(r",\s*([}\]])", r"\1", text)
            # Replace single quotes with double quotes for JSON keys/values
            # (only if the text doesn't already use double quotes properly)
            if "'" in text and '"' not in text:
                text = text.replace("'", '"')
            # Remove any control characters
            text = _re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
            # Fix unescaped newlines in strings
            text = _re.sub(r'(?<!\\)\n', '\\n', text)

            data = json.loads(text)

            if not isinstance(data, list):
                raise SynthesisExecutionError(
                    message="Expected JSON array from LLM",
                    details={"response_type": type(data).__name__},
                )

            test_cases: list[TestCase] = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                question = item.get("question", "").strip()
                answer = item.get("answer", "").strip()
                if question and answer:
                    test_cases.append(
                        TestCase(
                            question=question,
                            ground_truth=answer,
                            context=context,
                            test_type=TestCaseType.STANDARD,
                            source_document=source_document,
                            chunk_index=chunk_index,
                        )
                    )

            return test_cases

        except json.JSONDecodeError as e:
            raise SynthesisExecutionError(
                message=f"Failed to parse LLM response as JSON: {e}",
                original_error=e,
                details={"response_preview": raw_response[:200]},
            ) from e
