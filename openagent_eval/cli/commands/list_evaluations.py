"""List command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from openagent_eval.reports.manager import ReportManager
from openagent_eval.cli.utils.constants import DEFAULT_OUTPUT_DIR
from openagent_eval.cli.utils.display import display_report_list

console = Console()


def list_command(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Number of evaluations to show.",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Filter by output format.",
    ),
    output_dir: str = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Directory where reports are stored (default: ./reports).",
    ),
) -> None:
    """List previous evaluation runs."""
    console.print("[bold blue]OpenAgent Eval[/bold blue] - Evaluation History\n")

    manager = ReportManager()
    reports_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    try:
        reports = manager.list_reports(reports_dir)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to list reports: {e}")
        raise typer.Exit(code=1) from e

    display_report_list(reports, limit, output, reports_dir, manager)
