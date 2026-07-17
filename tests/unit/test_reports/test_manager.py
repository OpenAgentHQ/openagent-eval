"""Tests for ReportManager.reconstruct() edge cases.

These tests characterize the *current* behavior of
``ReportManager.reconstruct()`` for happy-path and malformed inputs.

NOTE ON THE ORIGINATING ISSUE (#105): the issue states that reconstruct()
"silently creates a default Config when the config section is missing".
That premise does NOT match the code as it stands: a missing/empty/None
``config`` section raises ``ValueError`` (see manager.py:178-182). The tests
below pin the *actual* raise-on-missing behavior rather than the aspirational
silent-default behavior described in the issue.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

from openagent_eval.config.models import Config
from openagent_eval.core.engine import EvaluationReport
from openagent_eval.reports.manager import ReportManager

if TYPE_CHECKING:
    from pathlib import Path


def _valid_config_dict() -> dict[str, Any]:
    """A minimal ``config`` payload accepted by ``Config(**config)``.

    ``dataset`` and ``llm`` are the only required top-level fields; everything
    else on ``Config`` has a default.
    """
    return {
        "dataset": {"path": "tests/sample_data/test_dataset.json"},
        "llm": {"provider": "openai", "model": "gpt-4o"},
    }


class TestReconstructHappyPath:
    """reconstruct() with a complete report JSON round-trips correctly."""

    def test_round_trips_saved_report(
        self,
        evaluation_report: EvaluationReport,
        tmp_path: Path,
    ) -> None:
        """A report saved then loaded reconstructs into an equivalent object."""
        manager = ReportManager()
        manager.save_report(evaluation_report, tmp_path, report_id="rt")
        data = manager.load_report("rt", tmp_path)

        rebuilt = manager.reconstruct(data)

        assert isinstance(rebuilt, EvaluationReport)
        # Config survives the model_dump -> Config(**dump) round-trip.
        assert isinstance(rebuilt.config, Config)
        assert rebuilt.config == evaluation_report.config
        # Results are preserved exactly (count and per-item fields).
        assert len(rebuilt.result.results) == 3
        assert rebuilt.result.results[0].question == "What is Python?"
        assert rebuilt.result.results[0].answer == "Python is a programming language."
        assert rebuilt.result.results[0].ground_truth == (
            "Python is a high-level programming language."
        )
        assert rebuilt.result.results[0].contexts == [
            "Python is a programming language created by Guido van Rossum."
        ]
        assert rebuilt.result.results[0].metrics == {
            "precision": 0.95,
            "recall": 0.88,
            "faithfulness": 0.92,
        }
        assert rebuilt.result.results[0].metadata == {"id": 1}
        # Errors are preserved exactly (count and content).
        assert len(rebuilt.result.errors) == 2
        assert rebuilt.result.errors[0]["error_type"] == "ProviderConnectionError"
        # Summary and metadata are preserved.
        assert rebuilt.summary == data["summary"]
        assert rebuilt.metadata == data["metadata"]

    def test_reconstructs_plain_dict(self) -> None:
        """reconstruct() works on a hand-built dict, not just a saved report."""
        data: dict[str, Any] = {
            "config": _valid_config_dict(),
            "results": [
                {
                    "question": "Q1",
                    "answer": "A1",
                    "ground_truth": "GT1",
                    "contexts": ["c1"],
                    "metrics": {"precision": 0.5},
                    "metadata": {"id": 7},
                }
            ],
            "summary": {"total": 1},
            "metadata": {"engine": "openagent-eval"},
            "errors": [{"error": "boom", "error_type": "X"}],
        }

        rebuilt = ReportManager.reconstruct(data)

        assert isinstance(rebuilt, EvaluationReport)
        assert len(rebuilt.result.results) == 1
        assert rebuilt.result.results[0].question == "Q1"
        assert rebuilt.result.results[0].metadata == {"id": 7}
        assert rebuilt.summary == {"total": 1}
        assert len(rebuilt.result.errors) == 1

    def test_missing_optional_sections_use_defaults(self) -> None:
        """Only ``config`` is required; other sections default to empty."""
        rebuilt = ReportManager.reconstruct({"config": _valid_config_dict()})

        assert rebuilt.result.results == []
        assert rebuilt.result.errors == []
        assert rebuilt.summary == {}
        assert rebuilt.metadata == {}


class TestReconstructMissingConfig:
    """reconstruct() with the config section missing.

    CHARACTERIZATION: contrary to issue #105's description ("silently creates a
    default Config"), the current code RAISES ``ValueError`` for a missing,
    ``None``, or empty ``config`` section (manager.py:178-182). The empty-dict
    case is covered because the guard is ``if not config`` (truthiness), not
    ``if config is None``.
    """

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({"results": []}, id="key-absent"),
            pytest.param({"config": None}, id="config-none"),
            pytest.param({"config": {}}, id="config-empty-dict"),
        ],
    )
    def test_missing_config_raises_value_error(self, data: dict[str, Any]) -> None:
        """A falsy config section raises ValueError with a descriptive message."""
        with pytest.raises(ValueError) as exc_info:
            ReportManager.reconstruct(data)
        assert "'config' section is missing" in str(exc_info.value)


class TestReconstructMalformedData:
    """reconstruct() with malformed data raises informative errors."""

    @pytest.mark.parametrize(
        "bad_config",
        [
            pytest.param("not-a-dict", id="config-str"),
            pytest.param([1, 2, 3], id="config-list"),
        ],
    )
    def test_config_not_a_mapping_raises_type_error(self, bad_config: Any) -> None:
        """A non-mapping config value fails at ``Config(**config)``."""
        with pytest.raises(TypeError) as exc_info:
            ReportManager.reconstruct({"config": bad_config})
        assert "must be a mapping" in str(exc_info.value)

    def test_results_containing_non_dict_raises_attribute_error(self) -> None:
        """A results list holding a non-dict fails on the ``.get`` access."""
        data = {"config": _valid_config_dict(), "results": ["not-a-dict"]}
        with pytest.raises(AttributeError) as exc_info:
            ReportManager.reconstruct(data)
        assert "get" in str(exc_info.value)

    def test_invalid_config_field_value_raises_validation_error(self) -> None:
        """A config value that violates a Config constraint fails validation."""
        bad = _valid_config_dict()
        # temperature has an upper bound of 2.0 on LLMConfig.
        bad["llm"] = {"provider": "openai", "model": "gpt-4o", "temperature": 9.0}
        with pytest.raises(ValidationError) as exc_info:
            ReportManager.reconstruct({"config": bad})
        assert "temperature" in str(exc_info.value)


class TestReconstructMissingRequiredFields:
    """reconstruct() with a config that omits required fields."""

    def test_missing_both_required_fields(self) -> None:
        """Omitting dataset and llm yields exactly two validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            ReportManager.reconstruct({"config": {"verbose": True}})
        assert exc_info.value.error_count() == 2
        message = str(exc_info.value)
        assert "dataset" in message
        assert "llm" in message

    def test_missing_llm_only(self) -> None:
        """Omitting just llm yields exactly one validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ReportManager.reconstruct(
                {"config": {"dataset": {"path": "tests/sample_data/test_dataset.json"}}}
            )
        assert exc_info.value.error_count() == 1
        assert "llm" in str(exc_info.value)
