"""Doctor command for OpenAgent Eval."""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from openagent_eval import __version__
from openagent_eval.cli.context import get_context
from openagent_eval.cli.utils.discovery import find_config_file
from openagent_eval.config.loader import load_config
from openagent_eval.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pathlib import Path

console = Console()

_LLM_PROVIDER_EXTRAS: dict[str, tuple[tuple[str, ...], str]] = {
    "anthropic": (("anthropic",), "providers"),
    "gemini": (("google.genai",), "providers"),
    "groq": (("groq",), "providers"),
    "openai": (("openai", "tiktoken"), "providers"),
}

_RETRIEVER_EXTRAS: dict[str, tuple[tuple[str, ...], str]] = {
    "bm25": (("rank_bm25",), "bm25"),
    "elasticsearch": (("elasticsearch",), "elasticsearch"),
    "faiss": (("faiss",), "faiss"),
    "pgvector": (("psycopg", "pgvector"), "pgvector"),
    "pinecone": (("pinecone",), "pinecone"),
    "qdrant": (("qdrant_client",), "qdrant"),
    "weaviate": (("weaviate",), "weaviate"),
}


def doctor_command(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information.",
    ),
    check_api: bool = typer.Option(
        False,
        "--check-api",
        help="Test API connectivity (requires API keys).",
    ),
) -> None:
    """Check environment, dependencies, and API connectivity for OpenAgent Eval.

    Args:
        verbose (bool): Show detailed system, Python, and version information.
            Defaults to False.
        check_api (bool): Test connectivity to available API endpoints.
            Defaults to False.

    Returns:
        None. Prints environment status tables and recommendations directly to the console.

    Example:
        $ oaeval doctor --check-api
    """
    ctx = get_context()

    if verbose:
        ctx.verbose = True

    console.print("[bold blue]OpenAgent Eval[/bold blue] - Environment Check\n")

    # Environment status
    table = Table(title="Environment Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    python_ok = sys.version_info >= (3, 11)
    table.add_row(
        "Python",
        "[green]OK[/green]" if python_ok else "[red]MISSING[/red]",
        f"v{python_version}" + ("" if python_ok else " (3.11+ required)"),
    )

    # Check openagent-eval version
    table.add_row(
        "openagent-eval",
        "[green]OK[/green]",
        f"v{__version__}",
    )

    dependencies = [
        ("typer", "CLI framework"),
        ("rich", "Terminal UI"),
        ("pydantic", "Data validation"),
        ("yaml", "Configuration"),
        ("loguru", "Logging"),
        ("jinja2", "HTML templates"),
        ("httpx", "HTTP client"),
    ]

    for dep_name, dep_desc in dependencies:
        try:
            importlib.import_module(dep_name.replace("-", "_"))
            table.add_row(dep_name, "[green]OK[/green]", dep_desc)
        except ImportError:
            table.add_row(dep_name, "[red]MISSING[/red]", f"{dep_desc} (not installed)")

    console.print(table)

    # API key status
    key_table = Table(title="API Key Availability")
    key_table.add_column("Provider", style="cyan")
    key_table.add_column("Environment Variable", style="yellow")
    key_table.add_column("Status", style="bold")

    api_keys = [
        ("OpenAI", "OPENAI_API_KEY"),
        ("Gemini", "GEMINI_API_KEY"),
        ("Anthropic", "ANTHROPIC_API_KEY"),
        ("Groq", "GROQ_API_KEY"),
        ("OpenRouter", "OPENROUTER_API_KEY"),
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

    # API connectivity tests
    if check_api and available_providers:
        console.print("\n[bold]API Connectivity Tests:[/bold]")
        _test_api_connectivity(available_providers)

    # Configuration file check
    console.print("\n[bold]Configuration:[/bold]")
    config_path = _check_config_files()
    _check_configured_provider_extras(config_path)

    # Summary
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
        console.print(f"[dim]Platform: {sys.platform}[/dim]")

    # Recommendations
    _print_recommendations(python_ok, available_providers)


def _test_api_connectivity(providers: list[str]) -> None:
    """Test API connectivity for available providers.

    Args:
        providers: List of available provider names.
    """
    import httpx

    test_urls = {
        "OpenAI": "https://api.openai.com/v1/models",
        "Gemini": "https://generativelanguage.googleapis.com/v1/models",
        "Anthropic": "https://api.anthropic.com/v1/messages",
        "Groq": "https://api.groq.com/openai/v1/models",
        "OpenRouter": "https://openrouter.ai/api/v1/models",
    }

    for provider in providers:
        url = test_urls.get(provider)
        if not url:
            continue

        try:
            # Just test if we can reach the endpoint (doesn't need auth for this check)
            with httpx.Client(timeout=5.0) as client:
                client.head(url)
                # Any response means the endpoint is reachable
                console.print(f"  [green]OK[/green] {provider}: reachable")
        except httpx.TimeoutException:
            console.print(
                f"  [yellow]TIMEOUT[/yellow] {provider}: connection timed out"
            )
        except httpx.ConnectError:
            console.print(f"  [red]FAILED[/red] {provider}: connection failed")
        except Exception as e:
            console.print(f"  [yellow]SKIP[/yellow] {provider}: {type(e).__name__}")


def _check_config_files() -> Path | None:
    """Check for configuration files in current directory."""
    config_path = find_config_file()

    if config_path is None:
        console.print("  [dim]No config file in current directory[/dim]")
        console.print("  [dim]Run 'oaeval init' to create one[/dim]")
        return None

    console.print(f"  [green]OK[/green] Found config: {config_path}")
    return config_path


def _check_configured_provider_extras(config_path: Path | None) -> None:
    """Warn when the active config uses providers whose extras are not installed."""
    if config_path is None:
        return

    try:
        config = load_config(config_path)
    except ConfigurationError as exc:
        console.print(
            f"  [yellow]WARNING[/yellow] Could not inspect configured providers: {exc.message}"
        )
        return

    missing = [
        *_missing_extra_rows("LLM", config.llm.provider, _LLM_PROVIDER_EXTRAS),
        *_missing_extra_rows("Retriever", config.retriever.provider, _RETRIEVER_EXTRAS),
    ]

    if not missing:
        console.print("  [green]OK[/green] Configured provider extras installed")
        return

    table = Table(title="Configured Provider Extras")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Install")

    for provider, extra in missing:
        table.add_row(
            provider,
            "[yellow]MISSING[/yellow]",
            escape(f'pip install "openagent-eval[{extra}]"'),
        )

    console.print(table)


def _missing_extra_rows(
    kind: str,
    provider: str,
    extras: dict[str, tuple[tuple[str, ...], str]],
) -> list[tuple[str, str]]:
    key = provider.lower().strip()
    if key not in extras:
        return []

    modules, extra = extras[key]
    if all(_module_available(module) for module in modules):
        return []

    return [(f"{kind}: {provider}", extra)]


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _print_recommendations(python_ok: bool, providers: list[str]) -> None:
    """Print recommendations based on check results.

    Args:
        python_ok: Whether Python version is compatible.
        providers: List of available providers.
    """
    recommendations = []

    if not python_ok:
        recommendations.append("Upgrade Python to 3.11 or later")

    if not providers:
        recommendations.append("Set at least one API key (e.g., OPENAI_API_KEY)")
        recommendations.append("Run 'oaeval doctor --check-api' to test connectivity")

    if recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in recommendations:
            console.print(f"  [yellow]- {rec}[/yellow]")
