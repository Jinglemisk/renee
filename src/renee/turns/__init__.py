"""Turn management system for Renee game framework.

Provides flexible, game-defined time structures with support for:
- Hierarchical time units (rounds, turns, phases)
- Multiple turn order strategies (alternating, clockwise, initiative, simultaneous)
- Phase traits (skippable, mandatory, timed, action limits)
- Event hooks for turn/phase/round transitions
"""

from .manager import TurnManager, TurnManagerState
from .structure import TimeStructure, TimeUnit, Phase
from .order import (
    TurnOrderStrategy,
    TurnState,
    AlternatingOrder,
    ClockwiseOrder,
    InitiativeOrder,
    SimultaneousOrder,
    CustomOrder,
)

__all__ = [
    # Manager
    "TurnManager",
    "TurnManagerState",
    # Structure
    "TimeStructure",
    "TimeUnit",
    "Phase",
    # Order strategies
    "TurnOrderStrategy",
    "TurnState",
    "AlternatingOrder",
    "ClockwiseOrder",
    "InitiativeOrder",
    "SimultaneousOrder",
    "CustomOrder",
]
