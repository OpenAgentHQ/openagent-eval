"""Unit tests for CLI test command."""

import asyncio
import inspect
import json
import re
from typing import Annotated, get_origin, get_type_hints
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from openagent_eval.cicd.thresholds import EvaluationResult
from openagent_eval.cli.commands import test as test_command
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

    def test_result_annotations_resolve_to_evaluation_result(self):
        """CLI result helpers resolve their annotations at runtime."""
        helpers = (test_command._display_results, test_command._output_json)
        annotations = {}
        resolution_errors = {}

        for helper in helpers:
            try:
                annotations[helper.__name__] = get_type_hints(helper)["result"]
            except NameError as exc:
                resolution_errors[helper.__name__] = str(exc)

        assert not resolution_errors, (
            f"CLI result annotations did not resolve: {resolution_errors}"
        )
        assert annotations == {helper.__name__: EvaluationResult for helper in helpers}

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

    def test_threshold_parameter_has_safe_annotated_default(self):
        """Regression test for issue #304: threshold uses Annotated with None default."""
        sig = inspect.signature(test_command.test_command)
        param = sig.parameters["threshold"]
        assert param.default is None

        hints = get_type_hints(test_command.test_command, include_extras=True)
        assert get_origin(hints["threshold"]) is Annotated

    def test_test_command_default_empty_threshold(self, tmp_path):
        """Running oaeval test without -t defaults to an empty threshold list."""
        config_path = _write_offline_config(tmp_path)

        result = runner.invoke(app, ["test", str(config_path)])
        output = _strip_ansi(result.output)

        assert result.exit_code == 0, output
        assert "Thresholds:" not in output
        assert "PASSED" in output

    def test_test_command_long_threshold_option(self, tmp_path):
        """Long --threshold option parses and evaluates threshold gates."""
        config_path = _write_offline_config(tmp_path)

        result = runner.invoke(
            app,
            ["test", str(config_path), "--threshold", "exact_match:gte:0.5"],
        )
        output = _strip_ansi(result.output)

        assert result.exit_code == 0, output
        assert "Thresholds: exact_match:gte:0.5" in output
        assert "exact_match: 1.0000 gte 0.5000" in output

    def test_test_command_multiple_thresholds_and_isolation(self, tmp_path):
        """Multiple -t/--threshold options evaluate all gates without leaking state."""
        config_path = _write_offline_config(tmp_path)

        first = runner.invoke(
            app,
            [
                "test",
                str(config_path),
                "-t",
                "exact_match:gte:0.5",
                "--threshold",
                "exact_match:lte:1.0",
            ],
        )
        first_output = _strip_ansi(first.output)
        assert first.exit_code == 0, first_output
        assert "Thresholds: exact_match:gte:0.5, exact_match:lte:1.0" in first_output
        assert "exact_match: 1.0000 gte 0.5000" in first_output
        assert "exact_match: 1.0000 lte 1.0000" in first_output

        # Subsequent call without -t must not inherit thresholds from the previous call.
        second = runner.invoke(app, ["test", str(config_path)])
        second_output = _strip_ansi(second.output)
        assert second.exit_code == 0, second_output
        assert "Thresholds:" not in second_output

    def test_test_command_multiple_thresholds_mixed_pass_fail(self, tmp_path):
        """If any gate among multiple -t options fails, exit code is 1."""
        config_path = _write_offline_config(tmp_path)

        result = runner.invoke(
            app,
            [
                "test",
                str(config_path),
                "-t",
                "exact_match:gte:0.5",
                "-t",
                "exact_match:lt:0.5",
            ],
        )
        output = _strip_ansi(result.output)

        assert result.exit_code == 1, output
        assert "exact_match: 1.0000 gte 0.5000" in output
        assert "exact_match: 1.0000 NOT lt 0.5000" in output

    def test_test_command_fail_on_error_options(self, tmp_path):
        """--fail-on-error exits 1 on unexpected errors; --no-fail-on-error exits 0."""
        config_path = _write_offline_config(tmp_path)

        with patch(
            "openagent_eval.cli.commands.test.OAEvalPlugin.run_evaluation",
            side_effect=RuntimeError("unexpected failure"),
        ):
            fail_result = runner.invoke(
                app,
                ["test", str(config_path), "--fail-on-error"],
            )
            no_fail_result = runner.invoke(
                app,
                ["test", str(config_path), "--no-fail-on-error"],
            )

        assert fail_result.exit_code == 1, fail_result.output
        assert "unexpected failure" in _strip_ansi(fail_result.output)
        assert no_fail_result.exit_code == 0, no_fail_result.output
        assert "unexpected failure" in _strip_ansi(no_fail_result.output)

    def test_test_command_invalid_threshold_value_preserves_cause(self, tmp_path):
        """Invalid threshold value chains the underlying ValueError (issue #303)."""
        config_path = _write_offline_config(tmp_path)

        with pytest.raises(typer.Exit) as exc_info:
            test_command.test_command(
                config_path=str(config_path),
                threshold=["faithfulness:gte:not_a_number"],
                fail_on_error=True,
                timeout=300,
                verbose=False,
                json_output=False,
            )

        assert exc_info.value.exit_code == 2
        assert isinstance(exc_info.value.__cause__, ValueError)
