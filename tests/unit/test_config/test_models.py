"""Tests for the configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from openagent_eval.config.loader import load_config
from openagent_eval.config.models import (
    Config,
    DatasetConfig,
    LLMConfig,
    MetricsConfig,
    OutputFormat,
    ReportConfig,
    RetrieverConfig,
)
from openagent_eval.exceptions import ConfigurationError


class TestConfigModels:
    """Tests for configuration Pydantic models."""

    def test_dataset_config(self) -> None:
        """Test DatasetConfig creation."""
        config = DatasetConfig(path="data.json")
        assert config.path == "data.json"
        assert config.format is None
        assert config.limit is None
        assert config.shuffle is False

    def test_llm_config(self) -> None:
        """Test LLMConfig creation."""
        config = LLMConfig(provider="openai", model="gpt-4o")
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.0
        assert config.max_tokens is None

    def test_llm_config_api_key_validation(self) -> None:
        """Test LLMConfig API key validation."""
        # Valid API key
        config = LLMConfig(provider="openai", model="gpt-4o", api_key="sk" + "a" * 40)
        assert config.api_key is not None

        # Invalid API key (too short)
        with pytest.raises(Exception):
            LLMConfig(provider="openai", model="gpt-4o", api_key="short")

    def test_retriever_config(self) -> None:
        """Test RetrieverConfig creation."""
        config = RetrieverConfig(provider="chroma", settings={"collection": "docs"})
        assert config.provider == "chroma"
        assert config.settings == {"collection": "docs"}

    def test_metrics_config(self) -> None:
        """Test MetricsConfig creation."""
        config = MetricsConfig()
        assert "context_precision" in config.retrieval
        assert "faithfulness" in config.generation
        assert "latency" in config.performance
        assert "token_count" in config.cost

    def test_report_config(self) -> None:
        """Test ReportConfig creation."""
        config = ReportConfig()
        assert config.output == OutputFormat.TERMINAL
        assert config.output_dir == "./reports"
        assert config.include_examples is True
        assert config.max_examples == 10

    def test_config_creation(self) -> None:
        """Test Config creation with all fields."""
        config = Config(
            dataset=DatasetConfig(path="data.json"),
            llm=LLMConfig(provider="openai", model="gpt-4o"),
        )
        assert config.dataset.path == "data.json"
        assert config.llm.provider == "openai"
        assert config.verbose is False
        assert config.parallel is True
        assert config.max_workers == 4
        assert config.timeout == 300.0


class TestConfigLoader:
    """Tests for configuration loading."""

    def test_load_config(self, sample_config_path: Path) -> None:
        """Test loading configuration from YAML file."""
        config = load_config(sample_config_path)
        assert isinstance(config, Config)
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4o"

    def test_load_config_not_found(self) -> None:
        """Test loading configuration from non-existent file."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("nonexistent.yaml")
        assert "not found" in str(exc_info.value).lower()

    def test_load_config_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading configuration with invalid YAML."""
        config_path = tmp_path / "invalid.yaml"
        config_path.write_text("invalid: yaml: [", encoding="utf-8")

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(config_path)
        assert "Invalid YAML syntax" in str(exc_info.value)

    def test_load_config_empty(self, tmp_path: Path) -> None:
        """Test loading empty configuration file."""
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("", encoding="utf-8")

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(config_path)
        assert "empty" in str(exc_info.value).lower()

    def test_load_config_legacy_dataset_string(self, tmp_path: Path) -> None:
        """Test loading configuration with legacy dataset string format."""
        config_dict = {
            "dataset": "data.json",
            "llm": {"provider": "openai", "model": "gpt-4o"},
        }
        config_path = tmp_path / "legacy.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        config = load_config(config_path)
        assert config.dataset.path == "data.json"

    def test_load_config_legacy_metrics_list(self, tmp_path: Path) -> None:
        """Test loading configuration with legacy metrics list format."""
        config_dict = {
            "dataset": {"path": "data.json"},
            "llm": {"provider": "openai", "model": "gpt-4o"},
            "metrics": ["precision", "recall", "faithfulness"],
        }
        config_path = tmp_path / "legacy_metrics.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        config = load_config(config_path)
        # Legacy metric names are normalised to canonical registry names.
        assert "context_precision" in config.metrics.retrieval
        assert "context_recall" in config.metrics.retrieval
        assert "faithfulness" in config.metrics.generation
