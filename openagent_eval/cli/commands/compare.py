"""Compare command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console  # noqa: B008

from openagent_eval.cli.context import get_context
from openagent_eval.cli.utils.constants import DEFAULT_OUTPUT_DIR
from openagent_eval.cli.utils.helpers import resolve_report_id
from openagent_eval.exceptions.cli import CommandError
from openagent_eval.reports.base import ExperimentComparison
from openagent_eval.reports.comparison import ComparisonReport
from openagent_eval.reports.manager import ReportManager

console = Console()


def compare_command(
    experiment_a: str = typer.Argument(
        help="First experiment ID or path.",
    ),
    experiment_b: str = typer.Argument(
        help="Second experiment ID or path.",
    ),
    metrics: list[str] | None = typer.Option(  # noqa: B008
        None,
        "--metrics",
        "-m",
        help="Specific metrics to compare (default: all).",
    ),
    output_dir: str | None = typer.Option(  # noqa: B008
        None,
        "--output-dir",
        "-d",
        help="Directory where reports are stored (default: ./reports).",
    ),
) -> None:
    """Compare two evaluation experiments side by side."""
    ctx = get_context()

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

    # Handle JSON output
    if ctx.json_output:
        _output_json_comparison(data_a, data_b, experiment_a, experiment_b)
        return

    console.print(comparison_output)


def _output_json_comparison(
    data_a: dict,
    data_b: dict,
    name_a: str,
    name_b: str,
) -> None:
    """Output comparison as JSON.

    Args:
        data_a: First report data.
        data_b: Second report data.
        name_a: First experiment name.
        name_b: Second experiment name.
    """
    import json

    output_data = {
        "experiment_a": {
            "name": name_a,
            "report_id": data_a.get("report_id", "unknown"),
            "created_at": data_a.get("created_at", "unknown"),
        },
        "experiment_b": {
            "name": name_b,
            "report_id": data_b.get("report_id", "unknown"),
            "created_at": data_b.get("created_at", "unknown"),
        },
    }

    # Add scores if available
    if "scores" in data_a:
        output_data["experiment_a"]["scores"] = data_a["scores"]
    if "scores" in data_b:
        output_data["experiment_b"]["scores"] = data_b["scores"]

    # Add metrics if available
    if "metrics" in data_a:
        output_data["experiment_a"]["metrics"] = data_a["metrics"]
    if "metrics" in data_b:
        output_data["experiment_b"]["metrics"] = data_b["metrics"]

    console.print(json.dumps(output_data, indent=2, default=str))
