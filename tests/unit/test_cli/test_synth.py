"""Tests for the synthetic data CLI command."""

from __future__ import annotations

import asyncio
import json
import re
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from typer.testing import CliRunner

from openagent_eval.cli.commands.synth import _create_provider
from openagent_eval.cli.main import app
from openagent_eval.exceptions.synthesis import SynthesisError
from openagent_eval.providers.llm.mock import MockLLMProvider
from openagent_eval.synthesis import SyntheticDataset, TestCase, TestCaseType

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def test_create_provider_uses_offline_mock_provider() -> None:
    """The mock CLI option must not fall back to a network provider."""
    provider = _create_provider("mock", "synthetic-test-model")

    assert isinstance(provider, MockLLMProvider)

    response = asyncio.run(provider.generate_with_usage("test prompt"))
    assert response.provider == "mock"
    assert response.model == "synthetic-test-model"


@pytest.fixture
def fake_generator(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Replace SyntheticDataGenerator so no LLM/network call is ever made.

    Yields a holder dict recording every constructed generator instance and its
    constructor kwargs. Set ``holder["generate_error"]`` before invoking the CLI
    to make the (async) generate methods raise, exercising error handling.
    """
    dataset = SyntheticDataset(
        test_cases=[
            TestCase(
                question="What is RAG?",
                ground_truth="Retrieval-Augmented Generation.",
                context="RAG combines retrieval and generation.",
                test_type=TestCaseType.STANDARD,
            ),
        ]
    )
    holder: dict = {"instances": [], "dataset": dataset, "generate_error": None}

    def factory(**kwargs: object) -> SimpleNamespace:
        generate = AsyncMock(return_value=holder["dataset"])
        generate_from_text = AsyncMock(return_value=holder["dataset"])
        if holder["generate_error"] is not None:
            generate.side_effect = holder["generate_error"]
            generate_from_text.side_effect = holder["generate_error"]
        instance = SimpleNamespace(
            init_kwargs=kwargs,
            generate=generate,
            generate_from_text=generate_from_text,
        )
        holder["instances"].append(instance)
        return instance

    monkeypatch.setattr(
        "openagent_eval.cli.commands.synth.SyntheticDataGenerator", factory
    )
    return holder


def test_synth_help_lists_documented_flags() -> None:
    """Help output must expose the command's public flags."""
    result = runner.invoke(app, ["synth", "--help"])
    assert result.exit_code == 0
    output = strip_ansi(result.output)
    for flag in ("--corpus", "--text", "--count", "--adversarial", "--output"):
        assert flag in output
    assert "--llm-provider" in output


def test_synth_requires_corpus_or_text() -> None:
    """Providing neither --corpus nor --text is a usage error (exit 2)."""
    result = runner.invoke(app, ["synth"])
    assert result.exit_code == 2
    assert "--corpus" in result.output or "--text" in result.output


def test_synth_rejects_both_corpus_and_text() -> None:
    """Providing both --corpus and --text is a usage error (exit 2)."""
    result = runner.invoke(
        app,
        ["synth", "--llm-provider", "mock", "--corpus", "docs/", "--text", "hi"],
    )
    assert result.exit_code == 2
    assert "both" in strip_ansi(result.output).lower()


def test_synth_corpus_is_wired_to_generate(fake_generator: dict) -> None:
    """--corpus routes to generator.generate with the parsed arguments."""
    result = runner.invoke(
        app,
        ["synth", "--llm-provider", "mock", "--corpus", "kb/", "--count", "7"],
    )
    assert result.exit_code == 0, result.output

    instance = fake_generator["instances"][0]
    instance.generate.assert_awaited_once()
    instance.generate_from_text.assert_not_awaited()
    kwargs = instance.generate.await_args.kwargs
    assert kwargs["corpus_path"] == "kb/"
    assert kwargs["count"] == 7
    assert kwargs["adversarial"] is False
    assert kwargs["adversarial_types"] is None


def test_synth_text_is_wired_to_generate_from_text(fake_generator: dict) -> None:
    """--text routes to generator.generate_from_text with the inline text."""
    result = runner.invoke(
        app,
        [
            "synth",
            "--llm-provider",
            "mock",
            "--text",
            "Some document body.",
            "--count",
            "3",
        ],
    )
    assert result.exit_code == 0, result.output

    instance = fake_generator["instances"][0]
    instance.generate_from_text.assert_awaited_once()
    instance.generate.assert_not_awaited()
    kwargs = instance.generate_from_text.await_args.kwargs
    assert kwargs["text"] == "Some document body."
    assert kwargs["count"] == 3


def test_synth_default_count_is_ten(fake_generator: dict) -> None:
    """Omitting --count must fall back to the documented default of 10."""
    result = runner.invoke(
        app, ["synth", "--llm-provider", "mock", "--corpus", "kb/"]
    )
    assert result.exit_code == 0, result.output

    kwargs = fake_generator["instances"][0].generate.await_args.kwargs
    assert kwargs["count"] == 10


def test_synth_adversarial_types_are_parsed_and_passed(fake_generator: dict) -> None:
    """--adversarial + --types must reach generate as parsed TestCaseType enums."""
    result = runner.invoke(
        app,
        [
            "synth",
            "--llm-provider",
            "mock",
            "--corpus",
            "kb/",
            "--adversarial",
            "--types",
            "unanswerable,misleading",
        ],
    )
    assert result.exit_code == 0, result.output

    kwargs = fake_generator["instances"][0].generate.await_args.kwargs
    assert kwargs["adversarial"] is True
    assert kwargs["adversarial_types"] == [
        TestCaseType.UNANSWERABLE,
        TestCaseType.MISLEADING,
    ]


def test_synth_invalid_adversarial_type_exits_two(fake_generator: dict) -> None:
    """An unknown adversarial type is a usage error and never calls generate."""
    result = runner.invoke(
        app,
        [
            "synth",
            "--llm-provider",
            "mock",
            "--corpus",
            "kb/",
            "--types",
            "not-a-real-type",
        ],
    )
    assert result.exit_code == 2
    assert "Invalid adversarial type" in strip_ansi(result.output)
    assert fake_generator["instances"] == []


def test_synth_generator_options_are_wired(fake_generator: dict) -> None:
    """Chunking / concurrency flags reach the SyntheticDataGenerator constructor."""
    result = runner.invoke(
        app,
        [
            "synth",
            "--llm-provider",
            "mock",
            "--corpus",
            "kb/",
            "--chunk-size",
            "500",
            "--chunk-overlap",
            "40",
            "--max-concurrent",
            "3",
        ],
    )
    assert result.exit_code == 0, result.output

    init_kwargs = fake_generator["instances"][0].init_kwargs
    assert init_kwargs["chunk_size"] == 500
    assert init_kwargs["chunk_overlap"] == 40
    assert init_kwargs["max_concurrent"] == 3


def test_synth_provider_options_are_wired(fake_generator: dict) -> None:
    """--llm-provider / --llm-model select the provider handed to the generator."""
    result = runner.invoke(
        app,
        [
            "synth",
            "--corpus",
            "kb/",
            "--llm-provider",
            "mock",
            "--llm-model",
            "custom-synth-model",
        ],
    )
    assert result.exit_code == 0, result.output

    provider = fake_generator["instances"][0].init_kwargs["llm_provider"]
    assert isinstance(provider, MockLLMProvider)
    assert provider._model == "custom-synth-model"


def test_synth_synthesis_error_exits_one(fake_generator: dict) -> None:
    """A SynthesisError from generation surfaces as exit code 1 with its message."""
    fake_generator["generate_error"] = SynthesisError("corpus was empty")
    result = runner.invoke(
        app, ["synth", "--llm-provider", "mock", "--corpus", "kb/"]
    )
    assert result.exit_code == 1
    assert "corpus was empty" in strip_ansi(result.output)


def test_synth_output_writes_dataset_file(
    fake_generator: dict, tmp_path: Path
) -> None:
    """--output writes the generated dataset to the requested path as JSON."""
    out_path = tmp_path / "nested" / "dataset.json"
    result = runner.invoke(
        app,
        [
            "synth",
            "--llm-provider",
            "mock",
            "--corpus",
            "kb/",
            "--output",
            str(out_path),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["total_count"] == 1
    assert payload["test_cases"][0]["question"] == "What is RAG?"
