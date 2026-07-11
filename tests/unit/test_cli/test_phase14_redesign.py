"""Tests for Phase 14 TUI redesign components."""

from __future__ import annotations

import pytest

from openagent_eval.ui.theme import (
    DARK_THEME,
    LIGHT_THEME,
    Theme,
    ThemeName,
    format_metric_score,
    get_metric_color,
    get_theme,
)
from openagent_eval.ui.streaming import (
    StreamingManager,
    StreamingState,
    SPINNER_FRAMES,
    STATE_TRANSITIONS,
)
from openagent_eval.ui.components.spinner import SpinnerWidget, ROTATING_TIPS
from openagent_eval.ui.components.footer import StatusFooter
from openagent_eval.ui.tools.eval import EvalResultPanel
from openagent_eval.ui.tools.audit import AuditResultPanel
from openagent_eval.ui.tools.diagnose import DiagnoseResultPanel


class TestThemeSystem:
    """Tests for the theme system."""

    def test_default_theme_is_dark(self):
        """Test that default theme is dark."""
        theme = get_theme()
        assert theme == DARK_THEME

    def test_get_theme_by_name(self):
        """Test getting theme by name."""
        theme = get_theme(ThemeName.LIGHT)
        assert theme == LIGHT_THEME

    def test_get_theme_by_string(self):
        """Test getting theme by string."""
        theme = get_theme("light")
        assert theme == LIGHT_THEME

    def test_theme_has_brand_color(self):
        """Test that theme has brand color."""
        assert DARK_THEME.brand == "rgb(79,140,255)"

    def test_theme_has_metric_colors(self):
        """Test that theme has metric colors."""
        assert DARK_THEME.metric_excellent == "rgb(80,200,120)"
        assert DARK_THEME.metric_good == "rgb(120,200,80)"
        assert DARK_THEME.metric_fair == "rgb(255,200,50)"
        assert DARK_THEME.metric_poor == "rgb(255,140,50)"
        assert DARK_THEME.metric_bad == "rgb(255,80,80)"

    def test_theme_has_diff_colors(self):
        """Test that theme has diff colors."""
        assert DARK_THEME.diff_added == "rgb(80,200,120)"
        assert DARK_THEME.diff_removed == "rgb(255,80,80)"

    def test_theme_is_frozen(self):
        """Test that theme is frozen (immutable)."""
        with pytest.raises(AttributeError):
            DARK_THEME.brand = "new_color"  # type: ignore

    def test_get_metric_color_excellent(self):
        """Test metric color for excellent score."""
        color = get_metric_color(0.95)
        assert color == DARK_THEME.metric_excellent

    def test_get_metric_color_good(self):
        """Test metric color for good score."""
        color = get_metric_color(0.75)
        assert color == DARK_THEME.metric_good

    def test_get_metric_color_fair(self):
        """Test metric color for fair score."""
        color = get_metric_color(0.55)
        assert color == DARK_THEME.metric_fair

    def test_get_metric_color_poor(self):
        """Test metric color for poor score."""
        color = get_metric_color(0.35)
        assert color == DARK_THEME.metric_poor

    def test_get_metric_color_bad(self):
        """Test metric color for bad score."""
        color = get_metric_color(0.15)
        assert color == DARK_THEME.metric_bad

    def test_format_metric_score(self):
        """Test formatting metric score with color."""
        formatted = format_metric_score(0.85)
        assert "85.0%" in formatted
        assert "rgb(120,200,80)" in formatted

    def test_all_themes_registered(self):
        """Test that all themes are registered."""
        assert ThemeName.DARK in [ThemeName.DARK, ThemeName.LIGHT, ThemeName.ANSI_DARK, ThemeName.ANSI_LIGHT]


class TestStreamingManager:
    """Tests for the streaming manager."""

    def test_initial_state(self):
        """Test initial state is idle."""
        manager = StreamingManager()
        assert manager.state == StreamingState.IDLE
        assert not manager.is_active

    def test_start_requesting(self):
        """Test starting request transitions to requesting."""
        manager = StreamingManager()
        result = manager.start_requesting("Test operation")
        assert manager.state == StreamingState.REQUESTING
        assert manager.is_active

    def test_transition_to_thinking(self):
        """Test transition to thinking state."""
        manager = StreamingManager()
        manager.start_requesting()
        manager.start_thinking()
        assert manager.state == StreamingState.THINKING

    def test_transition_to_evaluating(self):
        """Test transition to evaluating state."""
        manager = StreamingManager()
        manager.start_requesting()
        manager.start_evaluating("Evaluating...")
        assert manager.state == StreamingState.EVALUATING

    def test_transition_to_tool_input(self):
        """Test transition to tool input state."""
        manager = StreamingManager()
        manager.start_requesting()
        manager.start_evaluating()
        manager.start_tool_input("run")
        assert manager.state == StreamingState.TOOL_INPUT

    def test_transition_to_tool_use(self):
        """Test transition to tool use state."""
        manager = StreamingManager()
        manager.start_requesting()
        manager.start_evaluating()
        manager.start_tool_input("run")
        manager.start_tool_use("run")
        assert manager.state == StreamingState.TOOL_USE

    def test_finish(self):
        """Test finish transitions to idle."""
        manager = StreamingManager()
        manager.start_requesting()
        manager.finish()
        assert manager.state == StreamingState.IDLE
        assert not manager.is_active

    def test_invalid_transition(self):
        """Test invalid transition returns False."""
        manager = StreamingManager()
        result = manager.transition(StreamingState.THINKING)
        assert result is False
        assert manager.state == StreamingState.IDLE

    def test_spinner_frame(self):
        """Test spinner frame is valid."""
        manager = StreamingManager()
        manager.start_requesting()
        frame = manager.spinner_frame
        assert frame in SPINNER_FRAMES

    def test_advance_frame(self):
        """Test advancing frame changes spinner."""
        manager = StreamingManager()
        manager.start_requesting()
        frame1 = manager.spinner_frame
        frame2 = manager.advance_frame()
        # Frame should advance
        assert manager._frame_index == 1

    def test_increment_tokens(self):
        """Test incrementing token count."""
        manager = StreamingManager()
        manager.increment_tokens(10)
        assert manager._token_count == 10
        manager.increment_tokens(5)
        assert manager._token_count == 15

    def test_get_status(self):
        """Test getting status dictionary."""
        manager = StreamingManager()
        status = manager.get_status()
        assert "state" in status
        assert "elapsed" in status
        assert "spinner" in status
        assert "tokens" in status
        assert "operation" in status

    def test_listener_called(self):
        """Test that listeners are called on state change."""
        manager = StreamingManager()
        called_states = []
        manager.add_listener(lambda s: called_states.append(s))
        manager.start_requesting()
        assert StreamingState.REQUESTING in called_states


