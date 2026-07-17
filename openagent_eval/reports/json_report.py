"""JSON report generator.

This module provides a structured JSON report that serializes evaluation
results into a machine-readable format for programmatic consumption.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openagent_eval.reports.base import ReportGenerator


class JSONReport(ReportGenerator):
    """Generate JSON-formatted evaluation reports.

    Produces a structured JSON document with:
    - Metadata (timestamp, version, engine)
    - Summary statistics
    - Metric averages
    - Individual evaluation results
    - Error details
    - Configuration snapshot
    """

    def __init__(self, indent: int = 2, sort_keys: bool = False) -> None:
        """Initialize the JSON report generator.

        Args:
            indent: JSON indentation level. Use 0 for compact output.
            sort_keys: Whether to sort dictionary keys alphabetically.
        """
        self.indent = indent
        self.sort_keys = sort_keys

    def generate(self, report: Any) -> str:
        """Generate a JSON report string.

        Args:
            report: EvaluationReport containing config, results, and summary.

        Returns:
            JSON-formatted report string.
        """
        result = report.result
        summary = report.summary
        config = report.config

        # Build structured data
        report_data: dict[str, Any] = {
            "metadata": {
                "engine": report.metadata.get("engine", "openagent-eval"),
                "version": report.metadata.get("version", "0.1.0"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "title": report.metadata.get("title", "OpenAgent Eval Report"),
            },
            "summary": {
                "total_items": summary.get("total_items", 0),
                "successful_evaluations": summary.get("successful_evaluations", 0),
                "failed_evaluations": summary.get("failed_evaluations", 0),
                "metrics_summary": summary.get("metrics_summary", {}),
            },
            "results": [],
            "errors": result.errors,
            "configuration": {
                "dataset": {
                    "path": config.dataset.path,
                    "format": config.dataset.format,
                    "limit": config.dataset.limit,
                },
                "llm": {
                    "provider": config.llm.provider,
                    "model": config.llm.model,
                    "temperature": config.llm.temperature,
                },
                "retriever": {
                    "provider": config.retriever.provider,
                    "settings": config.retriever.settings,
                },
                "report": {
                    "output": config.report.output.value,
                    "output_dir": config.report.output_dir,
                },
            },
        }

        # Format individual results
        for eval_result in result.results:
            report_data["results"].append({
                "question": eval_result.question,
                "answer": eval_result.answer,
                "ground_truth": eval_result.ground_truth,
                "contexts": eval_result.contexts,
                "metrics": eval_result.metrics,
                "metadata": eval_result.metadata,
            })

        # Compute failure analysis
        if result.errors:
            error_types: dict[str, int] = {}
            for err in result.errors:
                err_type = err.get("error_type", "Unknown")
                error_types[err_type] = error_types.get(err_type, 0) + 1
            report_data["failure_analysis"] = {
                "total_errors": len(result.errors),
                "error_breakdown": error_types,
            }

        return json.dumps(
            report_data,
            indent=self.indent if self.indent > 0 else None,
            sort_keys=self.sort_keys,
            ensure_ascii=False,
        )

    def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
        """Generate JSON report and write to file.

        Args:
            report: EvaluationReport containing config, results, and summary.
            output_path: Path to write the report file.

        Returns:
            Path to the written file.
        """
        path = Path(output_path)
        if not str(path).endswith(".json"):
            path = path / "report.json"
        path = self._prepare_output_file(path)
        content = self.generate(report)
        path.write_text(content, encoding="utf-8")
        return path

    def generate_compact(self, report: Any) -> str:
        """Generate a compact JSON report without indentation.

        Args:
            report: EvaluationReport containing config, results, and summary.

        Returns:
            Compact JSON string.
        """
        original_indent = self.indent
        self.indent = 0
        content = self.generate(report)
        self.indent = original_indent
        return content
