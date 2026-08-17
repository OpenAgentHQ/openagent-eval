"""Unit tests for CLI test command."""

import asyncio
import json
import re

from typer.testing import CliRunner

from openagent_eval.cli.main import app

runner = CliRunner()


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _write_offline_config(tmp_path):
    """Write a fully offline dataset + config for CLI test runs.

    The mock providers echo ``ground_truth``, so ``exact_match`` scores
    exactly 1.0. Returns the config path.
    """
    dataset_path = tmp_path / "data.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "question": "What is RAG?",
                    "ground_truth": "RAG combines retrieval with generation.",
                    "context": "RAG combines retrieval with generation.",
                    "ground_truth_contexts": [
                        "RAG combines retrieval with generation."
                    ],
                }
            ]
        )
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""
dataset:
  path: {dataset_path}
llm:
  provider: mock
  model: mock-model
retriever:
  provider: mock
  settings:
    collection_name: c
metrics:
  retrieval: []
  generation: ["exact_match"]
  performance: []
  cost: []
report:
  output: json
  output_dir: {tmp_path / "reports_out"}
parallel: false
"""
    )
    return config_path


class TestTestCommand:
    """Tests for oaeval test command."""

    def test_test_command_help(self):
        """Test test command help output."""
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        output = _strip_ansi(result.output)
        assert "Run evaluation as a CI/CD test" in output

    def test_test_command_no_config(self):
        """Test test command without config shows error."""
        result = runner.invoke(app, ["test"])
        assert result.exit_code != 0

    def test_test_command_nonexistent_config(self):
        """Test test command with nonexistent config."""
        result = runner.invoke(app, ["test", "/nonexistent/config.yaml"])
        assert result.exit_code == 2

    def test_test_command_invalid_threshold_format(self):
        """Test test command with invalid threshold format."""
        result = runner.invoke(
            app,
            ["test", "config.yaml", "-t", "invalid_format"],
        )
        assert result.exit_code == 2

    def test_test_command_invalid_threshold_value(self):
        """Test test command with invalid threshold value."""
        result = runner.invoke(
            app,
            ["test", "config.yaml", "-t", "faithfulness:gte:not_a_number"],
        )
        assert result.exit_code == 2

    def test_test_command_invalid_operator(self):
        """Test test command with invalid operator."""
        result = runner.invoke(
            app,
            ["test", "config.yaml", "-t", "faithfulness:invalid:0.8"],
        )
        assert result.exit_code == 2

    def test_test_command_json_output(self):
        """Test test command with --json flag."""
        result = runner.invoke(app, ["test", "--help"])
        output = _strip_ansi(result.output)
        assert "json" in output.lower()

    def test_test_command_timeout_option(self):
        """Test test command with --timeout option."""
        result = runner.invoke(app, ["test", "--help"])
        output = _strip_ansi(result.output)
        assert "timeout" in output.lower()

    def test_test_command_threshold_option(self):
        """Test test command with --threshold option."""
        result = runner.invoke(app, ["test", "--help"])
        output = _strip_ansi(result.output)
        assert "threshold" in output.lower()
        assert "-t" in output

    def test_test_command_passing_threshold_is_not_reported_missing(self, tmp_path):
        """Regression test for issue #228.

        A threshold that should pass must not fail with "metric not found":
        the gate summary returned by ``OAEvalPlugin.run_evaluation`` must
        carry ``metrics_summary`` so the CLI threshold-evaluation path can
        look the metric up. Uses fully offline mock providers (the mock
        echoes ``ground_truth``, so ``exact_match`` scores exactly 1.0).

        Also asserts the positive behaviour: the threshold was actually
        evaluated against the real computed value, not silently waved
        through.
        """
        config_path = _write_offline_config(tmp_path)

        result = runner.invoke(
            app,
            ["test", str(config_path), "-t", "exact_match:gte:0.5"],
        )
        output = _strip_ansi(result.output)

        assert "not found in results" not in output
        # The threshold must be evaluated against the real value (1.0),
        # and the gate must be reported as passing.
        assert "exact_match: 1.0000 gte 0.5000" in output, output
        assert "PASS" in output, output
        assert result.exit_code == 0, output

    def test_test_command_failing_threshold_is_enforced(self, tmp_path):
        """Complement to the #228 regression test.

        A threshold that genuinely cannot be met (``exact_match`` scores
        exactly 1.0 with the offline mock providers, so ``gte:1.5`` must
        fail) must exit non-zero and report the failure with the real
        actual value. This catches an implementation that auto-passes or
        skips missing/unresolvable metrics: a suite that only checks the
        passing direction cannot notice that enforcement stopped.
        """
        config_path = _write_offline_config(tmp_path)

        result = runner.invoke(
            app,
            ["test", str(config_path), "-t", "exact_match:gte:1.5"],
        )
        output = _strip_ansi(result.output)

        # The metric must resolve (not "not found") and the failure must
        # be reported against the real computed value (1.0).
        assert "not found in results" not in output
        assert "exact_match: 1.0000 NOT gte 1.5000" in output, output
        assert result.exit_code == 1, output

    def test_test_command_after_completed_asyncio_run(self, tmp_path):
        """Regression test for issue #261.

        ``asyncio.run()`` calls ``asyncio.set_event_loop(None)`` when it
        completes, so afterwards ``asyncio.get_event_loop()`` in the main
        thread raises ``RuntimeError`` instead of auto-creating a loop.
        ``run_evaluation`` must not depend on that policy state: after a
        completed ``asyncio.run`` in the same process, the evaluation must
        still actually run and the threshold must be evaluated against the
        real metrics — not swallowed into an ``error`` summary that the
        CLI then reports as "not found in results".
        """
        asyncio.run(asyncio.sleep(0))

        config_path = _write_offline_config(tmp_path)

        result = runner.invoke(
            app,
            ["test", str(config_path), "-t", "exact_match:gte:0.5"],
        )
        output = _strip_ansi(result.output)

        assert "not found in results" not in output
        # The evaluation must have actually run: the threshold is
        # evaluated against the real computed value (1.0) and passes.
        assert "exact_match: 1.0000 gte 0.5000" in output, output
        assert "PASS" in output, output
        assert result.exit_code == 0, output
