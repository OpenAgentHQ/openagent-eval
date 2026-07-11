"""Unit tests for CI/CD models."""

import pytest

from openagent_eval.cicd.models import (
    CICDConfig,
    EvaluationGate,
    GateBehavior,
    TestResult,
    TestStatus,
    ThresholdConfig,
    ThresholdOperator,
)


class TestThresholdOperator:
    """Tests for ThresholdOperator enum."""

    def test_all_operators_exist(self):
        """Test that all expected operators are defined."""
        operators = list(ThresholdOperator)
        assert len(operators) == 6
        assert ThresholdOperator.GT in operators
        assert ThresholdOperator.GTE in operators
        assert ThresholdOperator.LT in operators
        assert ThresholdOperator.LTE in operators
        assert ThresholdOperator.EQ in operators
        assert ThresholdOperator.NEQ in operators

    def test_operator_values(self):
        """Test operator string values."""
        assert ThresholdOperator.GT.value == "gt"
        assert ThresholdOperator.GTE.value == "gte"
        assert ThresholdOperator.LT.value == "lt"
        assert ThresholdOperator.LTE.value == "lte"
        assert ThresholdOperator.EQ.value == "eq"
        assert ThresholdOperator.NEQ.value == "neq"


class TestThresholdConfig:
    """Tests for ThresholdConfig model."""

    def test_basic_creation(self):
        """Test creating a basic threshold config."""
        config = ThresholdConfig(
            metric="faithfulness",
            operator=ThresholdOperator.GTE,
            value=0.8,
        )
        assert config.metric == "faithfulness"
        assert config.operator == ThresholdOperator.GTE
        assert config.value == 0.8
        assert config.required is True

    def test_optional_fields(self):
        """Test creating threshold with optional fields."""
        config = ThresholdConfig(
            metric="latency",
            value=1000,
            required=False,
        )
        assert config.metric == "latency"
        assert config.operator == ThresholdOperator.GTE  # default
        assert config.required is False

    def test_all_operators(self):
        """Test creating thresholds with all operators."""
        for op in ThresholdOperator:
            config = ThresholdConfig(
                metric="test",
                operator=op,
                value=0.5,
            )
            assert config.operator == op


class TestGateBehavior:
    """Tests for GateBehavior enum."""

    def test_all_behaviors_exist(self):
        """Test that all expected behaviors are defined."""
        behaviors = list(GateBehavior)
        assert len(behaviors) == 3
        assert GateBehavior.FAIL in behaviors
        assert GateBehavior.WARN in behaviors
        assert GateBehavior.SKIP in behaviors

    def test_behavior_values(self):
        """Test behavior string values."""
        assert GateBehavior.FAIL.value == "fail"
        assert GateBehavior.WARN.value == "warn"
        assert GateBehavior.SKIP.value == "skip"


class TestEvaluationGate:
    """Tests for EvaluationGate model."""

    def test_basic_creation(self):
        """Test creating a basic evaluation gate."""
        gate = EvaluationGate(
            name="test_gate",
            thresholds=[
                ThresholdConfig(metric="faithfulness", value=0.8),
            ],
        )
        assert gate.name == "test_gate"
        assert len(gate.thresholds) == 1
        assert gate.behavior == GateBehavior.FAIL

    def test_empty_thresholds(self):
        """Test creating gate with empty thresholds."""
        gate = EvaluationGate(name="empty_gate")
        assert gate.name == "empty_gate"
        assert gate.thresholds == []

    def test_multiple_thresholds(self):
        """Test creating gate with multiple thresholds."""
        gate = EvaluationGate(
            name="multi_gate",
            thresholds=[
                ThresholdConfig(metric="faithfulness", value=0.8),
                ThresholdConfig(metric="relevancy", value=0.7),
                ThresholdConfig(metric="latency", value=1000),
            ],
        )
        assert len(gate.thresholds) == 3

    def test_custom_behavior(self):
        """Test creating gate with custom behavior."""
        gate = EvaluationGate(
            name="warn_gate",
            behavior=GateBehavior.WARN,
        )
        assert gate.behavior == GateBehavior.WARN


class TestCICDConfig:
    """Tests for CICDConfig model."""

    def test_basic_creation(self):
        """Test creating a basic CI/CD config."""
        config = CICDConfig()
        assert config.config_path is None
        assert config.gates == []
        assert config.fail_on_error is True
        assert config.timeout == 300
        assert config.retry_count == 0
        assert config.output_format == "json"

    def test_custom_config(self):
        """Test creating CI/CD config with custom values."""
        config = CICDConfig(
            config_path="/path/to/config.yaml",
            fail_on_error=False,
            timeout=600,
            retry_count=3,
            output_format="terminal",
        )
        assert config.config_path == "/path/to/config.yaml"
        assert config.fail_on_error is False
        assert config.timeout == 600
        assert config.retry_count == 3
        assert config.output_format == "terminal"

    def test_with_gates(self):
        """Test creating CI/CD config with gates."""
        config = CICDConfig(
            gates=[
                EvaluationGate(
                    name="gate1",
                    thresholds=[
                        ThresholdConfig(metric="faithfulness", value=0.8),
                    ],
                ),
                EvaluationGate(
                    name="gate2",
                    thresholds=[
                        ThresholdConfig(metric="relevancy", value=0.7),
                    ],
                ),
            ],
        )
        assert len(config.gates) == 2


class TestTestStatus:
    """Tests for TestStatus enum."""

    def test_all_statuses_exist(self):
        """Test that all expected statuses are defined."""
        statuses = list(TestStatus)
        assert len(statuses) == 4
        assert TestStatus.PASSED in statuses
        assert TestStatus.FAILED in statuses
        assert TestStatus.SKIPPED in statuses
        assert TestStatus.ERROR in statuses

    def test_status_values(self):
        """Test status string values."""
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"


class TestTestResult:
    """Tests for TestResult model."""

    def test_basic_creation(self):
        """Test creating a basic test result."""
        result = TestResult(
            test_name="test_rag",
            status=TestStatus.PASSED,
        )
        assert result.test_name == "test_rag"
        assert result.status == TestStatus.PASSED
        assert result.metrics == {}
        assert result.gate_results == []
        assert result.error_message is None
        assert result.duration_seconds == 0.0

    def test_with_metrics(self):
        """Test creating test result with metrics."""
        result = TestResult(
            test_name="test_rag",
            status=TestStatus.PASSED,
            metrics={"faithfulness": 0.85, "relevancy": 0.75},
        )
        assert result.metrics["faithfulness"] == 0.85
        assert result.metrics["relevancy"] == 0.75

    def test_with_gate_results(self):
        """Test creating test result with gate results."""
        result = TestResult(
            test_name="test_rag",
            status=TestStatus.FAILED,
            gate_results=[
                {
                    "gate_name": "gate1",
                    "passed": False,
                    "thresholds": [],
                }
            ],
        )
        assert len(result.gate_results) == 1
        assert result.gate_results[0]["gate_name"] == "gate1"

    def test_with_error(self):
        """Test creating test result with error."""
        result = TestResult(
            test_name="test_rag",
            status=TestStatus.ERROR,
            error_message="Config file not found",
        )
        assert result.error_message == "Config file not found"
