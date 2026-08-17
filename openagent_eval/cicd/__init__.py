"""CI/CD integration module for OpenAgent Eval.

This module provides pytest plugin integration and threshold-based test gating
for CI/CD pipelines.
"""

from openagent_eval.cicd.models import (
    CICDConfig,
    EvaluationGate,
    TestResult,
    ThresholdConfig,
)
from openagent_eval.cicd.plugin import OAEvalPlugin
from openagent_eval.cicd.thresholds import GateResult, ThresholdEvaluator

__all__ = [
    "CICDConfig",
    "ThresholdConfig",
    "TestResult",
    "EvaluationGate",
    "ThresholdEvaluator",
    "GateResult",
    "OAEvalPlugin",
]
