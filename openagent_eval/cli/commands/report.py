"""Report command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from openagent_eval.cli.context import get_context
from openagent_eval.cli.utils.constants import DEFAULT_OUTPUT_DIR
from openagent_eval.cli.utils.helpers import get_report_generator, resolve_report_id
from openagent_eval.exceptions.cli import CommandError
from openagent_eval.reports.manager import ReportManager
from openagent_eval.reports.terminal import TerminalReport

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
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Directory where reports are stored (default: ./reports).",
    ),
) -> None:
    """View evaluation reports."""
    ctx = get_context()

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

    # Handle JSON output
    if ctx.json_output or output == "json":
        _output_json_report(evaluation_report, data)
        return

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


def _output_json_report(report: object, data: dict) -> None:
    """Output report as JSON.

    Args:
        report: Evaluation report object.
        data: Raw report data dict.
    """
    import json

    # Extract useful fields from the report
    output_data = {
        "report_id": data.get("report_id", "unknown"),
        "created_at": data.get("created_at", "unknown"),
    }

    # Add summary if available
    if hasattr(report, "summary"):
        output_data["summary"] = report.summary

    # Add raw data
    if "scores" in data:
        output_data["scores"] = data["scores"]
    if "metrics" in data:
        output_data["metrics"] = data["metrics"]
    if "config" in data:
        output_data["config"] = data["config"]

    console.print(json.dumps(output_data, indent=2, default=str))
