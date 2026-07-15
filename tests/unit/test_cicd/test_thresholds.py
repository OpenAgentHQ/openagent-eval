"""Unit tests for threshold evaluation."""


from openagent_eval.cicd.models import (
    CICDConfig,
    EvaluationGate,
    GateBehavior,
    ThresholdConfig,
    ThresholdOperator,
)
from openagent_eval.cicd.thresholds import (
    EvaluationResult,
    GateResult,
    ThresholdEvaluator,
    ThresholdResult,
)


class TestThresholdEvaluator:
    """Tests for ThresholdEvaluator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CICDConfig(
            gates=[
                EvaluationGate(
                    name="test_gate",
                    thresholds=[
                        ThresholdConfig(
                            metric="faithfulness",
                            operator=ThresholdOperator.GTE,
                            value=0.8,
                        ),
                        ThresholdConfig(
                            metric="relevancy",
                            operator=ThresholdOperator.GTE,
                            value=0.7,
                        ),
                    ],
                )
            ]
        )
        self.evaluator = ThresholdEvaluator(self.config)

    def test_init(self):
        """Test ThresholdEvaluator initialization."""
        assert self.evaluator.config == self.config

    def test_compare_gt(self):
        """Test greater than comparison."""
        assert ThresholdEvaluator._compare(0.9, ThresholdOperator.GT, 0.8) is True
        assert ThresholdEvaluator._compare(0.8, ThresholdOperator.GT, 0.8) is False
        assert ThresholdEvaluator._compare(0.7, ThresholdOperator.GT, 0.8) is False

    def test_compare_gte(self):
        """Test greater than or equal comparison."""
        assert ThresholdEvaluator._compare(0.9, ThresholdOperator.GTE, 0.8) is True
        assert ThresholdEvaluator._compare(0.8, ThresholdOperator.GTE, 0.8) is True
        assert ThresholdEvaluator._compare(0.7, ThresholdOperator.GTE, 0.8) is False

    def test_compare_lt(self):
        """Test less than comparison."""
        assert ThresholdEvaluator._compare(0.7, ThresholdOperator.LT, 0.8) is True
        assert ThresholdEvaluator._compare(0.8, ThresholdOperator.LT, 0.8) is False
        assert ThresholdEvaluator._compare(0.9, ThresholdOperator.LT, 0.8) is False

    def test_compare_lte(self):
        """Test less than or equal comparison."""
        assert ThresholdEvaluator._compare(0.7, ThresholdOperator.LTE, 0.8) is True
        assert ThresholdEvaluator._compare(0.8, ThresholdOperator.LTE, 0.8) is True
        assert ThresholdEvaluator._compare(0.9, ThresholdOperator.LTE, 0.8) is False

    def test_compare_eq(self):
        """Test equal comparison."""
        assert ThresholdEvaluator._compare(0.8, ThresholdOperator.EQ, 0.8) is True
        assert ThresholdEvaluator._compare(0.8000001, ThresholdOperator.EQ, 0.8) is True
        assert ThresholdEvaluator._compare(0.9, ThresholdOperator.EQ, 0.8) is False

    def test_compare_neq(self):
        """Test not equal comparison."""
        assert ThresholdEvaluator._compare(0.9, ThresholdOperator.NEQ, 0.8) is True
        assert ThresholdEvaluator._compare(0.8, ThresholdOperator.NEQ, 0.8) is False
        assert ThresholdEvaluator._compare(0.81, ThresholdOperator.NEQ, 0.8) is True

    def test_evaluate_threshold_pass(self):
        """Test evaluating a passing threshold."""
        threshold = ThresholdConfig(
            metric="faithfulness",
            operator=ThresholdOperator.GTE,
            value=0.8,
        )
        result = self.evaluator.evaluate_threshold(threshold, 0.85)
        assert result.passed is True
        assert result.actual_value == 0.85
        assert "✓" in result.message

    def test_evaluate_threshold_fail(self):
        """Test evaluating a failing threshold."""
        threshold = ThresholdConfig(
            metric="faithfulness",
            operator=ThresholdOperator.GTE,
            value=0.8,
        )
        result = self.evaluator.evaluate_threshold(threshold, 0.75)
        assert result.passed is False
        assert result.actual_value == 0.75
        assert "✗" in result.message

    def test_evaluate_threshold_none_value(self):
        """Test evaluating threshold with None value."""
        threshold = ThresholdConfig(
            metric="faithfulness",
            operator=ThresholdOperator.GTE,
            value=0.8,
        )
        result = self.evaluator.evaluate_threshold(threshold, None)
        assert result.passed is False
        assert result.actual_value is None
        assert "not found" in result.message

    def test_evaluate_gate_pass(self):
        """Test evaluating a passing gate."""
        gate = EvaluationGate(
            name="pass_gate",
            thresholds=[
                ThresholdConfig(metric="faithfulness", value=0.8),
            ],
        )
        metrics = {"faithfulness": 0.85}
        result = self.evaluator.evaluate_gate(gate, metrics)
        assert result.passed is True
        assert len(result.threshold_results) == 1
        assert result.threshold_results[0].passed is True

    def test_evaluate_gate_fail(self):
        """Test evaluating a failing gate."""
        gate = EvaluationGate(
            name="fail_gate",
            thresholds=[
                ThresholdConfig(metric="faithfulness", value=0.8),
            ],
        )
        metrics = {"faithfulness": 0.75}
        result = self.evaluator.evaluate_gate(gate, metrics)
        assert result.passed is False
        assert len(result.failure_reasons) > 0

    def test_evaluate_gate_missing_metric(self):
        """Test evaluating gate with missing metric."""
        gate = EvaluationGate(
            name="missing_gate",
            thresholds=[
                ThresholdConfig(metric="faithfulness", value=0.8),
            ],
        )
        metrics = {}
        result = self.evaluator.evaluate_gate(gate, metrics)
        assert result.passed is False

    def test_evaluate_all_gates_pass(self):
        """Test evaluating all gates that pass."""
        metrics = {
            "faithfulness": 0.85,
            "relevancy": 0.75,
        }
        result = self.evaluator.evaluate_all_gates(metrics)
        assert result.passed is True
        assert result.summary["passed_gates"] == 1
        assert result.summary["failed_gates"] == 0

    def test_evaluate_all_gates_fail(self):
        """Test evaluating all gates with one failing."""
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
                        ThresholdConfig(metric="relevancy", value=0.9),  # Will fail
                    ],
                ),
            ]
        )
        evaluator = ThresholdEvaluator(config)
        metrics = {
            "faithfulness": 0.85,
            "relevancy": 0.75,
        }
        result = evaluator.evaluate_all_gates(metrics)
        assert result.passed is False
        assert result.summary["passed_gates"] == 1
        assert result.summary["failed_gates"] == 1

    def test_evaluate_all_gates_warn_behavior(self):
        """Test evaluating gates with warn behavior doesn't fail."""
        config = CICDConfig(
            gates=[
                EvaluationGate(
                    name="warn_gate",
                    thresholds=[
                        ThresholdConfig(metric="faithfulness", value=0.8),
                    ],
                    behavior=GateBehavior.WARN,
                ),
            ]
        )
        evaluator = ThresholdEvaluator(config)
        metrics = {"faithfulness": 0.75}  # Will fail threshold
        result = evaluator.evaluate_all_gates(metrics)
        # Warn behavior doesn't fail overall
        assert result.passed is True
        assert result.summary["failed_gates"] == 1

    def test_create_test_result_passed(self):
        """Test creating TestResult from passed evaluation."""
        # Use a simple config with one gate that will pass
        config = CICDConfig(
            gates=[
                EvaluationGate(
                    name="simple_gate",
                    thresholds=[
                        ThresholdConfig(
                            metric="score",
                            operator=ThresholdOperator.GTE,
                            value=0.8,
                        ),
                    ],
                )
            ]
        )
        evaluator = ThresholdEvaluator(config)
        metrics = {"score": 0.85}
        eval_result = evaluator.evaluate_all_gates(metrics)
        test_result = evaluator.create_test_result(eval_result, duration_seconds=1.5)
        assert test_result.status.value == "passed"
        assert test_result.duration_seconds == 1.5
        assert len(test_result.gate_results) == 1

    def test_create_test_result_failed(self):
        """Test creating TestResult from failed evaluation."""
        metrics = {"faithfulness": 0.75}  # Will fail
        eval_result = self.evaluator.evaluate_all_gates(metrics)
        test_result = self.evaluator.create_test_result(eval_result)
        assert test_result.status.value == "failed"


class TestThresholdResult:
    """Tests for ThresholdResult dataclass."""

    def test_creation(self):
        """Test creating a ThresholdResult."""
        result = ThresholdResult(
            metric="faithfulness",
            operator=ThresholdOperator.GTE,
            threshold_value=0.8,
            actual_value=0.85,
            passed=True,
            message="faithfulness: 0.8500 gte 0.8000 ✓",
        )
        assert result.metric == "faithfulness"
        assert result.passed is True


class TestGateResult:
    """Tests for GateResult dataclass."""

    def test_creation(self):
        """Test creating a GateResult."""
        result = GateResult(
            gate_name="test_gate",
            passed=True,
            behavior=GateBehavior.FAIL,
        )
        assert result.gate_name == "test_gate"
        assert result.passed is True
        assert result.threshold_results == []
        assert result.failure_reasons == []


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_creation(self):
        """Test creating an EvaluationResult."""
        result = EvaluationResult(passed=True)
        assert result.passed is True
        assert result.gate_results == []
        assert result.summary == {}
