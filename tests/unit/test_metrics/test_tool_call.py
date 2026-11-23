"""Recorded tool traces are scored in order against the expected calls."""

import pytest
from pydantic import ValidationError

from openagent_eval.datasets.models import DatasetItemModel
from openagent_eval.metrics import get_metric

SEARCH = {"name": "search_documents", "arguments": {"matter_id": "A"}}
WRONG_MATTER = {"name": "search_documents", "arguments": {"matter_id": "B"}}
DRAFT = {"name": "draft_document", "arguments": {}}


@pytest.mark.parametrize(
    ("expected", "actual", "score"),
    [
        ([SEARCH], [SEARCH], 1.0),
        ([SEARCH], [WRONG_MATTER], 0.5),
        ([SEARCH], [DRAFT], 0.0),
        ([DRAFT], [DRAFT], 1.0),
        ([SEARCH, DRAFT], [DRAFT, SEARCH], 0.0),
        ([SEARCH, DRAFT], [SEARCH], 0.5),
        ([SEARCH], [SEARCH, SEARCH], 0.5),
        ([], [SEARCH], 0.0),
        ([SEARCH], [], 0.0),
        ([], [], 1.0),
        (None, [], 0.0),
        ([], None, 0.0),
        (None, None, 0.0),
    ],
)
def test_scores_recorded_sequence(expected, actual, score):
    metric = get_metric("tool_call_correctness")()
    result = metric.evaluate(expected_tool_calls=expected, actual_tool_calls=actual)
    assert result.score == score


@pytest.mark.parametrize(
    ("expected", "actual", "score"),
    [
        ({"matter": "A", "page": 2}, {"page": 2, "matter": "B"}, 0.75),
        ({"x": None}, {"y": None}, 0.5),
        ({"x": 1}, {"x": 1, "y": None}, 0.75),
        ({"x": 1, "y": None}, {"x": 1}, 0.75),
        ({"x": {"a": [1, 2], "b": 0}}, {"x": {"b": 0.0, "a": [1, 2]}}, 1.0),
        ({"x": [1, 2]}, {"x": [2, 1]}, 0.5),
        ({"x": [True]}, {"x": [1]}, 0.5),
    ],
)
def test_argument_similarity_uses_keys_and_json_values(expected, actual, score):
    result = get_metric("tool_call_correctness")().evaluate(
        expected_tool_calls=[{"name": "search", "arguments": expected}],
        actual_tool_calls=[{"name": "search", "arguments": actual}],
    )
    assert result.score == score


@pytest.mark.parametrize("field", ["expected_tool_calls", "actual_tool_calls"])
@pytest.mark.parametrize(
    "bad_call",
    [{"name": "  "}, {"arguments": {}}, {"name": "search", "arguments": "oops"}],
)
def test_invalid_dataset_call_is_rejected(field, bad_call):
    with pytest.raises(ValidationError):
        DatasetItemModel.model_validate({"question": "Search?", field: [bad_call]})
