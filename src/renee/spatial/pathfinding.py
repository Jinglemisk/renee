"""A* pathfinding implementation for grid-based movement."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Callable

from renee.types.core import Position
from renee.spatial.grid import Grid


@dataclass(frozen=True, slots=True)
class PathfindingOptions:
    """Options for pathfinding behavior.

    Attributes:
        diagonal: Allow diagonal movement
        max_distance: Maximum search distance (None for unlimited)
        cost_fn: Optional custom cost function (pos, grid) -> float
    """

    diagonal: bool = False
    max_distance: int | None = None
    cost_fn: Callable[[Position, Grid], float] | None = None


def find_path(
    grid: Grid,
    start: Position,
    goal: Position,
    options: PathfindingOptions | None = None,
) -> list[Position] | None:
    """Find a path from start to goal using A* algorithm.

    Args:
        grid: The grid to pathfind on
        start: Starting position
        goal: Goal position
        options: Pathfinding options (default: no diagonals, unlimited distance)

    Returns:
        List of positions forming the path from start to goal (inclusive),
        or None if no path exists.

    Example:
        >>> grid = Grid(10, 10)
        >>> path = find_path(grid, Position(0, 0), Position(5, 5))
        >>> if path:
        ...     print(f"Path length: {len(path)}")
    """
    if options is None:
        options = PathfindingOptions()

    # Early exit if goal is blocked or out of bounds
    if grid.is_blocked(goal) or not grid.in_bounds(goal):
        return None

    # Early exit if start equals goal
    if start == goal:
        return [start]

    # Priority queue: (f_score, counter, position)
    # Counter prevents comparison errors when f_scores are equal
    counter = 0
    open_set: list[tuple[float, int, Position]] = [(0.0, counter, start)]
    counter += 1

    # Track best path to each position
    came_from: dict[Position, Position] = {}

    # Cost from start to each position
    g_score: dict[Position, float] = {start: 0.0}

    # Estimated total cost from start to goal through each position
    f_score: dict[Position, float] = {start: _heuristic(start, goal, options.diagonal)}

    # Set of positions in open_set (for fast membership testing)
    open_set_positions: set[Position] = {start}

    while open_set:
        # Get position with lowest f_score
        _, _, current = heapq.heappop(open_set)
        open_set_positions.discard(current)

        # Check if we reached the goal
        if current == goal:
            return _reconstruct_path(came_from, current)

        # Explore neighbors
        neighbors = grid.get_passable_neighbors(current, diagonal=options.diagonal)

        for neighbor in neighbors:
            # Calculate movement cost
            if options.cost_fn:
                move_cost = options.cost_fn(neighbor, grid)
            else:
                move_cost = grid.get_cost(neighbor)

            # Skip if cost is infinite (blocked)
            if move_cost == float("inf"):
                continue

            # Calculate tentative g_score
            tentative_g_score = g_score[current] + move_cost

            # Check max distance constraint
            if options.max_distance is not None:
                distance = start.manhattan_distance(neighbor)
                if distance > options.max_distance:
                    continue

            # If this path to neighbor is better than previous
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f = tentative_g_score + _heuristic(neighbor, goal, options.diagonal)
                f_score[neighbor] = f

                if neighbor not in open_set_positions:
                    heapq.heappush(open_set, (f, counter, neighbor))
                    counter += 1
                    open_set_positions.add(neighbor)

    # No path found
    return None


def _heuristic(pos: Position, goal: Position, diagonal: bool) -> float:
    """Calculate heuristic distance between two positions.

    Uses Manhattan distance for cardinal movement, Chebyshev for diagonal.

    Args:
        pos: Current position
        goal: Goal position
        diagonal: Whether diagonal movement is allowed

    Returns:
        Estimated distance to goal
    """
    if diagonal:
        # Chebyshev distance for 8-way movement
        return float(pos.chebyshev_distance(goal))
    else:
        # Manhattan distance for 4-way movement
        return float(pos.manhattan_distance(goal))


def _reconstruct_path(came_from: dict[Position, Position], current: Position) -> list[Position]:
    """Reconstruct path from came_from mapping.

    Args:
        came_from: Mapping of position to previous position
        current: End position

    Returns:
        List of positions from start to current (inclusive)
    """
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def get_movement_cost(
    grid: Grid,
    start: Position,
    end: Position,
    options: PathfindingOptions | None = None,
) -> float | None:
    """Calculate the total movement cost from start to end.

    Args:
        grid: The grid to pathfind on
        start: Starting position
        goal: Goal position
        options: Pathfinding options

    Returns:
        Total movement cost, or None if no path exists
    """
    path = find_path(grid, start, end, options)
    if path is None:
        return None

    total_cost = 0.0
    for i in range(len(path) - 1):
        current = path[i]
        next_pos = path[i + 1]
        if options and options.cost_fn:
            total_cost += options.cost_fn(next_pos, grid)
        else:
            total_cost += grid.get_cost(next_pos)

    return total_cost


def get_reachable_positions(
    grid: Grid,
    start: Position,
    max_cost: float,
    diagonal: bool = False,
) -> dict[Position, float]:
    """Get all positions reachable within a movement budget.

    Uses Dijkstra's algorithm to find all positions reachable within max_cost.

    Args:
        grid: The grid to search on
        start: Starting position
        max_cost: Maximum movement cost
        diagonal: Allow diagonal movement

    Returns:
        Dictionary mapping reachable positions to their movement cost from start
    """
    # Priority queue: (cost, counter, position)
    counter = 0
    open_set: list[tuple[float, int, Position]] = [(0.0, counter, start)]
    counter += 1

    # Best cost to reach each position
    costs: dict[Position, float] = {start: 0.0}

    # Positions in open set
    open_set_positions: set[Position] = {start}

    while open_set:
        current_cost, _, current = heapq.heappop(open_set)
        open_set_positions.discard(current)

        # Don't explore beyond max cost
        if current_cost > max_cost:
            continue

        # Explore neighbors
        neighbors = grid.get_passable_neighbors(current, diagonal=diagonal)

        for neighbor in neighbors:
            move_cost = grid.get_cost(neighbor)

            # Skip blocked tiles
            if move_cost == float("inf"):
                continue

            tentative_cost = current_cost + move_cost

            # Only consider if within budget
            if tentative_cost <= max_cost:
                if neighbor not in costs or tentative_cost < costs[neighbor]:
                    costs[neighbor] = tentative_cost

                    if neighbor not in open_set_positions:
                        heapq.heappush(open_set, (tentative_cost, counter, neighbor))
                        counter += 1
                        open_set_positions.add(neighbor)

    return costs
