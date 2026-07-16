"""Configuration loader for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError as PydanticValidationError

from openagent_eval.config.models import Config
from openagent_eval.exceptions import ConfigurationError

_FIELD_FORMAT_HINTS = {
    "llm.provider": (
        "llm:\n"
        "  provider: openai | gemini | anthropic | groq | openrouter | ollama | mock\n"
        "  model: gpt-4o (or your preferred model)"
    ),
    "llm.model": (
        "llm:\n"
        "  provider: openai | gemini | anthropic | groq | openrouter | ollama | mock\n"
        "  model: gpt-4o (or your preferred model)"
    ),
}


def _format_validation_error(
    error: PydanticValidationError,
    config_path: str | Path,
) -> str:
    lines = []

    for err in error.errors():
        location = ".".join(str(part) for part in err["loc"])

        if err["type"] == "missing":
            lines.append(
                f"Missing required field '{location}' in {config_path}"
            )

            hint = _FIELD_FORMAT_HINTS.get(location)
            if hint:
                lines.append(f"Expected format:\n{hint}")
        else:
            lines.append(
                f"Invalid value for '{location}': {err['msg']}"
            )

    return "\n\n".join(lines)


def load_config(config_path: str | Path) -> Config:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Validated configuration model.

    Raises:
        ConfigurationError: If configuration is invalid or cannot be loaded.
    """
    path = Path(config_path)

    if not path.exists():
        raise ConfigurationError(
            message=f"Configuration file not found: {config_path}",
            config_path=str(config_path),
        )

    if path.suffix not in (".yaml", ".yml"):
        raise ConfigurationError(
            message=f"Configuration file must be YAML format (.yaml or .yml): {config_path}",
            config_path=str(config_path),
        )

    try:
        with open(path, encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            message=f"Invalid YAML syntax in configuration file: {e}",
            config_path=str(config_path),
        ) from e
    except Exception as e:
        raise ConfigurationError(
            message=f"Failed to read configuration file: {e}",
            config_path=str(config_path),
        ) from e

    if raw_config is None:
        raise ConfigurationError(
            message="Configuration file is empty",
            config_path=str(config_path),
        )

    try:
        # Handle legacy 'dataset' field (string path)
        if isinstance(raw_config.get("dataset"), str):
            raw_config["dataset"] = {"path": raw_config["dataset"]}

        # Handle legacy 'metrics' field (flat list of strings) and translate
        # legacy metric names to the canonical registry names.
        _LEGACY_METRIC_MAP = {
            "precision": "context_precision",
            "recall": "context_recall",
            "mrr": "mrr",
            "ndcg": "ndcg",
            "hit_rate": "hit_rate",
            "faithfulness": "faithfulness",
            "relevancy": "answer_relevancy",
            "hallucination": "hallucination",
            "similarity": "semantic_similarity",
            "latency": "latency",
            "tokens": "token_count",
        }
        if isinstance(raw_config.get("metrics"), list):
            metrics_list = raw_config.pop("metrics")
            normalised = [
                _LEGACY_METRIC_MAP.get(m, m) for m in metrics_list
            ]
            raw_config["metrics"] = {
                "retrieval": [
                    m for m in normalised
                    if m in ("context_precision", "context_recall", "recall_at_k",
                             "precision_at_k", "hit_rate", "mrr", "ndcg")
                ],
                "generation": [
                    m for m in normalised
                    if m in ("faithfulness", "answer_relevancy", "hallucination",
                             "semantic_similarity", "exact_match", "f1_score",
                             "bleu", "rouge", "bertscore")
                ],
                "performance": [m for m in normalised if m in ("latency",)],
                "cost": [m for m in normalised if m in ("token_count",)],
            }

            # Surface metrics that were silently dropped (unknown name or typo)
            # so users are not left wondering why an expected metric never ran.
            kept = set(
                raw_config["metrics"]["retrieval"]
                + raw_config["metrics"]["generation"]
                + raw_config["metrics"]["performance"]
                + raw_config["metrics"]["cost"]
            )
            dropped = [m for m in normalised if m not in kept]
            if dropped:
                import logging

                logging.getLogger(__name__).warning(
                    "The following metrics were not recognised and will be "
                    f"ignored: {sorted(set(dropped))}"
                )

        # Handle legacy 'retrieval' block (provider/collection_name) -> 'retriever'.
        if "retrieval" in raw_config and "retriever" not in raw_config:
            retrieval = raw_config.pop("retrieval") or {}
            provider = retrieval.get("provider") or "chroma"
            settings = {}
            if retrieval.get("collection_name"):
                settings["collection_name"] = retrieval["collection_name"]
            settings.update(retrieval.get("settings", {}))
            raw_config["retriever"] = {"provider": provider, "settings": settings}

        # Handle legacy 'output' field (string format)
        if isinstance(raw_config.get("output"), str):
            output_format = raw_config.pop("output")
            raw_config.setdefault("report", {})["output"] = output_format

        config = Config(**raw_config)
        return config

    except PydanticValidationError as e:
        raise ConfigurationError(
            message=_format_validation_error(e, config_path),
            config_path=str(config_path),
        ) from e

    except Exception as e:
        raise ConfigurationError(
            message=f"Invalid configuration: {e}",
            config_path=str(config_path),

        ) from e
