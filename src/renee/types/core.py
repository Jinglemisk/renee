"""Core semantic types for Renee.

These types carry meaning beyond Python primitives and enable
validation, documentation, and IDE support.
"""

from dataclasses import dataclass
from typing import NewType, TypeVar

# Entity reference - an int at runtime, but semantically meaningful
EntityId = NewType("EntityId", int)

# Generic type variable for component retrieval
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Position:
    """A position on a 2D grid.

    Immutable to prevent accidental mutation. Use world.add_component()
    with a new Position to move an entity.
    """

    x: int
    y: int

    def __add__(self, other: "Position") -> "Position":
        """Add two positions (vector addition)."""
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Position") -> "Position":
        """Subtract two positions (vector subtraction)."""
        return Position(self.x - other.x, self.y - other.y)

    def manhattan_distance(self, other: "Position") -> int:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def chebyshev_distance(self, other: "Position") -> int:
        """Calculate Chebyshev distance (king's move) to another position."""
        return max(abs(self.x - other.x), abs(self.y - other.y))
