"""Dashboard screens for OpenAgent Eval TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Rule, Static

from openagent_eval.ui.widgets import (
    BannerWidget,
    InfoPanel,
    MetricsSummaryWidget,
    ProgressWidget,
    QuickActions,
    ResultsTableWidget,
    StatusWidget,
)


class MainDashboard(Screen):
    """Main dashboard screen with overview."""

    DEFAULT_CSS = """
    MainDashboard {
        layout: vertical;
    }

    MainDashboard #top-section {
        height: auto;
        padding: 0 1;
    }

    MainDashboard #middle-section {
        height: 1fr;
        padding: 0 1;
    }

    MainDashboard #bottom-section {
        height: auto;
        padding: 0 1;
    }

    MainDashboard .grid {
        height: 1fr;
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1 2;
    }

    MainDashboard .metrics-grid {
        height: auto;
        layout: grid;
        grid-size: 2 1;
        grid-gutter: 1 2;
    }
    """

    BINDINGS = [
        ("1", "run_evaluation", "Run Eval"),
        ("2", "audit_corpus", "Audit"),
        ("3", "diagnose", "Diagnose"),
        ("q", "quit", "Quit"),
        ("h", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        # Top section: Banner + Status
        with Vertical(id="top-section"):
            yield BannerWidget()
            yield StatusWidget(id="status")
            yield Rule()

        # Middle section: Main content grid
        with Vertical(id="middle-section"):
            with Horizontal(classes="metrics-grid"):
                yield MetricsSummaryWidget(
                    title="Retrieval Metrics",
                    id="retrieval-metrics"
                )
                yield MetricsSummaryWidget(
                    title="Generation Metrics",
                    id="generation-metrics"
                )

            with Horizontal(classes="grid"):
                yield ResultsTableWidget(
                    title="Recent Commands",
                    columns=["Command", "Status", "Duration", "Last Run"],
                    id="recent-table"
                )
                yield QuickActions(id="quick-actions")

        # Bottom section: Progress
        with Vertical(id="bottom-section"):
            yield ProgressWidget(label="Overall Progress", id="progress")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the dashboard on mount."""
        status = self.query_one("#status", StatusWidget)
        status.set_complete("Dashboard loaded")

        # Populate recent commands table
        table_widget = self.query_one("#recent-table", ResultsTableWidget)
        table_widget.add_row("run", "[green]Idle[/green]", "-", "-")
        table_widget.add_row("audit", "[green]Idle[/green]", "-", "-")
        table_widget.add_row("diagnose", "[green]Idle[/green]", "-", "-")

    def action_run_evaluation(self) -> None:
        """Switch to evaluation screen."""
        self.app.push_screen(EvaluateScreen())

    def action_audit_corpus(self) -> None:
        """Switch to audit screen."""
        self.app.push_screen(AuditScreen())

    def action_diagnose(self) -> None:
        """Switch to diagnose screen."""
        self.app.push_screen(DiagnoseScreen())

    def action_help(self) -> None:
        """Show help screen."""
        self.app.push_screen(HelpScreen())


