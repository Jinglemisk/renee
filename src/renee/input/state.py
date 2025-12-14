"""Input state shared across renderers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InputState:
    keys_down: set[str] = field(default_factory=set)
    keys_pressed: set[str] = field(default_factory=set)
    mouse_pos: tuple[int, int] | None = None
    mouse_buttons_down: set[int] = field(default_factory=set)
    quit_requested: bool = False

