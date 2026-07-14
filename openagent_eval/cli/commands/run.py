"""Run command for OpenAgent Eval."""

from __future__ import annotations

import time
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from openagent_eval import __version__
from openagent_eval.cli.context import get_context
from openagent_eval.cli.utils.discovery import get_config_path
from openagent_eval.cli.utils.display import display_run_result
from openagent_eval.cli.utils.helpers import (
    apply_output_override,
    execute_evaluation,
    get_report_generator,
    load_config_from_path,
    load_dataset_for_run,
)
from openagent_eval.exceptions import ConfigurationError
from openagent_eval.reports.manager import ReportManager

console = Console()


def run_command(
    config_path: str | None = typer.Argument(
        None,
        help="Path to configuration file. Auto-discovered if not provided.",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Override output format (terminal, markdown, html, json).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate config and show evaluation plan without running.",
    ),
    metrics: str | None = typer.Option(
        None,
        "--metrics",
        "-m",
        help="Comma-separated list of metrics to run (overrides config).",
    ),
) -> None:
    """Run evaluation pipeline with the specified configuration."""
    ctx = get_context()

    # Merge command-level verbose with global
    if verbose:
        ctx.verbose = True

    # Get config path (explicit or auto-discovered)
    try:
        resolved_path = get_config_path(config_path)
    except SystemExit as exc:
        raise typer.Exit(code=2) from exc

    path = resolved_path

    if not ctx.quiet:
        console.print(f"[bold blue]OpenAgent Eval[/bold blue] v{__version__}")
        console.print(f"[dim]Configuration: {path}[/dim]\n")

    # Load configuration
    try:
        config = load_config_from_path(path)
    except ConfigurationError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(code=2) from e

    apply_output_override(config, output)

    # Override metrics if specified
    if metrics:
        _apply_metrics_override(config, metrics)

    # Dry-run mode
    if dry_run:
        _run_dry_run(config, path)
        return

    # Show evaluation plan if verbose
    if ctx.verbose:
        _show_evaluation_plan(config)

    # Run evaluation with progress
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        disable=ctx.quiet,
    ) as progress:
        task = progress.add_task("Loading configuration...", total=None)
        config = load_config_from_path(path)
        apply_output_override(config, output)

        progress.update(task, description="Loading dataset...")
        dataset_items = load_dataset_for_run(config)
        total_items = len(dataset_items)
        progress.update(task, description=f"Loaded {total_items} items", completed=1, total=1)

        progress.update(task, description=f"Running evaluation ({total_items} items)...", total=total_items)
        report = execute_evaluation(config, dataset_items)
        progress.update(task, completed=total_items)

        progress.update(task, description="Generating report...")
        format_name = config.report.output.value
        manager = ReportManager()
        output_dir = Path(config.report.output_dir)
        report_path = manager.save_report(report, output_dir)

        # Also emit the requested report format to disk (terminal only prints).
        format_file: Path | None = None
        if format_name != "terminal":
            generator = get_report_generator(format_name)
            ext = {"markdown": ".md", "html": ".html", "json": ".json"}.get(
                format_name, ".txt"
            )
            format_file = output_dir / f"{report_path.stem}{ext}"
            generator.generate_to_file(report, format_file)

        progress.update(task, description="Complete!", completed=True)

    elapsed = time.time() - start_time

    if ctx.json_output:
        _output_json_result(report, report_path, elapsed)
    else:
        display_run_result(report, format_name, report_path, output_dir, verbose, format_file)


def _apply_metrics_override(config: object, metrics_str: str) -> None:
    """Apply metrics override from CLI flag.

    Args:
        config: Configuration object.
        metrics_str: Comma-separated metrics string.
    """
    from openagent_eval.config.models import MetricsConfig

    metric_list = [m.strip() for m in metrics_str.split(",") if m.strip()]

    # Categorize metrics
    retrieval_metrics = [
        "context_precision", "context_recall", "mrr", "ndcg",
        "hit_rate", "precision_at_k", "recall_at_k",
    ]
    generation_metrics = [
        "faithfulness", "answer_relevancy", "hallucination",
        "semantic_similarity", "exact_match", "f1_score",
        "bleu", "rouge", "bertscore",
    ]
    performance_metrics = ["latency"]
    cost_metrics = ["token_count"]

    config.metrics = MetricsConfig(
        retrieval=[m for m in metric_list if m in retrieval_metrics],
        generation=[m for m in metric_list if m in generation_metrics],
        performance=[m for m in metric_list if m in performance_metrics],
        cost=[m for m in metric_list if m in cost_metrics],
    )


