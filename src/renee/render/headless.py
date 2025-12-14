"""Headless renderer.

Stores the last rendered command list for inspection (tests, simulations).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from renee.input import InputState
from renee.render.commands import RenderCommand, normalize_command
from renee.render.renderer import Renderer


class HeadlessRenderer(Renderer):
    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._last_commands: list[RenderCommand] = []
        self._input: InputState = InputState()

    @property
    def last_commands(self) -> list[RenderCommand]:
        return list(self._last_commands)

    def set_input(self, state: InputState) -> None:
        self._input = state

    def initialize(self, config: Mapping[str, Any] | None = None) -> None:
        self._config = dict(config or {})

    def render(self, commands: Sequence[RenderCommand]) -> None:
        self._last_commands = [normalize_command(c) for c in commands]

    def get_input(self) -> InputState:
        return self._input

    def shutdown(self) -> None:
        self._last_commands = []

