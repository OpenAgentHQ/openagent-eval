"""Tests for EvalPortReport generator.

Every test here validates its produced ResultSet against the real
``openeval.validate.validate_result_set`` from evalport-sdk (not a mock or a
hand-rolled schema check) -- these tests are skipped, not faked, if
evalport-sdk is not installed (see ``pytest.importorskip`` below), since
validating against anything other than the actual EvalPort SDK's validator
would not prove the adapter's output is spec-conformant.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from openagent_eval.core.engine import EvaluationReport
from openagent_eval.core.pipeline import EvaluationResult, PipelineResult
from openagent_eval.reports.evalport import (
    DEFAULT_PASS_THRESHOLD,
    EvalPortReport,
    evaluation_report_to_result_set,
)

if TYPE_CHECKING:
    from pathlib import Path

    from openagent_eval.config.models import Config

openeval_validate = pytest.importorskip(
    "openeval.validate",
    reason="evalport-sdk not installed (pip install openagent-eval[evalport])",
)


def _assert_valid_result_set(result_set: dict[str, Any]) -> None:
    """Validate a ResultSet dict against the real evalport-sdk validator."""
    validation = openeval_validate.validate_result_set(result_set)
    assert validation.valid, (
        f"ResultSet failed EvalPort validation: {validation.errors}"
    )


class TestEvaluationReportToResultSet:
    """Tests for the standalone evaluation_report_to_result_set() function."""

    def test_returns_valid_result_set(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """The produced dict validates against openeval.validate.validate_result_set."""
        result_set = evaluation_report_to_result_set(evaluation_report)
        _assert_valid_result_set(result_set)

    def test_version_is_semver(self, evaluation_report: EvaluationReport) -> None:
        """version must match the same SEMVER_RE the real validator checks it against."""
        from openeval import SEMVER_RE

        result_set = evaluation_report_to_result_set(evaluation_report)
        assert isinstance(result_set["version"], str)
        assert SEMVER_RE.match(result_set["version"])

    def test_result_count_includes_errors(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """results includes both successful EvaluationResults and pipeline errors.

        The fixture has 3 EvaluationResults + 2 pipeline errors -- EvalPort's
        Result schema has no concept of an item that was never evaluated, so
        each error becomes its own failed Result rather than being dropped.
        """
        result_set = evaluation_report_to_result_set(evaluation_report)
        assert len(result_set["results"]) == 5
        assert result_set["summary"]["total"] == 5

    def test_test_case_id_reads_metadata_id(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """test_case_id prefers EvaluationResult.metadata['id'] when present."""
        result_set = evaluation_report_to_result_set(evaluation_report)
        # pipeline_result_with_data fixture sets metadata={"id": 1/2/3} on its
        # three successful EvaluationResults, in order.
        ids = [r["test_case_id"] for r in result_set["results"][:3]]
        assert ids == ["1", "2", "3"]

    def test_test_case_id_falls_back_positionally_for_errors(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """Errors with no metadata.id fall back to f'{run_id}_error_{i}'."""
        result_set = evaluation_report_to_result_set(evaluation_report, run_id="myrun")
        error_ids = [r["test_case_id"] for r in result_set["results"][3:]]
        assert error_ids == ["myrun_error_0", "myrun_error_1"]

    def test_grader_results_one_per_metric(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """Each metric on an EvaluationResult becomes one GraderResult."""
        result_set = evaluation_report_to_result_set(evaluation_report)
        first = result_set["results"][0]
        grader_ids = {g["grader_id"] for g in first["grader_results"]}
        assert grader_ids == {"precision", "recall", "faithfulness"}
        for g in first["grader_results"]:
            assert g["type"] == "custom"
            assert 0.0 <= g["score"] <= 1.0
            assert isinstance(g["passed"], bool)

    def test_default_threshold_pass(self, evaluation_report: EvaluationReport) -> None:
        """All fixture scores are >= 0.5, the default threshold -> every result passes."""
        result_set = evaluation_report_to_result_set(evaluation_report)
        for r in result_set["results"][:3]:
            assert r["passed"] is True
            assert all(g["passed"] for g in r["grader_results"])

    def test_custom_threshold_can_fail_a_metric(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """A stricter evalport_thresholds entry can flip a grader (and the result) to failing."""
        # Item 1's precision is 0.95; item 3's precision is 0.78.
        result_set = evaluation_report_to_result_set(
            evaluation_report, evalport_thresholds={"precision": 0.99}
        )
        precisions = [
            next(g for g in r["grader_results"] if g["grader_id"] == "precision")
            for r in result_set["results"][:3]
        ]
        assert all(g["passed"] is False for g in precisions)
        # A failing grader_result makes the whole Result fail, per EvalPort's
        # "every grader result must pass" convention.
        assert all(r["passed"] is False for r in result_set["results"][:3])

    def test_derived_pass_is_flagged(self, evaluation_report: EvaluationReport) -> None:
        """Every result's metadata.openeval_derived_pass is True, since OpenAgent Eval
        has no native pass/fail -- this is always a threshold-derived judgment."""
        result_set = evaluation_report_to_result_set(evaluation_report)
        for r in result_set["results"]:
            assert r["metadata"]["openeval_derived_pass"] is True

    def test_actual_output_maps_from_answer(
        self, evaluation_report: EvaluationReport
    ) -> None:
        result_set = evaluation_report_to_result_set(evaluation_report)
        assert (
            result_set["results"][0]["actual_output"]
            == "Python is a programming language."
        )

    def test_question_and_ground_truth_preserved_in_metadata(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """question/ground_truth/contexts have no Result-schema field of their own
        (Result has no `input`/`expected_output`), so they're preserved under
        metadata.openagent_eval instead of being dropped or invented as new
        top-level keys the schema doesn't define."""
        result_set = evaluation_report_to_result_set(evaluation_report)
        first_meta = result_set["results"][0]["metadata"]["openagent_eval"]
        assert first_meta["question"] == "What is Python?"
        assert (
            first_meta["ground_truth"] == "Python is a high-level programming language."
        )
        assert first_meta["contexts"] == [
            "Python is a programming language created by Guido van Rossum."
        ]

    def test_error_entries_carry_error_detail(
        self, evaluation_report: EvaluationReport
    ) -> None:
        result_set = evaluation_report_to_result_set(evaluation_report)
        error_results = result_set["results"][3:]
        assert error_results[0]["error"]["message"] == "Connection timeout"
        assert error_results[0]["error"]["detail"] == "ProviderConnectionError"
        assert error_results[0]["grader_results"] == []
        assert error_results[0]["passed"] is False

    def test_duration_ms_present_when_latency_available(
        self, sample_config: Config
    ) -> None:
        """metadata['latency_ms'] (set by Pipeline._evaluate_item) maps to duration_ms,
        rounded to the nearest non-negative integer millisecond."""
        result = PipelineResult(
            results=[
                EvaluationResult(
                    question="q",
                    answer="a",
                    metrics={"faithfulness": 0.9},
                    metadata={"id": "x1", "latency_ms": 123.6},
                )
            ],
        )
        report = EvaluationReport(config=sample_config, result=result)
        result_set = evaluation_report_to_result_set(report)
        assert result_set["results"][0]["duration_ms"] == 124
        _assert_valid_result_set(result_set)

    def test_duration_ms_absent_when_latency_missing(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """The fixture's EvaluationResults carry no latency_ms -> no duration_ms key."""
        result_set = evaluation_report_to_result_set(evaluation_report)
        assert "duration_ms" not in result_set["results"][0]

    def test_score_out_of_range_is_clamped(self, sample_config: Config) -> None:
        """A misbehaving third-party metric that doesn't go through MetricResult's
        own [0,1] enforcement is still defensively clamped before it can produce
        an invalid ResultSet."""
        result = PipelineResult(
            results=[
                EvaluationResult(
                    question="q",
                    answer="a",
                    metrics={"weird_metric": 1.5},
                    metadata={"id": "x1"},
                )
            ],
        )
        report = EvaluationReport(config=sample_config, result=result)
        result_set = evaluation_report_to_result_set(report)
        assert result_set["results"][0]["grader_results"][0]["score"] == 1.0
        _assert_valid_result_set(result_set)

    def test_none_scores_are_skipped(self, sample_config: Config) -> None:
        result = PipelineResult(
            results=[
                EvaluationResult(
                    question="q",
                    answer="a",
                    metrics={"faithfulness": None},  # type: ignore[dict-item]
                    metadata={"id": "x1"},
                )
            ],
        )
        report = EvaluationReport(config=sample_config, result=result)
        result_set = evaluation_report_to_result_set(report)
        assert result_set["results"][0]["grader_results"] == []
        # No grader results -> cannot confirm a pass.
        assert result_set["results"][0]["passed"] is False

    def test_empty_report_raises(
        self, evaluation_report_empty: EvaluationReport
    ) -> None:
        with pytest.raises(ValueError, match="empty"):
            evaluation_report_to_result_set(evaluation_report_empty)

    def test_suite_id_defaults_to_dataset_path(
        self, evaluation_report: EvaluationReport
    ) -> None:
        result_set = evaluation_report_to_result_set(evaluation_report)
        assert result_set["suite_id"] == "tests/sample_data/test_dataset.json"

    def test_suite_id_override(self, evaluation_report: EvaluationReport) -> None:
        result_set = evaluation_report_to_result_set(
            evaluation_report, suite_id="custom_suite"
        )
        assert result_set["suite_id"] == "custom_suite"

    def test_run_id_override(self, evaluation_report: EvaluationReport) -> None:
        result_set = evaluation_report_to_result_set(evaluation_report, run_id="run-42")
        assert result_set["run_id"] == "run-42"

    def test_summary_pass_rate(self, evaluation_report: EvaluationReport) -> None:
        result_set = evaluation_report_to_result_set(evaluation_report)
        summary = result_set["summary"]
        assert summary["total"] == 5
        assert summary["passed"] == 3  # 3 successful, all pass at the default threshold
        assert summary["failed"] == 2  # 2 pipeline errors
        assert summary["pass_rate"] == pytest.approx(3 / 5)

    def test_openagent_eval_metadata_present(
        self, evaluation_report: EvaluationReport
    ) -> None:
        result_set = evaluation_report_to_result_set(evaluation_report)
        assert result_set["metadata"]["openagent_eval"]["engine"] == "openagent-eval"
        assert result_set["metadata"]["openagent_eval"]["config_summary"] == (
            evaluation_report.summary
        )

    def test_default_pass_threshold_constant(self) -> None:
        assert DEFAULT_PASS_THRESHOLD == 0.5


class TestEvalPortReport:
    """Tests for the EvalPortReport ReportGenerator subclass."""

    def test_generate_returns_valid_json(
        self, evaluation_report: EvaluationReport
    ) -> None:
        report = EvalPortReport()
        result = report.generate(evaluation_report)
        assert isinstance(result, str)
        data = json.loads(result)
        _assert_valid_result_set(data)

    def test_generate_respects_constructor_thresholds(
        self, evaluation_report: EvaluationReport
    ) -> None:
        report = EvalPortReport(evalport_thresholds={"precision": 0.99})
        data = json.loads(report.generate(evaluation_report))
        assert data["results"][0]["passed"] is False

    def test_to_result_set_matches_generate(
        self, evaluation_report: EvaluationReport
    ) -> None:
        report = EvalPortReport(run_id="fixed-run")
        as_dict = report.to_result_set(evaluation_report)
        as_json = json.loads(report.generate(evaluation_report))
        assert as_dict == as_json

    def test_generate_to_file(
        self, evaluation_report: EvaluationReport, tmp_path: Path
    ) -> None:
        report = EvalPortReport()
        output_path = tmp_path / "result_set.json"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path == output_path
        assert result_path.exists()
        data = json.loads(result_path.read_text(encoding="utf-8"))
        _assert_valid_result_set(data)

    def test_generate_to_file_adds_extension_for_bare_path(
        self, evaluation_report: EvaluationReport, tmp_path: Path
    ) -> None:
        """A suffix-less path is treated as a directory, matching JSONReport's
        own generate_to_file() convention."""
        report = EvalPortReport()
        output_path = tmp_path / "out"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path == output_path / "result_set.json"
        assert result_path.exists()

    def test_generate_to_file_replaces_non_json_extension(
        self, evaluation_report: EvaluationReport, tmp_path: Path
    ) -> None:
        report = EvalPortReport()
        output_path = tmp_path / "result_set.txt"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path == tmp_path / "result_set.json"
        assert result_path.exists()

    def test_generate_to_file_creates_parent_directories(
        self, evaluation_report: EvaluationReport, tmp_path: Path
    ) -> None:
        report = EvalPortReport()
        output_path = tmp_path / "nested" / "dir" / "result_set.json"
        result_path = report.generate_to_file(evaluation_report, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_generate_empty_report_raises(
        self, evaluation_report_empty: EvaluationReport
    ) -> None:
        report = EvalPortReport()
        with pytest.raises(ValueError, match="empty"):
            report.generate(evaluation_report_empty)

    def test_compact_indent(self, evaluation_report: EvaluationReport) -> None:
        report = EvalPortReport(indent=0)
        result = report.generate(evaluation_report)
        assert "\n" not in result
        data = json.loads(result)
        _assert_valid_result_set(data)

    def test_is_a_report_generator(self) -> None:
        from openagent_eval.reports.base import ReportGenerator

        assert issubclass(EvalPortReport, ReportGenerator)

    def test_importable_from_reports_package(self) -> None:
        """EvalPortReport is exported from openagent_eval.reports, matching
        every other built-in generator (TerminalReport, JSONReport, ...)."""
        from openagent_eval.reports import EvalPortReport as PackageExport

        assert PackageExport is EvalPortReport
