"""Tests for EvalPortReport generator.

Every test here validates its produced ResultSet against the real
``openeval.validate.validate_result_set`` from evalport-sdk (not a mock or a
hand-rolled schema check) -- these tests are skipped, not faked, if
evalport-sdk is not installed (see ``pytest.importorskip`` below), since
validating against anything other than the actual EvalPort SDK's validator
would not prove the adapter's output is spec-conformant.

Two families of fixtures are used:

- The shared ``evaluation_report`` fixture from ``conftest.py`` (backed by
  ``pipeline_result_with_data``): 3 successful ``EvaluationResult``s plus a
  separate, non-overlapping ``PipelineResult.errors`` list. That shape is
  shared with every other report generator's tests (``JSONReport`` etc.,
  which read ``result.errors`` directly and are unaffected by anything
  below), so it is left untouched here -- this module only asserts what its
  own exporter does with it, which is to walk ``result.results`` and ignore
  ``result.errors`` entirely (see the module docstring on
  ``openagent_eval.reports.evalport`` for why).
- The local ``realistic_evaluation_report`` fixture below, which instead
  mirrors what ``Pipeline._evaluate_item`` actually produces on a failure:
  the SAME failure recorded both as a zeroed, ``metadata["failed"] = True``
  ``EvaluationResult`` in ``results`` AND as a dict in ``errors``. This is
  the shape that exposed the double-counting bug this module's exporter used
  to have (every failure exported twice), so it is what the regression tests
  for that fix are built against -- asserting against the old fixture would
  not catch a regression, since that fixture was never shaped like real
  pipeline output in the first place.
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


@pytest.fixture
def realistic_pipeline_result() -> PipelineResult:
    """A PipelineResult shaped exactly like real ``Pipeline.execute()`` output.

    2 items succeed normally. 2 items fail inside
    ``Pipeline._evaluate_item``'s exception boundary -- each failure is
    represented TWICE in the real pipeline's own output, matching
    ``pipeline.py``'s actual behavior (post-fix, which now also spreads the
    original item's ``metadata`` into the failure, same as the success
    path):

    - once as a zeroed ``EvaluationResult`` in ``results`` (``metrics`` all
      ``0.0``, ``metadata={"failed": True, "error": ..., "error_type": ...,
      **item_metadata}``), in dataset order;
    - once as a plain dict in ``errors`` (``{"item": ..., "error": ...,
      "error_type": ...}``), in whatever order the coroutines completed --
      here written in reverse of dataset order specifically to prove the
      exporter does not (and safely cannot) rely on ``errors`` ordering.
    """
    results = [
        EvaluationResult(
            question="What is Python?",
            answer="Python is a programming language.",
            metrics={"faithfulness": 0.9},
            metadata={"id": "ok-1"},
        ),
        EvaluationResult(
            question="Failing question A",
            answer="",
            metrics={"faithfulness": 0.0},
            metadata={
                "failed": True,
                "error": "Connection timeout",
                "error_type": "ProviderConnectionError",
                "id": "fail-a",
            },
        ),
        EvaluationResult(
            question="What is RAG?",
            answer="RAG combines retrieval and generation.",
            metrics={"faithfulness": 0.85},
            metadata={"id": "ok-2"},
        ),
        EvaluationResult(
            question="Failing question B",
            answer="",
            metrics={"faithfulness": 0.0},
            # No dataset-provided id -- must fall back positionally to this
            # item's own index within `results` (3), not the index it
            # happens to occupy in the (differently ordered) `errors` list.
            metadata={
                "failed": True,
                "error": "Invalid response format",
                "error_type": "ProviderExecutionError",
            },
        ),
    ]
    errors = [
        # Reverse dataset order on purpose (see docstring above).
        {
            "item": {"question": "Failing question B"},
            "error": "Invalid response format",
            "error_type": "ProviderExecutionError",
        },
        {
            "item": {"question": "Failing question A"},
            "error": "Connection timeout",
            "error_type": "ProviderConnectionError",
        },
    ]
    return PipelineResult(
        results=results,
        summary={"total": 4, "errors": 2},
        errors=errors,
    )


@pytest.fixture
def realistic_evaluation_report(
    sample_config: Config,
    realistic_pipeline_result: PipelineResult,
) -> EvaluationReport:
    """An EvaluationReport wrapping :func:`realistic_pipeline_result`."""
    return EvaluationReport(
        config=sample_config,
        result=realistic_pipeline_result,
        summary={
            "total_items": 4,
            "successful_evaluations": 2,
            "failed_evaluations": 2,
        },
        metadata={
            "version": "0.1.0",
            "engine": "openagent-eval",
            "title": "Realistic Report",
        },
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

    def test_result_count_matches_results_only(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """results is sourced from PipelineResult.results alone.

        The shared `evaluation_report` fixture's `pipeline_result_with_data`
        has 3 successful EvaluationResults and a separately-tracked,
        non-overlapping `errors` list (a shape real pipeline output never
        actually produces -- see this module's docstring). The exporter
        does not consume `PipelineResult.errors` at all (see
        `openagent_eval.reports.evalport`'s module docstring for why), so
        only the 3 successes show up here.
        """
        result_set = evaluation_report_to_result_set(evaluation_report)
        assert len(result_set["results"]) == 3
        assert result_set["summary"]["total"] == 3

    def test_test_case_id_reads_metadata_id(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """test_case_id prefers EvaluationResult.metadata['id'] when present."""
        result_set = evaluation_report_to_result_set(evaluation_report)
        # pipeline_result_with_data fixture sets metadata={"id": 1/2/3} on its
        # three successful EvaluationResults, in order.
        ids = [r["test_case_id"] for r in result_set["results"][:3]]
        assert ids == ["1", "2", "3"]

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

    def test_non_numeric_latency_ms_does_not_crash(self, sample_config: Config) -> None:
        """A non-numeric latency_ms (e.g. injected via a dataset item's own
        metadata spread) is ignored rather than raising a TypeError out of
        round()."""
        result = PipelineResult(
            results=[
                EvaluationResult(
                    question="q",
                    answer="a",
                    metrics={"faithfulness": 0.9},
                    metadata={"id": "x1", "latency_ms": "not-a-number"},
                )
            ],
        )
        report = EvaluationReport(config=sample_config, result=result)
        result_set = evaluation_report_to_result_set(report)
        assert "duration_ms" not in result_set["results"][0]
        _assert_valid_result_set(result_set)

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

    def test_started_at_completed_at_override(
        self, evaluation_report: EvaluationReport
    ) -> None:
        result_set = evaluation_report_to_result_set(
            evaluation_report,
            started_at="2026-01-01T00:00:00Z",
            completed_at="2026-01-01T00:05:00Z",
        )
        assert result_set["started_at"] == "2026-01-01T00:00:00Z"
        assert result_set["completed_at"] == "2026-01-01T00:05:00Z"
        _assert_valid_result_set(result_set)

    def test_summary_pass_rate(self, evaluation_report: EvaluationReport) -> None:
        result_set = evaluation_report_to_result_set(evaluation_report)
        summary = result_set["summary"]
        assert summary["total"] == 3
        assert (
            summary["passed"] == 3
        )  # all 3 successful results pass at the default threshold
        assert summary["failed"] == 0
        assert summary["pass_rate"] == pytest.approx(1.0)

    def test_openagent_eval_metadata_present(
        self, evaluation_report: EvaluationReport
    ) -> None:
        result_set = evaluation_report_to_result_set(evaluation_report)
        assert result_set["metadata"]["openagent_eval"]["engine"] == "openagent-eval"
        assert result_set["metadata"]["openagent_eval"]["title"] == "Test Report"
        assert result_set["metadata"]["openagent_eval"]["config_summary"] == (
            evaluation_report.summary
        )

    def test_title_omitted_when_report_has_no_title(
        self, sample_config: Config
    ) -> None:
        """report.metadata.get('title') is None for every real Engine.run() call
        today (Engine never sets a 'title' key) -- the exported metadata should
        omit the key entirely rather than ship a literal `"title": null`."""
        result = PipelineResult(
            results=[
                EvaluationResult(
                    question="q",
                    answer="a",
                    metrics={"faithfulness": 0.9},
                    metadata={"id": "x1"},
                )
            ],
        )
        report = EvaluationReport(
            config=sample_config,
            result=result,
            metadata={"version": "0.1.0", "engine": "openagent-eval"},  # no "title"
        )
        result_set = evaluation_report_to_result_set(report)
        assert "title" not in result_set["metadata"]["openagent_eval"]
        _assert_valid_result_set(result_set)

    def test_default_pass_threshold_constant(self) -> None:
        assert DEFAULT_PASS_THRESHOLD == 0.5

    def test_default_threshold_above_one_raises(
        self, evaluation_report: EvaluationReport
    ) -> None:
        with pytest.raises(ValueError, match=r"default_threshold.*\[0\.0, 1\.0\]"):
            evaluation_report_to_result_set(evaluation_report, default_threshold=1.5)

    def test_default_threshold_below_zero_raises(
        self, evaluation_report: EvaluationReport
    ) -> None:
        with pytest.raises(ValueError, match=r"default_threshold.*\[0\.0, 1\.0\]"):
            evaluation_report_to_result_set(evaluation_report, default_threshold=-0.1)

    def test_evalport_thresholds_entry_out_of_range_raises(
        self, evaluation_report: EvaluationReport
    ) -> None:
        with pytest.raises(ValueError, match=r"evalport_thresholds\['precision'\]"):
            evaluation_report_to_result_set(
                evaluation_report, evalport_thresholds={"precision": 1.2}
            )


class TestFailedItemRepresentation:
    """Regression coverage for the double-counting bug (#369 review, point 1).

    ``Pipeline._evaluate_item``'s exception boundary records a failure twice
    -- once as a zeroed ``EvaluationResult`` in ``results``, once as a plain
    dict in ``errors`` -- so every test here uses the
    ``realistic_evaluation_report``/``realistic_pipeline_result`` fixtures,
    which reproduce exactly that double-appearance shape, rather than the
    shared ``evaluation_report`` fixture (whose ``results``/``errors`` never
    overlap and so cannot catch a double-counting regression).
    """

    def test_failed_items_are_not_double_counted(
        self, realistic_evaluation_report: EvaluationReport
    ) -> None:
        """4 PipelineResult.results entries (2 ok + 2 failed) -> exactly 4
        Results out, not 6 -- each of the 2 failures must appear once, not
        once from `results` and again from `errors`."""
        result_set = evaluation_report_to_result_set(realistic_evaluation_report)
        assert len(result_set["results"]) == 4
        assert result_set["summary"]["total"] == 4
        assert result_set["summary"]["passed"] == 2
        assert result_set["summary"]["failed"] == 2
        _assert_valid_result_set(result_set)

    def test_failed_result_shape(
        self, realistic_evaluation_report: EvaluationReport
    ) -> None:
        result_set = evaluation_report_to_result_set(realistic_evaluation_report)
        failed = [r for r in result_set["results"] if r["passed"] is False]
        assert len(failed) == 2
        for r in failed:
            assert r["grader_results"] == []
            assert r["metadata"]["openeval_derived_pass"] is True

    def test_failed_result_error_sourced_from_evaluation_result(
        self, realistic_evaluation_report: EvaluationReport
    ) -> None:
        """error.message/error.detail come from the EvaluationResult's own
        metadata (the source of truth used here), not from a separate walk
        over PipelineResult.errors."""
        result_set = evaluation_report_to_result_set(realistic_evaluation_report)
        by_id = {r["test_case_id"]: r for r in result_set["results"]}
        assert by_id["fail-a"]["error"] == {
            "message": "Connection timeout",
            "detail": "ProviderConnectionError",
        }

    def test_failed_result_test_case_id_uses_preserved_item_id(
        self, realistic_evaluation_report: EvaluationReport
    ) -> None:
        """The dataset item's own id, preserved by Pipeline._evaluate_item's
        exception handler into the failed EvaluationResult's metadata, is
        used exactly like a successful item's id would be."""
        result_set = evaluation_report_to_result_set(realistic_evaluation_report)
        ids = [r["test_case_id"] for r in result_set["results"]]
        assert "fail-a" in ids

    def test_failed_result_test_case_id_positional_fallback(
        self, realistic_evaluation_report: EvaluationReport
    ) -> None:
        """The second failure carries no id, so it falls back to this item's
        own positional index within `results` (3) -- not any index derived
        from `errors`, whose order does not track dataset position under the
        parallel executor (see the fixture's docstring)."""
        result_set = evaluation_report_to_result_set(
            realistic_evaluation_report, run_id="myrun"
        )
        ids = [r["test_case_id"] for r in result_set["results"]]
        assert "myrun_item_3" in ids

    def test_failed_result_metadata_excludes_bookkeeping_keys(
        self, realistic_evaluation_report: EvaluationReport
    ) -> None:
        """`failed`/`error`/`error_type` are Pipeline's own bookkeeping keys,
        already surfaced via the Result-level `error` object -- they must not
        also leak into metadata.openagent_eval verbatim."""
        result_set = evaluation_report_to_result_set(realistic_evaluation_report)
        by_id = {r["test_case_id"]: r for r in result_set["results"]}
        failed_meta = by_id["fail-a"]["metadata"].get("openagent_eval", {})
        assert "failed" not in failed_meta
        assert "error" not in failed_meta
        assert "error_type" not in failed_meta


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

    def test_constructor_threshold_out_of_range_raises_on_generate(
        self, evaluation_report: EvaluationReport
    ) -> None:
        report = EvalPortReport(default_threshold=2.0)
        with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
            report.generate(evaluation_report)

    def test_started_at_completed_at_passthrough(
        self, evaluation_report: EvaluationReport
    ) -> None:
        report = EvalPortReport(
            started_at="2026-02-02T00:00:00Z",
            completed_at="2026-02-02T00:10:00Z",
        )
        data = json.loads(report.generate(evaluation_report))
        assert data["started_at"] == "2026-02-02T00:00:00Z"
        assert data["completed_at"] == "2026-02-02T00:10:00Z"

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

    def test_negative_indent_is_also_compact(
        self, evaluation_report: EvaluationReport
    ) -> None:
        """Matches JSONReport's own convention: any indent <= 0 is compact."""
        report = EvalPortReport(indent=-1)
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
