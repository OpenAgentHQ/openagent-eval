"""Doctor command for OpenAgent Eval."""

from __future__ import annotations

import importlib
import os
import sys

import typer
from rich.console import Console
from rich.table import Table

from openagent_eval import __version__

console = Console()


def doctor_command(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information.",
    ),
) -> None:
    """Check environment and dependencies for OpenAgent Eval."""
    console.print("[bold blue]OpenAgent Eval[/bold blue] - Environment Check\n")

    table = Table(title="Environment Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_ok = sys.version_info >= (3, 11)
    table.add_row(
        "Python",
        "[green]OK[/green]" if python_ok else "[red]MISSING[/red]",
        f"v{python_version}" + ("" if python_ok else " (3.11+ required)"),
    )

    dependencies = [
        ("typer", "CLI framework"),
        ("rich", "Terminal UI"),
        ("pydantic", "Data validation"),
        ("yaml", "Configuration"),
        ("loguru", "Logging"),
        ("jinja2", "HTML templates"),
    ]

    for dep_name, dep_desc in dependencies:
        try:
            importlib.import_module(dep_name.replace("-", "_"))
            table.add_row(dep_name, "[green]OK[/green]", dep_desc)
        except ImportError:
            table.add_row(dep_name, "[red]MISSING[/red]", f"{dep_desc} (not installed)")

    console.print(table)

    key_table = Table(title="API Key Availability")
    key_table.add_column("Provider", style="cyan")
    key_table.add_column("Environment Variable", style="yellow")
    key_table.add_column("Status", style="bold")

    api_keys = [
        ("OpenAI", "OPENAI_API_KEY"),
        ("Gemini", "GEMINI_API_KEY"),
        ("Anthropic", "ANTHROPIC_API_KEY"),
        ("Groq", "GROQ_API_KEY"),
    ]

    available_providers: list[str] = []
    for provider_name, env_var in api_keys:
        key_value = os.environ.get(env_var)
        if key_value:
            key_table.add_row(provider_name, env_var, "[green]Available[/green]")
            available_providers.append(provider_name)
        else:
            key_table.add_row(provider_name, env_var, "[dim]Not set[/dim]")

    console.print(key_table)

    console.print("\n[bold]Summary:[/bold]")
    if python_ok:
        console.print("[green]OK[/green] Python version is compatible")
    else:
        console.print("[red]MISSING[/red] Python 3.11+ required")

    if available_providers:
        console.print(
            f"[green]OK[/green] Available providers: {', '.join(available_providers)}"
        )
    else:
        console.print("[yellow]WARNING[/yellow] No API keys configured")

    if verbose:
        console.print(f"\n[dim]Python: {sys.executable}[/dim]")
        console.print(f"[dim]Version: {__version__}[/dim]")

    console.print("\n[dim]Run 'pip install openagent-eval[all]' to install all dependencies.[/dim]")
