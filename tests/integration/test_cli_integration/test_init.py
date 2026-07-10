"""Tests for oaeval init command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from openagent_eval.cli.main import app


def test_init_creates_config(runner: CliRunner, tmp_path: Path) -> None:
    """init command creates a valid config.yaml file."""
    config_path = tmp_path / "config.yaml"

    result = runner.invoke(app, ["init", "--config", str(config_path), "--no-interactive"])

    assert result.exit_code == 0
    assert config_path.exists()
    content = config_path.read_text(encoding="utf-8")
    assert "dataset:" in content
    assert "llm:" in content
    assert "provider:" in content


def test_init_force_overwrite(runner: CliRunner, tmp_path: Path) -> None:
    """init --force overwrites existing file without confirmation."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("existing content", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config_path), "--force", "--no-interactive"])

    assert result.exit_code == 0
    content = config_path.read_text(encoding="utf-8")
    assert "existing content" not in content
    assert "dataset:" in content


def test_init_creates_parent_directories(runner: CliRunner, tmp_path: Path) -> None:
    """init creates parent directories if they don't exist."""
    config_path = tmp_path / "subdir" / "config.yaml"

    result = runner.invoke(app, ["init", "--config", str(config_path), "--no-interactive"])

    assert result.exit_code == 0
    assert config_path.exists()


def test_init_aborts_when_file_exists(runner: CliRunner, tmp_path: Path) -> None:
    """init aborts when file exists and user declines overwrite."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("existing", encoding="utf-8")

    # User declines overwrite (n)
    result = runner.invoke(app, ["init", "--config", str(config_path)], input="n\n")

    assert result.exit_code == 0
    content = config_path.read_text(encoding="utf-8")
    assert content == "existing"
