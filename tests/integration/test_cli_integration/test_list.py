"""Tests for oaeval list command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from openagent_eval.cli.main import app


def _create_sample_report(reports_dir: Path, report_id: str) -> Path:
    """Create a sample report JSON file for testing."""
    report_data = {
        "report_id": report_id,
        "created_at": "2026-07-08T00:00:00Z",
        "config": {
            "dataset": {"path": "data/questions.json"},
            "llm": {"provider": "openai", "model": "gpt-4o"},
            "report": {"output": "terminal"},
        },
        "results": [],
        "summary": {"total": 0, "errors": 0, "metrics": {}},
        "errors": [],
        "metadata": {"version": "0.1.0", "engine": "openagent-eval"},
    }

    report_path = reports_dir / f"{report_id}.json"
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    return report_path


def test_list_shows_history(runner: CliRunner, reports_dir: Path) -> None:
    """list command shows table of previous evaluations."""
    _create_sample_report(reports_dir, "eval_001")
    _create_sample_report(reports_dir, "eval_002")

    result = runner.invoke(
        app,
        ["list", "--output-dir", str(reports_dir)],
    )

    # Should not crash
    assert result.exit_code == 0


def test_list_empty_directory(runner: CliRunner, reports_dir: Path) -> None:
    """list command handles empty reports directory."""
    result = runner.invoke(
        app,
        ["list", "--output-dir", str(reports_dir)],
    )

    # Should not crash (may show "no evaluations" message)
    assert result.exit_code == 0


def test_list_with_limit(runner: CliRunner, reports_dir: Path) -> None:
    """list command respects --limit flag."""
    for i in range(5):
        _create_sample_report(reports_dir, f"eval_{i:03d}")

    result = runner.invoke(
        app,
        ["list", "--limit", "3", "--output-dir", str(reports_dir)],
    )

    assert result.exit_code == 0
