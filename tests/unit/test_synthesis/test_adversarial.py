"""Tests for AdversarialTestCaseGenerator."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from openagent_eval.exceptions.synthesis import SynthesisExecutionError
from openagent_eval.synthesis.adversarial import AdversarialTestCaseGenerator
from openagent_eval.synthesis.models import TestCaseType


def _make_mock_llm(response: str | Exception = "[]") -> MagicMock:
    """Create a mock LLM provider."""
    mock = MagicMock()
    mock.generate = AsyncMock()
    if isinstance(response, Exception):
        mock.generate.side_effect = response
    else:
        mock.generate.return_value = response
    return mock


class TestAdversarialTestCaseGenerator:
    """Tests for AdversarialTestCaseGenerator."""

    def test_init(self) -> None:
        """Test initialization."""
        mock_llm = _make_mock_llm()
        gen = AdversarialTestCaseGenerator(mock_llm)
        assert gen._llm is mock_llm

    @pytest.mark.asyncio
    async def test_generate_empty_context(self) -> None:
        """Test that empty context returns empty list."""
        mock_llm = _make_mock_llm()
        gen = AdversarialTestCaseGenerator(mock_llm)
        result = await gen.generate(
            context="",
            test_type=TestCaseType.UNANSWERABLE,
        )
        assert result == []
        mock_llm.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_unanswerable(self) -> None:
        """Test unanswerable question generation."""
        llm_response = json.dumps(
            [
                {
                    "question": "What is the company's revenue for 2025?",
                    "answer": "",
                },
            ]
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="The company was founded in 2020.",
            test_type=TestCaseType.UNANSWERABLE,
            count=1,
            source_document="company.txt",
            chunk_index=0,
        )

        assert len(result) == 1
        assert "revenue" in result[0].question.lower()
        assert result[0].ground_truth == ""
        assert result[0].test_type == TestCaseType.UNANSWERABLE

    @pytest.mark.asyncio
    async def test_generate_misleading(self) -> None:
        """Test misleading question generation."""
        llm_response = json.dumps(
            [
                {
                    "question": "Why did the project fail last quarter?",
                    "answer": "The provided text does not mention any project failure.",
                },
            ]
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="The project was completed successfully on time.",
            test_type=TestCaseType.MISLEADING,
            count=1,
        )

        assert len(result) == 1
        assert result[0].test_type == TestCaseType.MISLEADING

    @pytest.mark.asyncio
    async def test_generate_counterfactual(self) -> None:
        """Test counterfactual question generation."""
        llm_response = json.dumps(
            [
                {
                    "question": "How did the team handle the budget surplus?",
                    "answer": "The text states there was a budget deficit, not a surplus.",
                },
            ]
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="The team managed a budget deficit of $50,000.",
            test_type=TestCaseType.COUNTERFACTUAL,
            count=1,
        )

        assert len(result) == 1
        assert result[0].test_type == TestCaseType.COUNTERFACTUAL

    @pytest.mark.asyncio
    async def test_generate_unsupported_type(self) -> None:
        """Test generation with unsupported test type."""
        mock_llm = _make_mock_llm()
        gen = AdversarialTestCaseGenerator(mock_llm)

        with pytest.raises(
            SynthesisExecutionError, match="Unsupported adversarial test type"
        ):
            await gen.generate(
                context="Test context.",
                test_type="invalid_type",  # type: ignore[arg-type]
            )

    @pytest.mark.asyncio
    async def test_generate_llm_failure(self) -> None:
        """Test handling of LLM generation failure."""
        mock_llm = _make_mock_llm(RuntimeError("API error"))
        gen = AdversarialTestCaseGenerator(mock_llm)

        with pytest.raises(SynthesisExecutionError, match="LLM generation failed"):
            await gen.generate(
                context="Test context.",
                test_type=TestCaseType.UNANSWERABLE,
            )

    @pytest.mark.asyncio
    async def test_generate_invalid_json(self) -> None:
        """Test handling of invalid JSON response."""
        mock_llm = _make_mock_llm("not valid json {{{")
        gen = AdversarialTestCaseGenerator(mock_llm)

        with pytest.raises(SynthesisExecutionError, match="Failed to parse"):
            await gen.generate(
                context="Test context.",
                test_type=TestCaseType.AMBIGUOUS,
            )

    @pytest.mark.asyncio
    async def test_generate_all_types(self) -> None:
        """Test generating all adversarial types."""
        responses = {}
        for test_type in TestCaseType:
            if test_type == TestCaseType.STANDARD:
                continue
            responses[test_type] = json.dumps(
                [
                    {
                        "question": f"Test {test_type.value}?",
                        "answer": f"Answer for {test_type.value}.",
                    },
                ]
            )

        call_count = 0
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock()

        async def mock_generate(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            # Return a response based on which type we're generating
            for tt, resp in responses.items():
                if tt.value in prompt.lower():
                    return resp
            # Default fallback
            return json.dumps([{"question": "Fallback?", "answer": "Fallback."}])

        mock_llm.generate = mock_generate
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate_all_types(
            context="Test context for all types.",
            count_per_type=1,
        )

        # Should have 5 adversarial types (all except STANDARD)
        assert len(result) == 5
        types_generated = {tc.test_type for tc in result}
        assert TestCaseType.UNANSWERABLE in types_generated
        assert TestCaseType.AMBIGUOUS in types_generated
        assert TestCaseType.MISLEADING in types_generated
        assert TestCaseType.MULTI_HOP in types_generated
        assert TestCaseType.COUNTERFACTUAL in types_generated

    @pytest.mark.asyncio
    async def test_generate_filters_empty_questions(self) -> None:
        """Test that empty questions are filtered out."""
        llm_response = json.dumps(
            [
                {"question": "Valid?", "answer": "Valid."},
                {"question": "", "answer": "No question."},
                {"question": "Also valid?", "answer": "Also valid."},
            ]
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test.",
            test_type=TestCaseType.UNANSWERABLE,
            count=3,
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_generate_preserves_metadata(self) -> None:
        """Test that metadata is preserved in generated test cases."""
        llm_response = json.dumps(
            [
                {"question": "Test?", "answer": "Answer."},
            ]
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test context.",
            test_type=TestCaseType.MULTI_HOP,
            source_document="doc.txt",
            chunk_index=5,
        )

        assert len(result) == 1
        assert result[0].source_document == "doc.txt"
        assert result[0].chunk_index == 5
        assert result[0].context == "Test context."

    @pytest.mark.asyncio
    async def test_generate_json_with_trailing_comma(self) -> None:
        """Test parsing JSON with trailing commas before closing bracket."""
        llm_response = '[\n  {"question": "What is X?", "answer": "X is Y."},\n]'
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test context.",
            test_type=TestCaseType.UNANSWERABLE,
            count=1,
        )

        assert len(result) == 1
        assert result[0].question == "What is X?"

    @pytest.mark.asyncio
    async def test_generate_json_with_extra_text_around(self) -> None:
        """Test parsing JSON when LLM wraps it with extra text."""
        llm_response = 'Here are unanswerable questions:\n[\n  {"question": "What is the budget?", "answer": ""}\n]\nLet me know if you need more.'
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="The project was completed.",
            test_type=TestCaseType.UNANSWERABLE,
            count=1,
        )

        assert len(result) == 1
        assert "budget" in result[0].question.lower()

    @pytest.mark.asyncio
    async def test_generate_json_with_single_quotes(self) -> None:
        """Test parsing JSON with single quotes instead of double quotes."""
        llm_response = "[{'question': 'What is X?', 'answer': 'Not mentioned.'}]"
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test context.",
            test_type=TestCaseType.MISLEADING,
            count=1,
        )

        assert len(result) == 1
        assert result[0].question == "What is X?"

    @pytest.mark.asyncio
    async def test_generate_json_in_markdown_code_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        llm_response = '```json\n[\n  {"question": "Why did it fail?", "answer": "Text does not say."}\n]\n```'
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="It succeeded.",
            test_type=TestCaseType.MISLEADING,
            count=1,
        )

        assert len(result) == 1
        assert "fail" in result[0].question.lower()

    @pytest.mark.asyncio
    async def test_generate_json_with_multiple_items_and_trailing_comma(self) -> None:
        """Test parsing JSON with multiple items and trailing comma."""
        llm_response = '[\n  {"question": "Q1?", "answer": ""},\n  {"question": "Q2?", "answer": ""},\n]'
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test.",
            test_type=TestCaseType.UNANSWERABLE,
            count=2,
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_generate_single_json_object(self) -> None:
        """Characterization: parser accepts a single JSON object response."""
        llm_response = '{"question": "Single?", "answer": "Single answer."}'
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test.",
            test_type=TestCaseType.MISLEADING,
            count=1,
        )

        assert len(result) == 1
        assert result[0].question == "Single?"
        assert result[0].ground_truth == "Single answer."
        assert result[0].test_type == TestCaseType.MISLEADING

    @pytest.mark.asyncio
    async def test_generate_concatenated_json_objects(self) -> None:
        """Characterization: parser accepts concatenated JSON objects."""
        llm_response = (
            '{"question": "Q1?", "answer": ""}{"question": "Q2?", "answer": ""}'
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test.",
            test_type=TestCaseType.UNANSWERABLE,
            count=2,
        )

        assert len(result) == 2
        assert result[0].question == "Q1?"
        assert result[1].question == "Q2?"

    @pytest.mark.asyncio
    async def test_generate_regex_tier_with_nested_braces(self) -> None:
        """Characterization: parser falls back to regex tier for nested braces."""
        llm_response = '{"question": "Q?", "answer": "{nested}"}'
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test.",
            test_type=TestCaseType.AMBIGUOUS,
            count=1,
        )

        assert len(result) == 1
        assert result[0].question == "Q?"
        assert result[0].ground_truth == "{nested}"
        assert result[0].test_type == TestCaseType.AMBIGUOUS

    @pytest.mark.asyncio
    async def test_generate_final_fallback_tier(self) -> None:
        """Characterization: parser uses final fallback for loose Q/A patterns."""
        llm_response = (
            'Here is a question:\n"question": "Fallback?"\n"answer": "Fallback answer."'
        )
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test.",
            test_type=TestCaseType.COUNTERFACTUAL,
            count=1,
        )

        assert len(result) == 1
        assert result[0].question == "Fallback?"
        assert result[0].ground_truth == "Fallback answer."
        assert result[0].test_type == TestCaseType.COUNTERFACTUAL

    @pytest.mark.asyncio
    async def test_generate_accepts_empty_answer_single_object(self) -> None:
        """Characterization: adversarial accepts a single object with empty answer."""
        llm_response = '{"question": "Q?", "answer": ""}'
        mock_llm = _make_mock_llm(llm_response)
        gen = AdversarialTestCaseGenerator(mock_llm)

        result = await gen.generate(
            context="Test.",
            test_type=TestCaseType.UNANSWERABLE,
            count=1,
        )

        assert len(result) == 1
        assert result[0].question == "Q?"
        assert result[0].ground_truth == ""
        assert result[0].test_type == TestCaseType.UNANSWERABLE
