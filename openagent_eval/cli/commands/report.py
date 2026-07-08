"""Report command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from openagent_eval.exceptions.cli import CommandError
from openagent_eval.reports.manager import ReportManager
from openagent_eval.reports.terminal import TerminalReport
from openagent_eval.cli.utils.constants import DEFAULT_OUTPUT_DIR
from openagent_eval.cli.utils.helpers import get_report_generator, resolve_report_id

console = Console()


def report_command(
    report_id: str = typer.Argument(
        help="Report ID or 'latest' for the most recent report.",
    ),
    output: str = typer.Option(
        "terminal",
        "--output",
        "-o",
        help="Output format (terminal, markdown, html, json).",
    ),
    output_dir: str = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Directory where reports are stored (default: ./reports).",
    ),
) -> None:
    """View evaluation reports."""
    console.print("[bold blue]OpenAgent Eval[/bold blue] - Report Viewer")
    console.print(f"[dim]Report: {report_id}[/dim]\n")

    manager = ReportManager()
    reports_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    try:
        data = resolve_report_id(report_id, reports_dir, manager)
    except CommandError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(code=e.exit_code) from None

    evaluation_report = manager.reconstruct(data)

    try:
        generator = get_report_generator(output)
    except CommandError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(code=e.exit_code) from None

    if output == "terminal":
        gen = TerminalReport()
        gen.print_report(evaluation_report)
    else:
        report_content = generator.generate(evaluation_report)
        console.print(report_content)

    console.print(f"\n[dim]Report ID: {data.get('report_id', 'unknown')}[/dim]")
