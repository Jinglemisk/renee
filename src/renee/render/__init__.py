"""Rendering system for Renee game framework.

Provides abstract renderer interface and concrete implementations for:
- Terminal: ASCII-based rendering with ANSI colors
- Headless: No-op renderer for testing and AI simulation
- Pygame: Full graphical rendering (optional)

Renderers process RenderCommands to display game state.
"""

from renee.render.commands import (
    RenderCommand,
    ClearCommand,
    DrawSpriteCommand,
    DrawRectCommand,
    DrawTextCommand,
    DrawTilemapCommand,
    DrawLineCommand,
    DrawCircleCommand,
)
from renee.render.renderer import Renderer, InputState
from renee.render.headless import HeadlessRenderer
from renee.render.terminal import TerminalRenderer

__all__ = [
    # Base classes
    "Renderer",
    "InputState",
    # Commands
    "RenderCommand",
    "ClearCommand",
    "DrawSpriteCommand",
    "DrawRectCommand",
    "DrawTextCommand",
    "DrawTilemapCommand",
    "DrawLineCommand",
    "DrawCircleCommand",
    # Concrete renderers
    "HeadlessRenderer",
    "TerminalRenderer",
]
