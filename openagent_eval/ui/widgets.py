"""Custom Textual widgets for OpenAgent Eval dashboard."""

from __future__ import annotations

from importlib.metadata import version

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Label, ProgressBar, Rule, Static


def _get_version() -> str:
    """Get the package version."""
    try:
        return version("openagent-eval")
    except Exception:
        return "0.3.0"


class BannerWidget(Widget):
    """ASCII art banner widget for the dashboard with gradient styling."""

    DEFAULT_CSS = """
    BannerWidget {
        height: 9;
        content-align: center middle;
        padding: 0 1;
        background: $surface;
    }

    BannerWidget Static {
        width: 100%;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        ver = _get_version()
        yield Static(
            f"[bold cyan]    ___   ___    [/bold cyan]\n"
            f"[bold cyan]   / __| / _ \\   [/bold cyan]\n"
            f"[bold bright_cyan]  | (__ | (_) |  [/bold bright_cyan]\n"
            f"[bold bright_blue]   \\___| \\___/   [/bold bright_blue]  [dim]v{ver}[/dim]\n"
            f"\n"
            f"[italic bright_blue]   RAG Evaluation Framework[/italic bright_blue]\n"
            f"[dim]   Open-source CLI for evaluating RAG systems[/dim]"
        )


class StatusWidget(Widget):
    """Display current status information with icon."""

    DEFAULT_CSS = """
    StatusWidget {
        height: 3;
        padding: 0 1;
        background: $surface;
    }

    StatusWidget Label {
        width: 100%;
    }
    """

    status_text = reactive("Ready")
    status_icon = reactive("[green]>[/green]")

    def compose(self) -> ComposeResult:
        yield Label(f"{self.status_icon} [bold]Status:[/bold] {self.status_text}")

    def set_status(self, status: str, icon: str = "[green]>[/green]") -> None:
        """Update the status text."""
        self.status_text = status
        self.status_icon = icon

    def set_running(self, status: str) -> None:
        """Set status to running state."""
        self.set_status(status, "[yellow]>[/yellow]")

    def set_complete(self, status: str) -> None:
        """Set status to completed state."""
        self.set_status(status, "[green]>[/green]")

    def set_error(self, status: str) -> None:
        """Set status to error state."""
        self.set_status(status, "[red]>[/red]")


class MetricsSummaryWidget(Widget):
    """Display a summary of evaluation metrics with color-coded scores."""

    DEFAULT_CSS = """
    MetricsSummaryWidget {
        height: 10;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }

    MetricsSummaryWidget .title {
        text-align: center;
        padding-bottom: 1;
        text-style: bold;
    }

    MetricsSummaryWidget .metric-row {
        height: 1;
    }
    """

    def __init__(self, title: str = "Metrics Summary", metrics: dict[str, float] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self.metrics = metrics or {}

    def compose(self) -> ComposeResult:
        yield Static(f"[bold bright_blue]{self._title}[/bold bright_blue]", classes="title")
        yield Rule()
        if self.metrics:
            for name, score in self.metrics.items():
                # Color based on score quality
                if score >= 0.9:
                    color = "bold green"
                    indicator = ">"
                elif score >= 0.7:
                    color = "bright_green"
                    indicator = ">"
                elif score >= 0.5:
                    color = "yellow"
                    indicator = ">"
                elif score >= 0.3:
                    color = "bright_red"
                    indicator = ">"
                else:
                    color = "red"
                    indicator = ">"

                # Format the metric name
                display_name = name.replace("_", " ").title()
                yield Label(
                    f"  [dim]{indicator}[/dim] [{color}]{display_name}:[/{color}] [{color}]{score:.1%}[/{color}]",
                    classes="metric-row"
                )
        else:
            yield Label("  [dim]> No data loaded[/dim]", classes="metric-row")
            yield Label("  [dim]  Run an evaluation to see results[/dim]", classes="metric-row")


class ResultsTableWidget(Widget):
    """Display results in a sortable table with styling."""

    DEFAULT_CSS = """
    ResultsTableWidget {
        height: 14;
        padding: 1;
        border: solid $secondary;
        background: $surface;
    }

    ResultsTableWidget DataTable {
        height: 100%;
    }
    """

    def __init__(self, title: str = "Results", columns: list[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self.columns = columns or ["Metric", "Score", "Status"]

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*self.columns)
        table.cursor_type = "row"
        table.cursor_foreground = "bold bright_blue"

    def add_row(self, *values: str | float) -> None:
        """Add a row to the table."""
        table = self.query_one(DataTable)
        table.add_row(*values)

    def clear_rows(self) -> None:
        """Clear all rows from the table."""
        table = self.query_one(DataTable)
        table.clear()


class ProgressWidget(Widget):
    """Display a progress bar with label and percentage."""

    DEFAULT_CSS = """
    ProgressWidget {
        height: 4;
        padding: 0 1;
        background: $surface;
    }

    ProgressWidget Label {
        height: 1;
    }

    ProgressWidget ProgressBar {
        height: 2;
        margin: 0 1;
    }
    """

    def __init__(self, label: str = "Progress", total: int = 100, **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._total = total

    def compose(self) -> ComposeResult:
        yield Label(f"[bold bright_blue]{self._label}[/bold bright_blue]")
        yield ProgressBar(total=self._total)

    def update_progress(self, current: int) -> None:
        """Update the progress bar."""
        progress = self.query_one(ProgressBar)
        progress.progress = current


class InfoPanel(Widget):
    """Display information in a styled panel."""

    DEFAULT_CSS = """
    InfoPanel {
        height: auto;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }

    InfoPanel .panel-title {
        text-style: bold;
        padding-bottom: 1;
    }

    InfoPanel .panel-row {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(self, title: str = "Info", rows: list[tuple[str, str]] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._rows = rows or []

    def compose(self) -> ComposeResult:
        yield Static(f"[bold bright_blue]{self._title}[/bold bright_blue]", classes="panel-title")
        yield Rule()
        for label, value in self._rows:
            yield Label(f"  [dim]{label}:[/dim] [bright_white]{value}[/bright_white]", classes="panel-row")

    def update_row(self, index: int, label: str, value: str) -> None:
        """Update a specific row."""
        if 0 <= index < len(self._rows):
            self._rows[index] = (label, value)
            self.refresh()


class QuickActions(Widget):
    """Display quick action buttons."""

    DEFAULT_CSS = """
    QuickActions {
        height: 5;
        padding: 1;
        border: solid $accent;
        background: $surface;
    }

    QuickActions .actions-title {
        text-style: bold;
        padding-bottom: 1;
    }

    QuickActions .action-row {
        height: 1;
    }
    """

    def __init__(self, actions: list[tuple[str, str, str]] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._actions = actions or [
            ("1", "Run Evaluation", "bright_blue"),
            ("2", "Audit Corpus", "bright_cyan"),
            ("3", "Diagnose", "bright_green"),
            ("h", "Help", "dim"),
        ]

    def compose(self) -> ComposeResult:
        yield Static("[bold bright_blue]Quick Actions[/bold bright_blue]", classes="actions-title")
        yield Rule()
        for key, action, color in self._actions:
            # Build the markup string to avoid f-string issues with Rich tags
            key_markup = f"[bold {color}][{key}][/bold {color}]"
            yield Label(
                f"  {key_markup} {action}",
                classes="action-row"
            )
