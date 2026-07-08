"""CLI display helpers for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def display_run_result(
    report: Any,
    format_name: str,
    report_path: Path,
    output_dir: Path,
    verbose: bool,
) -> None:
    """Display the evaluation run result."""
    console.print("\n[green]OK[/green] Evaluation complete!")

    if hasattr(report, "summary"):
        summary = report.summary
        total = summary.get("total_items", summary.get("total", 0))
        errors = summary.get("failed_evaluations", summary.get("errors", 0))
        console.print(f"[dim]Items: {total} | Errors: {errors}[/dim]")

    console.print(f"[dim]Report saved to: {report_path}[/dim]")


def display_report_list(
    reports: list[dict[str, str]],
    limit: int,
    output_filter: str | None,
    output_dir: Path,
    manager: Any,
) -> None:
    """Display a table of evaluation reports."""
    from openagent_eval.reports.manager import ReportManager

    if not reports:
        console.print("[yellow]No evaluations found.[/yellow]")
        return

    if output_filter:
        filtered: list[dict[str, str]] = []
        for r in reports:
            try:
                data = manager.load_report(r["report_id"], output_dir)
                report_format = (
                    data.get("config", {}).get("report", {}).get("output", "terminal")
                )
                if report_format == output_filter:
                    filtered.append(r)
            except (FileNotFoundError, KeyError):
                continue
        reports = filtered

    reports = reports[:limit]

    table = Table(title="Recent Evaluations")
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="green")
    table.add_column("Config", style="yellow")
    table.add_column("Status", style="bold")

    for r in reports:
        report_id = r["report_id"]
        created_at = r.get("created_at", "unknown")
        config_name = "unknown"
        status = "OK"
        try:
            data = manager.load_report(report_id, output_dir)
            config_name = data.get("config", {}).get("dataset", {}).get("path", "unknown")
            errors = data.get("errors", [])
            status = "[green]OK[/green]" if not errors else "[red]FAILED[/red]"
        except (FileNotFoundError, KeyError):
            status = "[yellow]UNKNOWN[/yellow]"

        if created_at and "T" in created_at:
            created_at = created_at.split("T")[0]

        table.add_row(report_id, created_at, config_name, status)

    console.print(table)
    console.print(f"\n[dim]Showing {len(reports)} evaluations[/dim]")
