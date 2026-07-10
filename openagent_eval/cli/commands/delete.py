"""Delete command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from openagent_eval.cli.utils.constants import DEFAULT_OUTPUT_DIR
from openagent_eval.reports.manager import ReportManager

console = Console()


def delete_command(
    report_id: str = typer.Argument(
        help="Report ID to delete, or 'all' to delete all reports.",
    ),
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Directory where reports are stored (default: ./reports).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt.",
    ),
) -> None:
    """Delete evaluation reports."""
    console.print("[bold blue]OpenAgent Eval[/bold blue] - Delete Reports\n")

    manager = ReportManager()
    reports_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    # Handle 'all' case
    if report_id.lower() == "all":
        _delete_all_reports(manager, reports_dir, force)
        return

    # Single report deletion
    _delete_single_report(report_id, manager, reports_dir, force)


def _delete_single_report(
    report_id: str,
    manager: ReportManager,
    reports_dir: Path,
    force: bool,
) -> None:
    """Delete a single report.

    Args:
        report_id: Report ID to delete.
        manager: Report manager instance.
        reports_dir: Reports directory.
        force: Skip confirmation.
    """
    # Check if report exists
    try:
        data = manager.load_report(report_id, reports_dir)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] Report not found: {report_id}")
        raise typer.Exit(code=1) from exc

    # Show report info
    created_at = data.get("created_at", "unknown")
    console.print(f"[bold]Report to delete:[/bold] {report_id}")
    console.print(f"[dim]Created: {created_at}[/dim]\n")

    # Confirm deletion
    if not force and not Confirm.ask("Are you sure you want to delete this report?"):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # Delete the report
    try:
        report_path = reports_dir / f"{report_id}.json"
        if report_path.exists():
            report_path.unlink()
            console.print(f"[green]OK[/green] Deleted report: {report_id}")
        else:
            console.print(f"[yellow]Warning:[/yellow] Report file not found: {report_path}")
    except OSError as exc:
        console.print(f"[red]Error:[/red] Failed to delete report: {exc}")
        raise typer.Exit(code=1) from exc


def _delete_all_reports(
    manager: ReportManager,
    reports_dir: Path,
    force: bool,
) -> None:
    """Delete all reports.

    Args:
        manager: Report manager instance.
        reports_dir: Reports directory.
        force: Skip confirmation.
    """
    # List all reports
    try:
        reports = manager.list_reports(reports_dir)
    except Exception as exc:
        console.print(f"[red]Error:[/red] Failed to list reports: {exc}")
        raise typer.Exit(code=1) from exc

    if not reports:
        console.print("[yellow]No reports found to delete.[/yellow]")
        return

    # Show count
    console.print(f"[bold]Found {len(reports)} report(s)[/bold]\n")

    # Confirm deletion
    if not force and not Confirm.ask(
        f"Are you sure you want to delete ALL {len(reports)} reports?"
    ):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # Delete each report
    deleted = 0
    for report in reports:
        report_id = report.get("report_id", "unknown")
        try:
            report_path = reports_dir / f"{report_id}.json"
            if report_path.exists():
                report_path.unlink()
                deleted += 1
        except OSError:
            console.print(f"[yellow]Warning:[/yellow] Failed to delete: {report_id}")

    console.print(f"\n[green]OK[/green] Deleted {deleted} report(s)")
