"""Config file auto-discovery for OpenAgent Eval."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console

# Default config file names to search for (in order of priority)
_CONFIG_NAMES = ["config.yaml", "config.yml", "oaeval.yaml", "oaeval.yml"]

# Environment variable for config path
_CONFIG_ENV_VAR = "OAEVAL_CONFIG"


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Find configuration file by searching common locations.

    Search order:
    1. OAEVAL_CONFIG environment variable
    2. Current working directory
    3. Parent directories up to filesystem root

    Args:
        start_dir: Directory to start searching from. Defaults to cwd.

    Returns:
        Path to config file if found, None otherwise.
    """
    # 1. Check environment variable
    env_config = os.environ.get(_CONFIG_ENV_VAR)
    if env_config:
        env_path = Path(env_config)
        if env_path.exists() and env_path.is_file():
            return env_path
        return None

    # 2. Search from start_dir (default: cwd)
    search_dir = start_dir or Path.cwd()

    # Walk up the directory tree
    current = search_dir.resolve()
    while True:
        # Check current directory
        config = _check_directory(current)
        if config is not None:
            return config

        # Move to parent
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            break
        current = parent

    return None


def _check_directory(directory: Path) -> Path | None:
    """Check if a directory contains a config file.

    Args:
        directory: Directory to check.

    Returns:
        Path to config file if found, None otherwise.
    """
    for name in _CONFIG_NAMES:
        candidate = directory / name
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def get_config_path(explicit_path: str | None = None) -> Path:
    """Get config path, using explicit path or auto-discovery.

    Args:
        explicit_path: Explicit config path from CLI argument.

    Returns:
        Path to config file.

    Raises:
        SystemExit: If no config file found.
    """
    console = Console(stderr=True)

    if explicit_path:
        path = Path(explicit_path)
        if not path.exists():
            console.print(f"[red]Error:[/red] Configuration file not found: {explicit_path}")
            console.print("[dim]Tip: Run 'oaeval init' to create a configuration file[/dim]")
            raise typer.Exit(code=2)
        return path

    # Auto-discover
    found = find_config_file()
    if found is None:
        console.print("[red]Error:[/red] No configuration file found")
        console.print("[dim]Searched for: config.yaml, config.yml, oaeval.yaml, oaeval.yml[/dim]")
        console.print("[dim]Tip: Run 'oaeval init' to create a configuration file[/dim]")
        console.print("[dim]Or set OAEVAL_CONFIG environment variable[/dim]")
        raise typer.Exit(code=2)

    return found
