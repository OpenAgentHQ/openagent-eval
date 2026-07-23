"""List command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from openagent_eval.cli.context import get_context
from openagent_eval.cli.utils.constants import DEFAULT_OUTPUT_DIR
from openagent_eval.cli.utils.display import display_report_list
from openagent_eval.reports.manager import ReportManager

console = Console()


def list_command(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Number of evaluations to show.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Filter by output format.",
    ),
    output_dir: str | None = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Directory where reports are stored (default: ./reports).",
    ),
    sort: Literal["date", "score", "cost"] = typer.Option(
        "date",
        "--sort",
        "-s",
        help="Sort by: date, score, or cost.",
    ),
    reverse: bool = typer.Option(
        False,
        "--reverse",
        "-r",
        help="Reverse sort order.",
    ),
    search: str | None = typer.Option(
        None,
        "--search",
        help="Search reports by config path or ID.",
    ),
) -> None:
    """List previous evaluation runs with filtering and sorting options.

    Args:
        limit (int): Maximum number of evaluations to show. Defaults to 10.
        output (str | None): Filter reports by output format (e.g. 'terminal', 'markdown', 'html', 'json').
            Defaults to None.
        output_dir (str | None): Directory where reports are stored. If not specified,
            defaults to the project's standard reports directory (./reports).
        sort (Literal["date", "score", "cost"]): Field to sort reports by: 'date', 'score', or 'cost'.
            Defaults to 'date'.
        reverse (bool): Reverse the sort order (ascending instead of descending). Defaults to False.
        search (str | None): Search term to filter reports by config path or report ID.
            Defaults to None.

    Returns:
        None. Prints a formatted table/list of reports to the console, or outputs JSON
        to standard output if configured.
        Raises typer.Exit(code=1) if listing reports fails.

    Example:
        $ oaeval list --limit 5 --sort score --reverse
    """
    ctx = get_context()

    console.print("[bold blue]OpenAgent Eval[/bold blue] - Evaluation History\n")

    manager = ReportManager()
    reports_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    try:
        reports = manager.list_reports(reports_dir)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to list reports: {e}")
        raise typer.Exit(code=1) from e

    # Apply filters
    if output:
        reports = _filter_by_output(reports, output, reports_dir, manager)

    if search:
        reports = _filter_by_search(reports, search, reports_dir, manager)

    # Sort reports
    reports = _sort_reports(reports, sort, reverse, reports_dir, manager)

    # Apply limit
    reports = reports[:limit]

    # Display
    if ctx.json_output:
        _display_json_list(reports, reports_dir, manager)
    else:
        display_report_list(reports, limit, output, reports_dir, manager)


def _filter_by_output(
    reports: list[dict],
    output_filter: str,
    output_dir: Path,
    manager: ReportManager,
) -> list[dict]:
    """Filter reports by output format.

    Args:
        reports: List of report dicts.
        output_filter: Output format to filter by.
        output_dir: Reports directory.
        manager: Report manager instance.

    Returns:
        Filtered list of reports.
    """
    filtered: list[dict] = []
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
    return filtered


def _filter_by_search(
    reports: list[dict],
    search_term: str,
    output_dir: Path,
    manager: ReportManager,
) -> list[dict]:
    """Filter reports by search term.

    Args:
        reports: List of report dicts.
        search_term: Term to search for.
        output_dir: Reports directory.
        manager: Report manager instance.

    Returns:
        Filtered list of reports.
    """
    search_lower = search_term.lower()
    filtered: list[dict] = []

    for r in reports:
        # Check report ID
        if search_lower in r.get("report_id", "").lower():
            filtered.append(r)
            continue

        # Check config path
        try:
            data = manager.load_report(r["report_id"], output_dir)
            config_path = data.get("config", {}).get("dataset", {}).get("path", "")
            if search_lower in config_path.lower():
                filtered.append(r)
        except (FileNotFoundError, KeyError):
            continue

    return filtered


def _sort_reports(
    reports: list[dict],
    sort_by: str,
    reverse: bool,
    output_dir: Path,
    manager: ReportManager,
) -> list[dict]:
    """Sort reports by specified criteria.

    Args:
        reports: List of report dicts.
        sort_by: Sort criteria (date, score, cost).
        reverse: Whether to reverse sort order.
        output_dir: Reports directory.
        manager: Report manager instance.

    Returns:
        Sorted list of reports.
    """
    if sort_by == "date":
        # Sort by created_at (default behavior)
        return sorted(
            reports,
            key=lambda r: r.get("created_at", ""),
            reverse=not reverse,
        )

    # For score and cost, we need to load report data
    def _get_sort_key(report: dict) -> float:
        try:
            data = manager.load_report(report["report_id"], output_dir)
            if sort_by == "score":
                # Get average score from metrics
                metrics = data.get("metrics", {})
                if metrics:
                    return sum(metrics.values()) / len(metrics)
                return 0.0
            elif sort_by == "cost":
                # Get total cost
                return data.get("cost", {}).get("total", 0.0)
        except (FileNotFoundError, KeyError):
            pass
        return 0.0

    return sorted(reports, key=_get_sort_key, reverse=not reverse)


def _display_json_list(
    reports: list[dict],
    output_dir: Path,
    manager: ReportManager,
) -> None:
    """Display reports as JSON.

    Args:
        reports: List of report dicts.
        output_dir: Reports directory.
        manager: Report manager instance.
    """
    import json

    output_data = []
    for r in reports:
        report_id = r.get("report_id", "unknown")
        created_at = r.get("created_at", "unknown")
        config_name = "unknown"
        status = "unknown"

        try:
            data = manager.load_report(report_id, output_dir)
            config_name = data.get("config", {}).get("dataset", {}).get("path", "unknown")
            errors = data.get("errors", [])
            status = "ok" if not errors else "failed"
        except (FileNotFoundError, KeyError):
            status = "unknown"

        output_data.append({
            "report_id": report_id,
            "created_at": created_at,
            "config": config_name,
            "status": status,
        })

    console.print(json.dumps(output_data, indent=2))
