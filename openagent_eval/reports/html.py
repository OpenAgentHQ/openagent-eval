"""HTML report generator using Jinja2.

This module provides an HTML-formatted report that renders evaluation
results as a styled web page with responsive tables and sections.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openagent_eval.reports.base import ReportGenerator


class HTMLReport(ReportGenerator):
    """Generate HTML-formatted evaluation reports.

    Produces a styled HTML page with:
    - Responsive header with title and timestamp
    - Summary statistics grid
    - Color-coded metrics table
    - Error analysis section
    - Sample result cards
    - Configuration details
    """

    def __init__(self, template_path: Path | str | None = None) -> None:
        """Initialize the HTML report generator.

        Args:
            template_path: Optional path to a Jinja2 template file.
                Uses built-in template if not provided.
        """
        self._template_path = template_path
        self._template_str: str | None = None

    def _load_template(self) -> str:
        """Load the Jinja2 template string.

        Returns:
            Template string content.
        """
        if self._template_str is not None:
            return self._template_str

        if self._template_path is not None:
            path = Path(self._template_path)
            if path.exists():
                self._template_str = path.read_text(encoding="utf-8")
                return self._template_str

        # Load built-in template
        builtin_path = Path(__file__).parent / "templates" / "report.html"
        if builtin_path.exists():
            self._template_str = builtin_path.read_text(encoding="utf-8")
            return self._template_str

        raise FileNotFoundError(
            f"HTML template not found at {builtin_path}. "
            "Ensure the package is installed correctly and includes "
            "openagent_eval/reports/templates/report.html, or provide a valid custom template path."
        )

    def _render_template(self, context: dict[str, Any]) -> str:
        """Render a Jinja2 template string with context.

        Args:
            context: Template context variables.

        Returns:
            Rendered HTML string.

        Raises:
            ImportError: If jinja2 is not installed.
        """
        from jinja2 import Environment, select_autoescape

        template_str = self._load_template()
        env = Environment(autoescape=select_autoescape(["html", "xml"]))
        template = env.from_string(template_str)
        return template.render(**context)

    def generate(self, report: Any) -> str:
        """Generate an HTML report string.

        Args:
            report: EvaluationReport containing config, results, and summary.

        Returns:
            HTML-formatted report string.
        """
        result = report.result
        summary = report.summary
        config = report.config
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Compute overall score
        metrics = summary.get("metrics_summary", {})
        numeric_metric_values = [
            value for value in metrics.values()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
        overall_score = (
            sum(numeric_metric_values) / len(numeric_metric_values)
            if numeric_metric_values else None
        )

        # Format results for template, respecting the configured example limit
        max_examples = min(len(result.results), config.report.max_examples)
        results_data = []
        for eval_result in result.results[:max_examples]:
            results_data.append({
                "question": eval_result.question,
                "answer": eval_result.answer,
                "metrics": eval_result.metrics,
            })

        # Count errors by type
        error_types: dict[str, int] = {}
        for err in result.errors:
            err_type = err.get("error_type", "Unknown")
            error_types[err_type] = error_types.get(err_type, 0) + 1

        context = {
            "title": report.metadata.get("title", "OpenAgent Eval Report"),
            "timestamp": now,
            "total_items": summary.get("total_items", 0),
            "successful": summary.get("successful_evaluations", 0),
            "failed": summary.get("failed_evaluations", 0),
            "overall_score": overall_score,
            "metrics": metrics,
            "errors": error_types,
            "results": results_data,
            "config": config,
            "version": report.metadata.get("version", "0.1.0"),
        }

        return self._render_template(context)

    def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
        """Generate HTML report and write to file.

        Args:
            report: EvaluationReport containing config, results, and summary.
            output_path: Path to write the report file.

        Returns:
            Path to the written file.
        """
        path = Path(output_path)
        if path.suffix == "":
            path = path / "report.html"
        elif path.suffix.lower() != ".html":
            path = path.with_suffix(".html")
        path = self._prepare_output_file(path)
        content = self.generate(report)
        path.write_text(content, encoding="utf-8")
        return path
