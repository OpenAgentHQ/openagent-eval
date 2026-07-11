"""Status footer widget with session information."""

from __future__ import annotations

from importlib.metadata import version

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


def _get_version() -> str:
    """Get the package version.

    Returns:
        Version string.
    """
    try:
        return version("openagent-eval")
    except Exception:
        return "0.3.0"


class StatusFooter(Widget):
    """Status footer displaying session information.

    Shows model, cost, elapsed time, token count, and progress.
    Claude Code-style status bar at the bottom of the screen.
    """

    DEFAULT_CSS = """
    StatusFooter {
        height: 1;
        dock: bottom;
        padding: 0 1;
        background: $surface;
        layer: footer;
    }

    StatusFooter Label {
        width: 100%;
    }
    """

    model_name: reactive[str] = reactive("gpt-4")
    cost: reactive[float] = reactive(0.0)
    elapsed: reactive[float] = reactive(0.0)
    token_count: reactive[int] = reactive(0)
    progress: reactive[int] = reactive(0)

    def compose(self):
        """Compose the footer widget."""
        yield Label(self._build_status_text())

    def update_model(self, model: str) -> None:
        """Update the model name.

        Args:
            model: Model identifier.
        """
        self.model_name = model
        self._refresh_label()

    def update_cost(self, cost: float) -> None:
        """Update the cost.

        Args:
            cost: Cost in dollars.
        """
        self.cost = cost
        self._refresh_label()

    def update_elapsed(self, elapsed: float) -> None:
        """Update elapsed time.

        Args:
            elapsed: Elapsed time in seconds.
        """
        self.elapsed = elapsed
        self._refresh_label()

    def update_tokens(self, count: int) -> None:
        """Update token count.

        Args:
            count: Total tokens used.
        """
        self.token_count = count
        self._refresh_label()

    def update_progress(self, percent: int) -> None:
        """Update progress percentage.

        Args:
            percent: Progress 0-100.
        """
        self.progress = max(0, min(100, percent))
        self._refresh_label()

    def _build_status_text(self) -> str:
        """Build the status text string.

        Returns:
            Rich-formatted status string.
        """
        version = _get_version()
        model = self.model_name
        cost = f"${self.cost:.2f}" if self.cost > 0 else "$0.00"
        elapsed = self._format_elapsed()
        tokens = self._format_tokens()
        progress = f"{self.progress}%" if self.progress > 0 else ""

        parts = [
            f"[dim]v{version}[/dim]",
            f"[blue]>[/blue] [bold]{model}[/bold]",
            f"[dim]cost:[/dim] {cost}",
            f"[dim]time:[/dim] {elapsed}",
        ]

        if self.token_count > 0:
            parts.append(f"[dim]tokens:[/dim] {tokens}")

        if progress:
            parts.append(f"[dim]progress:[/dim] {progress}")

        return " │ ".join(parts)

    def _format_elapsed(self) -> str:
        """Format elapsed time.

        Returns:
            Formatted time string.
        """
        if self.elapsed < 60:
            return f"{self.elapsed:.1f}s"
        minutes = int(self.elapsed // 60)
        seconds = self.elapsed % 60
        return f"{minutes}m {seconds:.1f}s"

    def _format_tokens(self) -> str:
        """Format token count.

        Returns:
            Formatted token string.
        """
        if self.token_count < 1000:
            return str(self.token_count)
        elif self.token_count < 1_000_000:
            return f"{self.token_count / 1000:.1f}K"
        return f"{self.token_count / 1_000_000:.1f}M"

    def _refresh_label(self) -> None:
        """Refresh the label display."""
        try:
            label = self.query_one(Label)
            label.update(self._build_status_text())
        except Exception:
            pass
