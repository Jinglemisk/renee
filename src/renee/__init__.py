"""Renee: An AI-native turn-based game framework.

Core exports for easy access to fundamental types and systems.
"""

from renee.actions import ActionPipeline
from renee.events import EventBus
from renee.ecs.world import World
from renee.rules import RuleEngine
from renee.schema import SchemaRegistry
from renee.spatial import Grid
from renee.turns import TurnManager
from renee.types import EntityId, Position

__version__ = "0.1.0"

__all__ = [
    "ActionPipeline",
    "EventBus",
    "Grid",
    "RuleEngine",
    "SchemaRegistry",
    "TurnManager",
    "World",
    "EntityId",
    "Position",
    "__version__",
]
