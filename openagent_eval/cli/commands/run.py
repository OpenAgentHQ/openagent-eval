"""Run command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from openagent_eval import __version__
from openagent_eval.exceptions import ConfigurationError
from openagent_eval.reports.manager import ReportManager
from openagent_eval.cli.utils.helpers import (
    apply_output_override,
    execute_evaluation,
    load_config_from_path,
    load_dataset_for_run,
)
from openagent_eval.cli.utils.display import display_run_result

console = Console()


def run_command(
    config_path: str = typer.Argument(
        help="Path to configuration file.",
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
) -> None:
    """Run evaluation pipeline with the specified configuration."""
    path = Path(config_path)

    if not path.exists():
        raise ConfigurationError(
            message=f"Configuration file not found: {config_path}",
            config_path=config_path,
        )

    console.print(f"[bold blue]OpenAgent Eval[/bold blue] v{__version__}")
    console.print(f"[dim]Configuration: {config_path}[/dim]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading configuration...", total=None)
        config = load_config_from_path(config_path)
        apply_output_override(config, output)

        progress.update(task, description="Loading dataset...")
        dataset_items = load_dataset_for_run(config)

        progress.update(task, description="Running evaluation...")
        report = execute_evaluation(config, dataset_items)

        progress.update(task, description="Generating report...")
        format_name = config.report.output.value
        manager = ReportManager()
        output_dir = Path(config.report.output_dir)
        report_path = manager.save_report(report, output_dir)

        progress.update(task, description="Complete!", completed=True)

    display_run_result(report, format_name, report_path, output_dir, verbose)
