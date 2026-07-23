"""Diagnose command for OpenAgent Eval.

Loads an evaluation report and runs component diagnosis to attribute blame
when things go wrong — retrieval, generation, or chunking.

Usage::

    oaeval diagnose reports/eval_2024_01_15.json
    oaeval diagnose reports/eval_2024_01_15.json --output json
    oaeval diagnose reports/eval_2024_01_15.json --threshold 0.5
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from openagent_eval.cli.context import get_context
from openagent_eval.diagnosis import DiagnosisAnalyzer
from openagent_eval.diagnosis.models import BlameTarget, FailureMode

console = Console()

# Human-readable labels for blame targets
_BLAME_LABELS: dict[str, str] = {
    BlameTarget.RETRIEVAL.value: "[red]Retrieval[/red]",
    BlameTarget.GENERATION.value: "[yellow]Generation[/yellow]",
    BlameTarget.CHUNKING.value: "[cyan]Chunking[/cyan]",
    BlameTarget.DATASET.value: "[magenta]Dataset[/magenta]",
    BlameTarget.UNKNOWN.value: "[dim]Unknown[/dim]",
}

# Human-readable labels for failure modes
_FAILURE_LABELS: dict[str, str] = {
    FailureMode.EMPTY_RETRIEVAL.value: "Empty Retrieval",
    FailureMode.LOW_CONTEXT_RELEVANCE.value: "Low Context Relevance",
    FailureMode.MISSING_CONTEXT.value: "Missing Context",
    FailureMode.HALLUCINATION.value: "Hallucination",
    FailureMode.OFF_TOPIC_ANSWER.value: "Off-Topic Answer",
    FailureMode.CHUNKING_SPLIT_INFO_LOST.value: "Chunking Split",
    FailureMode.STALE_INDEX.value: "Stale Index",
    FailureMode.EMBEDDING_MISMATCH.value: "Embedding Mismatch",
}


def diagnose_command(
    report_path: str = typer.Argument(
        ...,
        help="Path to evaluation report JSON file.",
    ),
    output: str = typer.Option(
        "terminal",
        "--output",
        "-o",
        help="Output format (terminal, json).",
    ),
    threshold: float = typer.Option(
        0.3,
        "--threshold",
        "-t",
        help="Minimum confidence threshold for failure detection (0.0-1.0).",
    ),
    max_recommendations: int = typer.Option(
        5,
        "--max-recs",
        help="Maximum number of recommendations to show.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed failure information.",
    ),
) -> None:
    """Diagnose evaluation failures and attribute blame to specific components.

    Args:
        report_path (str): Path to the evaluation report JSON file.
        output (str): Output format. Must be either 'terminal' or 'json'.
            Defaults to 'terminal'.
        threshold (float): Minimum confidence threshold for failure detection (0.0-1.0).
            Defaults to 0.3.
        max_recommendations (int): Maximum number of recommendations to show in the report.
            Defaults to 5.
        verbose (bool): Show detailed failure information for each item.
            Defaults to False.

    Returns:
        None. Prints a formatted diagnosis report to the console or outputs JSON
        to standard output.
        Raises typer.Exit(code=2) if the report file does not exist, is not a JSON
        file, or cannot be parsed.

    Example:
        $ oaeval diagnose reports/eval_report.json --threshold 0.5 --verbose
    """
    ctx = get_context()
    path = Path(report_path)

    if not path.exists():
        console.print(f"[red]Error:[/red] Report file not found: {path}")
        raise typer.Exit(code=2)

    if not path.suffix == ".json":
        console.print("[red]Error:[/red] Report file must be a JSON file.")
        raise typer.Exit(code=2)

    # Load evaluation results from the report
    try:
        results = _load_report(path)
    except (json.JSONDecodeError, KeyError) as e:
        console.print(f"[red]Error:[/red] Failed to parse report: {e}")
        raise typer.Exit(code=2) from e

    if not results:
        console.print("[yellow]Warning:[/yellow] No evaluation results found in report.")
        raise typer.Exit(code=0)

    # Run diagnosis
    analyzer = DiagnosisAnalyzer(
        blame_threshold=threshold,
        max_recommendations=max_recommendations,
    )

    report = analyzer.analyze(results)

    # Output
    if output == "json" or ctx.json_output:
        _output_json(report)
    else:
        _display_terminal(report, verbose)


def _load_report(path: Path) -> list[dict[str, object]]:
    """Load evaluation results from a JSON report file.

    Supports two formats:
    1. Direct list of evaluation results
    2. PipelineResult wrapper with a "results" key

    Args:
        path: Path to the JSON report file.

    Returns:
        List of evaluation result dicts.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Handle PipelineResult wrapper
    if isinstance(data, dict) and "results" in data:
        return data["results"]  # type: ignore[no-any-return]

    # Handle direct list
    if isinstance(data, list):
        return data  # type: ignore[no-any-return]

    return []


