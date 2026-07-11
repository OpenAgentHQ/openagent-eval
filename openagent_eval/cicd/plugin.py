"""pytest plugin for OpenAgent Eval CI/CD integration.

This plugin allows users to run RAG evaluations as pytest tests
with threshold-based gating for CI/CD pipelines.

Usage in pytest:
    # In conftest.py or test file
    import pytest
    from openagent_eval.cicd import OAEvalPlugin

    def test_rag_evaluation():
        result = OAEvalPlugin.run_evaluation("config.yaml")
        assert result.passed, f"Evaluation failed: {result.summary}"

Usage via pytest plugin:
    # In pytest.ini or pyproject.toml
    [tool.pytest.ini_options]
    addopts = "-p openagent_eval.cicd.plugin"

    # Or via command line
    pytest -p openagent_eval.cicd.plugin
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any, Generator

import pytest

from openagent_eval.cicd.models import CICDConfig, EvaluationGate, ThresholdConfig
from openagent_eval.cicd.thresholds import EvaluationResult, ThresholdEvaluator


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options for OpenAgent Eval."""
    group = parser.getgroup("oaeval", "OpenAgent Eval CI/CD")
    group.addoption(
        "--oaeval-config",
        action="store",
        default=None,
        help="Path to OpenAgent Eval configuration file",
    )
    group.addoption(
        "--oaeval-threshold",
        action="append",
        default=[],
        metavar="METRIC:OP:VALUE",
        help=(
            "Add a threshold gate. Format: metric_name:operator:value. "
            "Operators: gt, gte, lt, lte, eq, neq. "
            "Example: faithfulness:gte:0.8"
        ),
    )
    group.addoption(
        "--oaeval-fail-on-error",
        action="store_true",
        default=True,
        help="Fail test on evaluation errors (default: True)",
    )
    group.addoption(
        "--oaeval-timeout",
        action="store",
        type=int,
        default=300,
        help="Timeout in seconds for evaluation (default: 300)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure the OpenAgent Eval plugin."""
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "oaeval: mark test as an OpenAgent Eval CI/CD test",
    )

    # Store oaeval config for later use
    config._oaeval_config = CICDConfig(  # type: ignore[attr-defined]
        config_path=config.getoption("--oaeval-config"),
        fail_on_error=config.getoption("--oaeval-fail-on-error"),
        timeout=config.getoption("--oaeval-timeout"),
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify collected items to add OpenAgent Eval markers."""
    for item in items:
        if "oaeval" in item.keywords:
            item.add_marker(pytest.mark.oaeval)


class OAEvalPlugin:
    """pytest plugin for OpenAgent Eval CI/CD integration.

    This plugin provides:
    - Threshold-based test gating
    - Integration with pytest exit codes
    - CI/CD-friendly output
    """

    @staticmethod
    def run_evaluation(
        config_path: str | Path,
        thresholds: list[str] | None = None,
        timeout: int = 300,
    ) -> EvaluationResult:
        """Run an evaluation and return results.

        Args:
            config_path: Path to evaluation configuration file.
            thresholds: List of threshold strings (metric:operator:value).
            timeout: Timeout in seconds.

        Returns:
            EvaluationResult with pass/fail status and details.
        """
        from openagent_eval.config.loader import load_config
        from openagent_eval.core.engine import Engine

        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load evaluation config
        eval_config = load_config(str(config_path))

        # Parse thresholds
        cicd_config = CICDConfig(
            config_path=str(config_path),
            timeout=timeout,
        )

        if thresholds:
            for threshold_str in thresholds:
                parts = threshold_str.split(":")
                if len(parts) != 3:
                    raise ValueError(
                        f"Invalid threshold format: {threshold_str}. "
                        "Expected: metric:operator:value"
                    )
                metric_name, operator_str, value_str = parts
                try:
                    value = float(value_str)
                except ValueError:
                    raise ValueError(f"Invalid threshold value: {value_str}")

                cicd_config.gates.append(
                    EvaluationGate(
                        name=f"gate_{metric_name}",
                        thresholds=[
                            ThresholdConfig(
                                metric=metric_name,
                                operator=operator_str,  # type: ignore[arg-type]
                                value=value,
                            )
                        ],
                    )
                )

        # Run evaluation
        start_time = time.time()

        try:
            # Create engine and run
            engine = Engine(eval_config)

            # Load dataset
            from openagent_eval.cli.utils.helpers import load_dataset_for_run

            dataset_items = load_dataset_for_run(eval_config)

            # Run async evaluation
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run, engine.run(dataset_items)
                    ).result(timeout=timeout)
            else:
                result = loop.run_until_complete(engine.run(dataset_items))

            # Extract metrics from summary
            metrics = result.summary.get("metrics_summary", {})

            # Flatten metrics if needed
            flat_metrics: dict[str, Any] = {}
            for key, value in metrics.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flat_metrics[f"{key}_{sub_key}"] = sub_value
                else:
                    flat_metrics[key] = value

            # Also add top-level summary metrics
            flat_metrics["total_items"] = result.summary.get("total_items", 0)
            flat_metrics["successful_evaluations"] = result.summary.get(
                "successful_evaluations", 0
            )
            flat_metrics["failed_evaluations"] = result.summary.get(
                "failed_evaluations", 0
            )

            duration = time.time() - start_time

        except Exception as e:
            duration = time.time() - start_time
            # Create a failed result
            evaluator = ThresholdEvaluator(cicd_config)
            return EvaluationResult(
                passed=False,
                gate_results=[],
                summary={
                    "error": str(e),
                    "duration_seconds": duration,
                },
            )

        # Evaluate thresholds
        evaluator = ThresholdEvaluator(cicd_config)
        eval_result = evaluator.evaluate_all_gates(flat_metrics)
        eval_result.summary["duration_seconds"] = duration

        return eval_result

    @staticmethod
    def run_evaluation_from_config(
        cicd_config: CICDConfig,
    ) -> EvaluationResult:
        """Run an evaluation using a CICDConfig object.

        Args:
            cicd_config: CI/CD configuration.

        Returns:
            EvaluationResult with pass/fail status and details.
        """
        if not cicd_config.config_path:
            raise ValueError("config_path is required in CICDConfig")

        return OAEvalPlugin.run_evaluation(
            config_path=cicd_config.config_path,
            timeout=cicd_config.timeout,
        )


def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    """Create test report for OpenAgent Eval tests."""
    outcome = yield
    report = outcome.get_result()

    # Store oaeval results in report
    if hasattr(item, "_oaeval_result"):
        report.oaeval_result = item._oaeval_result  # type: ignore[attr-defined]


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Setup hook for OpenAgent Eval tests."""
    # Check if this is an oaeval test
    if "oaeval" in item.keywords:
        # Mark as oaeval test
        item._is_oaeval_test = True  # type: ignore[attr-defined]


def pytest_sessionfinish(
    session: pytest.Session, exitstatus: int
) -> None:
    """Called after whole test run finished."""
    # Store final status for CI/CD
    session._oaeval_exitstatus = exitstatus  # type: ignore[attr-defined]
