"""Compare command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from openagent_eval.exceptions.cli import CommandError
from openagent_eval.reports.comparison import ComparisonReport
from openagent_eval.reports.base import ExperimentComparison
from openagent_eval.reports.manager import ReportManager
from openagent_eval.cli.utils.constants import DEFAULT_OUTPUT_DIR
from openagent_eval.cli.utils.helpers import resolve_report_id

console = Console()


def compare_command(
    experiment_a: str = typer.Argument(
        help="First experiment ID or path.",
    ),
    experiment_b: str = typer.Argument(
        help="Second experiment ID or path.",
    ),
    metrics: list[str] = typer.Option(
        None,
        "--metrics",
        "-m",
        help="Specific metrics to compare (default: all).",
    ),
    output_dir: str = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Directory where reports are stored (default: ./reports).",
    ),
) -> None:
    """Compare two evaluation experiments side by side."""
    console.print("[bold blue]OpenAgent Eval[/bold blue] - Experiment Comparison")
    console.print(f"[dim]Comparing: {experiment_a} vs {experiment_b}[/dim]\n")

    manager = ReportManager()
    reports_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    try:
        data_a = resolve_report_id(experiment_a, reports_dir, manager)
    except CommandError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(code=e.exit_code) from None

    try:
        data_b = resolve_report_id(experiment_b, reports_dir, manager)
    except CommandError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(code=e.exit_code) from None

    # Reconstruct EvaluationReports and extract PipelineResults
    report_a = manager.reconstruct(data_a)
    report_b = manager.reconstruct(data_b)

    # Create ExperimentComparison (needs PipelineResult objects)
    comparison = ExperimentComparison(
        baseline_name=experiment_a,
        experiment_name=experiment_b,
        baseline_results=report_a.result,
        experiment_results=report_b.result,
    )

    # Generate comparison
    generator = ComparisonReport()
    comparison_output = generator.generate(comparison)

    console.print(comparison_output)
