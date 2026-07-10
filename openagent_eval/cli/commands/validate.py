"""Validate command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from openagent_eval.cli.utils.discovery import get_config_path
from openagent_eval.config.loader import load_config
from openagent_eval.config.validator import validate_api_keys, validate_config
from openagent_eval.exceptions import ConfigurationError

console = Console()


def validate_command(
    config_path: str | None = typer.Argument(
        None,
        help="Path to configuration file. Auto-discovered if not provided.",
    ),
) -> None:
    """Validate configuration without running evaluation."""
    # Get config path (explicit or auto-discovered)
    try:
        path = get_config_path(config_path)
    except SystemExit as exc:
        raise typer.Exit(code=2) from exc

    console.print("[bold blue]OpenAgent Eval[/bold blue] - Configuration Validator")
    console.print(f"[dim]Config: {path}[/dim]\n")

    # Track validation state
    has_errors = False
    warnings: list[str] = []
    errors: list[str] = []

    # 1. Validate YAML syntax
    console.print("[bold]1. Checking YAML syntax...[/bold]")
    try:
        config = load_config(path)
        console.print("  [green]OK[/green] YAML syntax valid")
    except ConfigurationError as e:
        console.print(f"  [red]FAILED[/red] {e.message}")
        errors.append(e.message)
        has_errors = True
        # Can't continue without valid config
        _print_summary(has_errors, warnings, errors)
        return

    # 2. Validate configuration schema
    console.print("\n[bold]2. Validating configuration schema...[/bold]")
    try:
        config_warnings = validate_config(config)
        warnings.extend(config_warnings)
        console.print("  [green]OK[/green] Configuration schema valid")
    except ConfigurationError as e:
        console.print(f"  [red]FAILED[/red] {e.message}")
        errors.append(e.message)
        has_errors = True

    # 3. Check API keys
    console.print("\n[bold]3. Checking API keys...[/bold]")
    missing_keys = validate_api_keys(config)
    if missing_keys:
        for key in missing_keys:
            msg = f"Missing API key: {key}"
            warnings.append(msg)
            console.print(f"  [yellow]WARNING[/yellow] {msg}")
    else:
        console.print("  [green]OK[/green] All required API keys configured")

    # 4. Validate dataset path
    console.print("\n[bold]4. Checking dataset...[/bold]")
    dataset_path = Path(config.dataset.path)
    if dataset_path.exists():
        console.print(f"  [green]OK[/green] Dataset found: {config.dataset.path}")
        # Show dataset size
        try:
            size = dataset_path.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            console.print(f"  [dim]Size: {size_str}[/dim]")
        except OSError:
            pass
    else:
        msg = f"Dataset file not found: {config.dataset.path}"
        errors.append(msg)
        has_errors = True
        console.print(f"  [red]FAILED[/red] {msg}")

    # 5. Validate output directory
    console.print("\n[bold]5. Checking output directory...[/bold]")
    output_dir = Path(config.report.output_dir)
    if output_dir.exists():
        console.print(f"  [green]OK[/green] Output directory exists: {config.report.output_dir}")
    else:
        warnings.append(f"Output directory will be created: {config.report.output_dir}")
        console.print(f"  [yellow]NOTE[/yellow] Will create: {config.report.output_dir}")

    # 6. Check provider configuration
    console.print("\n[bold]6. Checking provider configuration...[/bold]")
    console.print(f"  [dim]LLM: {config.llm.provider} ({config.llm.model})[/dim]")
    console.print(f"  [dim]Retriever: {config.retriever.provider}[/dim]")

    # 7. Check metrics
    console.print("\n[bold]7. Checking metrics...[/bold]")
    all_metrics = (
        config.metrics.retrieval
        + config.metrics.generation
        + config.metrics.performance
        + config.metrics.cost
    )
    console.print(f"  [dim]Configured: {len(all_metrics)} metrics[/dim]")
    if config.metrics.retrieval:
        console.print(f"    [dim]Retrieval: {', '.join(config.metrics.retrieval)}[/dim]")
    if config.metrics.generation:
        console.print(f"    [dim]Generation: {', '.join(config.metrics.generation)}[/dim]")
    if config.metrics.performance:
        console.print(f"    [dim]Performance: {', '.join(config.metrics.performance)}[/dim]")
    if config.metrics.cost:
        console.print(f"    [dim]Cost: {', '.join(config.metrics.cost)}[/dim]")

    # Print summary
    _print_summary(has_errors, warnings, errors)


def _print_summary(has_errors: bool, warnings: list[str], errors: list[str]) -> None:
    """Print validation summary.

    Args:
        has_errors: Whether any errors were found.
        warnings: List of warning messages.
        errors: List of error messages.
    """
    console.print("\n[bold]Summary:[/bold]")

    if has_errors:
        console.print(f"[red]FAILED[/red] {len(errors)} error(s) found")
        for error in errors:
            console.print(f"  [red]- {error}[/red]")
        console.print("\n[dim]Fix the errors above and try again.[/dim]")
        raise typer.Exit(code=2)
    else:
        console.print("[green]PASSED[/green] Configuration is valid")
        if warnings:
            console.print(f"[yellow]WARNING[/yellow] {len(warnings)} warning(s)")
            for warning in warnings:
                console.print(f"  [yellow]- {warning}[/yellow]")
        console.print("\n[dim]Ready to run: oaeval run <config>[/dim]")
