"""Threshold evaluation for CI/CD gating."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openagent_eval.cicd.models import (
    CICDConfig,
    EvaluationGate,
    GateBehavior,
    ThresholdConfig,
    ThresholdOperator,
    TestResult,
    TestStatus,
)


@dataclass
class ThresholdResult:
    """Result of evaluating a single threshold."""

    metric: str
    operator: ThresholdOperator
    threshold_value: float
    actual_value: float | None
    passed: bool
    message: str


@dataclass
class GateResult:
    """Result of evaluating a gate."""

    gate_name: str
    passed: bool
    behavior: GateBehavior
    threshold_results: list[ThresholdResult] = field(default_factory=list)
    failure_reasons: list[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Overall evaluation result."""

    passed: bool
    gate_results: list[GateResult] = field(default_factory=list)
    test_result: TestResult | None = None
    summary: dict[str, Any] = field(default_factory=dict)


class ThresholdEvaluator:
    """Evaluates metric thresholds for CI/CD gating.

    This class compares actual metric values against configured thresholds
    to determine if evaluation passes or fails.
    """

    def __init__(self, config: CICDConfig) -> None:
        """Initialize the threshold evaluator.

        Args:
            config: CI/CD configuration with gates and thresholds.
        """
        self.config = config

    def evaluate_threshold(
        self, threshold: ThresholdConfig, actual_value: float | None
    ) -> ThresholdResult:
        """Evaluate a single threshold.

        Args:
            threshold: The threshold configuration.
            actual_value: The actual metric value.

        Returns:
            ThresholdResult with pass/fail status.
        """
        if actual_value is None:
            return ThresholdResult(
                metric=threshold.metric,
                operator=threshold.operator,
                threshold_value=threshold.value,
                actual_value=None,
                passed=False,
                message=f"Metric '{threshold.metric}' not found in results",
            )

        passed = self._compare(actual_value, threshold.operator, threshold.value)

        if passed:
            message = (
                f"{threshold.metric}: {actual_value:.4f} "
                f"{threshold.operator.value} {threshold.value:.4f} ✓"
            )
        else:
            message = (
                f"{threshold.metric}: {actual_value:.4f} "
                f"NOT {threshold.operator.value} {threshold.value:.4f} ✗"
            )

        return ThresholdResult(
            metric=threshold.metric,
            operator=threshold.operator,
            threshold_value=threshold.value,
            actual_value=actual_value,
            passed=passed,
            message=message,
        )

    def evaluate_gate(
        self,
        gate: EvaluationGate,
        metrics: dict[str, Any],
    ) -> GateResult:
        """Evaluate all thresholds in a gate.

        Args:
            gate: The evaluation gate.
            metrics: Dictionary of metric name -> value.

        Returns:
            GateResult with overall pass/fail status.
        """
        threshold_results: list[ThresholdResult] = []
        failure_reasons: list[str] = []
        all_passed = True

        for threshold in gate.thresholds:
            actual_value = metrics.get(threshold.metric)
            if isinstance(actual_value, (int, float)):
                actual_float = float(actual_value)
            elif actual_value is None:
                actual_float = None
            else:
                # Try to convert string to float
                try:
                    actual_float = float(actual_value)
                except (ValueError, TypeError):
                    actual_float = None

            result = self.evaluate_threshold(threshold, actual_float)
            threshold_results.append(result)

            if not result.passed:
                all_passed = False
                if threshold.required:
                    failure_reasons.append(result.message)

        return GateResult(
            gate_name=gate.name,
            passed=all_passed,
            behavior=gate.behavior,
            threshold_results=threshold_results,
            failure_reasons=failure_reasons,
        )

    def evaluate_all_gates(
        self, metrics: dict[str, Any]
    ) -> EvaluationResult:
        """Evaluate all gates against the provided metrics.

        Args:
            metrics: Dictionary of metric name -> value.

        Returns:
            EvaluationResult with overall pass/fail status.
        """
        gate_results: list[GateResult] = []
        overall_passed = True
        summary: dict[str, Any] = {
            "total_gates": len(self.config.gates),
            "passed_gates": 0,
            "failed_gates": 0,
            "total_thresholds": 0,
            "passed_thresholds": 0,
            "failed_thresholds": 0,
        }

        for gate in self.config.gates:
            result = self.evaluate_gate(gate, metrics)
            gate_results.append(result)

            if result.passed:
                summary["passed_gates"] += 1
            else:
                summary["failed_gates"] += 1
                if result.behavior == GateBehavior.FAIL:
                    overall_passed = False

            for tr in result.threshold_results:
                summary["total_thresholds"] += 1
                if tr.passed:
                    summary["passed_thresholds"] += 1
                else:
                    summary["failed_thresholds"] += 1

        return EvaluationResult(
            passed=overall_passed,
            gate_results=gate_results,
            summary=summary,
        )

    def create_test_result(
        self,
        evaluation_result: EvaluationResult,
        duration_seconds: float = 0.0,
    ) -> TestResult:
        """Create a TestResult from an evaluation result.

        Args:
            evaluation_result: The evaluation result.
            duration_seconds: Test duration in seconds.

        Returns:
            TestResult with status and gate results.
        """
        if evaluation_result.passed:
            status = TestStatus.PASSED
        else:
            status = TestStatus.FAILED

        gate_results_data = []
        for gr in evaluation_result.gate_results:
            gate_results_data.append(
                {
                    "gate_name": gr.gate_name,
                    "passed": gr.passed,
                    "behavior": gr.behavior.value,
                    "thresholds": [
                        {
                            "metric": tr.metric,
                            "operator": tr.operator.value,
                            "threshold": tr.threshold_value,
                            "actual": tr.actual_value,
                            "passed": tr.passed,
                            "message": tr.message,
                        }
                        for tr in gr.threshold_results
                    ],
                    "failure_reasons": gr.failure_reasons,
                }
            )

        return TestResult(
            test_name="oaeval_evaluation",
            status=status,
            metrics=evaluation_result.summary,
            gate_results=gate_results_data,
            duration_seconds=duration_seconds,
        )

    @staticmethod
    def _compare(
        actual: float, operator: ThresholdOperator, threshold: float
    ) -> bool:
        """Compare actual value against threshold.

        Args:
            actual: The actual metric value.
            operator: The comparison operator.
            threshold: The threshold value.

        Returns:
            True if the comparison passes.
        """
        if operator == ThresholdOperator.GT:
            return actual > threshold
        elif operator == ThresholdOperator.GTE:
            return actual >= threshold
        elif operator == ThresholdOperator.LT:
            return actual < threshold
        elif operator == ThresholdOperator.LTE:
            return actual <= threshold
        elif operator == ThresholdOperator.EQ:
            return abs(actual - threshold) < 1e-6
        elif operator == ThresholdOperator.NEQ:
            return abs(actual - threshold) >= 1e-6
        else:
            return False
