"""Init command for OpenAgent Eval."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from openagent_eval.exceptions import ConfigurationError
from openagent_eval.cli.utils.constants import DEFAULT_CONFIG_CONTENT

console = Console()


def init_command(
    config_path: str = typer.Option(
        "config.yaml",
        "--config",
        "-c",
        help="Path to create configuration file.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration file.",
    ),
) -> None:
    """Create a new evaluation configuration file."""
    path = Path(config_path)

    if path.exists() and not force and not Confirm.ask(
        f"Configuration file '{config_path}' already exists. Overwrite?"
    ):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit()

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG_CONTENT, encoding="utf-8")
        console.print(f"[green]OK[/green] Configuration created: {config_path}")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("  1. Edit the configuration file")
        console.print("  2. Run [bold]oaeval run[/bold] to start evaluation")
    except OSError as e:
        raise ConfigurationError(
            message=f"Failed to create configuration: {e}",
            config_path=config_path,
        ) from e
