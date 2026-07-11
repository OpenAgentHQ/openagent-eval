"""CI/CD integration module for OpenAgent Eval.

This module provides pytest plugin integration and threshold-based test gating
for CI/CD pipelines.
"""

from openagent_eval.cicd.models import (
    CICDConfig,
    ThresholdConfig,
    TestResult,
    EvaluationGate,
)
from openagent_eval.cicd.thresholds import ThresholdEvaluator, GateResult
from openagent_eval.cicd.plugin import OAEvalPlugin

__all__ = [
    "CICDConfig",
    "ThresholdConfig",
    "TestResult",
    "EvaluationGate",
    "ThresholdEvaluator",
    "GateResult",
    "OAEvalPlugin",
]
