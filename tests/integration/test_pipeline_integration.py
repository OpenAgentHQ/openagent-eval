"""Integration tests for the evaluation pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openagent_eval.config.models import Config, DatasetConfig, LLMConfig, MetricsConfig
from openagent_eval.core.engine import Engine


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for the evaluation pipeline."""

    def test_engine_initialization(self, sample_config: Config):
        """Test that the engine can be initialized with a valid config."""
        engine = Engine(config=sample_config)
        assert engine is not None
        assert engine.config == sample_config

    def test_engine_with_dataset_path(self, sample_config_path: Path):
        """Test that the engine can be initialized with a config file path."""
        config = Config(
            dataset=DatasetConfig(path=str(sample_config_path)),
            llm=LLMConfig(provider="openai", model="gpt-4o"),
            metrics=MetricsConfig(
                retrieval=["precision"],
                generation=["faithfulness"],
            ),
        )
        engine = Engine(config=config)
        assert engine is not None

    def test_dataset_loading(self, sample_dataset_path: Path):
        """Test that datasets can be loaded from a file."""
        from openagent_eval.datasets.json_loader import JSONDatasetLoader

        loader = JSONDatasetLoader()
        dataset = loader.load(sample_dataset_path)

        assert dataset is not None
        assert len(dataset.items) > 0
        assert dataset.items[0].question is not None

    def test_config_validation(self, sample_config_dict: dict):
        """Test that configuration validation works correctly."""
        config = Config(**sample_config_dict)
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4o"

    def test_config_validation_with_defaults(self):
        """Test that configuration validation works with default values."""
        config = Config(
            dataset=DatasetConfig(path="test.json"),
            llm=LLMConfig(provider="openai", model="gpt-4o"),
        )
        assert config.retriever.provider == "chroma"
        assert config.metrics.retrieval == ["precision", "recall", "mrr"]

    def test_metric_registry(self):
        """Test that metrics can be registered and retrieved."""
        from openagent_eval.metrics.base import BaseMetric
        from openagent_eval.metrics.models import MetricResultModel

        # Create a simple test metric
        class TestMetric(BaseMetric):
            name = "test_metric"
            description = "A test metric"

            def evaluate(self, **kwargs) -> MetricResultModel:
                return MetricResultModel(
                    score=1.0,
                    reason="Test metric",
                    metadata={},
                )

        metric = TestMetric()
        result = metric.evaluate()

        assert result.score == 1.0
        assert result.reason == "Test metric"


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_cli_invocation(self):
        """Test that the CLI can be invoked."""
        from typer.testing import CliRunner

        from openagent_eval.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "oaeval" in result.output.lower() or "openagent" in result.output.lower()
