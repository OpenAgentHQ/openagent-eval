"""Evaluation result panel renderer."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Label, Rule, Static

from openagent_eval.ui.theme import format_metric_score, get_metric_color


class EvalResultPanel(Widget):
    """Panel for displaying evaluation results.

    Renders metrics with color-coded scores, progress indicators,
    and detailed result tables.
    """

    DEFAULT_CSS = """
    EvalResultPanel {
        height: auto;
        min-height: 10;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }

    EvalResultPanel .panel-header {
        height: 1;
        text-style: bold;
        padding-bottom: 1;
    }

    EvalResultPanel .metric-row {
        height: 1;
        padding: 0 2;
    }

    EvalResultPanel DataTable {
        height: auto;
        max-height: 12;
    }
    """

    def __init__(self, title: str = "Evaluation Results", **kwargs):
        """Initialize the eval result panel.

        Args:
            title: Panel title.
        """
        super().__init__(**kwargs)
        self._title = title
        self._metrics: dict[str, float] = {}

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        yield Static(f"[bold blue]{self._title}[/bold blue]", classes="panel-header")
        yield Rule()

        if self._metrics:
            for name, score in self._metrics.items():
                display_name = name.replace("_", " ").title()
                color = get_metric_color(score)
                yield Label(
                    f"  [dim]>[/dim] [{color}]{display_name}:[/{color}] "
                    f"[{color}]{score:.1%}[/{color}]",
                    classes="metric-row"
                )
        else:
            yield Label("  [dim]> No data loaded[/dim]", classes="metric-row")
            yield Label("  [dim]  Run an evaluation to see results[/dim]", classes="metric-row")

    def update_metrics(self, metrics: dict[str, float]) -> None:
        """Update the metrics display.

        Args:
            metrics: Dictionary of metric names to scores.
        """
        self._metrics = metrics
        self.refresh()
