"""Theme system with 70+ semantic tokens for Claude Code-inspired TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ThemeName(str, Enum):
    """Built-in theme names."""

    DARK = "dark"
    LIGHT = "light"
    ANSI_DARK = "ansi-dark"
    ANSI_LIGHT = "ansi-light"


@dataclass(frozen=True)
class Theme:
    """Theme with semantic color tokens.

    Flat structure for O(1) lookup. Each token maps to a raw color value.
    """

    # Brand identity
    brand: str = "rgb(79,140,255)"
    brand_shimmer: str = "rgb(120,170,255)"
    brand_dim: str = "rgb(60,100,180)"

    # UI surface roles
    prompt_border: str = "rgb(79,140,255)"
    user_message_bg: str = "rgb(40,44,52)"
    selection_bg: str = "rgb(79,140,255,0.3)"

    # Semantic status colors
    success: str = "rgb(80,200,120)"
    success_dim: str = "rgb(80,200,120,0.5)"
    error: str = "rgb(255,80,80)"
    error_dim: str = "rgb(255,80,80,0.5)"
    warning: str = "rgb(255,200,50)"
    warning_dim: str = "rgb(255,200,50,0.5)"
    info: str = "rgb(120,180,255)"
    info_dim: str = "rgb(120,180,255,0.5)"

    # Metrics (color-coded by quality)
    metric_excellent: str = "rgb(80,200,120)"
    metric_good: str = "rgb(120,200,80)"
    metric_fair: str = "rgb(255,200,50)"
    metric_poor: str = "rgb(255,140,50)"
    metric_bad: str = "rgb(255,80,80)"

    # Diff colors (4 variants per operation)
    diff_added: str = "rgb(80,200,120)"
    diff_added_dimmed: str = "rgb(80,200,120,0.5)"
    diff_added_word: str = "rgb(80,200,120,0.3)"
    diff_removed: str = "rgb(255,80,80)"
    diff_removed_dimmed: str = "rgb(255,80,80,0.5)"
    diff_removed_word: str = "rgb(255,80,80,0.3)"
    diff_context: str = "rgb(128,128,128)"

    # Tool-specific colors
    tool_eval: str = "rgb(79,140,255)"
    tool_audit: str = "rgb(200,120,255)"
    tool_diagnose: str = "rgb(255,160,50)"
    tool_report: str = "rgb(120,200,80)"
    tool_compare: str = "rgb(80,200,200)"

    # Text colors
    text_primary: str = "rgb(255,255,255)"
    text_secondary: str = "rgb(180,180,180)"
    text_dimmed: str = "rgb(128,128,128)"
    text_inverse: str = "rgb(0,0,0)"

    # UI element colors
    border_default: str = "rgb(60,64,72)"
    border_active: str = "rgb(79,140,255)"
    border_error: str = "rgb(255,80,80)"
    background_default: str = "rgb(30,30,30)"
    background_surface: str = "rgb(40,44,52)"
    background_elevated: str = "rgb(50,54,62)"

    # Spinner frames
    spinner_color: str = "rgb(79,140,255)"

    # Permission dialog
    permission_allow: str = "rgb(80,200,120)"
    permission_deny: str = "rgb(255,80,80)"
    permission_question: str = "rgb(255,200,50)"

    # Code syntax
    code_keyword: str = "rgb(200,120,255)"
    code_string: str = "rgb(80,200,120)"
    code_number: str = "rgb(255,160,50)"
    code_comment: str = "rgb(128,128,128)"

    # Rainbow colors (for special highlighting)
    rainbow_red: str = "rgb(255,80,80)"
    rainbow_orange: str = "rgb(255,160,50)"
    rainbow_yellow: str = "rgb(255,200,50)"
    rainbow_green: str = "rgb(80,200,120)"
    rainbow_blue: str = "rgb(79,140,255)"
    rainbow_indigo: str = "rgb(120,80,255)"
    rainbow_violet: str = "rgb(200,80,255)"


# Pre-defined themes
DARK_THEME = Theme()

LIGHT_THEME = Theme(
    brand="rgb(40,100,200)",
    brand_shimmer="rgb(60,120,220)",
    brand_dim="rgb(80,140,240)",
    prompt_border="rgb(40,100,200)",
    user_message_bg="rgb(240,240,240)",
    selection_bg="rgb(40,100,200,0.2)",
    success="rgb(30,150,80)",
    error="rgb(200,50,50)",
    warning="rgb(180,140,0)",
    info="rgb(60,120,200)",
    text_primary="rgb(30,30,30)",
    text_secondary="rgb(100,100,100)",
    text_dimmed="rgb(160,160,160)",
    text_inverse="rgb(255,255,255)",
    border_default="rgb(200,200,200)",
    border_active="rgb(40,100,200)",
    background_default="rgb(255,255,255)",
    background_surface="rgb(245,245,245)",
    background_elevated="rgb(240,240,240)",
)

ANSI_DARK_THEME = Theme(
    brand="bright_blue",
    brand_shimmer="bright_cyan",
    brand_dim="blue",
    prompt_border="bright_blue",
    user_message_bg="bright_black",
    selection_bg="bright_blue",
    success="bright_green",
    error="bright_red",
    warning="bright_yellow",
    info="bright_cyan",
    metric_excellent="bright_green",
    metric_good="green",
    metric_fair="yellow",
    metric_poor="bright_red",
    metric_bad="red",
    diff_added="bright_green",
    diff_removed="bright_red",
    tool_eval="bright_blue",
    tool_audit="bright_magenta",
    tool_diagnose="bright_yellow",
    text_primary="bright_white",
    text_secondary="bright_black",
    text_dimmed="black",
    border_default="bright_black",
    border_active="bright_blue",
    background_default="black",
    background_surface="bright_black",
    background_elevated="bright_black",
    spinner_color="bright_blue",
)

# Theme registry
THEMES: dict[ThemeName, Theme] = {
    ThemeName.DARK: DARK_THEME,
    ThemeName.LIGHT: LIGHT_THEME,
    ThemeName.ANSI_DARK: ANSI_DARK_THEME,
    ThemeName.ANSI_LIGHT: LIGHT_THEME,  # Uses light theme with ANSI colors
}


def get_theme(name: ThemeName | str = ThemeName.DARK) -> Theme:
    """Get theme by name.

    Args:
        name: Theme name or ThemeName enum value.

    Returns:
        Theme instance.
    """
    if isinstance(name, str):
        name = ThemeName(name)
    return THEMES.get(name, DARK_THEME)


def get_metric_color(score: float, theme: Theme | None = None) -> str:
    """Get color for a metric score.

    Args:
        score: Score between 0.0 and 1.0.
        theme: Optional theme to use.

    Returns:
        Color string for the score.
    """
    t = theme or DARK_THEME
    if score >= 0.9:
        return t.metric_excellent
    elif score >= 0.7:
        return t.metric_good
    elif score >= 0.5:
        return t.metric_fair
    elif score >= 0.3:
        return t.metric_poor
    return t.metric_bad


def format_metric_score(score: float, theme: Theme | None = None) -> str:
    """Format a metric score with color.

    Args:
        score: Score between 0.0 and 1.0.
        theme: Optional theme to use.

    Returns:
        Rich-formatted string with color.
    """
    color = get_metric_color(score, theme)
    return f"[{color}]{score:.1%}[/{color}]"