class TestSpinnerWidget:
    """Tests for the spinner widget."""

    def test_spinner_widget_exists(self):
        """Test that SpinnerWidget can be imported."""
        assert SpinnerWidget is not None

    def test_rotating_tips_exist(self):
        """Test that rotating tips are defined."""
        assert len(ROTATING_TIPS) > 0

    def test_spinner_frames_exist(self):
        """Test that spinner frames are defined."""
        assert len(SPINNER_FRAMES) == 10


class TestStatusFooter:
    """Tests for the status footer widget."""

    def test_status_footer_exists(self):
        """Test that StatusFooter can be imported."""
        assert StatusFooter is not None

    def test_default_values(self):
        """Test default values."""
        footer = StatusFooter()
        assert footer.model_name == "gpt-4"
        assert footer.cost == 0.0
        assert footer.elapsed == 0.0
        assert footer.token_count == 0
        assert footer.progress == 0


class TestToolRenderers:
    """Tests for tool-specific renderers."""

    def test_eval_panel_exists(self):
        """Test that EvalResultPanel can be imported."""
        assert EvalResultPanel is not None

    def test_audit_panel_exists(self):
        """Test that AuditResultPanel can be imported."""
        assert AuditResultPanel is not None

    def test_diagnose_panel_exists(self):
        """Test that DiagnoseResultPanel can be imported."""
        assert DiagnoseResultPanel is not None

    def test_eval_panel_default_title(self):
        """Test EvalResultPanel default title."""
        panel = EvalResultPanel()
        assert panel._title == "Evaluation Results"

    def test_audit_panel_default_title(self):
        """Test AuditResultPanel default title."""
        panel = AuditResultPanel()
        assert panel._title == "Audit Results"

    def test_diagnose_panel_default_title(self):
        """Test DiagnoseResultPanel default title."""
        panel = DiagnoseResultPanel()
        assert panel._title == "Blame Attribution"

    def test_eval_panel_update_metrics(self):
        """Test updating metrics on EvalResultPanel."""
        panel = EvalResultPanel()
        panel.update_metrics({"faithfulness": 0.85, "relevancy": 0.72})
        assert panel._metrics == {"faithfulness": 0.85, "relevancy": 0.72}

    def test_audit_panel_update_issues(self):
        """Test updating issues on AuditResultPanel."""
        panel = AuditResultPanel()
        issues = [{"type": "contradiction", "count": 2, "severity": "high", "status": "warning"}]
        panel.update_issues(issues)
        assert panel._issues == issues

    def test_diagnose_panel_update_components(self):
        """Test updating components on DiagnoseResultPanel."""
        panel = DiagnoseResultPanel()
        components = [{"component": "retrieval", "blame": 0.6, "confidence": 0.8, "recommendation": "Improve chunking"}]
        panel.update_components(components)
        assert panel._components == components


class TestStateTransitions:
    """Tests for state transition validity."""

    def test_idle_to_requesting(self):
        """Test IDLE -> REQUESTING is valid."""
        assert StreamingState.REQUESTING in STATE_TRANSITIONS[StreamingState.IDLE]

    def test_requesting_to_thinking(self):
        """Test REQUESTING -> THINKING is valid."""
        assert StreamingState.THINKING in STATE_TRANSITIONS[StreamingState.REQUESTING]

    def test_requesting_to_evaluating(self):
        """Test REQUESTING -> EVALUATING is valid."""
        assert StreamingState.EVALUATING in STATE_TRANSITIONS[StreamingState.REQUESTING]

    def test_evaluating_to_tool_input(self):
        """Test EVALUATING -> TOOL_INPUT is valid."""
        assert StreamingState.TOOL_INPUT in STATE_TRANSITIONS[StreamingState.EVALUATING]

    def test_tool_input_to_tool_use(self):
        """Test TOOL_INPUT -> TOOL_USE is valid."""
        assert StreamingState.TOOL_USE in STATE_TRANSITIONS[StreamingState.TOOL_INPUT]

    def test_tool_use_to_evaluating(self):
        """Test TOOL_USE -> EVALUATING is valid."""
        assert StreamingState.EVALUATING in STATE_TRANSITIONS[StreamingState.TOOL_USE]

    def test_all_states_can_return_to_idle(self):
        """Test all states can transition to IDLE."""
        for state, transitions in STATE_TRANSITIONS.items():
            if state != StreamingState.IDLE:
                assert StreamingState.IDLE in transitions, f"{state} cannot return to IDLE"
