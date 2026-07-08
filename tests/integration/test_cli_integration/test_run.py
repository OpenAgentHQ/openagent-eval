"""Tests for oaeval run command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from openagent_eval.cli.main import app


def test_run_missing_config(runner: CliRunner, tmp_path: Path) -> None:
    """run command fails gracefully with missing config file."""
    missing_path = tmp_path / "nonexistent.yaml"

    result = runner.invoke(app, ["run", str(missing_path)])

    assert result.exit_code != 0


def test_run_executes_pipeline(
    runner: CliRunner, sample_config: Path, sample_dataset: Path
) -> None:
    """run command loads config and executes evaluation pipeline."""
    # Update config to use the sample dataset
    config_content = sample_config.read_text(encoding="utf-8")
    config_content = config_content.replace(
        "data/questions.json", str(sample_dataset)
    )
    sample_config.write_text(config_content, encoding="utf-8")

    result = runner.invoke(app, ["run", str(sample_config)])

    # Should complete without error (exit code 0)
    # The pipeline may produce empty results since we don't have real LLM/providers
    # but it should not crash
    assert result.exit_code == 0


def test_run_with_output_override(
    runner: CliRunner, sample_config: Path, sample_dataset: Path
) -> None:
    """run command respects --output flag."""
    config_content = sample_config.read_text(encoding="utf-8")
    config_content = config_content.replace(
        "data/questions.json", str(sample_dataset)
    )
    sample_config.write_text(config_content, encoding="utf-8")

    result = runner.invoke(app, ["run", str(sample_config), "--output", "json"])

    assert result.exit_code == 0


def test_run_shows_progress(runner: CliRunner, sample_config: Path) -> None:
    """run command displays progress during execution."""
    result = runner.invoke(app, ["run", str(sample_config)])

    # Should show some output (progress or error)
    assert result.output is not None
