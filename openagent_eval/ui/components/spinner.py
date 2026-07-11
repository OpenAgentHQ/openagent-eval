"""Animated spinner widget with elapsed time and rotating tips."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

if TYPE_CHECKING:
    from textual.app import ComposeResult

# Educational tips (Claude Code style)
ROTATING_TIPS: list[str] = [
    "Tip: Use 'oaeval run --dry-run' to preview evaluations",
    "Tip: Press 'd' to toggle dark mode",
    "Tip: Use Ctrl+C to cancel running evaluations",
    "Tip: Check 'oaeval doctor' for system diagnostics",
    "Tip: Use --config to specify custom configuration",
    "Tip: Press 'h' for help in any screen",
    "Tip: Results are saved in reports/ directory",
    "Tip: Use 'oaeval compare' to compare evaluation runs",
]

# Spinner animation frames
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class SpinnerWidget(Widget):
    """Animated spinner with elapsed time and rotating tips.

    Displays a spinner animation, current operation, elapsed time,
    token count, and rotating educational tips.
    """

    DEFAULT_CSS = """
    SpinnerWidget {
        height: 5;
        padding: 0 1;
        background: $surface;
    }

    SpinnerWidget .spinner-line {
        height: 1;
    }

    SpinnerWidget .tip-line {
        height: 1;
        padding: 0 2;
    }
    """

    _spinner_index: int = 0
    _tip_index: int = 0
    _start_time: float | None = None
    _elapsed: float = 0.0

    operation_text: reactive[str] = reactive("Processing...")
    is_active: reactive[bool] = reactive(False)
    token_count: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        """Compose the spinner widget."""
        yield Label("", classes="spinner-line")
        yield Label("", classes="spinner-line")
        yield Label(self._get_tip(), classes="tip-line")

    def start(self, operation: str = "Processing...") -> None:
        """Start the spinner animation.

        Args:
            operation: Description of the current operation.
        """
        self.operation_text = operation
        self.is_active = True
        self._start_time = time.time()
        self._spinner_index = 0
        self._update_display()

    def stop(self) -> None:
        """Stop the spinner animation."""
        self.is_active = False
        if self._start_time is not None:
            self._elapsed = time.time() - self._start_time
        self._start_time = None
        self._update_display()

    def increment_tokens(self, count: int = 1) -> None:
        """Increment token count.

        Args:
            count: Number of tokens to add.
        """
        self.token_count += count
        self._update_display()

    def advance_frame(self) -> None:
        """Advance spinner animation frame."""
        if not self.is_active:
            return
        self._spinner_index = (self._spinner_index + 1) % len(SPINNER_FRAMES)
        self._update_display()

    def next_tip(self) -> None:
        """Show the next rotating tip."""
        self._tip_index = (self._tip_index + 1) % len(ROTATING_TIPS)
        self._update_tip()

    def _get_elapsed(self) -> str:
        """Get formatted elapsed time string.

        Returns:
            Formatted time string (e.g., "1.2s", "1m 2.3s").
        """
        if self._start_time is None:
            elapsed = self._elapsed
        else:
            elapsed = time.time() - self._start_time

        if elapsed < 60:
            return f"{elapsed:.1f}s"
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        return f"{minutes}m {seconds:.1f}s"

    def _get_tip(self) -> str:
        """Get current tip text.

        Returns:
            Rich-formatted tip string.
        """
        tip = ROTATING_TIPS[self._tip_index % len(ROTATING_TIPS)]
        return f"[dim]{tip}[/dim]"

    def _update_display(self) -> None:
        """Update the display with current state."""
        try:
            spinner_line = self.query_one(".spinner-line", Label)
            if self.is_active:
                spinner = SPINNER_FRAMES[self._spinner_index % len(SPINNER_FRAMES)]
                elapsed = self._get_elapsed()
                spinner_line.update(
                    f"[bold blue]{spinner}[/bold blue] "
                    f"[white]{self.operation_text}[/white] "
                    f"[dim]({elapsed})[/dim]"
                )
            else:
                if self._elapsed > 0:
                    spinner_line.update(
                        f"[green]✓[/green] "
                        f"[white]Completed in {self._elapsed:.1f}s[/white]"
                    )
                else:
                    spinner_line.update("[dim]Ready[/dim]")
        except Exception:
            pass

    def _update_tip(self) -> None:
        """Update the tip display."""
        try:
            tip_line = self.query_one(".tip-line", Label)
            tip_line.update(self._get_tip())
        except Exception:
            pass
