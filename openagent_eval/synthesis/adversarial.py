"""Adversarial test case generator — creates tricky edge cases.

Generates unanswerable, ambiguous, misleading, multi-hop, and counterfactual
questions to stress-test RAG systems beyond standard Q&A.
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
# Prompt templates for each adversarial type
# ---------------------------------------------------------------------------

_ADVERSARIAL_PROMPTS: dict[TestCaseType, str] = {
    TestCaseType.UNANSWERABLE: """\
You are a test case generator for a RAG evaluation system.

Given the following document chunk, generate {count} UNANSWERABLE questions.
These are questions whose answers CANNOT be determined from the provided context.

Return a JSON array of objects with "question" and "answer" keys.
For unanswerable questions, set "answer" to an empty string "".

Example:
[
  {{"question": "What is the revenue for 2025?", "answer": ""}},
  {{"question": "Who is the CTO of the company?", "answer": ""}}
]

Rules:
- Questions should SEEM related to the topic but require external information
- Do NOT include questions that CAN be answered from the context
- The question should be specific enough that a human would say "I can't answer that from this text"

Document chunk:
\"\"\"
{context}
\"\"\"

Generate {count} unanswerable question-answer pairs as a JSON array:""",

    TestCaseType.AMBIGUOUS: """\
You are a test case generator for a RAG evaluation system.

Given the following document chunk, generate {count} AMBIGUOUS questions.
These are questions with multiple valid interpretations.

Return a JSON array of objects with "question" and "answer" keys.
For ambiguous questions, provide ONE valid interpretation as the answer.

Example:
[
  {{"question": "What about the results?", "answer": "The results showed a 15% improvement."}}
]

Rules:
- Questions should have pronouns or references that could mean multiple things
- The question should be grammatically correct but unclear in meaning
- Provide one valid interpretation as the ground truth

Document chunk:
\"\"\"
{context}
\"\"\"

Generate {count} ambiguous question-answer pairs as a JSON array:""",

    TestCaseType.MISLEADING: """\
You are a test case generator for a RAG evaluation system.

Given the following document chunk, generate {count} MISLEADING questions.
These questions tempt the model to hallucinate by referencing plausible but incorrect information.

Return a JSON array of objects with "question" and "answer" keys.
The answer should indicate that the premise is incorrect or not supported.

Example:
[
  {{"question": "Why did the project fail last quarter?", "answer": "The provided text does not mention any project failure."}}
]

Rules:
- Questions should assume something that isn't in the text
- The correct answer should point out the false assumption
- Make the false premise sound plausible

Document chunk:
\"\"\"
{context}
\"\"\"

Generate {count} misleading question-answer pairs as a JSON array:""",

    TestCaseType.MULTI_HOP: """\
You are a test case generator for a RAG evaluation system.

Given the following document chunk, generate {count} MULTI-HOP questions.
These require connecting information from different parts of the text.

Return a JSON array of objects with "question" and "answer" keys.

Example:
[
  {{"question": "How does X relate to Y mentioned earlier?", "answer": "X is the predecessor of Y because..."}}
]

Rules:
- Questions should require combining at least two pieces of information
- The answer must synthesize multiple facts from the context
- Make the reasoning chain clear in the answer

Document chunk:
\"\"\"
{context}
\"\"\"

Generate {count} multi-hop question-answer pairs as a JSON array:""",

    TestCaseType.COUNTERFACTUAL: """\
You are a test case generator for a RAG evaluation system.

Given the following document chunk, generate {count} COUNTERFACTUAL questions.
These are based on false premises that contradict the text.

Return a JSON array of objects with "question" and "answer" keys.
The answer should correct the false premise.

Example:
[
  {{"question": "How did the team handle the budget surplus?", "answer": "The text states there was a budget deficit, not a surplus."}}
]

Rules:
- Questions should contain a false claim about the text
- The correct answer should identify and correct the false premise
- Make the false claim sound believable

Document chunk:
\"\"\"
{context}
\"\"\"

