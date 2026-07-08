"""Tests for oaeval report command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from openagent_eval.cli.main import app


def _create_sample_report(reports_dir: Path, report_id: str = "test_report") -> Path:
    """Create a sample report JSON file for testing."""
    report_data = {
        "report_id": report_id,
        "created_at": "2026-07-08T00:00:00Z",
        "config": {
            "dataset": {"path": "data/questions.json"},
            "llm": {"provider": "openai", "model": "gpt-4o"},
            "report": {"output": "terminal"},
        },
        "results": [
            {
                "question": "What is Python?",
                "answer": "Python is a programming language.",
                "ground_truth": "Python is a programming language.",
                "contexts": ["Python is a high-level programming language."],
                "metrics": {"faithfulness": 0.95, "latency": 0.5},
            }
        ],
        "summary": {
            "total": 1,
            "errors": 0,
            "metrics": {"faithfulness": 0.95, "latency": 0.5},
        },
        "errors": [],
        "metadata": {"version": "0.1.0", "engine": "openagent-eval"},
    }

    report_path = reports_dir / f"{report_id}.json"
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    return report_path


def test_report_displays_output(runner: CliRunner, reports_dir: Path) -> None:
    """report command shows results for a valid report ID."""
    _create_sample_report(reports_dir, "test_001")

    result = runner.invoke(
        app,
        ["report", "test_001", "--output", "terminal", "--output-dir", str(reports_dir)],
    )

    assert result.exit_code == 0


def test_report_latest(runner: CliRunner, reports_dir: Path) -> None:
    """report command handles 'latest' keyword."""
    _create_sample_report(reports_dir, "latest_test")

    result = runner.invoke(
        app,
        ["report", "latest", "--output-dir", str(reports_dir)],
    )

    assert result.exit_code == 0


def test_report_missing_report(runner: CliRunner) -> None:
    """report command handles missing report gracefully."""
    result = runner.invoke(app, ["report", "nonexistent_report"])

    # Should fail with error message
    assert result.exit_code != 0
