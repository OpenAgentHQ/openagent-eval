"""CLI context for global state management."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CLIContext:
    """Global CLI context passed to all commands.

    Attributes:
        quiet: Suppress non-essential output.
        json_output: Output machine-readable JSON.
        no_color: Disable color output.
        verbose: Enable verbose output.
    """

    quiet: bool = False
    json_output: bool = False
    no_color: bool = False
    verbose: bool = False


# Module-level singleton for global CLI state
_current_context: CLIContext | None = None


def get_context() -> CLIContext:
    """Get the current CLI context.

    Returns:
        The current CLI context, or a default context if not initialized.
    """
    global _current_context
    if _current_context is None:
        _current_context = CLIContext()
    return _current_context


def set_context(context: CLIContext) -> None:
    """Set the current CLI context.

    Args:
        context: The CLI context to set.
    """
    global _current_context
    _current_context = context


def reset_context() -> None:
    """Reset the CLI context to defaults."""
    global _current_context
    _current_context = CLIContext()
