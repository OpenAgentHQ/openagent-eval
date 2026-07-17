"""Tests for the configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from openagent_eval.config.loader import load_config
from openagent_eval.config.models import (
    Config,
    CorpusCheckType,
    CorpusConfig,
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

    # --- M13 regression test ---
    def test_load_config_warns_on_dropped_metrics(self, tmp_path: Path, caplog) -> None:
        """M13: Unrecognised metric names in legacy list must produce a warning."""
        import logging

        config_dict = {
            "dataset": {"path": "data.json"},
            "llm": {"provider": "openai", "model": "gpt-4o"},
            "metrics": ["precision", "totally_fake_metric"],
        }
        config_path = tmp_path / "dropped.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        with caplog.at_level(logging.WARNING, logger="openagent_eval.config.loader"):
            load_config(config_path)

        assert "totally_fake_metric" in caplog.text


class TestCorpusConfigIntegration:
    """Issue #121: the corpus: section is part of the main Config."""

    def test_corpus_defaults_to_none(self) -> None:
        """A Config without a corpus section leaves corpus unset."""
        config = Config(
            dataset=DatasetConfig(path="data.json"),
            llm=LLMConfig(provider="openai", model="gpt-4o"),
        )
        assert config.corpus is None

    def test_load_config_parses_corpus_section(self, tmp_path: Path) -> None:
        """A corpus: section in config.yaml parses into a CorpusConfig."""
        config_dict = {
            "dataset": {"path": "data.json"},
            "llm": {"provider": "openai", "model": "gpt-4o"},
            "corpus": {
                "path": "./knowledge_base/",
                "checks": ["contradiction", "staleness"],
                "staleness_days": 180,
                "similarity_threshold": 0.8,
                "max_documents": 50,
            },
        }
        config_path = tmp_path / "with_corpus.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        config = load_config(config_path)

        assert isinstance(config.corpus, CorpusConfig)
        assert config.corpus.path == "./knowledge_base/"
        assert config.corpus.checks == [
            CorpusCheckType.CONTRADICTION,
            CorpusCheckType.STALENESS,
        ]
        assert config.corpus.staleness_days == 180
        assert config.corpus.similarity_threshold == 0.8
        assert config.corpus.max_documents == 50

    def test_load_config_without_corpus_leaves_it_none(self, tmp_path: Path) -> None:
        """Omitting the corpus section keeps config.corpus as None."""
        config_dict = {
            "dataset": {"path": "data.json"},
            "llm": {"provider": "openai", "model": "gpt-4o"},
        }
        config_path = tmp_path / "no_corpus.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        config = load_config(config_path)

        assert config.corpus is None

    def test_load_config_corpus_unknown_key_is_ignored(self, tmp_path: Path) -> None:
        """Unknown keys in corpus: are silently ignored, matching sibling
        sections (pydantic ``extra="ignore"``); they neither error nor drop
        the known fields."""
        config_dict = {
            "dataset": {"path": "data.json"},
            "llm": {"provider": "openai", "model": "gpt-4o"},
            "corpus": {
                "path": "./kb/",
                "staleness_days": 90,
                "totally_fake_corpus_key": 123,
            },
        }
        config_path = tmp_path / "corpus_unknown.yaml"
        config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

        config = load_config(config_path)

        assert isinstance(config.corpus, CorpusConfig)
        assert config.corpus.staleness_days == 90
        assert not hasattr(config.corpus, "totally_fake_corpus_key")
