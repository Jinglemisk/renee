"""Renee: An AI-native turn-based game framework.

Core exports for easy access to fundamental types and systems.

Example (simple mode using Game orchestrator):
    from renee import Game, GameConfig

    config = GameConfig(title="My Game")
    game = Game(config)

    @game.on_start
    def setup():
        player = game.world.create_entity()
        # ...

    game.run()

Example (advanced mode using primitives):
    from renee import World, ActionPipeline, EventBus, RuleEngine

    world = World()
    bus = EventBus()
    rules = RuleEngine()
    pipeline = ActionPipeline(world=world, bus=bus, rules=rules)
"""

# Core types
from renee.types import EntityId, Position

# ECS
from renee.ecs.world import World

# Subsystems
from renee.actions import ActionPipeline
from renee.events import EventBus
from renee.rules import RuleEngine
from renee.rules.engine import rule
from renee.schema import SchemaRegistry
from renee.spatial import Grid
from renee.turns import TurnManager

# Game orchestrator
from renee.game import Game, GameConfig, GameState, GameMode

# Errors
from renee.errors import ReneeError

__version__ = "0.1.0"

__all__ = [
    # Core types
    "EntityId",
    "Position",
    # ECS
    "World",
    # Subsystems
    "ActionPipeline",
    "EventBus",
    "RuleEngine",
    "SchemaRegistry",
    "TurnManager",
    "Grid",
    # Game orchestrator
    "Game",
    "GameConfig",
    "GameState",
    "GameMode",
    # Decorators
    "rule",
    # Errors
    "ReneeError",
    # Version
    "__version__",
]
