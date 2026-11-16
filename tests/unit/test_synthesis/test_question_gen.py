"""Tests for QuestionGenerator."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from openagent_eval.exceptions.synthesis import SynthesisExecutionError
from openagent_eval.synthesis.models import TestCaseType
from openagent_eval.synthesis.question_gen import QuestionGenerator


def _make_mock_llm(response: str | Exception = "[]") -> MagicMock:
    """Create a mock LLM provider."""
    mock = MagicMock()
    mock.generate = AsyncMock()
    if isinstance(response, Exception):
        mock.generate.side_effect = response
    else:
        mock.generate.return_value = response
    return mock


class TestQuestionGenerator:
    """Tests for QuestionGenerator."""

    def test_init(self) -> None:
        """Test initialization."""
        mock_llm = _make_mock_llm()
        gen = QuestionGenerator(mock_llm)
        assert gen._llm is mock_llm

    @pytest.mark.asyncio
    async def test_generate_empty_context(self) -> None:
        """Test that empty context returns empty list."""
        mock_llm = _make_mock_llm()
        gen = QuestionGenerator(mock_llm)
        result = await gen.generate(context="", count=3)
        assert result == []
        mock_llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_whitespace_context(self) -> None:
        """Test that whitespace-only context returns empty list."""
        mock_llm = _make_mock_llm()
        gen = QuestionGenerator(mock_llm)
        result = await gen.generate(context="   \n  \t  ", count=3)
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_success(self) -> None:
        """Test successful question generation."""
        llm_response = json.dumps(
            [
                {
                    "question": "What is Python?",
                    "answer": "Python is a programming language.",
                },
                {
                    "question": "Is Python popular?",
                    "answer": "Yes, Python is widely used.",
                },
            ]
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(
            context="Python is a popular programming language.",
            count=2,
            source_document="test.txt",
            chunk_index=0,
        )

        assert len(result) == 2
        assert result[0].question == "What is Python?"
        assert result[0].ground_truth == "Python is a programming language."
        assert result[0].test_type == TestCaseType.STANDARD
        assert result[0].source_document == "test.txt"
        assert result[0].chunk_index == 0
        assert result[0].context == "Python is a popular programming language."

    @pytest.mark.asyncio
    async def test_generate_with_markdown_code_block(self) -> None:
        """Test parsing LLM response wrapped in markdown code block."""
        llm_response = '```json\n[\n  {"question": "Test?", "answer": "Test."}\n]\n```'
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test context.", count=1)

        assert len(result) == 1
        assert result[0].question == "Test?"

    @pytest.mark.asyncio
    async def test_generate_filters_empty_questions(self) -> None:
        """Test that empty questions or answers are filtered out."""
        llm_response = json.dumps(
            [
                {"question": "Valid?", "answer": "Valid answer."},
                {"question": "", "answer": "No question."},
                {"question": "No answer?", "answer": ""},
                {"question": "Also valid?", "answer": "Also valid."},
            ]
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test.", count=4)

        assert len(result) == 2
        assert result[0].question == "Valid?"
        assert result[1].question == "Also valid?"

    @pytest.mark.asyncio
    async def test_generate_llm_failure(self) -> None:
        """Test handling of LLM generation failure."""
        mock_llm = _make_mock_llm(RuntimeError("API error"))
        gen = QuestionGenerator(mock_llm)

        with pytest.raises(SynthesisExecutionError, match="LLM generation failed"):
            await gen.generate(context="Test context.", count=1)

    @pytest.mark.asyncio
    async def test_generate_invalid_json(self) -> None:
        """Test handling of invalid JSON response."""
        mock_llm = _make_mock_llm("not valid json {{{")
        gen = QuestionGenerator(mock_llm)

        with pytest.raises(SynthesisExecutionError, match="Failed to parse"):
            await gen.generate(context="Test context.", count=1)

    @pytest.mark.asyncio
    async def test_generate_non_array_response(self) -> None:
        """Test handling of non-array JSON response."""
        mock_llm = _make_mock_llm(json.dumps({"question": "Test?"}))
        gen = QuestionGenerator(mock_llm)

        with pytest.raises(SynthesisExecutionError, match="Failed to parse"):
            await gen.generate(context="Test context.", count=1)

    @pytest.mark.asyncio
    async def test_generate_non_dict_items_filtered(self) -> None:
        """Test that non-dict items in the array are filtered out."""
        llm_response = json.dumps(
            [
                "not a dict",
                {"question": "Valid?", "answer": "Valid answer."},
                42,
            ]
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test.", count=3)

        assert len(result) == 1
        assert result[0].question == "Valid?"

    @pytest.mark.asyncio
    async def test_generate_json_with_trailing_comma(self) -> None:
        """Test parsing JSON with trailing commas before closing bracket."""
        llm_response = '[\n  {"question": "Test?", "answer": "Test."},\n]'
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test context.", count=1)

        assert len(result) == 1
        assert result[0].question == "Test?"

    @pytest.mark.asyncio
    async def test_generate_json_with_extra_text_around(self) -> None:
        """Test parsing JSON when LLM wraps it with extra text."""
        llm_response = 'Here are some questions:\n[\n  {"question": "What is Python?", "answer": "A language."}\n]\nHope this helps!'
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Python is a language.", count=1)

        assert len(result) == 1
        assert result[0].question == "What is Python?"

    @pytest.mark.asyncio
    async def test_generate_json_with_single_quotes(self) -> None:
        """Test parsing JSON with single quotes instead of double quotes."""
        llm_response = "[{'question': 'What is Python?', 'answer': 'A language.'}]"
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Python is a language.", count=1)

        assert len(result) == 1
        assert result[0].question == "What is Python?"

    @pytest.mark.asyncio
    async def test_generate_json_in_markdown_code_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        llm_response = '```json\n[\n  {"question": "Test?", "answer": "Test."}\n]\n```'
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test context.", count=1)

        assert len(result) == 1
        assert result[0].question == "Test?"

    @pytest.mark.asyncio
    async def test_generate_json_with_multiple_items_and_trailing_comma(self) -> None:
        """Test parsing JSON with multiple items and trailing comma."""
        llm_response = '[\n  {"question": "Q1?", "answer": "A1."},\n  {"question": "Q2?", "answer": "A2."},\n]'
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test.", count=2)

        assert len(result) == 2
        assert result[0].question == "Q1?"
        assert result[1].question == "Q2?"

    @pytest.mark.asyncio
    async def test_generate_single_json_object(self) -> None:
        """Characterization: parser accepts a single JSON object response."""
        llm_response = '{"question": "Single?", "answer": "Single answer."}'
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test.", count=1)

        assert len(result) == 1
        assert result[0].question == "Single?"
        assert result[0].ground_truth == "Single answer."

    @pytest.mark.asyncio
    async def test_generate_concatenated_json_objects(self) -> None:
        """Characterization: parser accepts concatenated JSON objects."""
        llm_response = (
            '{"question": "Q1?", "answer": "A1."}{"question": "Q2?", "answer": "A2."}'
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test.", count=2)

        assert len(result) == 2
        assert result[0].question == "Q1?"
        assert result[1].question == "Q2?"

    @pytest.mark.asyncio
    async def test_generate_regex_tier_with_nested_braces(self) -> None:
        """Characterization: parser falls back to regex tier for nested braces."""
        llm_response = '{"question": "Q?", "answer": "{nested}"}'
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test.", count=1)

        assert len(result) == 1
        assert result[0].question == "Q?"
        assert result[0].ground_truth == "{nested}"

    @pytest.mark.asyncio
    async def test_generate_final_fallback_tier(self) -> None:
        """Characterization: parser uses final fallback for loose Q/A patterns."""
        llm_response = (
            'Here is a question:\n"question": "Fallback?"\n"answer": "Fallback answer."'
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        result = await gen.generate(context="Test.", count=1)

        assert len(result) == 1
        assert result[0].question == "Fallback?"
        assert result[0].ground_truth == "Fallback answer."

    @pytest.mark.asyncio
    async def test_generate_rejects_empty_answer_single_object(self) -> None:
        """Characterization: question_gen rejects a single object with empty answer."""
        llm_response = '{"question": "Q?", "answer": ""}'
        mock_llm = _make_mock_llm(llm_response)
        gen = QuestionGenerator(mock_llm)

        with pytest.raises(SynthesisExecutionError, match="Failed to parse"):
            await gen.generate(context="Test.", count=1)
