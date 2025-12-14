"""Input state tracking for Renee.

Tracks the current state of all input devices (keyboard, mouse, controller).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from renee.types import Position


@dataclass
class InputState:
    """Current state of all inputs."""

    # Keyboard
    keys_pressed: set[str] = field(default_factory=set)
    keys_just_pressed: set[str] = field(default_factory=set)
    keys_just_released: set[str] = field(default_factory=set)

    # Mouse
    mouse_position: tuple[int, int] = (0, 0)
    mouse_buttons: set[int] = field(default_factory=set)  # 1=left, 2=middle, 3=right
    mouse_just_clicked: set[int] = field(default_factory=set)
    mouse_scroll: int = 0  # Positive = up, negative = down

    # Controller (gamepad)
    controller_buttons: set[str] = field(default_factory=set)
    controller_axes: dict[str, float] = field(default_factory=dict)

    def is_key_pressed(self, key: str) -> bool:
        """Check if a key is currently pressed."""
        return key in self.keys_pressed

    def is_key_just_pressed(self, key: str) -> bool:
        """Check if a key was just pressed this frame."""
        return key in self.keys_just_pressed

    def is_key_just_released(self, key: str) -> bool:
        """Check if a key was just released this frame."""
        return key in self.keys_just_released

    def is_mouse_pressed(self, button: int) -> bool:
        """Check if a mouse button is currently pressed."""
        return button in self.mouse_buttons

    def is_mouse_just_clicked(self, button: int) -> bool:
        """Check if a mouse button was just clicked this frame."""
        return button in self.mouse_just_clicked

    def get_mouse_grid_pos(self, tile_size: int) -> Position:
        """Convert mouse position to grid position.

        Args:
            tile_size: Size of a tile in pixels.

        Returns:
            Grid position corresponding to the mouse position.
        """
        return Position(
            self.mouse_position[0] // tile_size,
            self.mouse_position[1] // tile_size
        )

    def clear_frame_events(self) -> None:
        """Clear events that only last one frame (just pressed/released/clicked)."""
        self.keys_just_pressed.clear()
        self.keys_just_released.clear()
        self.mouse_just_clicked.clear()
        self.mouse_scroll = 0
