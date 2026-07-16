"""Report manager for persisting and loading evaluation reports."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openagent_eval.core.engine import EvaluationReport
from openagent_eval.core.pipeline import EvaluationResult, PipelineResult
from openagent_eval.exceptions import ConfigurationError


class ReportManager:
    """Manage report persistence in a local output directory.

    Reports are stored as ``{report_id}.json`` files.  The manager
    provides helpers to save, load, list, and retrieve the most recent
    report.
    """

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    def save_report(
        self,
        report: EvaluationReport,
        output_dir: Path,
        report_id: str | None = None,
    ) -> Path:
        """Persist an evaluation report as JSON.

        Args:
            report: The evaluation report to save.
            output_dir: Directory where reports are stored.
            report_id: Optional identifier.  If *None* a UUID is generated.

        Returns:
            The path of the saved file.

        Raises:
            ConfigurationError: If *output_dir* cannot be created.
        """
        report_id = report_id or str(uuid.uuid4())
        output_dir = self._ensure_dir(output_dir)

        payload = {
            "report_id": report_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "config": report.config.model_dump(),
            "summary": report.summary,
            "metadata": report.metadata,
            "results": [
                {
                    "question": r.question,
                    "answer": r.answer,
                    "ground_truth": r.ground_truth,
                    "contexts": r.contexts,
                    "metrics": r.metrics,
                    "metadata": r.metadata,
                }
                for r in report.result.results
            ],
            "errors": report.result.errors,
        }

        path = output_dir / f"{report_id}.json"
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return path

    def load_report(
        self,
        report_id: str,
        output_dir: Path,
    ) -> dict[str, Any]:
        """Load a previously saved report by its ID.

        Args:
            report_id: The identifier of the report to load.
            output_dir: Directory where reports are stored.

        Returns:
            The deserialized report payload as a dictionary.

        Raises:
            FileNotFoundError: If the report file does not exist.
        """
        path = output_dir / f"{report_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Report not found: {report_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list_reports(self, output_dir: Path) -> list[dict[str, str]]:
        """List all reports in the output directory.

        Args:
            output_dir: Directory where reports are stored.

        Returns:
            A list of dicts with ``report_id`` and ``created_at`` keys,
            ordered by creation time (newest first).
        """
        output_dir = self._ensure_dir(output_dir)
        reports: list[dict[str, str]] = []

        for path in output_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                reports.append(
                    {
                        "report_id": data.get("report_id", path.stem),
                        "created_at": data.get("created_at", ""),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                # Skip files that are not valid report JSON.
                continue

        reports.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return reports

    def get_latest_report(self, output_dir: Path) -> dict[str, Any]:
        """Return the most recent report.

        Args:
            output_dir: Directory where reports are stored.

        Returns:
            The deserialized report payload of the newest report.

        Raises:
            FileNotFoundError: If no reports exist in the directory.
        """
        reports = self.list_reports(output_dir)
        if not reports:
            raise FileNotFoundError(f"No reports found in {output_dir}")
        return self.load_report(reports[0]["report_id"], output_dir)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _ensure_dir(path: Path) -> Path:
        """Create the directory if it does not exist and return it.

        Raises:
            ConfigurationError: If the directory cannot be created.
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ConfigurationError(
                message=f"Cannot create output directory: {path}",
                details={"path": str(path), "error": str(exc)},
            ) from exc
        return path

    # ------------------------------------------------------------------ #
    # Convenience: reconstruct an EvaluationReport from a saved dict      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def reconstruct(data: dict[str, Any]) -> EvaluationReport:
        """Reconstruct an ``EvaluationReport`` from a saved dictionary.

        This is useful when loading a report and passing it to report
        generators that expect the full dataclass.

        Raises:
            ValueError: If the ``config`` section is missing from the data.
        """
        from openagent_eval.config.models import Config

        config = data.get("config")
        if not config:
            raise ValueError(
                "Cannot reconstruct EvaluationReport: 'config' section is missing from data"
            )
        config = Config(**config)

        results = [
            EvaluationResult(
                question=r.get("question", ""),
                answer=r.get("answer", ""),
                ground_truth=r.get("ground_truth"),
                contexts=r.get("contexts", []),
                metrics=r.get("metrics", {}),
                metadata=r.get("metadata", {}),
            )
            for r in data.get("results", [])
        ]

        pipeline_result = PipelineResult(
            results=results,
            summary=data.get("summary", {}),
            errors=data.get("errors", []),
        )

        return EvaluationReport(
            config=config,
            result=pipeline_result,
            summary=data.get("summary", {}),
            metadata=data.get("metadata", {}),
        )
