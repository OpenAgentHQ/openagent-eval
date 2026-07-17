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
            context=context.strip().replace("{", "{{").replace("}", "}}"),
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
        import re as _re

        test_cases: list[TestCase] = []
        seen_questions: set[str] = set()

        def _add_test_case(question: str, answer: str) -> None:
            """Add test case if question not already seen."""
            if question and question not in seen_questions:
                seen_questions.add(question)
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

        # Clean code blocks and normalize text
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        # Normalize Python-style single quotes to JSON double quotes,
        # but only when text uses Python-style dict formatting (single-quoted keys),
        # to avoid breaking apostrophes in valid JSON (e.g. "company's").
        has_python_style = bool(_re.search(r"\{\s*'[^']*'\s*:", text))
        if has_python_style:
            text = text.replace("'", '"')

        # Strategy 0: Try parsing as a single JSON object (non-array response)
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                question = data.get("question", "").strip()
                answer = data.get("answer", "").strip()
                if question and answer:
                    _add_test_case(question, answer)
                    # Don't return here - continue to other strategies to find more questions
        except (json.JSONDecodeError, ValueError):
            pass

        # Strategy 1: Try to extract JSON array and parse it
        try:
            start_idx = text.find("[")
            end_idx = text.rfind("]")
            if start_idx != -1 and end_idx > start_idx:
                array_text = text[start_idx : end_idx + 1]
            else:
                array_text = text

            # Clean the JSON
            array_text = _re.sub(r",\s*([}\]])", r"\1", array_text)
            array_text = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", array_text)

            data = json.loads(array_text)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        question = item.get("question", "").strip()
                        answer = item.get("answer", "").strip()
                        if question and answer:
                            _add_test_case(question, answer)
                if test_cases:
                    return test_cases
        except (json.JSONDecodeError, ValueError):
            pass

        # Strategy 2: Extract individual JSON objects and parse them
        try:
            # Find all JSON objects in the response
            obj_pattern = _re.compile(r'\{[^{}]+\}', _re.DOTALL)
            objects = obj_pattern.findall(text)

            for obj_str in objects:
                try:
                    # Clean the object
                    obj_str = _re.sub(r",\s*([}\]])", r"\1", obj_str)
                    obj_str = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", obj_str)

                    item = json.loads(obj_str)
                    question = item.get("question", "").strip()
                    answer = item.get("answer", "").strip()
                    if question and answer:
                        _add_test_case(question, answer)
                except (json.JSONDecodeError, ValueError):
                    continue

            if test_cases:
                return test_cases
        except Exception:
            pass

        # Strategy 3: Extract question-answer pairs using regex
        qa_pattern = _re.compile(
            r'\{\s*"question"\s*:\s*"([^"]+)"\s*,\s*"answer"\s*:\s*"([^"]+)"\s*\}',
            _re.IGNORECASE,
        )
        matches = qa_pattern.findall(text)

        for question, answer in matches:
            question = question.strip()
            answer = answer.strip()
            if question and answer:
                _add_test_case(question, answer)

        if test_cases:
            return test_cases

        # Strategy 4: Try to find any question-answer patterns
        question_pattern = _re.compile(r'"question"\s*:\s*"([^"]+)"', _re.IGNORECASE)
        answer_pattern = _re.compile(r'"answer"\s*:\s*"([^"]+)"', _re.IGNORECASE)

        questions = question_pattern.findall(text)
        answers = answer_pattern.findall(text)

        for q, a in zip(questions, answers, strict=False):
            q = q.strip()
            a = a.strip()
            if q and a:
                _add_test_case(q, a)

        if test_cases:
            return test_cases

        # All strategies failed
        raise SynthesisExecutionError(
            message="Failed to parse LLM response",
            details={"response_preview": raw_response[:200]},
        )
