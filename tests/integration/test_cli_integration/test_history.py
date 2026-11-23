"""CLI coverage for metric history over both stored report formats."""

import json

import pytest
import yaml
from rich.text import Text

from openagent_eval.cli.main import app


def test_history_reads_real_runs(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = {
        "dataset": {"path": "questions.json"},
        "llm": {"provider": "mock", "model": "mock-model"},
        "retriever": {"provider": "mock"},
        "metrics": ["hit_rate"],
    }
    (tmp_path / "eval.yaml").write_text(yaml.safe_dump(config))
    for output, expected in [("terminal", []), ("json", ["signed notice"])]:
        (tmp_path / "questions.json").write_text(
            json.dumps(
                [{"question": "Find the notice", "ground_truth_contexts": expected}]
            )
        )
        run = runner.invoke(app, ["run", "eval.yaml", "--output", output])
        assert run.exit_code == 0, run.output

    result = runner.invoke(app, ["--json", "history", "hit_rate"])
    assert result.exit_code == 0, result.output
    rows = json.loads(result.output)
    assert [row["value"] for row in rows] == [0, 1]
    assert all(
        (tmp_path / "reports" / (r["report_id"] + ".json")).is_file() for r in rows
    )

    result = runner.invoke(app, ["history", "hit_rate"])
    assert result.exit_code == 0, result.output
    assert "+1" in Text.from_ansi(result.output).plain


def test_history_orders_by_instant_and_ignores_nonmatching_files(runner, tmp_path):
    for stem, timestamp, score in [
        ("b", "2026-01-01T12:00:00+03:00", 0),
        ("a", "2026-01-01T09:00:00Z", 0.25),
        ("later", "2026-01-01T10:00:00Z", 0.5),
        ("bad-date", "unknown", 1.0),
        ("boolean", "2026-01-01T10:00:00Z", True),
    ]:
        (tmp_path / f"{stem}.json").write_text(
            json.dumps(
                {
                    "created_at": timestamp,
                    "summary": {"metrics_summary": {"hit_rate": score}},
                }
            )
        )
    for stem, contents in [
        ("partial", "{"),
        ("array", "[]"),
        ("no_metric", '{"summary":{}}'),
    ]:
        (tmp_path / f"{stem}.json").write_text(contents)
    result = runner.invoke(app, ["--json", "history", "hit_rate", "-d", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert [r["report_id"] for r in json.loads(result.output)] == ["a", "b", "later"]


@pytest.mark.parametrize(
    ("flags", "message"), [([], "No recorded values"), (["--json"], "[]")]
)
def test_history_on_empty_store(runner, tmp_path, monkeypatch, flags, message):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, [*flags, "history", "hit_rate"])
    assert result.exit_code == 0, result.output
    assert message in result.output
    assert not (tmp_path / "reports").exists()
