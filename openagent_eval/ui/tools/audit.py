"""Audit result panel renderer."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Label, Rule, Static


class AuditResultPanel(Widget):
    """Panel for displaying corpus audit results.

    Renders issue lists with severity indicators and health scores.
    """

    DEFAULT_CSS = """
    AuditResultPanel {
        height: auto;
        min-height: 10;
        padding: 1;
        border: solid $secondary;
        background: $surface;
    }

    AuditResultPanel .panel-header {
        height: 1;
        text-style: bold;
        padding-bottom: 1;
    }

    AuditResultPanel DataTable {
        height: auto;
        max-height: 12;
    }
    """

    def __init__(self, title: str = "Audit Results", **kwargs):
        """Initialize the audit result panel.

        Args:
            title: Panel title.
        """
        super().__init__(**kwargs)
        self._title = title
        self._issues: list[dict] = []

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        yield Static(f"[bold magenta]{self._title}[/bold magenta]", classes="panel-header")
        yield Rule()

        if self._issues:
            table = DataTable()
            table.add_columns("Type", "Count", "Severity", "Status")
            table.cursor_type = "row"

            for issue in self._issues:
                severity_color = self._get_severity_color(issue.get("severity", "low"))
                status = issue.get("status", "unknown")
                status_color = "green" if status == "ok" else "yellow" if status == "warning" else "red"

                table.add_row(
                    issue.get("type", "unknown"),
                    str(issue.get("count", 0)),
                    f"[{severity_color}]{issue.get('severity', 'low')}[/{severity_color}]",
                    f"[{status_color}]{status}[/{status_color}]"
                )

            yield table
        else:
            yield Label("  [dim]> No issues found[/dim]")

    def update_issues(self, issues: list[dict]) -> None:
        """Update the issues display.

        Args:
            issues: List of issue dictionaries.
        """
        self._issues = issues
        self.refresh()

    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level.

        Args:
            severity: Severity level string.

        Returns:
            Color string.
        """
        colors = {
            "critical": "bold red",
            "high": "red",
            "medium": "yellow",
            "low": "green",
        }
        return colors.get(severity.lower(), "white")
