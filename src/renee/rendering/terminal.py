"""Terminal (ASCII) renderer.

This renderer is meant for debugging and headless-ish runs. It renders a simple
character buffer to a text stream.
"""

from __future__ import annotations

import sys
from typing import Any, Mapping, Sequence, TextIO

from renee.input import InputState
from renee.rendering.commands import RenderCommand, normalize_command
from renee.rendering.renderer import Renderer


class TerminalRenderer(Renderer):
    def __init__(self, *, width: int = 80, height: int = 24, out: TextIO | None = None) -> None:
        self.width = width
        self.height = height
        self.out = sys.stdout if out is None else out
        self._buffer: list[list[str]] = [[" " for _ in range(width)] for _ in range(height)]
        self._input = InputState()

    def initialize(self, config: Mapping[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self.width = int(cfg.get("width", self.width))
        self.height = int(cfg.get("height", self.height))
        self._buffer = [[" " for _ in range(self.width)] for _ in range(self.height)]

    def render(self, commands: Sequence[RenderCommand]) -> None:
        for raw in commands:
            cmd = normalize_command(raw)
            t = cmd["type"]
            if t == "clear":
                self._clear()
            elif t == "draw_text":
                self._draw_text(cmd.get("text", ""), int(cmd.get("x", 0)), int(cmd.get("y", 0)))
            elif t == "draw_rect":
                self._draw_rect(
                    int(cmd.get("x", 0)),
                    int(cmd.get("y", 0)),
                    int(cmd.get("w", 0)),
                    int(cmd.get("h", 0)),
                )
            elif t == "draw_sprite":
                sprite = str(cmd.get("sprite", "?"))
                self._put(sprite[:1] if sprite else "?", int(cmd.get("x", 0)), int(cmd.get("y", 0)))

        self._flush()

    def get_input(self) -> InputState:
        # Terminal renderer does not capture real-time input.
        return self._input

    def shutdown(self) -> None:
        self._clear()
        self._flush()

    def _clear(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                self._buffer[y][x] = " "

    def _put(self, ch: str, x: int, y: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self._buffer[y][x] = ch

    def _draw_text(self, text: str, x: int, y: int) -> None:
        for i, ch in enumerate(text):
            self._put(ch, x + i, y)

    def _draw_rect(self, x: int, y: int, w: int, h: int) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self._put("#", xx, yy)

    def _flush(self) -> None:
        self.out.write("\n".join("".join(row) for row in self._buffer) + "\n")
        self.out.flush()

