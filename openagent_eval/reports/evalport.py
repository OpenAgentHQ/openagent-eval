"""EvalPort report generator.

EvalPort (https://github.com/adhabnr-ux/evalport) is an open interchange
format (Apache 2.0) for portable LLM evaluation datasets: test cases,
graders, suites, and results as plain JSON, shared across evaluation tools
(DeepEval, Promptfoo, Inspect AI, AutoGen, CrewAI, Ragas, LangSmith,
Braintrust, MLflow, Opik, TruLens, and now OpenAgent Eval).

This module converts a completed :class:`~openagent_eval.core.engine.EvaluationReport`
into an EvalPort ``ResultSet`` (a plain ``dict`` matching the schema validated by
``openeval.validate.validate_result_set``). The direction is strictly
one-directional for v1 (``EvaluationReport -> ResultSet``); there is no
``from_openeval`` here, since OpenAgent Eval's own dataset/config loading
already has its own well-established shape (see ``config/loader.py`` and
``cli/commands/run.py``) that this adapter does not attempt to replace.

Design notes (agreed in OpenAgentHQ/openagent-eval Discussion #296 with
@himanshu-kumar):

- OpenAgent Eval's :class:`~openagent_eval.core.pipeline.EvaluationResult`
  has no native pass/fail concept -- only a ``metrics: dict[str, float]``
  of scores, each already validated to ``[0.0, 1.0]`` by
  ``MetricResult.__post_init__``. EvalPort's ``GraderResult.passed`` is
  required, so pass/fail is *derived* here via an optional
  ``evalport_thresholds`` mapping (``metric name -> threshold``), defaulting
  to ``0.5`` for any metric not explicitly listed. Because this pass/fail
  judgment is synthesized rather than native to the source data, every
  derived result is flagged transparently via
  ``metadata["openeval_derived_pass"] = True`` on that result -- a consumer
  that cares about the distinction between "the tool told us this passed"
  and "we inferred a pass from a threshold" can always tell which is which.
- ``test_case_id`` reads the dataset item's optional ``id`` field (preserved
  by the pipeline into ``EvaluationResult.metadata["id"]`` -- see
  ``Pipeline._evaluate_item``'s ``**item.get("metadata", {})`` spread) and
  falls back to the positional ``f"{run_id}_item_{i}"`` when absent, so a
  dataset that never set an ``id`` still produces stable, unique
  ``test_case_id`` values.
- ``metrics -> GraderResult`` (one grader result per metric, ``type="custom"``,
  ``grader_id`` = the metric name), ``answer -> actual_output``,
  ``metadata["latency_ms"] -> duration_ms`` (set by
  ``Pipeline._evaluate_item``/``_generate``), and run-level metadata
  (``EvaluationReport.metadata``, ``EvaluationReport.summary``) map onto the
  ``ResultSet``'s own top-level fields (``metadata``, ``summary``).

This adapter is a standalone, directly-importable :class:`ReportGenerator`
(the same ABC every other format in this package implements -- see
``reports/base.py``) rather than one wired into the CLI's ``--output`` flag
or ``config.models.OutputFormat``. That keeps this first version scoped to
exactly what was asked for -- ``EvalPortReport().generate_to_file(report,
"result_set.json")`` after a normal ``oaeval run`` -- without also having to
extend the pydantic ``Config`` tree and the CLI's format registry in the same
change; wiring it into ``--output evalport`` is a natural, separately-scoped
follow-up once this conversion itself has been reviewed against real
``oaeval run`` output.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from openagent_eval.reports.base import ReportGenerator

if TYPE_CHECKING:
    from openagent_eval.core.engine import EvaluationReport
    from openagent_eval.core.pipeline import EvaluationResult

try:
    from openeval import OPENEVAL_VERSION
except ImportError:  # pragma: no cover - evalport-sdk is an optional extra
    OPENEVAL_VERSION = "1.0.0"

__all__ = ["EvalPortReport", "evaluation_report_to_result_set"]

DEFAULT_PASS_THRESHOLD = 0.5


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clamp_unit(score: float) -> float:
    """Defensively clamp a score into EvalPort's required [0, 1] range.

    ``MetricResult.__post_init__`` already enforces ``0.0 <= score <= 1.0``
    for every built-in metric, so this is a belt-and-suspenders guard against
    a third-party custom metric that does not go through ``MetricResult`` and
    might otherwise produce a ``ResultSet`` that fails
    ``openeval.validate.validate_result_set``.
    """
    return max(0.0, min(1.0, float(score)))


def _test_case_id(eval_result: EvaluationResult, run_id: str, index: int) -> str:
    """Resolve a stable EvalPort ``test_case_id`` for one evaluated item.

    Prefers the dataset item's own ``id`` field, which the pipeline
    preserves into ``EvaluationResult.metadata["id"]`` when the source
    dataset item carries a ``metadata.id`` value (see
    ``Pipeline._evaluate_item``). Falls back to a positional id so results
    from datasets that never set ``id`` still get stable, unique ids.
    """
    item_id = eval_result.metadata.get("id")
    if item_id is not None:
        return str(item_id)
    return f"{run_id}_item_{index}"


def _grader_results(
    eval_result: EvaluationResult,
    thresholds: dict[str, float],
    default_threshold: float,
) -> list[dict[str, Any]]:
    """Convert one ``EvaluationResult.metrics`` dict into EvalPort ``GraderResult`` entries."""
    grader_results: list[dict[str, Any]] = []
    for metric_name, raw_score in eval_result.metrics.items():
        if raw_score is None:
            continue
        score = _clamp_unit(raw_score)
        threshold = thresholds.get(metric_name, default_threshold)
        grader_results.append(
            {
                "grader_id": metric_name,
                "type": "custom",
                "score": score,
                "passed": score >= threshold,
                "reason": f"{metric_name}={score:.4f} (threshold={threshold})",
            }
        )
    return grader_results


def _result_metadata(eval_result: EvaluationResult) -> dict[str, Any]:
    """Everything OpenAgent Eval attaches to an item that EvalPort's ``Result``
    schema itself doesn't have a dedicated field for -- the original
    question, ground-truth reference, retrieved contexts, token usage,
    per-item metric errors, and any caller-supplied dataset item metadata --
    is preserved here rather than silently dropped, matching the lossiness
    convention every other EvalPort adapter in the ecosystem follows (see
    e.g. ``trulens-connectors-openeval``'s ``metadata["trulens"]``).

    Notably, ``Result`` has no ``input``/``expected_output`` fields of its
    own (only ``test_case_id``, ``passed``, ``grader_results``,
    ``actual_output``, ``duration_ms``, ``completed_at``, ``attempt``,
    ``error``, ``metadata`` -- see ``openeval.Result.__dataclass_fields__``),
    so ``question``/``ground_truth``/``contexts`` are carried here rather
    than as invented top-level keys the schema doesn't define.
    """
    preserved = {
        k: v for k, v in eval_result.metadata.items() if k not in ("id", "latency_ms")
    }
    openagent_eval: dict[str, Any] = dict(preserved)
    if eval_result.question:
        openagent_eval["question"] = eval_result.question
    if eval_result.ground_truth is not None:
        openagent_eval["ground_truth"] = eval_result.ground_truth
    if eval_result.contexts:
        openagent_eval["contexts"] = eval_result.contexts
    return {"openagent_eval": openagent_eval} if openagent_eval else {}


def evaluation_report_to_result_set(
    report: EvaluationReport,
    *,
    evalport_thresholds: dict[str, float] | None = None,
    default_threshold: float = DEFAULT_PASS_THRESHOLD,
    suite_id: str | None = None,
    run_id: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> dict[str, Any]:
    """Convert a completed :class:`EvaluationReport` into an EvalPort ``ResultSet``.

    Args:
        report: The ``EvaluationReport`` produced by ``Engine.run()`` (or
            reconstructed via ``ReportManager.load_report`` /
            ``ReportManager.reconstruct``).
        evalport_thresholds: Optional ``metric name -> pass threshold``
            mapping. OpenAgent Eval's own metrics carry no native pass/fail
            concept -- only a ``[0.0, 1.0]`` score -- so a threshold is
            required to derive ``GraderResult.passed``. Any metric not
            listed here falls back to ``default_threshold``.
        default_threshold: Pass threshold applied to any metric not present
            in ``evalport_thresholds``. Defaults to ``0.5``, matching the
            convention used by the ``trulens-connectors-openeval`` and
            ``ares-openeval-adapter`` EvalPort adapters for bare ``[0, 1]``
            scores with no tool-native threshold.
        suite_id: The EvalPort ``ResultSet.suite_id``. OpenAgent Eval does
            not track the id of an externally-authored EvalPort suite it ran
            against (it loads datasets via ``config.dataset.path``, not
            EvalPort suites), so this defaults to that dataset path, falling
            back to ``"openagent_eval_run"`` if the config has none.
        run_id: The EvalPort ``ResultSet.run_id``. Defaults to
            ``report.metadata.get("run_id")``, falling back to a
            timestamp-based id if the report carries none.
        started_at / completed_at: ISO-8601 timestamps for the ResultSet.
            ``started_at`` is required by the EvalPort schema; both default
            to the current time if omitted, since ``EvaluationReport`` does
            not itself carry run-level start/end timestamps.

    Returns:
        A dict matching EvalPort's ``ResultSet`` schema. Validate with
        ``openeval.validate.validate_result_set()``.

    Raises:
        ValueError: if ``report.result.results`` is empty -- EvalPort's
            schema requires at least one ``Result`` per ``ResultSet``.
    """
    result = report.result
    if not result.results:
        raise ValueError(
            "evaluation_report_to_result_set: report.result.results is empty "
            "-- EvalPort's ResultSet schema requires at least one result."
        )

    thresholds = dict(evalport_thresholds or {})

    if suite_id is None:
        dataset_path = getattr(report.config.dataset, "path", None)
        suite_id = str(dataset_path) if dataset_path else "openagent_eval_run"

    if run_id is None:
        meta_run_id = report.metadata.get("run_id")
        run_id = (
            str(meta_run_id)
            if meta_run_id
            else f"openagent_eval_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
        )

    results: list[dict[str, Any]] = []
    for i, eval_result in enumerate(result.results):
        grader_results = _grader_results(eval_result, thresholds, default_threshold)
        passed = all(g["passed"] for g in grader_results) if grader_results else False

        entry: dict[str, Any] = {
            "test_case_id": _test_case_id(eval_result, run_id, i),
            "grader_results": grader_results,
            "passed": passed,
            "metadata": {
                **_result_metadata(eval_result),
                "openeval_derived_pass": True,
            },
        }

        if eval_result.answer is not None:
            entry["actual_output"] = eval_result.answer

        latency_ms = eval_result.metadata.get("latency_ms")
        if latency_ms is not None:
            entry["duration_ms"] = max(0, round(latency_ms))

        results.append(entry)

    # OpenAgent Eval's per-item failures (retrieval/generation errors caught by
    # Pipeline._evaluate_item's exception boundary) never produce an
    # EvaluationResult at all -- they are recorded only in
    # PipelineResult.errors, outside the per-item results list this loop
    # walks. EvalPort's Result schema requires exactly one Result per entry
    # in `results`, with no concept of an item that was never evaluated, so
    # each such failure is appended here as its own failed Result (no grader
    # results, `error` populated) rather than silently dropped -- keeping the
    # ResultSet's `results` length reflect the full evaluation attempt, not
    # just the items that completed successfully.
    for i, error_entry in enumerate(result.errors):
        item = error_entry.get("item", {}) or {}
        item_id = item.get("metadata", {}).get("id") if isinstance(item, dict) else None
        error_metadata: dict[str, Any] = {"openeval_derived_pass": True}
        question = item.get("question") if isinstance(item, dict) else None
        if question:
            error_metadata["openagent_eval"] = {"question": question}
        results.append(
            {
                "test_case_id": (
                    str(item_id) if item_id is not None else f"{run_id}_error_{i}"
                ),
                "grader_results": [],
                "passed": False,
                "error": {
                    "message": error_entry.get("error", "Unknown error"),
                    "detail": error_entry.get("error_type", "Unknown"),
                },
                "metadata": error_metadata,
            }
        )

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])

    result_set: dict[str, Any] = {
        "version": OPENEVAL_VERSION,
        "suite_id": suite_id,
        "run_id": run_id,
        "started_at": started_at or _now_iso(),
        "results": results,
        "summary": {
            "total": total,
            "passed": passed_count,
            "failed": total - passed_count,
            "pass_rate": (passed_count / total) if total else 0.0,
        },
        "metadata": {
            "openagent_eval": {
                "engine": report.metadata.get("engine", "openagent-eval"),
                "version": report.metadata.get("version"),
                "title": report.metadata.get("title"),
                "config_summary": report.summary,
            }
        },
    }
    result_set["completed_at"] = completed_at or _now_iso()

    return result_set


class EvalPortReport(ReportGenerator):
    """Generate EvalPort-formatted (``ResultSet`` JSON) evaluation reports.

    Usage mirrors every other generator in this package::

        from openagent_eval.reports.evalport import EvalPortReport

        report = EvalPortReport(evalport_thresholds={"faithfulness": 0.7})
        report.generate_to_file(evaluation_report, "result_set.json")

    The output validates against ``openeval.validate.validate_result_set()``
    and can be consumed by any EvalPort-speaking tool (openeval's own CLI,
    other adapters in the ecosystem, or a suite-comparison dashboard).
    """

    def __init__(
        self,
        *,
        evalport_thresholds: dict[str, float] | None = None,
        default_threshold: float = DEFAULT_PASS_THRESHOLD,
        suite_id: str | None = None,
        run_id: str | None = None,
        indent: int = 2,
    ) -> None:
        """Initialize the EvalPort report generator.

        Args:
            evalport_thresholds: Optional ``metric name -> pass threshold``
                mapping used to derive each ``GraderResult.passed``. See
                :func:`evaluation_report_to_result_set` for the full
                rationale.
            default_threshold: Pass threshold for any metric not listed in
                ``evalport_thresholds``. Defaults to ``0.5``.
            suite_id: Optional override for the ResultSet's ``suite_id``.
                Defaults to the run's dataset path.
            run_id: Optional override for the ResultSet's ``run_id``.
                Defaults to ``report.metadata["run_id"]`` or a generated,
                timestamp-based id.
            indent: JSON indentation level. Use ``0`` for compact output.
        """
        self.evalport_thresholds = evalport_thresholds
        self.default_threshold = default_threshold
        self.suite_id = suite_id
        self.run_id = run_id
        self.indent = indent

    def to_result_set(self, report: EvaluationReport) -> dict[str, Any]:
        """Convert ``report`` into an EvalPort ``ResultSet`` dict (unserialized)."""
        return evaluation_report_to_result_set(
            report,
            evalport_thresholds=self.evalport_thresholds,
            default_threshold=self.default_threshold,
            suite_id=self.suite_id,
            run_id=self.run_id,
        )

    def generate(self, report: EvaluationReport) -> str:
        """Generate an EvalPort ``ResultSet`` as a JSON string.

        Args:
            report: EvaluationReport containing config, results, and summary.

        Returns:
            JSON-formatted ``ResultSet`` string.
        """
        import json

        return json.dumps(
            self.to_result_set(report),
            indent=self.indent if self.indent > 0 else None,
            ensure_ascii=False,
        )

    def generate_to_file(
        self, report: EvaluationReport, output_path: Path | str
    ) -> Path:
        """Generate an EvalPort ``ResultSet`` and write it to a JSON file.

        Args:
            report: EvaluationReport containing config, results, and summary.
            output_path: Path to write the report file. A missing suffix is
                treated as a directory (matching ``JSONReport``'s own
                convention) and gets ``result_set.json`` appended; any
                non-``.json`` suffix is replaced.

        Returns:
            Path to the written file.
        """
        path = Path(output_path)
        if path.suffix == "":
            path = path / "result_set.json"
        elif path.suffix.lower() != ".json":
            path = path.with_suffix(".json")
        path = self._prepare_output_file(path)
        content = self.generate(report)
        path.write_text(content, encoding="utf-8")
        return path
