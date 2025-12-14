"""Rendering system.

The core engine outputs renderer-agnostic render commands. Concrete renderers
interpret those commands (pygame, terminal, headless).
"""

from renee.render.commands import (
    Clear,
    DrawCircle,
    DrawImage,
    DrawLine,
    DrawRect,
    DrawSprite,
    DrawText,
    DrawTilemap,
    RenderCommand,
    normalize_command,
)
from renee.render.headless import HeadlessRenderer
from renee.render.pygame_renderer import PygameRenderer
from renee.render.renderer import Renderer
from renee.render.terminal import TerminalRenderer

__all__ = [
    "Clear",
    "DrawCircle",
    "DrawImage",
    "DrawLine",
    "DrawRect",
    "DrawSprite",
    "DrawText",
    "DrawTilemap",
    "HeadlessRenderer",
    "PygameRenderer",
    "RenderCommand",
    "Renderer",
    "TerminalRenderer",
    "normalize_command",
]
