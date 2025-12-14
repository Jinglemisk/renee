"""Area query functions for spatial gameplay."""

from __future__ import annotations

import math
from enum import Enum
from typing import TYPE_CHECKING

from renee.types.core import Position, EntityId

if TYPE_CHECKING:
    from renee.ecs.world import World


class DistanceMetric(Enum):
    """Distance calculation method for area queries."""

    MANHATTAN = "manhattan"  # Taxicab distance (4-way)
    CHEBYSHEV = "chebyshev"  # Chessboard distance (8-way)
    EUCLIDEAN = "euclidean"  # Straight-line distance


def tiles_in_range(
    center: Position,
    range_val: int,
    metric: DistanceMetric | str = DistanceMetric.MANHATTAN,
) -> set[Position]:
    """Get all tiles within a given range of a center position.

    Args:
        center: Center position
        range_val: Maximum distance (inclusive)
        metric: Distance metric to use (manhattan, chebyshev, or euclidean)

    Returns:
        Set of positions within range

    Example:
        >>> tiles = tiles_in_range(Position(5, 5), 2, "manhattan")
        >>> Position(5, 7) in tiles
        True
        >>> Position(7, 7) in tiles
        False
    """
    if isinstance(metric, str):
        metric = DistanceMetric(metric)

    positions: set[Position] = set()

    # Determine search bounds
    if metric == DistanceMetric.EUCLIDEAN:
        # Use bounding box of range
        search_range = range_val
    else:
        search_range = range_val

    # Search in square around center
    for dy in range(-search_range, search_range + 1):
        for dx in range(-search_range, search_range + 1):
            pos = Position(center.x + dx, center.y + dy)

            # Calculate distance based on metric
            if metric == DistanceMetric.MANHATTAN:
                distance = center.manhattan_distance(pos)
            elif metric == DistanceMetric.CHEBYSHEV:
                distance = center.chebyshev_distance(pos)
            else:  # EUCLIDEAN
                distance = center.euclidean_distance(pos)

            if distance <= range_val:
                positions.add(pos)

    return positions


def tiles_in_rectangle(corner1: Position, corner2: Position) -> set[Position]:
    """Get all tiles in a rectangular area.

    Args:
        corner1: One corner of the rectangle
        corner2: Opposite corner of the rectangle

    Returns:
        Set of positions within the rectangle (inclusive)

    Example:
        >>> tiles = tiles_in_rectangle(Position(0, 0), Position(2, 2))
        >>> len(tiles)
        9
    """
    positions: set[Position] = set()

    x1, x2 = min(corner1.x, corner2.x), max(corner1.x, corner2.x)
    y1, y2 = min(corner1.y, corner2.y), max(corner1.y, corner2.y)

    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            positions.add(Position(x, y))

    return positions


def tiles_in_line(start: Position, end: Position) -> list[Position]:
    """Get all tiles along a line between two positions.

    Uses Bresenham's line algorithm.

    Args:
        start: Starting position
        end: Ending position

    Returns:
        List of positions along the line (inclusive)

    Example:
        >>> tiles = tiles_in_line(Position(0, 0), Position(3, 3))
        >>> len(tiles)
        4
    """
    # Import here to avoid circular dependency
    from renee.spatial.visibility import tiles_along_line

    return tiles_along_line(start, end)


def tiles_in_cone(
    origin: Position,
    direction: Position,
    angle_degrees: float,
    distance: int,
) -> set[Position]:
    """Get all tiles in a cone/arc area.

    Args:
        origin: The origin point of the cone
        direction: A position indicating the center direction of the cone
        angle_degrees: Total angle of the cone in degrees (e.g., 90 for a quarter circle)
        distance: Maximum distance of the cone

    Returns:
        Set of positions within the cone

    Example:
        >>> tiles = tiles_in_cone(
        ...     Position(5, 5),
        ...     Position(8, 5),  # Point east
        ...     angle_degrees=90,
        ...     distance=5
        ... )
    """
    positions: set[Position] = set()

    # Calculate the angle of the direction vector
    dx = direction.x - origin.x
    dy = direction.y - origin.y

    if dx == 0 and dy == 0:
        # No direction specified, return just origin
        return {origin}

    # Center angle in radians
    center_angle = math.atan2(dy, dx)

    # Half angle in radians
    half_angle = math.radians(angle_degrees / 2)

    # Check all tiles in range
    for dy in range(-distance, distance + 1):
        for dx in range(-distance, distance + 1):
            if dx == 0 and dy == 0:
                positions.add(origin)
                continue

            pos = Position(origin.x + dx, origin.y + dy)

            # Check distance
            dist = origin.euclidean_distance(pos)
            if dist > distance:
                continue

            # Check angle
            tile_angle = math.atan2(dy, dx)

            # Calculate angle difference (handling wrap-around)
            angle_diff = abs(tile_angle - center_angle)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            if angle_diff <= half_angle:
                positions.add(pos)

    return positions


