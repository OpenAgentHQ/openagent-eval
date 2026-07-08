"""Shared fixtures for CLI integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from openagent_eval.cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    """Create a Typer CliRunner for command invocation."""
    return CliRunner()


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    """Create a minimal valid config.yaml for testing."""
    config_content = """\
dataset: data/questions.json
llm:
  provider: openai
  model: gpt-4o
retriever:
  provider: chroma
metrics:
  - faithfulness
  - latency
output: terminal
output_dir: ./reports
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content, encoding="utf-8")
    return config_path


@pytest.fixture
def sample_dataset(tmp_path: Path) -> Path:
    """Create a minimal valid dataset JSON for testing."""
    import json

    dataset = [
        {
            "question": "What is Python?",
            "ground_truth": "Python is a programming language.",
            "context": "Python is a high-level programming language.",
        },
        {
            "question": "What ispytest?",
            "ground_truth": "pytest is a testing framework.",
            "context": "pytest is a Python testing framework.",
        },
    ]

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dataset_path = data_dir / "questions.json"
    dataset_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    return dataset_path


@pytest.fixture
def reports_dir(tmp_path: Path) -> Path:
    """Create a temporary reports directory."""
    reports = tmp_path / "reports"
    reports.mkdir()
    return reports
