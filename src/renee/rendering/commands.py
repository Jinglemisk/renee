"""Render command protocol.

Render commands are simple dataclasses that can be serialized to dictionaries.
Renderers should accept either dataclass instances or already-normalized dicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, MutableMapping, TypeAlias


Color: TypeAlias = tuple[int, int, int]
RenderCommand: TypeAlias = MutableMapping[str, Any]


@dataclass(frozen=True, slots=True)
class Clear:
    color: Color = (0, 0, 0)

    def to_dict(self) -> RenderCommand:
        return {"type": "clear", "color": list(self.color)}


@dataclass(frozen=True, slots=True)
class DrawRect:
    x: int
    y: int
    w: int
    h: int
    color: Color = (255, 255, 255)
    filled: bool = True

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_rect",
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "color": list(self.color),
            "filled": self.filled,
        }


@dataclass(frozen=True, slots=True)
class DrawText:
    text: str
    x: int
    y: int
    size: int = 16
    color: Color = (255, 255, 255)

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_text",
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "color": list(self.color),
        }


@dataclass(frozen=True, slots=True)
class DrawSprite:
    sprite: str
    x: int
    y: int
    flip_x: bool = False
    flip_y: bool = False

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_sprite",
            "sprite": self.sprite,
            "x": self.x,
            "y": self.y,
            "flip_x": self.flip_x,
            "flip_y": self.flip_y,
        }


@dataclass(frozen=True, slots=True)
class DrawImage:
    image: str
    x: int = 0
    y: int = 0
    parallax: float = 1.0

    def to_dict(self) -> RenderCommand:
        return {
            "type": "draw_image",
            "image": self.image,
            "x": self.x,
            "y": self.y,
            "parallax": self.parallax,
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

