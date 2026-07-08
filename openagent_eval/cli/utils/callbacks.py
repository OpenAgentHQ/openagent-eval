"""CLI callbacks for OpenAgent Eval."""

from __future__ import annotations

import typer


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from openagent_eval import __version__

        typer.echo(f"OpenAgent Eval v{__version__}")
        raise typer.Exit()
