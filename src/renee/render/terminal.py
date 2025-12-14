"""ASCII terminal renderer for the Renee rendering system.

Renders the game to the terminal using ASCII characters and ANSI colors.
Great for debugging, remote play, or retro aesthetics.
"""

from __future__ import annotations

import sys
from typing import Any

from renee.render.commands import (
    ClearCommand,
    DrawCircleCommand,
    DrawLineCommand,
    DrawRectCommand,
    DrawSpriteCommand,
    DrawTextCommand,
    DrawTilemapCommand,
    RenderCommand,
)
from renee.render.renderer import InputState, Renderer


class TerminalRenderer(Renderer):
    """ASCII-based terminal renderer.

    Maps sprites to characters and uses ANSI escape codes for colors.
    Grid-based output suitable for terminal display.
    """

    # ANSI color codes
    _COLORS: dict[str, str] = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m",
        "bg_black": "\033[40m",
        "bg_red": "\033[41m",
        "bg_green": "\033[42m",
        "bg_yellow": "\033[43m",
        "bg_blue": "\033[44m",
        "bg_magenta": "\033[45m",
        "bg_cyan": "\033[46m",
        "bg_white": "\033[47m",
    }

    def __init__(self) -> None:
        """Initialize the terminal renderer."""
        self._width: int = 80
        self._height: int = 24
        self._running: bool = False
        self._sprite_map: dict[str, str] = {}
        self._tilemap_map: dict[str, list[list[str]]] = {}
        self._buffer: list[list[str]] = []
        self._clear_char: str = " "
        self._input_state: InputState = InputState()

    def initialize(self, config: dict) -> None:
        """Setup the terminal renderer.

        Args:
            config: Configuration dictionary.
                   Keys: width (int), height (int),
                        sprite_map (dict[str, str]),
                        tilemap_map (dict[str, list[list[str]]]).
        """
        self._width = config.get("width", 80)
        self._height = config.get("height", 24)
        self._sprite_map = config.get("sprite_map", {})
        self._tilemap_map = config.get("tilemap_map", {})
        self._running = True

        # Initialize buffer
        self._buffer = [[self._clear_char for _ in range(self._width)]
                       for _ in range(self._height)]

        # Clear terminal
        self._clear_terminal()

    def render(self, commands: list[RenderCommand]) -> None:
        """Process and render commands to the terminal.

        Args:
            commands: List of render commands to execute.
        """
        # Sort by layer
        sorted_commands = sorted(commands, key=lambda c: c.layer)

        # Process commands
        for command in sorted_commands:
            self._process_command(command)

        # Display buffer
        self._display_buffer()

    def _process_command(self, command: RenderCommand) -> None:
        """Process a single render command.

        Args:
            command: The render command to process.
        """
        if isinstance(command, ClearCommand):
            self._handle_clear(command)
        elif isinstance(command, DrawSpriteCommand):
            self._handle_sprite(command)
        elif isinstance(command, DrawRectCommand):
            self._handle_rect(command)
        elif isinstance(command, DrawTextCommand):
            self._handle_text(command)
        elif isinstance(command, DrawTilemapCommand):
            self._handle_tilemap(command)
        elif isinstance(command, DrawLineCommand):
            self._handle_line(command)
        elif isinstance(command, DrawCircleCommand):
            self._handle_circle(command)

    def _handle_clear(self, command: ClearCommand) -> None:
        """Clear the buffer.

        Args:
            command: Clear command.
        """
        self._buffer = [[self._clear_char for _ in range(self._width)]
                       for _ in range(self._height)]

    def _handle_sprite(self, command: DrawSpriteCommand) -> None:
        """Draw a sprite character.

        Args:
            command: DrawSpriteCommand.
        """
        char = self._sprite_map.get(command.sprite, "?")
        x, y = command.x, command.y

        if 0 <= y < self._height and 0 <= x < self._width:
            self._buffer[y][x] = char

    def _handle_rect(self, command: DrawRectCommand) -> None:
        """Draw a rectangle.

        Args:
            command: DrawRectCommand.
        """
        char = "#" if command.filled else "+"

        for y in range(command.y, min(command.y + command.height, self._height)):
            for x in range(command.x, min(command.x + command.width, self._width)):
                if command.filled:
                    if 0 <= y < self._height and 0 <= x < self._width:
                        self._buffer[y][x] = char
                else:
                    # Only draw border
                    is_border = (y == command.y or y == command.y + command.height - 1 or
                               x == command.x or x == command.x + command.width - 1)
                    if is_border and 0 <= y < self._height and 0 <= x < self._width:
                        self._buffer[y][x] = char

    def _handle_text(self, command: DrawTextCommand) -> None:
        """Draw text.

        Args:
            command: DrawTextCommand.
        """
        x, y = command.x, command.y

        if 0 <= y < self._height:
            for i, char in enumerate(command.text):
                if 0 <= x + i < self._width:
                    self._buffer[y][x + i] = char

    def _handle_tilemap(self, command: DrawTilemapCommand) -> None:
        """Draw a tilemap.

        Args:
            command: DrawTilemapCommand.
        """
        tilemap = self._tilemap_map.get(command.tilemap, [])

        for tile_y, row in enumerate(tilemap):
            screen_y = tile_y + command.offset_y
            if 0 <= screen_y < self._height:
                for tile_x, char in enumerate(row):
                    screen_x = tile_x + command.offset_x
                    if 0 <= screen_x < self._width:
                        self._buffer[screen_y][screen_x] = char

    def _handle_line(self, command: DrawLineCommand) -> None:
        """Draw a line using Bresenham's algorithm.

        Args:
            command: DrawLineCommand.
        """
        x1, y1 = command.x1, command.y1
        x2, y2 = command.x2, command.y2

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= y1 < self._height and 0 <= x1 < self._width:
                self._buffer[y1][x1] = "*"

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def _handle_circle(self, command: DrawCircleCommand) -> None:
        """Draw a circle using midpoint algorithm.

        Args:
            command: DrawCircleCommand.
        """
        cx, cy, r = command.x, command.y, command.radius
        char = "O" if command.filled else "o"

        if command.filled:
            # Draw filled circle
            for y in range(max(0, cy - r), min(self._height, cy + r + 1)):
                for x in range(max(0, cx - r), min(self._width, cx + r + 1)):
                    dx = x - cx
                    dy = y - cy
                    if dx * dx + dy * dy <= r * r:
                        self._buffer[y][x] = char
        else:
            # Draw circle outline using midpoint algorithm
            x = r
            y = 0
            err = 0

            while x >= y:
                points = [
                    (cx + x, cy + y), (cx + y, cy + x),
                    (cx - y, cy + x), (cx - x, cy + y),
                    (cx - x, cy - y), (cx - y, cy - x),
                    (cx + y, cy - x), (cx + x, cy - y),
                ]
                for px, py in points:
                    if 0 <= py < self._height and 0 <= px < self._width:
                        self._buffer[py][px] = char

                if err <= 0:
                    y += 1
                    err += 2 * y + 1
                if err > 0:
                    x -= 1
                    err -= 2 * x + 1

    def _display_buffer(self) -> None:
        """Display the buffer to the terminal."""
        # Move cursor to top-left
        sys.stdout.write("\033[H")

        # Write buffer
        for row in self._buffer:
            sys.stdout.write("".join(row) + "\n")

        sys.stdout.flush()

    def _clear_terminal(self) -> None:
        """Clear the terminal screen."""
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def get_input(self) -> InputState:
        """Get current input state.

        Terminal renderer doesn't support interactive input in this basic version.

        Returns:
            Empty InputState object.
        """
        return self._input_state

    def shutdown(self) -> None:
        """Cleanup and restore terminal."""
        self._running = False
        # Reset terminal colors
        sys.stdout.write(self._COLORS["reset"])
        sys.stdout.flush()

    def is_running(self) -> bool:
        """Check if renderer is running.

        Returns:
            True if running, False otherwise.
        """
        return self._running

    def stop(self) -> None:
        """Stop the terminal renderer."""
        self._running = False

    def set_sprite_map(self, sprite_map: dict[str, str]) -> None:
        """Set the sprite-to-character mapping.

        Args:
            sprite_map: Dictionary mapping sprite names to characters.
        """
        self._sprite_map = sprite_map

    def set_tilemap_map(self, tilemap_map: dict[str, list[list[str]]]) -> None:
        """Set the tilemap definitions.

        Args:
            tilemap_map: Dictionary mapping tilemap names to 2D character arrays.
        """
        self._tilemap_map = tilemap_map
