"""Grid utilities for turn-based games.

The Grid stores blocked tiles and provides common algorithms:
- A* pathfinding (4-way)
- Line-of-sight (Bresenham)
- Area queries (Manhattan range)
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from typing import Iterable, Iterator

from renee.types import Position


@dataclass(frozen=True, slots=True)
class GridSize:
    width: int
    height: int

    def contains(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height


class Grid:
    def __init__(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Grid width/height must be > 0")
        self.size = GridSize(width=width, height=height)
        self._blocked: set[tuple[int, int]] = set()

    def in_bounds(self, pos: Position) -> bool:
        return self.size.contains(pos)

    def is_blocked(self, pos: Position) -> bool:
        return (pos.x, pos.y) in self._blocked

    def set_blocked(self, pos: Position, blocked: bool = True) -> None:
        if not self.in_bounds(pos):
            raise ValueError(f"Position out of bounds: {pos}")
        key = (pos.x, pos.y)
        if blocked:
            self._blocked.add(key)
        else:
            self._blocked.discard(key)

    def neighbors4(self, pos: Position) -> Iterator[Position]:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = Position(pos.x + dx, pos.y + dy)
            if self.in_bounds(n) and not self.is_blocked(n):
                yield n

    def a_star(self, start: Position, goal: Position) -> list[Position]:
        """Compute a 4-way A* path including start and goal.

        Returns empty list if no path exists.
        """

        if not self.in_bounds(start) or not self.in_bounds(goal):
            raise ValueError("Start/goal must be within grid bounds")
        if self.is_blocked(start) or self.is_blocked(goal):
            return []
        if start == goal:
            return [start]

        frontier: list[tuple[int, int, Position]] = []
        heapq.heappush(frontier, (0, 0, start))
        came_from: dict[Position, Position | None] = {start: None}
        cost_so_far: dict[Position, int] = {start: 0}
        tie = 0

        while frontier:
            _priority, _tie, current = heapq.heappop(frontier)
            if current == goal:
                break

            for nxt in self.neighbors4(current):
                new_cost = cost_so_far[current] + 1
                if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                    cost_so_far[nxt] = new_cost
                    priority = new_cost + nxt.manhattan_distance(goal)
                    tie += 1
                    heapq.heappush(frontier, (priority, tie, nxt))
                    came_from[nxt] = current

        if goal not in came_from:
            return []

        path: list[Position] = []
        cur: Position | None = goal
        while cur is not None:
            path.append(cur)
            cur = came_from[cur]
        path.reverse()
        return path

    def line_of_sight(self, a: Position, b: Position) -> bool:
        """True if the line from a→b does not pass through blocked tiles."""

        for p in bresenham(a, b):
            if p == a or p == b:
                continue
            if not self.in_bounds(p):
                return False
            if self.is_blocked(p):
                return False
        return True

    def tiles_in_manhattan_range(self, center: Position, distance: int) -> list[Position]:
        if distance < 0:
            raise ValueError("distance must be >= 0")
        tiles: list[Position] = []
        for dx in range(-distance, distance + 1):
            remaining = distance - abs(dx)
            for dy in range(-remaining, remaining + 1):
                p = Position(center.x + dx, center.y + dy)
                if self.in_bounds(p):
                    tiles.append(p)
        return tiles

    def entities_at(
        self,
        *,
        world: AnyWorld,
        pos: Position,
        position_component: type = Position,
    ) -> list[object]:
        """Return entities with a Position component matching pos."""

        return [
            e
            for e in world.query(position_component)  # type: ignore[arg-type]
            if world.get_component(e, position_component) == pos  # type: ignore[arg-type]
        ]


class AnyWorld:
    def query(self, *component_types: type, tags: set[str] | None = None) -> Iterable[object]: ...

    def get_component(self, entity: object, component_type: type) -> object: ...


def bresenham(a: Position, b: Position) -> Iterator[Position]:
    """Yield tiles along a line from a to b (inclusive)."""

    x0, y0 = a.x, a.y
    x1, y1 = b.x, b.y

    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    while True:
        yield Position(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy

