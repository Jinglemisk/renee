"""Renee: An AI-native turn-based game framework.

Core exports for easy access to fundamental types and systems.
"""

from renee.ecs.world import World
from renee.types import EntityId, Position

__version__ = "0.1.0"

__all__ = [
    "World",
    "EntityId",
    "Position",
    "__version__",
]