def entities_at_position(world: World, pos: Position) -> list[EntityId]:
    """Get all entities at a specific position.

    Args:
        world: The game world
        pos: The position to query

    Returns:
        List of entity IDs at the position

    Example:
        >>> entities = entities_at_position(world, Position(5, 5))
    """
    entities: list[EntityId] = []

    # Query all entities with Position component
    for entity_id in world.all_entities():
        entity_pos = world.get_component_or_none(entity_id, Position)
        if entity_pos == pos:
            entities.append(entity_id)

    return entities


def entities_in_range(
    world: World,
    center: Position,
    range_val: int,
    metric: DistanceMetric | str = DistanceMetric.MANHATTAN,
) -> dict[EntityId, Position]:
    """Get all entities within range of a position.

    Args:
        world: The game world
        center: Center position
        range_val: Maximum distance
        metric: Distance metric to use

    Returns:
        Dictionary mapping entity IDs to their positions

    Example:
        >>> entities = entities_in_range(world, Position(5, 5), 3)
    """
    if isinstance(metric, str):
        metric = DistanceMetric(metric)

    entities: dict[EntityId, Position] = {}

    # Query all entities with Position component
    for entity_id in world.all_entities():
        pos = world.get_component_or_none(entity_id, Position)
        if pos is None:
            continue

        # Calculate distance
        if metric == DistanceMetric.MANHATTAN:
            distance = center.manhattan_distance(pos)
        elif metric == DistanceMetric.CHEBYSHEV:
            distance = center.chebyshev_distance(pos)
        else:  # EUCLIDEAN
            distance = center.euclidean_distance(pos)

        if distance <= range_val:
            entities[entity_id] = pos

    return entities


def entities_in_cone(
    world: World,
    origin: Position,
    direction: Position,
    angle_degrees: float,
    distance: int,
) -> dict[EntityId, Position]:
    """Get all entities in a cone area.

    Args:
        world: The game world
        origin: Origin of the cone
        direction: Direction the cone points
        angle_degrees: Angle of the cone
        distance: Maximum distance

    Returns:
        Dictionary mapping entity IDs to their positions

    Example:
        >>> entities = entities_in_cone(
        ...     world,
        ...     Position(5, 5),
        ...     Position(8, 5),
        ...     angle_degrees=90,
        ...     distance=5
        ... )
    """
    # Get tiles in cone
    cone_tiles = tiles_in_cone(origin, direction, angle_degrees, distance)

    entities: dict[EntityId, Position] = {}

    # Query all entities with Position component
    for entity_id in world.all_entities():
        pos = world.get_component_or_none(entity_id, Position)
        if pos is None:
            continue

        if pos in cone_tiles:
            entities[entity_id] = pos

    return entities


def entities_in_rectangle(
    world: World,
    corner1: Position,
    corner2: Position,
) -> dict[EntityId, Position]:
    """Get all entities in a rectangular area.

    Args:
        world: The game world
        corner1: One corner of the rectangle
        corner2: Opposite corner

    Returns:
        Dictionary mapping entity IDs to their positions
    """
    # Get tiles in rectangle
    rect_tiles = tiles_in_rectangle(corner1, corner2)

    entities: dict[EntityId, Position] = {}

    # Query all entities with Position component
    for entity_id in world.all_entities():
        pos = world.get_component_or_none(entity_id, Position)
        if pos is None:
            continue

        if pos in rect_tiles:
            entities[entity_id] = pos

    return entities


def nearest_entity(
    world: World,
    center: Position,
    max_range: int | None = None,
    metric: DistanceMetric | str = DistanceMetric.EUCLIDEAN,
) -> tuple[EntityId, Position, float] | None:
    """Find the nearest entity to a position.

    Args:
        world: The game world
        center: Center position to search from
        max_range: Maximum search range (None for unlimited)
        metric: Distance metric to use

    Returns:
        Tuple of (entity_id, position, distance) or None if no entities found

    Example:
        >>> result = nearest_entity(world, Position(5, 5), max_range=10)
        >>> if result:
        ...     entity_id, pos, dist = result
    """
    if isinstance(metric, str):
        metric = DistanceMetric(metric)

    nearest: tuple[EntityId, Position, float] | None = None
    min_distance = float("inf")

    # Query all entities with Position component
    for entity_id in world.all_entities():
        pos = world.get_component_or_none(entity_id, Position)
        if pos is None:
            continue

        # Calculate distance
        if metric == DistanceMetric.MANHATTAN:
            distance = float(center.manhattan_distance(pos))
        elif metric == DistanceMetric.CHEBYSHEV:
            distance = float(center.chebyshev_distance(pos))
        else:  # EUCLIDEAN
            distance = center.euclidean_distance(pos)

        # Check max range
        if max_range is not None and distance > max_range:
            continue

        # Update nearest
        if distance < min_distance:
            min_distance = distance
            nearest = (entity_id, pos, distance)

    return nearest
