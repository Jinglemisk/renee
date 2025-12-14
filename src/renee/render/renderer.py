"""Renderer interface."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from renee.input import InputState
from renee.render.commands import RenderCommand


class Renderer(Protocol):
    def initialize(self, config: Mapping[str, Any] | None = None) -> None: ...

    def render(self, commands: Sequence[RenderCommand]) -> None: ...

    def get_input(self) -> InputState: ...

    def shutdown(self) -> None: ...

