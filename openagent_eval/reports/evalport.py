"""EvalPort report generator.

EvalPort (https://github.com/adhabnr-ux/evalport) is an open interchange
format (Apache 2.0) for portable LLM evaluation datasets: test cases,
graders, suites, and results as plain JSON, shared across evaluation tools
(DeepEval, Promptfoo, Inspect AI, AutoGen, CrewAI, and others).

This module converts a completed :class:`~openagent_eval.core.engine.EvaluationReport`
into an EvalPort ``ResultSet`` (a plain ``dict`` matching the schema validated by
``openeval.validate.validate_result_set``). The direction is strictly
one-directional for v1 (``EvaluationReport -> ResultSet``); there is no
``from_openeval`` here, since OpenAgent Eval's own dataset/config loading
already has its own well-established shape (see ``config/loader.py`` and
``cli/commands/run.py``) that this adapter does not attempt to replace.

Design notes (agreed in OpenAgentHQ/openagent-eval Discussion #296 with
@himanshu231204):

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
- **Pipeline failures.** ``Pipeline._evaluate_item``'s exception boundary
  does two things on a retrieval/generation/metric failure: it appends a
  dict to ``PipelineResult.errors``, *and* it returns a zeroed
  ``EvaluationResult`` (flagged via ``metadata["failed"] = True``) that
  lands in ``PipelineResult.results`` like every other item. Both
  representations describe the exact same failure. This adapter treats the
  ``EvaluationResult`` in ``results`` as the single source of truth for
  failed items and does not additionally walk ``PipelineResult.errors`` --
  earlier versions of this module did, and double-counted every failure (one
  Result from the zeroed ``EvaluationResult``, a second synthetic one from
  the matching ``errors`` entry), corrupting ``summary.total``/``pass_rate``
  silently. Sourcing failures from ``results`` alone also sidesteps a real
  ordering hazard: ``PipelineResult.results`` preserves dataset order
  (``Pipeline.execute`` awaits/gathers coroutines in item order), but
  ``PipelineResult.errors`` is appended to from inside each item's own
  coroutine, so under the parallel executor its order reflects completion
  time, not dataset position -- there is no safe way to zip
  ``errors[i]`` against ``items[i]``.

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

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from openagent_eval.reports.base import ReportGenerator

if TYPE_CHECKING:
    from openagent_eval.core.engine import EvaluationReport
    from openagent_eval.core.pipeline import EvaluationResult

logger = logging.getLogger(__name__)

try:
    from openeval import OPENEVAL_VERSION
except ImportError:  # pragma: no cover - evalport-sdk is an optional extra
    OPENEVAL_VERSION = "1.0.0"
    logger.warning(
        "evalport-sdk is not installed; EvalPortReport is falling back to a "
        "bundled OPENEVAL_VERSION=%r, which may be stale. Install the "
        "'evalport' extra (pip install openagent-eval[evalport]) to pick up "
        "the SDK's real current spec version.",
        OPENEVAL_VERSION,
    )

__all__ = ["EvalPortReport", "evaluation_report_to_result_set"]

DEFAULT_PASS_THRESHOLD = 0.5

# Keys on EvaluationResult.metadata that are either surfaced through a
# dedicated Result field elsewhere (id -> test_case_id, latency_ms ->
# duration_ms) or are Pipeline's own failure bookkeeping (failed, error,
# error_type -> the Result.error object) -- never re-exported verbatim into
# metadata.openagent_eval.
_METADATA_EXCLUDED_KEYS = ("id", "latency_ms", "failed", "error", "error_type")


def _now_iso() -> str:
    """Current UTC time as a Zulu-suffixed ISO-8601 string.

    Deliberately seconds-precision, no fractional component -- this matches
    the EvalPort SDK's own convention for ``started_at``/``completed_at``
    string fields. This is intentionally not the same convention
    ``reports/json_report.py`` uses for its own ``metadata.timestamp``
    (``datetime.now(UTC).isoformat()``, which keeps microseconds and a
    ``+00:00`` offset instead of ``Z``): these are two different fields in
    two different schemas, not a value that needs to round-trip between them.
    """
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


def _validate_threshold(label: str, value: float) -> None:
    """Raise ``ValueError`` if a pass threshold is outside EvalPort's [0, 1] score range.

    An out-of-range threshold fails silently otherwise: > 1.0 makes every
    result fail (no score can ever meet it), < 0.0 makes every result pass
    (every score already meets it) -- both are almost certainly a caller
    mistake (e.g. passing a percentage like ``70`` instead of ``0.7``), not a
    deliberate choice, so this is rejected outright rather than silently
    misbehaving.
    """
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be in [0.0, 1.0], got {value!r}")


def _test_case_id(eval_result: EvaluationResult, run_id: str, index: int) -> str:
    """Resolve a stable EvalPort ``test_case_id`` for one evaluated item.

    Prefers the dataset item's own ``id`` field, which the pipeline
    preserves into ``EvaluationResult.metadata["id"]`` when the source
    dataset item carries a ``metadata.id`` value (see
    ``Pipeline._evaluate_item``) -- including for a failed item, since the
    exception boundary now spreads the original item's ``metadata`` the same
    way the success path does. Falls back to a positional id, stable within
    one ``evaluation_report_to_result_set`` call because ``i`` is this item's
    index in ``PipelineResult.results``, which preserves dataset order.
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
    is preserved here rather than silently dropped.

    Notably, ``Result`` has no ``input``/``expected_output`` fields of its
    own (only ``test_case_id``, ``passed``, ``grader_results``,
    ``actual_output``, ``duration_ms``, ``completed_at``, ``attempt``,
    ``error``, ``metadata`` -- see ``openeval.Result.__dataclass_fields__``),
    so ``question``/``ground_truth``/``contexts`` are carried here rather
    than as invented top-level keys the schema doesn't define.
    """
    preserved = {
        k: v
        for k, v in eval_result.metadata.items()
        if k not in _METADATA_EXCLUDED_KEYS
    }
    openagent_eval: dict[str, Any] = dict(preserved)
    if eval_result.question:
        openagent_eval["question"] = eval_result.question
    if eval_result.ground_truth is not None:
        openagent_eval["ground_truth"] = eval_result.ground_truth
    if eval_result.contexts:
        openagent_eval["contexts"] = eval_result.contexts
    return {"openagent_eval": openagent_eval} if openagent_eval else {}


def _failed_result(eval_result: EvaluationResult, test_case_id: str) -> dict[str, Any]:
    """Build a failed EvalPort ``Result`` for an ``EvaluationResult`` whose
    ``metadata["failed"]`` is ``True`` -- i.e. an item whose retrieval,
    generation, or metric step raised inside
    ``Pipeline._evaluate_item``'s exception boundary.

    This is the only place a pipeline-level failure is represented in the
    exported ``ResultSet`` (see the module docstring's "Pipeline failures"
    note for why ``PipelineResult.errors`` is not also walked here).
    """
    metadata = {**_result_metadata(eval_result), "openeval_derived_pass": True}
    return {
        "test_case_id": test_case_id,
        "grader_results": [],
        "passed": False,
        "error": {
            "message": eval_result.metadata.get("error") or "Unknown error",
            "detail": eval_result.metadata.get("error_type") or "Unknown",
        },
        "metadata": metadata,
    }


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
            listed here falls back to ``default_threshold``. Every value
            (here and in ``default_threshold``) must be in ``[0.0, 1.0]``.
        default_threshold: Pass threshold applied to any metric not present
            in ``evalport_thresholds``. Defaults to ``0.5``, a neutral
            midpoint appropriate for bare ``[0, 1]`` scores with no
            tool-native threshold of their own. Must be in ``[0.0, 1.0]``.
        suite_id: The EvalPort ``ResultSet.suite_id``. OpenAgent Eval does
            not track the id of an externally-authored EvalPort suite it ran
            against (it loads datasets via ``config.dataset.path``, not
            EvalPort suites), so this defaults to that dataset path, falling
            back to ``"openagent_eval_run"`` if the config has none.
        run_id: The EvalPort ``ResultSet.run_id``. Defaults to
            ``report.metadata.get("run_id")``, falling back to a
            timestamp-based id if the report carries none -- which, as of
            this writing, is every real ``Engine.run()`` call: the engine
            does not currently set ``metadata["run_id"]`` (or
            ``metadata["title"]``, see ``suite_id``/the ``metadata.title``
            note below). Pass ``run_id`` explicitly if the caller has one.
        started_at / completed_at: ISO-8601 timestamps for the ResultSet.
            ``started_at`` is required by the EvalPort schema; both default
            to the current time if omitted, since ``EvaluationReport`` does
            not itself carry run-level start/end timestamps.

    Returns:
        A dict matching EvalPort's ``ResultSet`` schema. Validate with
        ``openeval.validate.validate_result_set()``.

    Raises:
        ValueError: if ``default_threshold`` or any value in
            ``evalport_thresholds`` is outside ``[0.0, 1.0]``, or if
            ``report.result.results`` is empty -- EvalPort's schema requires
            at least one ``Result`` per ``ResultSet``.
    """
    _validate_threshold("default_threshold", default_threshold)
    for metric_name, threshold in (evalport_thresholds or {}).items():
        _validate_threshold(f"evalport_thresholds[{metric_name!r}]", threshold)

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
        test_case_id = _test_case_id(eval_result, run_id, i)

        if eval_result.metadata.get("failed"):
            results.append(_failed_result(eval_result, test_case_id))
            continue

        grader_results = _grader_results(eval_result, thresholds, default_threshold)
        passed = all(g["passed"] for g in grader_results) if grader_results else False

        entry: dict[str, Any] = {
            "test_case_id": test_case_id,
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
            try:
                entry["duration_ms"] = max(0, round(latency_ms))
            except (TypeError, ValueError):
                # A non-numeric latency_ms (e.g. injected via a dataset item's
                # own metadata spread) shouldn't crash the whole export --
                # just omit duration_ms for this result.
                logger.warning(
                    "Ignoring non-numeric metadata['latency_ms']=%r for %s",
                    latency_ms,
                    test_case_id,
                )

        results.append(entry)

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])

    metadata_block: dict[str, Any] = {
        "engine": report.metadata.get("engine", "openagent-eval"),
        "version": report.metadata.get("version"),
        "config_summary": report.summary,
    }
    title = report.metadata.get("title")
    if title is not None:
        metadata_block["title"] = title

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
        "metadata": {"openagent_eval": metadata_block},
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
        started_at: str | None = None,
        completed_at: str | None = None,
        indent: int = 2,
    ) -> None:
        """Initialize the EvalPort report generator.

        Args:
            evalport_thresholds: Optional ``metric name -> pass threshold``
                mapping used to derive each ``GraderResult.passed``. See
                :func:`evaluation_report_to_result_set` for the full
                rationale. Every value must be in ``[0.0, 1.0]``.
            default_threshold: Pass threshold for any metric not listed in
                ``evalport_thresholds``. Defaults to ``0.5``. Must be in
                ``[0.0, 1.0]``.
            suite_id: Optional override for the ResultSet's ``suite_id``.
                Defaults to the run's dataset path.
            run_id: Optional override for the ResultSet's ``run_id``.
                Defaults to ``report.metadata["run_id"]`` or a generated,
                timestamp-based id.
            started_at: Optional override for the ResultSet's ``started_at``.
                Defaults to the current time when the report is generated,
                which is only an approximation of the real evaluation start
                -- pass the actual run-start timestamp here when it's known.
            completed_at: Optional override for the ResultSet's
                ``completed_at``, with the same caveat as ``started_at``.
            indent: JSON indentation level. ``0`` (or any negative value)
                produces compact, single-line output, matching
                ``JSONReport``'s own convention.
        """
        self.evalport_thresholds = evalport_thresholds
        self.default_threshold = default_threshold
        self.suite_id = suite_id
        self.run_id = run_id
        self.started_at = started_at
        self.completed_at = completed_at
        self.indent = indent

    def to_result_set(self, report: EvaluationReport) -> dict[str, Any]:
        """Convert ``report`` into an EvalPort ``ResultSet`` dict (unserialized)."""
        return evaluation_report_to_result_set(
            report,
            evalport_thresholds=self.evalport_thresholds,
            default_threshold=self.default_threshold,
            suite_id=self.suite_id,
            run_id=self.run_id,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )

    def generate(self, report: EvaluationReport) -> str:
        """Generate an EvalPort ``ResultSet`` as a JSON string.

        Args:
            report: EvaluationReport containing config, results, and summary.

        Returns:
            JSON-formatted ``ResultSet`` string.
        """
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
