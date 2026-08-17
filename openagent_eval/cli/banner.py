"""ASCII art banner for OpenAgent Eval CLI."""

from __future__ import annotations

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _generate_ascii_art(text: str = "oaeval") -> str:
    """Generate ASCII art for OAEVAL banner.

    Returns:
        ASCII art string.
    """
    return (
        "██████╗  █████╗ ███████╗██╗   ██╗ █████╗ ██╗\n"
        "██╔═══██╗██╔══██╗██╔════╝██║   ██║██╔══██╗██║\n"
        "██║   ██║███████║█████╗  ██║   ██║███████║██║\n"
        "██║   ██║██╔══██║██╔══╝  ╚██╗ ██╔╝██╔══██║██║\n"
        "╚██████╔╝██║  ██║███████╗ ╚████╔╝ ██║  ██║███████╗\n"
        " ╚═════╝ ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝"
    )


def create_banner(console: Console | None = None, show_version: bool = False) -> None:
    """Display the OpenAgent Eval ASCII art banner.

    Args:
        console: Rich Console instance. Creates one if not provided.
        show_version: Whether to show the version number.
    """
    if console is None:
        console = Console()

    ascii_art = _generate_ascii_art()

    # Create styled ASCII art
    lines = ascii_art.split("\n")
    styled_art = Text()

    for line in lines:
        if line.strip():
            styled_art.append(f"{line}\n", style="bold")
        else:
            styled_art.append("\n")

    # Add tagline
    styled_art.append("\n", style="default")
    styled_art.append(
        "      OpenAgent Eval • Production-Ready RAG Evaluation", style="italic"
    )

    # Create a panel
    panel = Panel(
        Align.center(styled_art),
        border_style="bold",
        padding=(1, 2),
        expand=False,
        title="[bold]oaeval[/bold]",
        subtitle="[dim]Press F1 for help[/dim]",
    )

    console.print()
    console.print(panel)
    console.print()


def create_mini_banner(console: Console | None = None) -> None:
    """Display a compact single-line banner with styling.

    Args:
        console: Rich Console instance. Creates one if not provided.
    """
    if console is None:
        console = Console()

    # Create a styled mini banner
    banner = Table(show_header=False, show_edge=False, box=None, padding=(0, 1))
    banner.add_column("name", style="bold")
    banner.add_column("tagline", style="italic")

    banner.add_row("OAEVAL", "Production-Ready RAG Evaluation")

    console.print(banner)
    console.print()


def create_rich_banner(console: Console | None = None) -> None:
    """Display a rich banner with feature highlights.

    Args:
        console: Rich Console instance. Creates one if not provided.
    """
    if console is None:
        console = Console()

    # Create the main banner text
    banner_text = Text()
    banner_text.append("  OAEVAL  ", style="bold")
    banner_text.append("  •  ", style="dim")
    banner_text.append("Production-Ready RAG Evaluation", style="italic")

    # Create feature highlights as text
    features_text = Text()
    features_text.append("  Features:\n", style="bold")
    features_text.append("  > Corpus Health Auditor\n", style="dim")
    features_text.append("  > NLI-based Faithfulness Scoring\n", style="dim")
    features_text.append("  > Component Blame Attribution\n", style="dim")
    features_text.append("  > Synthetic Test Data Generation", style="dim")

    # Combine into panel
    content = Text()
    content.append_text(banner_text)
    content.append("\n\n")
    content.append_text(features_text)

    panel = Panel(
        content,
        border_style="bold",
        padding=(1, 2),
        expand=False,
        title="[bold]OpenAgent Eval[/bold]",
        subtitle="[dim]Production-Ready RAG Evaluation[/dim]",
    )

    console.print()
    console.print(panel)
    console.print()
