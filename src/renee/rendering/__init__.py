"""Rendering system.

The core engine outputs renderer-agnostic render commands. Concrete renderers
interpret those commands (pygame, terminal, headless).
"""

from renee.rendering.commands import (
    Clear,
    DrawImage,
    DrawRect,
    DrawSprite,
    DrawText,
    RenderCommand,
    normalize_command,
)
from renee.rendering.headless import HeadlessRenderer
from renee.rendering.pygame_renderer import PygameRenderer
from renee.rendering.renderer import Renderer
from renee.rendering.terminal import TerminalRenderer

__all__ = [
    "Clear",
    "DrawImage",
    "DrawRect",
    "DrawSprite",
    "DrawText",
    "HeadlessRenderer",
    "PygameRenderer",
    "RenderCommand",
    "Renderer",
    "TerminalRenderer",
    "normalize_command",
]
