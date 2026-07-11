"""Diagnose result panel renderer."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Label, Rule, Static


class DiagnoseResultPanel(Widget):
    """Panel for displaying component diagnosis results.

    Renders blame attribution with confidence bars and recommendations.
    """

    DEFAULT_CSS = """
    DiagnoseResultPanel {
        height: auto;
        min-height: 10;
        padding: 1;
        border: solid $accent;
        background: $surface;
    }

    DiagnoseResultPanel .panel-header {
        height: 1;
        text-style: bold;
        padding-bottom: 1;
    }

    DiagnoseResultPanel DataTable {
        height: auto;
        max-height: 12;
    }
    """

    def __init__(self, title: str = "Blame Attribution", **kwargs):
        """Initialize the diagnose result panel.

        Args:
            title: Panel title.
        """
        super().__init__(**kwargs)
        self._title = title
        self._components: list[dict] = []

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        yield Static(f"[bold yellow]{self._title}[/bold yellow]", classes="panel-header")
        yield Rule()

        if self._components:
            table = DataTable()
            table.add_columns("Component", "Blame %", "Confidence", "Recommendation")
            table.cursor_type = "row"

            for comp in self._components:
                blame = comp.get("blame", 0)
                blame_color = self._get_blame_color(blame)
                confidence = comp.get("confidence", 0.0)
                confidence_color = "green" if confidence >= 0.7 else "yellow" if confidence >= 0.4 else "red"

                table.add_row(
                    comp.get("component", "unknown"),
                    f"[{blame_color}]{blame:.0%}[/{blame_color}]",
                    f"[{confidence_color}]{confidence:.1%}[/{confidence_color}]",
                    comp.get("recommendation", "-")
                )

            yield table
        else:
            yield Label("  [dim]> No components diagnosed[/dim]")
            yield Label("  [dim]  Run diagnosis to see results[/dim]")

    def update_components(self, components: list[dict]) -> None:
        """Update the components display.

        Args:
            components: List of component dictionaries.
        """
        self._components = components
        self.refresh()

    def _get_blame_color(self, blame: float) -> str:
        """Get color for blame percentage.

        Args:
            blame: Blame percentage (0.0 to 1.0).

        Returns:
            Color string.
        """
        if blame >= 0.5:
            return "bold red"
        elif blame >= 0.3:
            return "red"
        elif blame >= 0.1:
            return "yellow"
        return "green"
