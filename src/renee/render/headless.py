"""Headless renderer for testing and AI simulation.

The headless renderer doesn't actually render anything - it just stores
render commands for inspection. Perfect for testing game logic without
a display, or for AI agents to analyze what would be rendered.
"""

from __future__ import annotations

from renee.render.commands import RenderCommand
from renee.render.renderer import InputState, Renderer


class HeadlessRenderer(Renderer):
    """Renderer that stores commands without displaying them.

    Useful for:
    - Testing game logic without a display
    - AI simulation and analysis
    - Headless servers
    - Automated testing
    """

    def __init__(self) -> None:
        """Initialize the headless renderer."""
        self._commands: list[RenderCommand] = []
        self._running: bool = False
        self._input_state: InputState = InputState()

    def initialize(self, config: dict) -> None:
        """Setup the headless renderer.

        Args:
            config: Configuration dictionary (mostly ignored for headless).
        """
        self._running = True
        self._commands.clear()

    def render(self, commands: list[RenderCommand]) -> None:
        """Store render commands for later inspection.

        Args:
            commands: List of render commands to store.
        """
        # Sort commands by layer (lower layers first)
        sorted_commands = sorted(commands, key=lambda c: c.layer)
        self._commands.extend(sorted_commands)

    def get_input(self) -> InputState:
        """Get current input state (always empty for headless).

        Returns:
            Empty InputState object.
        """
        return self._input_state

    def shutdown(self) -> None:
        """Cleanup resources."""
        self._running = False
        self._commands.clear()

    def is_running(self) -> bool:
        """Check if renderer is running.

        Returns:
            True if running, False otherwise.
        """
        return self._running

    def get_commands(self) -> list[RenderCommand]:
        """Get stored render commands.

        Returns:
            List of all stored render commands in layer order.
        """
        return self._commands.copy()

    def clear_commands(self) -> None:
        """Clear stored render commands.

        Useful for resetting state between frames or tests.
        """
        self._commands.clear()

    def set_input(self, input_state: InputState) -> None:
        """Set the input state (for testing).

        Args:
            input_state: Input state to simulate.
        """
        self._input_state = input_state

    def stop(self) -> None:
        """Stop the headless renderer (sets is_running to False)."""
        self._running = False
