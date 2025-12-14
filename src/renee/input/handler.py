"""Input handler for Renee.

Processes raw input and maps it to game actions.
"""

from __future__ import annotations

from renee.input.bindings import InputBindings, DEFAULT_BINDINGS
from renee.input.state import InputState
from renee.types import Position


class InputHandler:
    """Handles input state updates and action mapping."""

    def __init__(self, bindings: InputBindings | None = None) -> None:
        """Initialize the input handler.

        Args:
            bindings: Custom input bindings. If None, uses DEFAULT_BINDINGS.
        """
        self.bindings = bindings or DEFAULT_BINDINGS
        self._previous_state: InputState | None = None
        self._current_state: InputState = InputState()

    def update(self, raw_state: InputState) -> None:
        """Update with new raw input state, computing just_pressed/released.

        This method processes the raw input and calculates frame-specific
        events like keys that were just pressed or just released.

        Args:
            raw_state: The new raw input state from the input backend.
        """
        self._previous_state = self._current_state
        self._current_state = raw_state

        # If we have a previous state, compute just_pressed and just_released
        if self._previous_state is not None:
            # Keys just pressed: in current but not in previous
            self._current_state.keys_just_pressed = (
                self._current_state.keys_pressed - self._previous_state.keys_pressed
            )

            # Keys just released: in previous but not in current
            self._current_state.keys_just_released = (
                self._previous_state.keys_pressed - self._current_state.keys_pressed
            )

            # Mouse buttons just clicked: in current but not in previous
            self._current_state.mouse_just_clicked = (
                self._current_state.mouse_buttons - self._previous_state.mouse_buttons
            )
        else:
            # First frame - everything just pressed is what's currently pressed
            self._current_state.keys_just_pressed = self._current_state.keys_pressed.copy()
            self._current_state.mouse_just_clicked = self._current_state.mouse_buttons.copy()

    def get_state(self) -> InputState:
        """Get current input state.

        Returns:
            The current input state.
        """
        return self._current_state

    def is_action_pressed(self, action: str) -> bool:
        """Check if action is pressed.

        Args:
            action: Logical action name.

        Returns:
            True if the action is currently pressed.
        """
        return self.bindings.is_action_pressed(action, self._current_state)

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed.

        Args:
            action: Logical action name.

        Returns:
            True if the action was just pressed this frame.
        """
        return self.bindings.is_action_just_pressed(action, self._current_state)

    def get_direction(self) -> Position | None:
        """Get movement direction from directional inputs.

        Combines input from up/down/left/right actions to create a
        direction vector. Supports diagonal movement.

        Returns:
            Position representing direction vector (e.g., (-1, 0) for left,
            (1, 1) for down-right), or None if no directional input.
        """
        dx = 0
        dy = 0

        if self.is_action_pressed("left"):
            dx -= 1
        if self.is_action_pressed("right"):
            dx += 1
        if self.is_action_pressed("up"):
            dy -= 1
        if self.is_action_pressed("down"):
            dy += 1

        # Return None if no direction input
        if dx == 0 and dy == 0:
            return None

        return Position(dx, dy)

    def get_mouse_position(self) -> tuple[int, int]:
        """Get current mouse position.

        Returns:
            Mouse position in screen coordinates (x, y).
        """
        return self._current_state.mouse_position

    def get_mouse_grid_position(self, tile_size: int) -> Position:
        """Get current mouse position in grid coordinates.

        Args:
            tile_size: Size of a tile in pixels.

        Returns:
            Grid position corresponding to the mouse position.
        """
        return self._current_state.get_mouse_grid_pos(tile_size)

    def get_all_pressed_actions(self) -> list[str]:
        """Get all actions currently pressed.

        Returns:
            List of all action names that are currently active.
        """
        return self.bindings.get_all_actions(self._current_state)

    def clear_state(self) -> None:
        """Clear all input state.

        Useful for resetting input when changing game states or
        when the game loses focus.
        """
        self._current_state = InputState()
        self._previous_state = None
