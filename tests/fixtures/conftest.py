"""Pytest configuration and fixtures for OpenAgent Eval tests."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from openagent_eval.config.models import Config, DatasetConfig, LLMConfig, MetricsConfig


@pytest.fixture
def sample_config() -> Config:
    """Create a sample configuration for testing."""
    return Config(
        dataset=DatasetConfig(path="tests/sample_data/test_dataset.json"),
        llm=LLMConfig(provider="openai", model="gpt-4o"),
        metrics=MetricsConfig(
            retrieval=["context_precision", "context_recall"],
            generation=["faithfulness"],
        ),
    )


@pytest.fixture
def sample_dataset() -> list[dict]:
    """Create a sample dataset for testing."""
    return [
        {
            "question": "What is Python?",
            "ground_truth": "Python is a programming language.",
            "context": "Python is a high-level programming language.",
            "metadata": {"id": 1},
        },
        {
            "question": "What is RAG?",
            "ground_truth": "RAG stands for Retrieval-Augmented Generation.",
            "context": "RAG combines retrieval and generation for better answers.",
            "metadata": {"id": 2},
        },
    ]


@pytest.fixture
def sample_config_dict() -> dict:
    """Create a sample configuration dictionary for testing."""
    return {
        "dataset": {"path": "tests/sample_data/test_dataset.json"},
        "llm": {"provider": "openai", "model": "gpt-4o"},
        "metrics": {
            "retrieval": ["context_precision", "context_recall"],
            "generation": ["faithfulness"],
        },
    }


@pytest.fixture
def sample_dataset_path(tmp_path: Path) -> Path:
    """Create a temporary dataset file for testing."""
    import json

    dataset = [
        {
            "question": "What is Python?",
            "ground_truth": "Python is a programming language.",
            "context": "Python is a high-level programming language.",
        },
        {
            "question": "What is RAG?",
            "ground_truth": "RAG stands for Retrieval-Augmented Generation.",
            "context": "RAG combines retrieval and generation for better answers.",
        },
    ]

    dataset_path = tmp_path / "test_dataset.json"
    dataset_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    return dataset_path


@pytest.fixture
def sample_config_path(tmp_path: Path) -> Path:
    """Create a temporary configuration file for testing."""
    import yaml

    config = {
        "dataset": {"path": "tests/sample_data/test_dataset.json"},
        "llm": {"provider": "openai", "model": "gpt-4o"},
        "metrics": {
            "retrieval": ["context_precision", "context_recall"],
            "generation": ["faithfulness"],
        },
    }

    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(yaml.dump(config), encoding="utf-8")
    return config_path
