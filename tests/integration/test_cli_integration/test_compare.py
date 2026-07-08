"""Tests for oaeval compare command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from openagent_eval.cli.main import app


def _create_sample_report(reports_dir: Path, report_id: str, faithfulness: float = 0.9) -> Path:
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
                "metrics": {"faithfulness": faithfulness, "latency": 0.5},
            }
        ],
        "summary": {
            "total": 1,
            "errors": 0,
            "metrics": {"faithfulness": faithfulness, "latency": 0.5},
        },
        "errors": [],
        "metadata": {"version": "0.1.0", "engine": "openagent-eval"},
    }

    report_path = reports_dir / f"{report_id}.json"
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    return report_path


def test_compare_shows_diff(runner: CliRunner, reports_dir: Path) -> None:
    """compare command shows side-by-side comparison."""
    _create_sample_report(reports_dir, "exp_a", faithfulness=0.85)
    _create_sample_report(reports_dir, "exp_b", faithfulness=0.92)

    result = runner.invoke(
        app,
        ["compare", "exp_a", "exp_b", "--output-dir", str(reports_dir)],
    )

    # Should not crash
    assert result.exit_code == 0


def test_compare_missing_report(runner: CliRunner) -> None:
    """compare command handles missing report gracefully."""
    result = runner.invoke(app, ["compare", "nonexistent_a", "nonexistent_b"])

    # Should fail with error message
    assert result.exit_code != 0


def test_compare_with_metrics_filter(runner: CliRunner, reports_dir: Path) -> None:
    """compare command respects --metrics filter."""
    _create_sample_report(reports_dir, "filter_a", faithfulness=0.80)
    _create_sample_report(reports_dir, "filter_b", faithfulness=0.90)

    result = runner.invoke(
        app,
        ["compare", "filter_a", "filter_b", "--metrics", "faithfulness", "--output-dir", str(reports_dir)],
    )

    assert result.exit_code == 0
