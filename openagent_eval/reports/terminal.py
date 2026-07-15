"""Terminal report generator using Rich.

This module provides a Rich-based terminal report that renders evaluation
results as formatted console output with tables, panels, and colors.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from openagent_eval.reports.base import ReportGenerator


class TerminalReport(ReportGenerator):
    """Generate terminal-formatted reports using Rich.

    Renders evaluation results as styled console output with:
    - Summary panel with key metrics
    - Detailed metrics table
    - Error breakdown (if any)
    - Example evaluations (if enabled)
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the terminal report generator.

        Args:
            console: Optional Rich Console instance. Creates one if not provided.
        """
        self.console = console or Console()

    def generate(self, report: Any) -> str:
        """Generate a terminal report string.

        Note: This returns the plain-text representation. For rich
        formatted output, use ``print_report`` instead.

        Args:
            report: EvaluationReport containing config, results, and summary.

        Returns:
            Plain-text report string.
        """
        lines: list[str] = []
        result = report.result
        summary = report.summary
        config = report.config

        # Header
        lines.append("=" * 60)
        lines.append("  OpenAgent Eval Report")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"  Total items:      {summary.get('total_items', 0)}")
        lines.append(f"  Successful:       {summary.get('successful_evaluations', 0)}")
        lines.append(f"  Failed:           {summary.get('failed_evaluations', 0)}")
        lines.append("")

        # Metrics summary
        metrics = summary.get("metrics_summary", {})
        if metrics:
            lines.append("METRICS")
            lines.append("-" * 40)
            for metric_name, avg_score in metrics.items():
                lines.append(f"  {metric_name:<30} {avg_score:.4f}")
            lines.append("")

        # Errors
        if result.errors:
            lines.append("ERRORS")
            lines.append("-" * 40)
            error_types: dict[str, int] = {}
            for err in result.errors:
                err_type = err.get("error_type", "Unknown")
                error_types[err_type] = error_types.get(err_type, 0) + 1
            for err_type, count in error_types.items():
                lines.append(f"  {err_type:<30} {count}")
            lines.append("")

        # Config info
        lines.append("CONFIGURATION")
        lines.append("-" * 40)
        lines.append(f"  Dataset:   {config.dataset.path}")
        lines.append(f"  LLM:       {config.llm.provider}/{config.llm.model}")
        lines.append(f"  Output:    {config.report.output.value}")
        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
        """Generate terminal report and write to file.

        Args:
            report: EvaluationReport containing config, results, and summary.
            output_path: Path to write the report file.

        Returns:
            Path to the written file.
        """
        path = self._ensure_output_dir(output_path)
        content = self.generate(report)
        path.write_text(content, encoding="utf-8")
        return path

    def print_report(self, report: Any) -> None:
        """Print a rich-formatted report to the console.

        Args:
            report: EvaluationReport containing config, results, and summary.
        """
        result = report.result
        summary = report.summary
        config = report.config

        # Title panel
        self.console.print(
            Panel(
                "[bold]OpenAgent Eval Report[/bold]",
                title="Evaluation Complete",
                border_style="green",
            )
        )

        # Summary table
        summary_table = Table(title="Summary", show_header=False, border_style="blue")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        summary_table.add_row("Total Items", str(summary.get("total_items", 0)))
        summary_table.add_row(
            "Successful", str(summary.get("successful_evaluations", 0))
        )
        summary_table.add_row("Failed", str(summary.get("failed_evaluations", 0)))
        self.console.print(summary_table)

        # Metrics table
        metrics = summary.get("metrics_summary", {})
        if metrics:
            metrics_table = Table(title="Metrics", border_style="blue")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Score", justify="right", style="green")
            for metric_name, avg_score in metrics.items():
                score_text = f"{avg_score:.4f}"
                # Color code: green for high, yellow for mid, red for low
                if avg_score >= 0.8:
                    score_style = "green"
                elif avg_score >= 0.5:
                    score_style = "yellow"
                else:
                    score_style = "red"
                metrics_table.add_row(
                    metric_name, f"[{score_style}]{score_text}[/{score_style}]"
                )
            self.console.print(metrics_table)

        # Error breakdown
        if result.errors:
            error_table = Table(title="Errors", border_style="red")
            error_table.add_column("Error Type", style="red")
            error_table.add_column("Count", justify="right", style="white")
            error_types: dict[str, int] = {}
            for err in result.errors:
                err_type = err.get("error_type", "Unknown")
                error_types[err_type] = error_types.get(err_type, 0) + 1
            for err_type, count in error_types.items():
                error_table.add_row(err_type, str(count))
            self.console.print(error_table)

        # Example results
        if result.results:
            example_table = Table(title="Sample Results", border_style="blue")
            example_table.add_column("#", style="dim")
            example_table.add_column("Question", max_width=40)
            example_table.add_column("Metrics", max_width=30)
            for i, eval_result in enumerate(result.results[:5], 1):
                metrics_str = ", ".join(
                    f"{k}={v:.2f}" for k, v in eval_result.metrics.items()
                )
                example_table.add_row(
                    str(i), eval_result.question[:40], metrics_str[:30]
                )
            self.console.print(example_table)

        # Config info
        self.console.print(
            Panel(
                f"Dataset: [cyan]{config.dataset.path}[/cyan]\n"
                f"LLM: [cyan]{config.llm.provider}/{config.llm.model}[/cyan]\n"
                f"Output: [cyan]{config.report.output.value}[/cyan]",
                title="Configuration",
                border_style="dim",
            )
        )