def _display_terminal(report: object, verbose: bool) -> None:
    """Display diagnosis report in terminal format.

    Args:
        report: DiagnosisReport instance.
        verbose: Whether to show detailed failure information.
    """
    from openagent_eval.diagnosis.models import DiagnosisReport

    assert isinstance(report, DiagnosisReport)

    # Header
    console.print(
        Panel(
            f"[bold blue]Diagnosis Report[/bold blue]\n"
            f"Items analyzed: {report.total_items}\n"
            f"Overall health: {report.overall_health:.1%}",
            title="Component Diagnosis",
            border_style="blue",
        )
    )

    # Health indicator
    if report.overall_health >= 0.8:
        health_color = "green"
        health_label = "Healthy"
    elif report.overall_health >= 0.5:
        health_color = "yellow"
        health_label = "Degraded"
    else:
        health_color = "red"
        health_label = "Unhealthy"

    console.print(
        f"\n[bold {health_color}]System Health: {health_label} "
        f"({report.overall_health:.1%})[/bold {health_color}]\n"
    )

    # Blame summary
    if report.blame_summary:
        blame_table = Table(title="Blame Attribution", show_lines=True)
        blame_table.add_column("Component", style="bold")
        blame_table.add_column("Failures", justify="right")
        blame_table.add_column("Percentage", justify="right")

        total_failures = sum(report.blame_summary.values())
        for blame_target, count in sorted(
            report.blame_summary.items(), key=lambda x: x[1], reverse=True
        ):
            label = _BLAME_LABELS.get(blame_target, blame_target)
            pct = (count / total_failures * 100) if total_failures > 0 else 0
            blame_table.add_row(label, str(count), f"{pct:.1f}%")

        console.print(blame_table)
        console.print()

    # Failure summary
    if report.failure_summary:
        failure_table = Table(title="Failure Modes", show_lines=True)
        failure_table.add_column("Failure Mode", style="bold")
        failure_table.add_column("Count", justify="right")

        for mode, count in sorted(
            report.failure_summary.items(), key=lambda x: x[1], reverse=True
        ):
            label = _FAILURE_LABELS.get(mode, mode)
            failure_table.add_row(label, str(count))

        console.print(failure_table)
        console.print()

    # Detailed failures (verbose mode)
    if verbose and report.failures:
        console.print("[bold]Detailed Failures:[/bold]\n")
        for i, failure in enumerate(report.failures[:20], 1):
            mode_label = _FAILURE_LABELS.get(failure.mode.value, failure.mode.value)
            blame_label = _BLAME_LABELS.get(failure.blame.value, failure.blame.value)
            console.print(
                f"  {i}. [bold]{mode_label}[/bold] -> {blame_label}\n"
                f"     Confidence: {failure.confidence:.2f}\n"
                f"     Reason: {failure.reason}\n"
                f"     Question: {failure.question[:80]}{'...' if len(failure.question) > 80 else ''}\n"
            )

        if len(report.failures) > 20:
            console.print(
                f"  [dim]... and {len(report.failures) - 20} more failures[/dim]\n"
            )

    # Chunking issues
    if report.chunking_issues:
        console.print("[bold]Chunking Issues:[/bold]\n")
        for issue in report.chunking_issues[:10]:
            console.print(
                f"  [cyan]{issue.issue_type}[/cyan]: {issue.description}\n"
            )

    # Recommendations
    if report.recommendations:
        console.print("[bold]Recommendations:[/bold]\n")
        for rec in report.recommendations:
            console.print(f"  -> {rec}")

    console.print()


def _output_json(report: object) -> None:
    """Output diagnosis report as JSON.

    Args:
        report: DiagnosisReport instance.
    """
    from openagent_eval.diagnosis.models import DiagnosisReport

    assert isinstance(report, DiagnosisReport)
    console.print(json.dumps(report.to_dict(), indent=2))
