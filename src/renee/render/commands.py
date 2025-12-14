"""Render command protocol.

Render commands are simple dataclasses that can be serialized to dictionaries.
Renderers should accept either dataclass instances or already-normalized dicts.
All commands support a layer field for draw order control.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, MutableMapping, TypeAlias


Color: TypeAlias = tuple[int, int, int]
RenderCommand: TypeAlias = MutableMapping[str, Any]


@dataclass(frozen=True, slots=True)
class Clear:
    """Clear the screen with a solid color."""

    color: Color = (0, 0, 0)
    layer: int = 0

    def to_dict(self) -> RenderCommand:
        return {"type": "clear", "color": list(self.color), "layer": self.layer}


@dataclass(frozen=True, slots=True)
class DrawRect:
    """Draw a rectangle (filled or outline)."""

    x: int
    y: int
    w: int
    h: int
    color: Color = (255, 255, 255)
    filled: bool = True
    layer: int = 0

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_rect",
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "color": list(self.color),
            "filled": self.filled,
            "layer": self.layer,
        }


@dataclass(frozen=True, slots=True)
class DrawText:
    """Draw text at a specific position."""

    text: str
    x: int
    y: int
    size: int = 16
    color: Color = (255, 255, 255)
    font: str | None = None
    layer: int = 0

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_text",
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "color": list(self.color),
            "font": self.font,
            "layer": self.layer,
        }


@dataclass(frozen=True, slots=True)
class DrawSprite:
    """Draw a sprite at a specific position."""

    sprite: str
    x: int
    y: int
    flip_x: bool = False
    flip_y: bool = False
    scale: float = 1.0
    rotation: float = 0.0
    alpha: int = 255
    layer: int = 0

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_sprite",
            "sprite": self.sprite,
            "x": self.x,
            "y": self.y,
            "flip_x": self.flip_x,
            "flip_y": self.flip_y,
            "scale": self.scale,
            "rotation": self.rotation,
            "alpha": self.alpha,
            "layer": self.layer,
        }


@dataclass(frozen=True, slots=True)
class DrawImage:
    """Draw an image at a specific position with parallax support."""

    image: str
    x: int = 0
    y: int = 0
    parallax: float = 1.0
    layer: int = 0

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_image",
            "image": self.image,
            "x": self.x,
            "y": self.y,
            "parallax": self.parallax,
            "layer": self.layer,
        }


@dataclass(frozen=True, slots=True)
class DrawLine:
    """Draw a line between two points."""

    x1: int
    y1: int
    x2: int
    y2: int
    color: Color = (255, 255, 255)
    width: int = 1
    layer: int = 0

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_line",
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "color": list(self.color),
            "width": self.width,
            "layer": self.layer,
        }


@dataclass(frozen=True, slots=True)
class DrawCircle:
    """Draw a circle (filled or outline)."""

    x: int
    y: int
    radius: int
    color: Color = (255, 255, 255)
    filled: bool = True
    layer: int = 0

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_circle",
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "color": list(self.color),
            "filled": self.filled,
            "layer": self.layer,
        }


@dataclass(frozen=True, slots=True)
class DrawTilemap:
    """Draw a tilemap with optional offset."""

    tilemap: str
    offset_x: int = 0
    offset_y: int = 0
    layer: int = 0

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_tilemap",
            "tilemap": self.tilemap,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "layer": self.layer,
        }


def normalize_command(cmd: Any) -> RenderCommand:
    """Convert a command object to a dict with a `type`."""

    if isinstance(cmd, MutableMapping):
        if "type" not in cmd:
            raise ValueError("Render command dict missing 'type'")
        return cmd
    if hasattr(cmd, "to_dict"):
        return cmd.to_dict()
    if dataclass_is_instance(cmd):
        d = asdict(cmd)
        if "type" not in d:
            raise ValueError("Dataclass command missing 'type'")
        return d
    raise TypeError(f"Unsupported render command: {type(cmd).__name__}")


def dataclass_is_instance(obj: Any) -> bool:
    return hasattr(obj, "__dataclass_fields__")
