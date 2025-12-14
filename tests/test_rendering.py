"""Tests for render commands and headless/terminal renderers."""

from __future__ import annotations

import io

from renee.render import Clear, DrawRect, DrawText, HeadlessRenderer, TerminalRenderer


class TestRendering:
    def test_headless_renderer_stores_commands(self) -> None:
        r = HeadlessRenderer()
        r.initialize()
        r.render([Clear(), DrawText("hi", 1, 1), DrawRect(0, 0, 2, 1)])
        cmds = r.last_commands
        assert cmds[0]["type"] == "clear"
        assert cmds[1]["type"] == "draw_text"
        assert cmds[2]["type"] == "draw_rect"

    def test_terminal_renderer_writes_buffer(self) -> None:
        out = io.StringIO()
        r = TerminalRenderer(width=10, height=3, out=out)
        r.initialize()
        r.render([Clear(), DrawText("hi", 1, 1)])
        text = out.getvalue()
        assert "hi" in text

