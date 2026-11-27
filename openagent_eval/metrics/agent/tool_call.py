"""Position-wise correctness of a recorded tool-call sequence."""

from typing import Any

from jsonschema import Draft202012Validator
from pydantic import TypeAdapter

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.types.tool_call import ToolCall

_TRACE = TypeAdapter(list[ToolCall])


def _score_call(expected: ToolCall, actual: ToolCall) -> float:
    if expected.name != actual.name:
        return 0.0

    keys = expected.arguments.keys() | actual.arguments.keys()
    if not keys:
        return 1.0

    # JSON equality distinguishes true from 1, including inside nested arrays.
    matches = sum(
        1
        for key in expected.arguments.keys() & actual.arguments.keys()
        if Draft202012Validator({"const": expected.arguments[key]}).is_valid(
            actual.arguments[key]
        )
    )
    return (1.0 + matches / len(keys)) / 2


class ToolCallCorrectness(BaseMetric):
    """Average position-wise scores over the length of the longer trace."""

    name = "tool_call_correctness"
    description = "Compare recorded tool names and arguments with an expected sequence."

    def evaluate(self, **kwargs: Any) -> MetricResult:
        """Score ordered calls, giving no credit for extra or missing steps."""
        for field in ("expected_tool_calls", "actual_tool_calls"):
            if kwargs.get(field) is None:
                return MetricResult(score=0.0, reason=f"Missing {field}")

        expected = _TRACE.validate_python(kwargs["expected_tool_calls"])
        actual = _TRACE.validate_python(kwargs["actual_tool_calls"])
        length = max(len(expected), len(actual))
        if not length:
            return MetricResult(
                score=1.0, reason="Both traces explicitly contain no calls"
            )

        scores = [
            _score_call(expected_call, actual_call)
            for expected_call, actual_call in zip(expected, actual, strict=False)
        ]
        return MetricResult(
            score=sum(scores) / length,
            reason=f"{scores.count(1.0)} of {length} positions match exactly",
            metadata={"expected_calls": len(expected), "actual_calls": len(actual)},
        )
