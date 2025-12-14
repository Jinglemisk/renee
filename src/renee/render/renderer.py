"""Base Renderer interface for the Renee rendering system.

This module defines the abstract Renderer interface and InputState dataclass.
All concrete renderers (headless, terminal, pygame) implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from renee.render.commands import RenderCommand


@dataclass
class InputState:
    """Current state of user input.

    Tracks keyboard keys, mouse position, and mouse buttons.
    This is a snapshot of the input state at a specific moment.
    """

    keys_pressed: set[str] = field(default_factory=set)
    keys_just_pressed: set[str] = field(default_factory=set)
    keys_just_released: set[str] = field(default_factory=set)
    mouse_x: int = 0
    mouse_y: int = 0
    mouse_buttons: set[int] = field(default_factory=set)
    mouse_just_pressed: set[int] = field(default_factory=set)
    mouse_just_released: set[int] = field(default_factory=set)


class Renderer(ABC):
    """Abstract base class for all renderers.

    Renderers interpret render commands and display them using
    a specific backend (terminal, pygame, headless, etc.).
    """

    @abstractmethod
    def initialize(self, config: dict) -> None:
        """Setup renderer (create window, load assets, etc.).

        Args:
            config: Renderer-specific configuration dictionary.
                   Common keys: width, height, title, fps.
        """
        pass

    @abstractmethod
    def render(self, commands: list[RenderCommand]) -> None:
        """Process and execute render commands.

        Args:
            commands: List of render commands to execute.
                     Commands are typically sorted by layer before rendering.
        """
        pass

    @abstractmethod
    def get_input(self) -> InputState:
        """Get current input state.

        Returns:
            InputState object containing keyboard and mouse state.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup resources and close renderer.

        Should be called when the game ends or renderer is no longer needed.
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if renderer is still running (e.g., window not closed).

        Returns:
            True if renderer is active, False otherwise.
        """
        pass
