"""Configuration validator for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

from openagent_eval.config.models import Config
from openagent_eval.exceptions import ConfigurationError


def validate_config(config: Config) -> list[str]:
    """Validate configuration and return any warnings.

    Args:
        config: The configuration to validate.

    Returns:
        List of warning messages (empty if no warnings).

    Raises:
        ConfigurationError: If configuration is invalid.
    """
    warnings: list[str] = []

    # Validate dataset path exists. HuggingFace hub datasets (format="hf") are
    # referenced by name rather than a local file, so skip this check for them.
    dataset_path = Path(config.dataset.path)
    if config.dataset.format != "hf" and not dataset_path.exists():
        raise ConfigurationError(
            message=f"Dataset file not found: {config.dataset.path}",
            field="dataset.path",
            details={"path": str(dataset_path)},
        )

    # Validate output directory is writable
    output_dir = Path(config.report.output_dir)
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            warnings.append(f"Created output directory: {output_dir}")
        except Exception as e:
            raise ConfigurationError(
                message=f"Cannot create output directory: {e}",
                field="report.output_dir",
                details={"path": str(output_dir)},
            ) from e

    # Warn about potentially expensive operations
    if config.metrics.generation and len(config.metrics.generation) > 5:
        warnings.append(
            f"Running {len(config.metrics.generation)} generation metrics may be slow and expensive"
        )

    # Warn about timeout
    if config.timeout < 60:
        warnings.append("Timeout is set to less than 60 seconds, evaluations may time out")

    return warnings


def validate_api_keys(config: Config) -> list[str]:
    """Check if required API keys are set.

    Args:
        config: The configuration to check.

    Returns:
        List of missing API key names.
    """
    import os

    missing_keys: list[str] = []

    provider_env_map = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    provider = config.llm.provider.lower()
    if provider in provider_env_map:
        env_var = provider_env_map[provider]
        if not config.llm.api_key and not os.environ.get(env_var):
            missing_keys.append(env_var)

    return missing_keys
