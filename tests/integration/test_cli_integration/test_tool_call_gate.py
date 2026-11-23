"""Exercise the public CLI against the bundled offline tool traces."""

from pathlib import Path

import pytest
from rich.text import Text

from openagent_eval.cli.main import app

EXAMPLE = Path(__file__).resolve().parents[3] / "examples" / "tool-call-correctness"


@pytest.mark.parametrize(("threshold", "exit_code"), [("0.5", 0), ("1", 1)])
def test_recorded_tool_call_gate(runner, monkeypatch, threshold, exit_code):
    monkeypatch.chdir(EXAMPLE.parents[1])
    result = runner.invoke(
        app,
        [
            "test",
            str(EXAMPLE / "config.yaml"),
            "-t",
            f"tool_call_correctness:gte:{threshold}",
            "--json",
        ],
    )
    assert result.exit_code == exit_code, result.output
    assert '"actual": 0.5' in Text.from_ansi(result.output).plain
