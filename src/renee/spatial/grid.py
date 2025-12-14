"""Grid data structure for 2D tile-based games."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from renee.types.core import Position


@dataclass(slots=True)
class Tile:
    """Represents a single tile on the grid."""

    position: Position
    blocked: bool = False
    cost: float = 1.0
    data: dict[str, Any] = field(default_factory=dict)


class Grid:
    """A 2D grid for tile-based games.

    Manages tile properties including passability, movement costs,
    and arbitrary tile data. Supports pathfinding and spatial queries.

    Example:
        >>> grid = Grid(20, 20)
        >>> grid.set_blocked(Position(5, 5), True)
        >>> grid.get_cost(Position(3, 3))
        1.0
    """

    def __init__(self, width: int, height: int, default_cost: float = 1.0) -> None:
        """Initialize a grid with the given dimensions.

        Args:
            width: Width of the grid in tiles
            height: Height of the grid in tiles
            default_cost: Default movement cost for tiles (default: 1.0)

        Raises:
            ValueError: If width or height is less than 1
        """
        if width < 1 or height < 1:
            raise ValueError(f"Grid dimensions must be at least 1x1, got {width}x{height}")

        self.width = width
        self.height = height
        self._default_cost = default_cost

        # Initialize grid with tiles
        self._tiles: dict[Position, Tile] = {}
        for y in range(height):
            for x in range(width):
                pos = Position(x, y)
                self._tiles[pos] = Tile(position=pos, cost=default_cost)

    def in_bounds(self, pos: Position) -> bool:
        """Check if a position is within grid bounds.

        Args:
            pos: The position to check

        Returns:
            True if position is within bounds, False otherwise
        """
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def is_blocked(self, pos: Position) -> bool:
        """Check if a tile is blocked (impassable).

        Args:
            pos: The position to check

        Returns:
            True if blocked or out of bounds, False if passable
        """
        if not self.in_bounds(pos):
            return True
        return self._tiles[pos].blocked

    def set_blocked(self, pos: Position, blocked: bool) -> None:
        """Set whether a tile is blocked.

        Args:
            pos: The position to modify
            blocked: Whether the tile should be blocked

        Raises:
            ValueError: If position is out of bounds
        """
        if not self.in_bounds(pos):
            raise ValueError(f"Position {pos} is out of bounds for grid {self.width}x{self.height}")
        self._tiles[pos].blocked = blocked

    def get_cost(self, pos: Position) -> float:
        """Get the movement cost for a tile.

        Args:
            pos: The position to query

        Returns:
            Movement cost (default: 1.0), or infinity if blocked or out of bounds
        """
        if not self.in_bounds(pos):
            return float("inf")
        tile = self._tiles[pos]
        if tile.blocked:
            return float("inf")
        return tile.cost

    def set_cost(self, pos: Position, cost: float) -> None:
        """Set the movement cost for a tile.

        Args:
            pos: The position to modify
            cost: The movement cost (must be positive)

        Raises:
            ValueError: If position is out of bounds or cost is negative
        """
        if not self.in_bounds(pos):
            raise ValueError(f"Position {pos} is out of bounds for grid {self.width}x{self.height}")
        if cost < 0:
            raise ValueError(f"Movement cost must be non-negative, got {cost}")
        self._tiles[pos].cost = cost

    def get_tile_data(self, pos: Position, key: str, default: Any = None) -> Any:
        """Get arbitrary data associated with a tile.

        Args:
            pos: The position to query
            key: The data key
            default: Default value if key not found

        Returns:
            The data value, or default if not found

        Raises:
            ValueError: If position is out of bounds
        """
        if not self.in_bounds(pos):
            raise ValueError(f"Position {pos} is out of bounds for grid {self.width}x{self.height}")
        return self._tiles[pos].data.get(key, default)

    def set_tile_data(self, pos: Position, key: str, value: Any) -> None:
        """Set arbitrary data on a tile.

        Args:
            pos: The position to modify
            key: The data key
            value: The value to set

        Raises:
            ValueError: If position is out of bounds
        """
        if not self.in_bounds(pos):
            raise ValueError(f"Position {pos} is out of bounds for grid {self.width}x{self.height}")
        self._tiles[pos].data[key] = value

    def clear_tile_data(self, pos: Position, key: str) -> None:
        """Clear a data key from a tile.

        Args:
            pos: The position to modify
            key: The data key to remove

        Raises:
            ValueError: If position is out of bounds
        """
        if not self.in_bounds(pos):
            raise ValueError(f"Position {pos} is out of bounds for grid {self.width}x{self.height}")
        self._tiles[pos].data.pop(key, None)

    def get_tile(self, pos: Position) -> Tile | None:
        """Get the tile at a position.

        Args:
            pos: The position to query

        Returns:
            The tile, or None if out of bounds
        """
        if not self.in_bounds(pos):
            return None
        return self._tiles[pos]

    def iter_tiles(self) -> Iterator[Tile]:
        """Iterate over all tiles in the grid.

        Yields:
            Tile objects in row-major order (top to bottom, left to right)
        """
        for y in range(self.height):
            for x in range(self.width):
                yield self._tiles[Position(x, y)]

    def iter_region(self, top_left: Position, bottom_right: Position) -> Iterator[Tile]:
        """Iterate over tiles in a rectangular region.

        Args:
            top_left: Top-left corner of the region
            bottom_right: Bottom-right corner of the region (inclusive)

        Yields:
            Tile objects in the specified region
        """
        # Clamp to grid bounds
        x1 = max(0, top_left.x)
        y1 = max(0, top_left.y)
        x2 = min(self.width - 1, bottom_right.x)
        y2 = min(self.height - 1, bottom_right.y)

        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                yield self._tiles[Position(x, y)]

    def get_passable_neighbors(self, pos: Position, diagonal: bool = False) -> list[Position]:
        """Get all passable neighboring positions.

        Args:
            pos: The center position
            diagonal: Whether to include diagonal neighbors

        Returns:
            List of passable neighboring positions
        """
        neighbors = pos.neighbors(diagonal=diagonal)
        return [n for n in neighbors if not self.is_blocked(n)]

    def clear(self, default_cost: float | None = None) -> None:
        """Reset all tiles to default state.

        Args:
            default_cost: Optional new default cost (uses current if None)
        """
        if default_cost is not None:
            self._default_cost = default_cost

        for tile in self._tiles.values():
            tile.blocked = False
            tile.cost = self._default_cost
            tile.data.clear()

    def __repr__(self) -> str:
        """String representation of the grid."""
        return f"Grid(width={self.width}, height={self.height})"