def _run_dry_run(config: object, config_path: Path) -> None:
    """Run dry-run mode showing evaluation plan.

    Args:
        config: Configuration object.
        config_path: Path to config file.
    """
    console.print("[bold blue]OpenAgent Eval[/bold blue] - Dry Run Mode\n")

    # Show configuration summary
    console.print("[bold]Configuration Summary:[/bold]")
    console.print(f"  [dim]Config file: {config_path}[/dim]")
    console.print(f"  [dim]Dataset: {config.dataset.path}[/dim]")
    console.print(f"  [dim]LLM: {config.llm.provider} ({config.llm.model})[/dim]")
    console.print(f"  [dim]Retriever: {config.retriever.provider}[/dim]")
    console.print(f"  [dim]Output: {config.report.output.value}[/dim]")
    console.print(f"  [dim]Output dir: {config.report.output_dir}[/dim]")

    # Show metrics
    all_metrics = (
        config.metrics.retrieval
        + config.metrics.generation
        + config.metrics.performance
        + config.metrics.cost
    )
    console.print(f"\n[bold]Metrics ({len(all_metrics)}):[/bold]")
    if config.metrics.retrieval:
        console.print(f"  [dim]Retrieval: {', '.join(config.metrics.retrieval)}[/dim]")
    if config.metrics.generation:
        console.print(f"  [dim]Generation: {', '.join(config.metrics.generation)}[/dim]")
    if config.metrics.performance:
        console.print(f"  [dim]Performance: {', '.join(config.metrics.performance)}[/dim]")
    if config.metrics.cost:
        console.print(f"  [dim]Cost: {', '.join(config.metrics.cost)}[/dim]")

    # Try to load dataset
    console.print("\n[bold]Dataset:[/bold]")
    try:
        dataset_items = load_dataset_for_run(config)
        console.print(f"  [green]OK[/green] Loaded {len(dataset_items)} items")

        # Show sample
        if dataset_items:
            console.print("\n  [dim]Sample item:[/dim]")
            sample = dataset_items[0]
            for key, value in list(sample.items())[:3]:
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                console.print(f"    [dim]{key}: {value}[/dim]")
    except Exception as e:
        console.print(f"  [red]Error:[/red] {e}")

    # Show warnings
    console.print("\n[bold]Warnings:[/bold]")
    if config.timeout < 60:
        console.print(
            f"  [yellow]Timeout is low ({config.timeout}s) - evaluations may time out[/yellow]"
        )
    if len(config.metrics.generation) > 5:
        console.print(f"  [yellow]Running {len(config.metrics.generation)} generation metrics may be slow[/yellow]")

    console.print("\n[dim]This was a dry run. No evaluations were performed.[/dim]")
    console.print("[dim]Run 'oaeval run <config>' to execute the evaluation.[/dim]")


def _show_evaluation_plan(config: object) -> None:
    """Show evaluation plan in verbose mode.

    Args:
        config: Configuration object.
    """
    console.print("[bold]Evaluation Plan:[/bold]")
    console.print(f"  Max workers: {config.max_workers}")
    console.print(f"  Timeout: {config.timeout}s")
    console.print(f"  Parallel: {config.parallel}")
    console.print("")


def _output_json_result(report: object, report_path: Path, elapsed: float) -> None:
    """Output result as JSON.

    Args:
        report: Evaluation report.
        report_path: Path to saved report.
        elapsed: Elapsed time in seconds.
    """
    import json

    result = {
        "status": "success",
        "report_path": str(report_path),
        "elapsed_seconds": round(elapsed, 2),
    }

    if hasattr(report, "summary"):
        result["summary"] = report.summary

    console.print(json.dumps(result, indent=2))