class EvaluateScreen(Screen):
    """Evaluation screen for running RAG evaluations."""

    DEFAULT_CSS = """
    EvaluateScreen {
        layout: vertical;
        padding: 1;
    }

    EvaluateScreen #screen-header {
        height: auto;
        padding: 0 1;
    }

    EvaluateScreen #config-section {
        height: 8;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }

    EvaluateScreen #results-section {
        height: 1fr;
        padding: 1;
        border: solid $secondary;
        background: $surface;
    }

    EvaluateScreen #progress-section {
        height: auto;
        padding: 1;
    }

    EvaluateScreen .config-grid {
        height: auto;
        layout: grid;
        grid-size: 3 1;
        grid-gutter: 1 2;
    }

    EvaluateScreen .config-item {
        height: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("r", "run_eval", "Run"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        # Screen header
        with Vertical(id="screen-header"):
            yield Static("[bold bright_blue]Evaluation Runner[/bold bright_blue]")
            yield Rule()

        # Configuration panel
        with Vertical(id="config-section"):
            yield Static("[bold bright_blue]Configuration[/bold bright_blue]")
            yield Rule()
            with Horizontal(classes="config-grid"):
                yield Label("[dim]Config:[/dim] [bright_white]config.yaml[/bright_white]", classes="config-item")
                yield Label("[dim]Metrics:[/dim] [bright_white]faithfulness, relevancy[/bright_white]", classes="config-item")
                yield Label("[dim]Provider:[/dim] [bright_white]openai[/bright_white]", classes="config-item")

        # Results section
        with Vertical(id="results-section"):
            yield ResultsTableWidget(
                title="Evaluation Results",
                columns=["Metric", "Score", "Status", "Details"],
                id="eval-results"
            )

        # Progress section
        with Vertical(id="progress-section"):
            yield ProgressWidget(label="Evaluation Progress", total=100, id="eval-progress")

        yield Footer()

    def action_go_back(self) -> None:
        """Go back to main dashboard."""
        self.app.pop_screen()

    def action_run_eval(self) -> None:
        """Trigger evaluation run."""
        progress = self.query_one("#eval-progress", ProgressWidget)
        progress.update_progress(50)


class AuditScreen(Screen):
    """Corpus audit screen."""

    DEFAULT_CSS = """
    AuditScreen {
        layout: vertical;
        padding: 1;
    }

    AuditScreen #screen-header {
        height: auto;
        padding: 0 1;
    }

    AuditScreen #audit-config {
        height: 8;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }

    AuditScreen #audit-results {
        height: 1fr;
        padding: 1;
        border: solid $secondary;
        background: $surface;
    }

    AuditScreen #audit-summary {
        height: auto;
        padding: 1;
    }

    AuditScreen .config-grid {
        height: auto;
        layout: grid;
        grid-size: 2 1;
        grid-gutter: 1 2;
    }

    AuditScreen .config-item {
        height: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("r", "run_audit", "Run Audit"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        # Screen header
        with Vertical(id="screen-header"):
            yield Static("[bold bright_blue]Corpus Health Audit[/bold bright_blue]")
            yield Rule()

        # Configuration panel
        with Vertical(id="audit-config"):
            yield Static("[bold bright_blue]Audit Configuration[/bold bright_blue]")
            yield Rule()
            with Horizontal(classes="config-grid"):
                yield Label("[dim]Corpus:[/dim] [bright_white]./knowledge_base/[/bright_white]", classes="config-item")
                yield Label("[dim]Checks:[/dim] [bright_white]contradiction, staleness, duplicate, coverage[/bright_white]", classes="config-item")

        # Results section
        with Vertical(id="audit-results"):
            yield ResultsTableWidget(
                title="Audit Results",
                columns=["Issue Type", "Count", "Severity", "Status"],
                id="audit-table"
            )

        # Summary section
        with Vertical(id="audit-summary"):
            yield MetricsSummaryWidget(
                title="Health Score",
                id="health-score"
            )

        yield Footer()

    def action_go_back(self) -> None:
        """Go back to main dashboard."""
        self.app.pop_screen()

    def action_run_audit(self) -> None:
        """Trigger corpus audit."""
        table = self.query_one("#audit-table", ResultsTableWidget)
        table.clear_rows()
        table.add_row("contradiction", "0", "[green]None[/green]", "[green]OK[/green]")
        table.add_row("staleness", "0", "[green]None[/green]", "[green]OK[/green]")
        table.add_row("duplicate", "0", "[green]None[/green]", "[green]OK[/green]")
        table.add_row("coverage_gap", "0", "[green]None[/green]", "[green]OK[/green]")


class DiagnoseScreen(Screen):
    """Component diagnosis screen."""

    DEFAULT_CSS = """
    DiagnoseScreen {
        layout: vertical;
        padding: 1;
    }

    DiagnoseScreen #screen-header {
        height: auto;
        padding: 0 1;
    }

    DiagnoseScreen #diag-config {
        height: 8;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }

    DiagnoseScreen #diag-results {
        height: 1fr;
        padding: 1;
        border: solid $secondary;
        background: $surface;
    }

    DiagnoseScreen #diag-summary {
        height: auto;
        padding: 1;
    }

    DiagnoseScreen .config-grid {
        height: auto;
        layout: grid;
        grid-size: 3 1;
        grid-gutter: 1 2;
    }

    DiagnoseScreen .config-item {
        height: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("r", "run_diagnose", "Run Diagnosis"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        # Screen header
        with Vertical(id="screen-header"):
            yield Static("[bold bright_blue]Component Diagnosis[/bold bright_blue]")
            yield Rule()

        # Configuration panel
        with Vertical(id="diag-config"):
            yield Static("[bold bright_blue]Diagnosis Configuration[/bold bright_blue]")
            yield Rule()
            with Horizontal(classes="config-grid"):
                yield Label("[dim]Report:[/dim] [bright_white]reports/latest.json[/bright_white]", classes="config-item")
                yield Label("[dim]Threshold:[/dim] [bright_white]0.5[/bright_white]", classes="config-item")
                yield Label("[dim]Mode:[/dim] [bright_white]blame_attribution[/bright_white]", classes="config-item")

        # Results section
        with Vertical(id="diag-results"):
            yield ResultsTableWidget(
                title="Blame Attribution",
                columns=["Component", "Blame %", "Confidence", "Recommendation"],
                id="blame-table"
            )

        # Summary section
        with Vertical(id="diag-summary"):
            yield ProgressWidget(label="Diagnosis Progress", id="diag-progress")

        yield Footer()

    def action_go_back(self) -> None:
        """Go back to main dashboard."""
        self.app.pop_screen()

    def action_run_diagnose(self) -> None:
        """Trigger diagnosis."""
        table = self.query_one("#blame-table", ResultsTableWidget)
        table.clear_rows()
        table.add_row("retrieval", "0%", "[dim]-[/dim]", "[dim]-[/dim]")
        table.add_row("generation", "0%", "[dim]-[/dim]", "[dim]-[/dim]")
        table.add_row("chunking", "0%", "[dim]-[/dim]", "[dim]-[/dim]")


class HelpScreen(Screen):
    """Help screen with keyboard shortcuts."""

    DEFAULT_CSS = """
    HelpScreen {
        layout: vertical;
        padding: 2;
        align: center middle;
    }

    HelpScreen #help-content {
        width: 60;
        height: auto;
        padding: 2;
        border: solid $primary;
        background: $surface;
    }

    HelpScreen .section-title {
        text-style: bold;
        padding-bottom: 1;
    }

    HelpScreen .shortcut-row {
        height: 1;
        padding: 0 2;
    }

    HelpScreen .divider {
        height: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("q", "go_back", "Close"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="help-content"):
            yield Static("[bold bright_blue]OpenAgent Eval TUI - Keyboard Shortcuts[/bold bright_blue]", classes="section-title")
            yield Rule()

            yield Static("[bold bright_blue]Global[/bold bright_blue]", classes="section-title")
            yield Label("  [bold cyan]q[/bold cyan] / [bold cyan]ctrl+c[/bold cyan]    Quit the application", classes="shortcut-row")
            yield Label("  [bold cyan]escape[/bold cyan]         Go back / Close screen", classes="shortcut-row")
            yield Label("  [bold cyan]h[/bold cyan]              Show this help", classes="shortcut-row")
            yield Rule(classes="divider")

            yield Static("[bold bright_blue]Main Dashboard[/bold bright_blue]", classes="section-title")
            yield Label("  [bold cyan]1[/bold cyan]              Run Evaluation", classes="shortcut-row")
            yield Label("  [bold cyan]2[/bold cyan]              Audit Corpus", classes="shortcut-row")
            yield Label("  [bold cyan]3[/bold cyan]              Diagnose", classes="shortcut-row")
            yield Rule(classes="divider")

            yield Static("[bold bright_blue]Evaluate Screen[/bold bright_blue]", classes="section-title")
            yield Label("  [bold cyan]r[/bold cyan]              Run evaluation", classes="shortcut-row")
            yield Label("  [bold cyan]escape[/bold cyan]         Back to dashboard", classes="shortcut-row")
            yield Rule(classes="divider")

            yield Static("[bold bright_blue]Audit Screen[/bold bright_blue]", classes="section-title")
            yield Label("  [bold cyan]r[/bold cyan]              Run audit", classes="shortcut-row")
            yield Label("  [bold cyan]escape[/bold cyan]         Back to dashboard", classes="shortcut-row")
            yield Rule(classes="divider")

            yield Static("[bold bright_blue]Diagnose Screen[/bold bright_blue]", classes="section-title")
            yield Label("  [bold cyan]r[/bold cyan]              Run diagnosis", classes="shortcut-row")
            yield Label("  [bold cyan]escape[/bold cyan]         Back to dashboard", classes="shortcut-row")
            yield Rule(classes="divider")

            yield Label("[dim]Press escape or q to close this help[/dim]")

        yield Footer()

    def action_go_back(self) -> None:
        """Go back to main dashboard."""
        self.app.pop_screen()
