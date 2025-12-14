"""Render command dataclasses for the Renee rendering system.

Render commands are abstract instructions that describe what to draw.
They are renderer-agnostic and can be interpreted by different backends
(headless, terminal, pygame, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RenderCommand:
    """Base class for render commands.

    All render commands support a layer field for draw order control.
    Higher layer values are drawn on top of lower values.
    """

    layer: int = field(default=0, kw_only=True)  # Draw order


@dataclass
class ClearCommand(RenderCommand):
    """Clear the screen with a solid color.

    Typically issued at the start of each frame.
    """

    color: tuple[int, int, int] = (0, 0, 0)


@dataclass
class DrawSpriteCommand(RenderCommand):
    """Draw a sprite at a specific position.

    Sprites are referenced by asset name and can be transformed
    with scaling, rotation, flipping, and transparency.
    """

    sprite: str  # Asset reference
    x: int
    y: int
    flip_x: bool = False
    flip_y: bool = False
    scale: float = 1.0
    rotation: float = 0.0
    alpha: int = 255


@dataclass
class DrawRectCommand(RenderCommand):
    """Draw a rectangle (filled or outline).

    Useful for UI elements, debug visualization, and simple shapes.
    """

    x: int
    y: int
    width: int
    height: int
    color: tuple[int, int, int]
    filled: bool = True


@dataclass
class DrawTextCommand(RenderCommand):
    """Draw text at a specific position.

    Text rendering with customizable font, size, and color.
    """

    text: str
    x: int
    y: int
    size: int = 16
    color: tuple[int, int, int] = (255, 255, 255)
    font: str | None = None


@dataclass
class DrawTilemapCommand(RenderCommand):
    """Draw a tilemap with optional offset.

    Tilemaps are referenced by asset name and can be scrolled
    using the offset parameters.
    """

    tilemap: str  # Asset reference to tilemap
    offset_x: int = 0
    offset_y: int = 0


@dataclass
class DrawLineCommand(RenderCommand):
    """Draw a line between two points.

    Useful for pathfinding visualization, UI elements, and effects.
    """

    x1: int
    y1: int
    x2: int
    y2: int
    color: tuple[int, int, int]
    width: int = 1


@dataclass
class DrawCircleCommand(RenderCommand):
    """Draw a circle (filled or outline).

    Useful for range indicators, effects, and UI elements.
    """

    x: int
    y: int
    radius: int
    color: tuple[int, int, int]
    filled: bool = True
