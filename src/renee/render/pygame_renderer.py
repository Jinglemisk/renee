"""Pygame-based renderer for the Renee rendering system.

This module provides a full-featured renderer using pygame for 2D games.
Supports sprites, tilemaps, text, shapes, and input handling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import pygame
except ImportError:
    pygame = None  # type: ignore

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

logger = logging.getLogger(__name__)


class PygameRenderer(Renderer):
    """Pygame-based 2D renderer.

    Renders game graphics using pygame, supporting sprites, text, shapes,
    and tilemaps. Handles keyboard and mouse input via pygame events.

    Configuration:
        width: int - Window width in pixels (default: 800)
        height: int - Window height in pixels (default: 600)
        title: str - Window title (default: "Renee Game")
        fps: int - Target frame rate (default: 60)
        fullscreen: bool - Enable fullscreen mode (default: False)
        asset_path: str - Path to game assets directory (default: "assets")
    """

    def __init__(self) -> None:
        """Initialize pygame renderer (call initialize() to setup)."""
        self.screen: Any = None
        self.clock: Any = None
        self.running: bool = False
        self.fps: int = 60
        self.asset_path: Path = Path("assets")

        # Input tracking
        self.current_input: InputState = InputState()
        self.previous_keys: set[str] = set()
        self.previous_mouse_buttons: set[int] = set()

        # Asset caches
        self.sprite_cache: dict[str, Any] = {}
        self.font_cache: dict[tuple[str | None, int], Any] = {}
        self.tilemap_cache: dict[str, Any] = {}

    def initialize(self, config: dict[str, Any]) -> None:
        """Setup pygame and create the game window.

        Args:
            config: Configuration dictionary with keys:
                   - width (int): Window width
                   - height (int): Window height
                   - title (str): Window title
                   - fps (int): Target frame rate
                   - fullscreen (bool): Fullscreen mode
                   - asset_path (str): Path to assets directory

        Raises:
            ImportError: If pygame is not installed.
            RuntimeError: If pygame initialization fails.
        """
        if pygame is None:
            raise ImportError(
                "pygame is not installed. Install it with: pip install pygame"
            )

        # Extract configuration
        width = config.get("width", 800)
        height = config.get("height", 600)
        title = config.get("title", "Renee Game")
        self.fps = config.get("fps", 60)
        fullscreen = config.get("fullscreen", False)
        asset_path = config.get("asset_path", "assets")
        self.asset_path = Path(asset_path)

        # Initialize pygame
        try:
            pygame.init()
            pygame.font.init()

            # Create display
            flags = pygame.FULLSCREEN if fullscreen else 0
            self.screen = pygame.display.set_mode((width, height), flags)
            pygame.display.set_caption(title)

            # Create clock for frame rate limiting
            self.clock = pygame.time.Clock()

            self.running = True
            logger.info(
                f"Pygame renderer initialized: {width}x{height} @ {self.fps} FPS"
            )

        except Exception as e:
            raise RuntimeError(f"Failed to initialize pygame: {e}")

    def render(self, commands: list[RenderCommand]) -> None:
        """Process and execute render commands.

        Commands are sorted by layer (lower values drawn first) and then
        executed using pygame drawing functions.

        Args:
            commands: List of render commands to execute.
        """
        if not self.running or self.screen is None:
            return

        # Sort commands by layer (lower layers drawn first)
        sorted_commands = sorted(commands, key=lambda cmd: cmd.layer)

        # Execute each command
        for command in sorted_commands:
            try:
                if isinstance(command, ClearCommand):
                    self._render_clear(command)
                elif isinstance(command, DrawSpriteCommand):
                    self._render_sprite(command)
                elif isinstance(command, DrawRectCommand):
                    self._render_rect(command)
                elif isinstance(command, DrawTextCommand):
                    self._render_text(command)
                elif isinstance(command, DrawTilemapCommand):
                    self._render_tilemap(command)
                elif isinstance(command, DrawLineCommand):
                    self._render_line(command)
                elif isinstance(command, DrawCircleCommand):
                    self._render_circle(command)
                else:
                    logger.warning(f"Unknown render command type: {type(command)}")
            except Exception as e:
                logger.error(f"Error rendering command {command}: {e}")

        # Update display and limit frame rate
        pygame.display.flip()
        if self.clock:
            self.clock.tick(self.fps)

    def get_input(self) -> InputState:
        """Process pygame events and return current input state.

        Updates keyboard and mouse state based on pygame events.
        Tracks key presses, releases, and mouse state changes.

        Returns:
            InputState object with current input information.
        """
        if not self.running:
            return self.current_input

        # Reset "just pressed/released" states
        self.current_input.keys_just_pressed.clear()
        self.current_input.keys_just_released.clear()
        self.current_input.mouse_just_pressed.clear()
        self.current_input.mouse_just_released.clear()

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                key_name = pygame.key.name(event.key)
                self.current_input.keys_pressed.add(key_name)
                self.current_input.keys_just_pressed.add(key_name)
            elif event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key)
                self.current_input.keys_pressed.discard(key_name)
                self.current_input.keys_just_released.add(key_name)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.current_input.mouse_buttons.add(event.button)
                self.current_input.mouse_just_pressed.add(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.current_input.mouse_buttons.discard(event.button)
                self.current_input.mouse_just_released.add(event.button)

        # Update mouse position
        mouse_pos = pygame.mouse.get_pos()
        self.current_input.mouse_x = mouse_pos[0]
        self.current_input.mouse_y = mouse_pos[1]

        return self.current_input

    def shutdown(self) -> None:
        """Cleanup pygame resources and quit.

        Clears caches and quits pygame properly.
        """
        self.running = False

        # Clear caches
        self.sprite_cache.clear()
        self.font_cache.clear()
        self.tilemap_cache.clear()

        # Quit pygame
        if pygame is not None:
            pygame.quit()

        logger.info("Pygame renderer shut down")

    def is_running(self) -> bool:
        """Check if the renderer window is still open.

        Returns:
            True if renderer is active, False if window was closed.
        """
        return self.running

    # Private rendering methods

    def _render_clear(self, command: ClearCommand) -> None:
        """Clear screen with a solid color."""
        if self.screen:
            self.screen.fill(command.color)

    def _render_sprite(self, command: DrawSpriteCommand) -> None:
        """Draw a sprite with transformations."""
        if not self.screen:
            return

        # Load sprite (with caching)
        sprite = self._load_sprite(command.sprite)
        if sprite is None:
            logger.warning(f"Failed to load sprite: {command.sprite}")
            return

        # Apply transformations
        transformed = sprite

        # Scale
        if command.scale != 1.0:
            new_width = int(sprite.get_width() * command.scale)
            new_height = int(sprite.get_height() * command.scale)
            transformed = pygame.transform.scale(transformed, (new_width, new_height))

        # Rotation
        if command.rotation != 0.0:
            transformed = pygame.transform.rotate(transformed, command.rotation)

        # Flip
        if command.flip_x or command.flip_y:
            transformed = pygame.transform.flip(
                transformed, command.flip_x, command.flip_y
            )

        # Alpha/transparency
        if command.alpha != 255:
            transformed = transformed.copy()
            transformed.set_alpha(command.alpha)

        # Draw sprite
        self.screen.blit(transformed, (command.x, command.y))

    def _render_rect(self, command: DrawRectCommand) -> None:
        """Draw a rectangle (filled or outline)."""
        if not self.screen:
            return

        rect = pygame.Rect(command.x, command.y, command.width, command.height)

        if command.filled:
            pygame.draw.rect(self.screen, command.color, rect)
        else:
            pygame.draw.rect(self.screen, command.color, rect, 1)

    def _render_text(self, command: DrawTextCommand) -> None:
        """Render text at a position."""
        if not self.screen:
            return

        # Load font (with caching)
        font = self._load_font(command.font, command.size)

        # Render text
        text_surface = font.render(command.text, True, command.color)

        # Draw text
        self.screen.blit(text_surface, (command.x, command.y))

    def _render_tilemap(self, command: DrawTilemapCommand) -> None:
        """Draw a tilemap with offset."""
        if not self.screen:
            return

        # Load tilemap data
        tilemap_data = self._load_tilemap(command.tilemap)
        if tilemap_data is None:
            logger.warning(f"Failed to load tilemap: {command.tilemap}")
            return

        # Extract tilemap information
        tile_width = tilemap_data.get("tile_width", 32)
        tile_height = tilemap_data.get("tile_height", 32)
        tiles = tilemap_data.get("tiles", [])
        tileset = tilemap_data.get("tileset", "")

        # Load tileset sprite
        tileset_sprite = self._load_sprite(tileset)
        if tileset_sprite is None:
            logger.warning(f"Failed to load tileset: {tileset}")
            return

        # Draw each tile
        for tile_data in tiles:
            tile_x = tile_data.get("x", 0)
            tile_y = tile_data.get("y", 0)
            tile_index = tile_data.get("index", 0)

            # Calculate source rect from tileset
            tiles_per_row = tileset_sprite.get_width() // tile_width
            src_x = (tile_index % tiles_per_row) * tile_width
            src_y = (tile_index // tiles_per_row) * tile_height
            src_rect = pygame.Rect(src_x, src_y, tile_width, tile_height)

            # Calculate destination position with offset
            dest_x = tile_x * tile_width + command.offset_x
            dest_y = tile_y * tile_height + command.offset_y

            # Blit tile
            self.screen.blit(tileset_sprite, (dest_x, dest_y), src_rect)

    def _render_line(self, command: DrawLineCommand) -> None:
        """Draw a line between two points."""
        if not self.screen:
            return

        pygame.draw.line(
            self.screen,
            command.color,
            (command.x1, command.y1),
            (command.x2, command.y2),
            command.width,
        )

    def _render_circle(self, command: DrawCircleCommand) -> None:
        """Draw a circle (filled or outline)."""
        if not self.screen:
            return

        if command.filled:
            pygame.draw.circle(
                self.screen, command.color, (command.x, command.y), command.radius
            )
        else:
            pygame.draw.circle(
                self.screen, command.color, (command.x, command.y), command.radius, 1
            )

    # Asset loading methods

    def _load_sprite(self, sprite_name: str) -> Any:
        """Load a sprite from disk with caching."""
        # Check cache first
        if sprite_name in self.sprite_cache:
            return self.sprite_cache[sprite_name]

        # Try to load sprite
        sprite_path = self.asset_path / sprite_name

        try:
            sprite = pygame.image.load(str(sprite_path))
            sprite = sprite.convert_alpha()  # Optimize for blitting
            self.sprite_cache[sprite_name] = sprite
            return sprite
        except Exception as e:
            logger.error(f"Failed to load sprite '{sprite_name}': {e}")
            return None

    def _load_font(self, font_name: str | None, size: int) -> Any:
        """Load a font with caching."""
        # Check cache first
        cache_key = (font_name, size)
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]

        # Load font
        try:
            if font_name is None:
                # Use default pygame font
                font = pygame.font.Font(None, size)
            else:
                # Load custom font from asset path
                font_path = self.asset_path / font_name
                font = pygame.font.Font(str(font_path), size)

            self.font_cache[cache_key] = font
            return font
        except Exception as e:
            logger.error(f"Failed to load font '{font_name}': {e}")
            # Fallback to default font
            font = pygame.font.Font(None, size)
            self.font_cache[cache_key] = font
            return font

    def _load_tilemap(self, tilemap_name: str) -> dict[str, Any] | None:
        """Load tilemap data with caching."""
        # Check cache first
        if tilemap_name in self.tilemap_cache:
            return self.tilemap_cache[tilemap_name]

        # Try to load tilemap
        tilemap_path = self.asset_path / tilemap_name

        try:
            import json

            with open(tilemap_path) as f:
                tilemap_data = json.load(f)

            self.tilemap_cache[tilemap_name] = tilemap_data
            return tilemap_data
        except Exception as e:
            logger.error(f"Failed to load tilemap '{tilemap_name}': {e}")
            return None
