"""Streaming output system with state machine for evaluation progress."""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Callable


class StreamingState(Enum):
    """State machine for streaming output."""

    IDLE = "idle"
    REQUESTING = "requesting"
    THINKING = "thinking"
    EVALUATING = "evaluating"
    TOOL_INPUT = "tool_input"
    TOOL_USE = "tool_use"


# Spinner animation frames (Claude Code style)
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# State transition triggers
STATE_TRANSITIONS: dict[StreamingState, list[StreamingState]] = {
    StreamingState.IDLE: [StreamingState.REQUESTING],
    StreamingState.REQUESTING: [StreamingState.THINKING, StreamingState.EVALUATING, StreamingState.IDLE],
    StreamingState.THINKING: [StreamingState.EVALUATING, StreamingState.TOOL_INPUT, StreamingState.IDLE],
    StreamingState.EVALUATING: [StreamingState.TOOL_INPUT, StreamingState.TOOL_USE, StreamingState.IDLE],
    StreamingState.TOOL_INPUT: [StreamingState.TOOL_USE, StreamingState.IDLE],
    StreamingState.TOOL_USE: [StreamingState.EVALUATING, StreamingState.IDLE],
}


class StreamingManager:
    """Manages streaming output state and animations.

    Tracks evaluation progress and manages spinner animations.
    """

    def __init__(self) -> None:
        self._state: StreamingState = StreamingState.IDLE
        self._start_time: float | None = None
        self._frame_index: int = 0
        self._elapsed: float = 0.0
        self._token_count: int = 0
        self._current_operation: str = ""
        self._listeners: list[Callable[[StreamingState], None]] = []

    @property
    def state(self) -> StreamingState:
        """Get current streaming state."""
        return self._state

    @property
    def is_active(self) -> bool:
        """Check if streaming is active (not idle)."""
        return self._state != StreamingState.IDLE

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    @property
    def spinner_frame(self) -> str:
        """Get current spinner animation frame."""
        return SPINNER_FRAMES[self._frame_index % len(SPINNER_FRAMES)]

    def add_listener(self, listener: Callable[[StreamingState], None]) -> None:
        """Add a state change listener.

        Args:
            listener: Callback function to invoke on state changes.
        """
        self._listeners.append(listener)

    def transition(self, new_state: StreamingState) -> bool:
        """Transition to a new state.

        Args:
            new_state: Target state.

        Returns:
            True if transition was successful.
        """
        if new_state not in STATE_TRANSITIONS.get(self._state, []):
            return False

        old_state = self._state
        self._state = new_state

        # Handle state entry
        if new_state == StreamingState.IDLE:
            self._stop()
        elif old_state == StreamingState.IDLE:
            self._start()

        # Notify listeners
        for listener in self._listeners:
            listener(new_state)

        return True

    def start_requesting(self, operation: str = "Starting...") -> None:
        """Start a new request.

        Args:
            operation: Description of the current operation.
        """
        self._current_operation = operation
        self.transition(StreamingState.REQUESTING)

    def start_thinking(self) -> None:
        """Transition to thinking state."""
        self.transition(StreamingState.THINKING)

    def start_evaluating(self, operation: str = "Evaluating...") -> None:
        """Transition to evaluating state.

        Args:
            operation: Description of the current operation.
        """
        self._current_operation = operation
        self.transition(StreamingState.EVALUATING)

    def start_tool_input(self, tool_name: str) -> None:
        """Transition to tool input state.

        Args:
            tool_name: Name of the tool being invoked.
        """
        self._current_operation = f"Using {tool_name}..."
        self.transition(StreamingState.TOOL_INPUT)

    def start_tool_use(self, tool_name: str) -> None:
        """Transition to tool use state.

        Args:
            tool_name: Name of the tool being executed.
        """
        self._current_operation = f"Executing {tool_name}..."
        self.transition(StreamingState.TOOL_USE)

    def finish(self) -> None:
        """Finish streaming and return to idle."""
        self.transition(StreamingState.IDLE)

    def increment_tokens(self, count: int = 1) -> None:
        """Increment token count.

        Args:
            count: Number of tokens to add.
        """
        self._token_count += count

    def get_status(self) -> dict[str, Any]:
        """Get current status information.

        Returns:
            Dictionary with status information.
        """
        return {
            "state": self._state.value,
            "elapsed": self.elapsed,
            "spinner": self.spinner_frame,
            "tokens": self._token_count,
            "operation": self._current_operation,
        }

    def _start(self) -> None:
        """Start the streaming timer."""
        self._start_time = time.time()
        self._frame_index = 0

    def _stop(self) -> None:
        """Stop the streaming timer."""
        self._elapsed = self.elapsed
        self._start_time = None

    def advance_frame(self) -> str:
        """Advance spinner animation frame.

        Returns:
            New spinner frame character.
        """
        self._frame_index += 1
        return self.spinner_frame