Generate {count} counterfactual question-answer pairs as a JSON array:""",
}


class AdversarialTestCaseGenerator:
    """Generates adversarial test cases for RAG stress testing.

    Creates unanswerable, ambiguous, misleading, multi-hop, and counterfactual
    questions that reveal weaknesses in RAG systems.

    Usage::

        generator = AdversarialTestCaseGenerator(llm_provider=openai_provider)
        test_cases = await generator.generate(
            context="The quick brown fox jumps over the lazy dog.",
            test_type=TestCaseType.UNANSWERABLE,
            count=2,
        )
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the adversarial generator.

        Args:
            llm_provider: LLM provider for adversarial question generation.
        """
        self._llm = llm_provider

    async def generate(
        self,
        context: str,
        test_type: TestCaseType = TestCaseType.UNANSWERABLE,
        count: int = 2,
        source_document: str = "",
        chunk_index: int = 0,
    ) -> list[TestCase]:
        """Generate adversarial test cases from a document chunk.

        Args:
            context: The document chunk text.
            test_type: Type of adversarial test case to generate.
            count: Number of test cases to generate.
            source_document: Path or identifier of the source document.
            chunk_index: Index of the chunk within the source document.

        Returns:
            List of TestCase instances with adversarial questions.

        Raises:
            SynthesisExecutionError: If generation or parsing fails.
        """
        if not context.strip():
            logger.warning("Empty context provided, skipping adversarial generation")
            return []

        prompt_template = _ADVERSARIAL_PROMPTS.get(test_type)
        if prompt_template is None:
            raise SynthesisExecutionError(
                message=f"Unsupported adversarial test type: {test_type}",
                details={"supported_types": [t.value for t in TestCaseType]},
            )

        prompt = prompt_template.format(count=count, context=context.strip())

        try:
            raw_response = await self._llm.generate(prompt)
        except Exception as e:
            raise SynthesisExecutionError(
                message=f"LLM generation failed for adversarial {test_type.value}: {e}",
                original_error=e,
                details={
                    "source_document": source_document,
                    "chunk_index": chunk_index,
                    "test_type": test_type.value,
                },
            ) from e

        return self._parse_response(
            raw_response,
            context=context,
            test_type=test_type,
            source_document=source_document,
            chunk_index=chunk_index,
        )

    async def generate_all_types(
        self,
        context: str,
        count_per_type: int = 1,
        source_document: str = "",
        chunk_index: int = 0,
    ) -> list[TestCase]:
        """Generate adversarial test cases for all types.

        Args:
            context: The document chunk text.
            count_per_type: Number of test cases per adversarial type.
            source_document: Source document identifier.
            chunk_index: Chunk index.

        Returns:
            Combined list of all adversarial test case types.
        """
        all_cases: list[TestCase] = []
        for test_type in TestCaseType:
            if test_type == TestCaseType.STANDARD:
                continue  # Standard is handled by QuestionGenerator
            cases = await self.generate(
                context=context,
                test_type=test_type,
                count=count_per_type,
                source_document=source_document,
                chunk_index=chunk_index,
            )
            all_cases.extend(cases)
        return all_cases

    def _parse_response(
        self,
        raw_response: str,
        context: str,
        test_type: TestCaseType,
        source_document: str,
        chunk_index: int,
    ) -> list[TestCase]:
        """Parse the LLM response into TestCase instances.

        Args:
            raw_response: Raw text response from the LLM.
            context: The original document chunk.
            test_type: The adversarial test type.
            source_document: Source document identifier.
            chunk_index: Chunk index.

        Returns:
            List of parsed TestCase instances.

        Raises:
            SynthesisExecutionError: If parsing fails.
        """
        import re as _re

        test_cases: list[TestCase] = []

        # Strategy 1: Try to extract JSON array and parse it
        try:
            text = raw_response.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            start_idx = text.find("[")
            end_idx = text.rfind("]")
            if start_idx != -1 and end_idx > start_idx:
                text = text[start_idx : end_idx + 1]

            # Clean the JSON
            text = _re.sub(r",\s*([}\]])", r"\1", text)
            text = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

            data = json.loads(text)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        question = item.get("question", "").strip()
                        answer = item.get("answer", "").strip()
                        if question:
                            test_cases.append(
                                TestCase(
                                    question=question,
                                    ground_truth=answer,
                                    context=context,
                                    test_type=test_type,
                                    source_document=source_document,
                                    chunk_index=chunk_index,
                                )
                            )
                if test_cases:
                    return test_cases
        except (json.JSONDecodeError, ValueError):
            pass

        # Strategy 2: Extract question-answer pairs using regex
        qa_pattern = _re.compile(
            r'\{\s*"question"\s*:\s*"([^"]+)"\s*,\s*"answer"\s*:\s*"([^"]+)"\s*\}',
            _re.IGNORECASE,
        )
        matches = qa_pattern.findall(raw_response)

        for question, answer in matches:
            question = question.strip()
            answer = answer.strip()
            if question:
                test_cases.append(
                    TestCase(
                        question=question,
                        ground_truth=answer,
                        context=context,
                        test_type=test_type,
                        source_document=source_document,
                        chunk_index=chunk_index,
                    )
                )

        if test_cases:
            return test_cases

        # Strategy 3: Try to find any question-answer patterns
        question_pattern = _re.compile(r'"question"\s*:\s*"([^"]+)"', _re.IGNORECASE)
        answer_pattern = _re.compile(r'"answer"\s*:\s*"([^"]+)"', _re.IGNORECASE)

        questions = question_pattern.findall(raw_response)
        answers = answer_pattern.findall(raw_response)

        for q, a in zip(questions, answers):
            q = q.strip()
            a = a.strip()
            if q:
                test_cases.append(
                    TestCase(
                        question=q,
                        ground_truth=a,
                        context=context,
                        test_type=test_type,
                        source_document=source_document,
                        chunk_index=chunk_index,
                    )
                )

        if test_cases:
            return test_cases

        # All strategies failed
        raise SynthesisExecutionError(
            message="Failed to parse adversarial LLM response",
            details={
                "response_preview": raw_response[:200],
                "test_type": test_type.value,
            },
        )
