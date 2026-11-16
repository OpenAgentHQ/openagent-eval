"""Tests for oaeval doctor command."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from openagent_eval.cli.main import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


def test_doctor_checks_env(runner: CliRunner) -> None:
    """doctor command verifies environment and dependencies."""
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    # Should display environment status
    assert "Environment Status" in result.output or "Python" in result.output


def test_doctor_verbose(runner: CliRunner) -> None:
    """doctor command shows detailed info with --verbose flag."""
    result = runner.invoke(app, ["doctor", "--verbose"])

    assert result.exit_code == 0
    # Verbose should show more details
    assert "Python" in result.output


def test_doctor_shows_api_keys(runner: CliRunner) -> None:
    """doctor command checks API key availability."""
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    # Should show API key status table
    assert "API Key" in result.output or "OpenAI" in result.output


def test_doctor_warns_for_missing_configured_provider_extras(
    runner: CliRunner, tmp_path
) -> None:
    """doctor command reports install commands for configured missing extras."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """\
dataset: data/questions.json
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
retriever:
  provider: qdrant
  settings:
    collection_name: docs
metrics:
  - latency
""",
        encoding="utf-8",
    )

    def fake_find_spec(module_name: str):
        if module_name in {"anthropic", "qdrant_client"}:
            return None
        return object()

    with patch(
        "openagent_eval.cli.commands.doctor.importlib.util.find_spec",
        side_effect=fake_find_spec,
    ):
        result = runner.invoke(app, ["doctor"], env={"OAEVAL_CONFIG": str(config_path)})

    assert result.exit_code == 0
    assert "LLM: anthropic" in result.output
    assert 'pip install "openagent-eval[providers]"' in result.output
    assert "Retriever: qdrant" in result.output
    assert 'pip install "openagent-eval[qdrant]"' in result.output
