"""Main Textual App for OpenAgent Eval TUI dashboard."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from openagent_eval.ui.components.command_input import Command, RichCommandInput
from openagent_eval.ui.components.footer import StatusFooter
from openagent_eval.ui.components.message_list import Message, MessageList, MessageRole
from openagent_eval.ui.components.spinner import SpinnerWidget
from openagent_eval.ui.screens import (
    AuditScreen,
    DiagnoseScreen,
    EvaluateScreen,
    HelpScreen,
    MainDashboard,
)
from openagent_eval.ui.streaming import StreamingManager, StreamingState
from openagent_eval.ui.theme import ThemeName, get_theme


class ChatScreen(Screen):
    """Claude Code-style chat screen with message list and command input.

    This is the main interaction screen, similar to Claude Code's interface.
    """

    DEFAULT_CSS = """
    ChatScreen {
        layout: vertical;
    }

    ChatScreen #header {
        height: auto;
        dock: top;
    }

    ChatScreen #messages-container {
        height: 1fr;
    }

    ChatScreen #footer {
        height: 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
        Binding("ctrl+l", "clear_messages", "Clear", show=True),
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(self, config_path: str | None = None):
        super().__init__()
        self.config_path = config_path
        self._streaming = StreamingManager()

    def compose(self) -> ComposeResult:
        """Compose the chat screen."""
        # Header
        yield Header(id="header")

        # Messages container
        with Vertical(id="messages-container"):
            yield MessageList(id="messages")

        # Footer with status
        yield StatusFooter(id="footer")

    def on_mount(self) -> None:
        """Initialize the chat screen on mount."""
        # Add welcome message
        messages = self.query_one("#messages", MessageList)
        messages.add_message(Message(
            role=MessageRole.SYSTEM,
            content="Welcome to OpenAgent Eval! Type a command to get started."
        ))

        # Add example commands
        messages.add_message(Message(
            role=MessageRole.SYSTEM,
            content="Available commands: eval, audit, diagnose, help, clear, quit"
        ))

        # Focus on the message list
        self.query_one("#messages").focus()

    def add_message(self, role: MessageRole, content: str, **kwargs) -> None:
        """Add a message to the chat.

        Args:
            role: Message role
            content: Message content
            **kwargs: Additional message attributes
        """
        messages = self.query_one("#messages", MessageList)
        messages.add_message(Message(role=role, content=content, **kwargs))

    def action_command_palette(self) -> None:
        """Show command palette (placeholder for now)."""
        self.add_message(MessageRole.SYSTEM, "Command palette coming soon!")

    def action_clear_messages(self) -> None:
        """Clear all messages."""
        messages = self.query_one("#messages", MessageList)
        messages.clear()
        self.add_message(MessageRole.SYSTEM, "Messages cleared.")

    def action_go_back(self) -> None:
        """Go back to main dashboard."""
        self.app.pop_screen()


class OAEvalDashboard(App):
    """Interactive evaluation dashboard for OpenAgent Eval.

    Launch with `oaeval ui` to explore evaluations, audit corpora,
    and diagnose component failures interactively.
    """

    TITLE = "OpenAgent Eval"
    SUB_TITLE = "RAG Evaluation Framework"

    CSS_PATH = str(Path(__file__).parent / "styles.tcss")

    # Use our custom theme
    THEME = "dark"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("f1", "show_help", "Help", show=True),
        Binding("1", "show_dashboard", "Dashboard", show=True),
        Binding("2", "show_evaluate", "Evaluate", show=True),
        Binding("3", "show_audit", "Audit", show=True),
        Binding("4", "show_diagnose", "Diagnose", show=True),
        Binding("5", "show_chat", "Chat", show=True),
        Binding("d", "toggle_dark", "Toggle Dark Mode", show=True),
    ]

    def __init__(self, config_path: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        self._streaming = StreamingManager()

    def compose(self) -> ComposeResult:
        """Compose the app's widget tree."""
        yield MainDashboard()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Show main dashboard
        self.push_screen(MainDashboard())

    def action_show_help(self) -> None:
        """Show help screen."""
        self.push_screen(HelpScreen())

    def action_show_dashboard(self) -> None:
        """Show main dashboard."""
        self.push_screen(MainDashboard())

    def action_show_evaluate(self) -> None:
        """Show evaluate screen."""
        self.push_screen(EvaluateScreen())

    def action_show_audit(self) -> None:
        """Show audit screen."""
        self.push_screen(AuditScreen())

    def action_show_diagnose(self) -> None:
        """Show diagnose screen."""
        self.push_screen(DiagnoseScreen())

    def action_show_chat(self) -> None:
        """Show chat screen."""
        self.push_screen(ChatScreen(config_path=self.config_path))

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark


def run_ui(config_path: str | None = None) -> None:
    """Launch the TUI dashboard.

    Args:
        config_path: Optional path to configuration file.
    """
    # Check if textual is installed
    try:
        import textual  # noqa: F401
    except ImportError:
        from rich.console import Console

        console = Console(stderr=True)
        console.print(
            "[red]Error:[/red] Textual is required for the TUI dashboard.\n"
            "Install it with: [bold]pip install openagent-eval[ui][/bold]"
        )
        raise SystemExit(1)

    app = OAEvalDashboard(config_path=config_path)
    app.run()
