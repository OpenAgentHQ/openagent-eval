"""oaeval ui command — Launch interactive TUI dashboard."""

from __future__ import annotations

import typer
from rich.console import Console


def ui_command(
    config_path: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file.",
    ),
) -> None:
    """Launch the OpenAgent Eval interactive TUI dashboard.

    The dashboard provides a keyboard-driven interface for:
    - Running evaluations
    - Auditing corpus health
    - Diagnosing component failures
    - Viewing results and metrics

    Keyboard shortcuts:
    - 1/2/3/4: Navigate to screens
    - r: Run operations
    - q/escape: Go back or quit
    - F1: Help
    """
    try:
        from openagent_eval.ui.app import run_ui

        run_ui(config_path=config_path)
    except ImportError as e:
        console = Console(stderr=True)
        console.print(
            f"[red]Error:[/red] Textual is required for the TUI dashboard.\n\n"
            f"Import error: {e}\n\n"
            "Install it with:\n"
            "  [bold]pip install openagent-eval[ui][/bold]\n"
            "  or\n"
            "  [bold]uv pip install openagent-eval[ui][/bold]"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console = Console(stderr=True)
        console.print(f"[red]Error launching TUI:[/red] {e}")
        raise typer.Exit(code=1)
