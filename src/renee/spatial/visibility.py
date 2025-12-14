"""Line-of-sight and field-of-view calculations."""

from __future__ import annotations

from renee.types.core import Position
from renee.spatial.grid import Grid


def has_line_of_sight(
    grid: Grid,
    start: Position,
    end: Position,
    ignore_start: bool = True,
    ignore_end: bool = True,
) -> bool:
    """Check if there is an unobstructed line of sight between two positions.

    Uses Bresenham's line algorithm to trace a line between positions.

    Args:
        grid: The grid to check
        start: Starting position
        end: Ending position
        ignore_start: Don't check if start position is blocked
        ignore_end: Don't check if end position is blocked

    Returns:
        True if line of sight is clear, False if blocked or out of bounds

    Example:
        >>> grid = Grid(10, 10)
        >>> grid.set_blocked(Position(5, 5), True)
        >>> has_line_of_sight(grid, Position(0, 0), Position(9, 9))
        False
    """
    # Get all positions along the line
    line = tiles_along_line(start, end)

    # Check each position
    for i, pos in enumerate(line):
        # Skip start/end if requested
        if ignore_start and i == 0:
            continue
        if ignore_end and i == len(line) - 1:
            continue

        # Check if position blocks sight
        if not grid.in_bounds(pos) or grid.is_blocked(pos):
            return False

    return True


def tiles_along_line(start: Position, end: Position) -> list[Position]:
    """Get all tile positions along a line between two points.

    Uses Bresenham's line algorithm for accurate grid-based line drawing.

    Args:
        start: Starting position
        end: Ending position

    Returns:
        List of positions along the line (inclusive of start and end)

    Example:
        >>> tiles = tiles_along_line(Position(0, 0), Position(3, 3))
        >>> len(tiles)
        4
    """
    positions: list[Position] = []

    x0, y0 = start.x, start.y
    x1, y1 = end.x, end.y

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    err = dx - dy

    x, y = x0, y0

    while True:
        positions.append(Position(x, y))

        if x == x1 and y == y1:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x += sx

        if e2 < dx:
            err += dx
            y += sy

    return positions


def compute_field_of_view(
    grid: Grid,
    origin: Position,
    radius: int,
    include_origin: bool = True,
) -> set[Position]:
    """Compute field of view from a position using shadow casting.

    Returns all tiles visible from the origin within the given radius,
    accounting for blocking terrain.

    Args:
        grid: The grid to compute FOV on
        origin: The viewing position
        radius: Maximum viewing distance
        include_origin: Whether to include origin in result

    Returns:
        Set of visible positions

    Example:
        >>> grid = Grid(20, 20)
        >>> visible = compute_field_of_view(grid, Position(10, 10), radius=5)
        >>> len(visible) > 0
        True
    """
    visible: set[Position] = set()

    if include_origin:
        visible.add(origin)

    # Cast shadows in 8 octants
    for octant in range(8):
        _cast_light(
            grid=grid,
            origin=origin,
            radius=radius,
            visible=visible,
            octant=octant,
            start_slope=1.0,
            end_slope=0.0,
            row=1,
        )

    return visible


def _cast_light(
    grid: Grid,
    origin: Position,
    radius: int,
    visible: set[Position],
    octant: int,
    start_slope: float,
    end_slope: float,
    row: int,
) -> None:
    """Recursive shadow casting helper.

    Args:
        grid: The grid
        origin: Viewing position
        radius: Max viewing distance
        visible: Set to add visible positions to
        octant: Current octant (0-7)
        start_slope: Starting slope of visibility
        end_slope: Ending slope of visibility
        row: Current row being processed
    """
    if start_slope < end_slope:
        return

    # Process tiles in this row
    for col in range(row, radius + 1):
        # Check if this column is out of range for this row
        if col > row:
            # Check if slope is still valid
            left_slope = (col - 0.5) / (row + 0.5)
            right_slope = (col + 0.5) / (row - 0.5)

            if start_slope < right_slope:
                continue
            if end_slope > left_slope:
                break

        # Transform to grid coordinates based on octant
        pos = _transform_octant(origin, row, col, octant)

        # Check if in bounds
        if not grid.in_bounds(pos):
            continue

        # Check if within radius (using Chebyshev distance)
        if origin.chebyshev_distance(pos) > radius:
            continue

        # Calculate slopes for this tile
        left_slope = (col - 0.5) / (row + 0.5)
        right_slope = (col + 0.5) / (row - 0.5)

        # If tile is visible, add it
        if start_slope >= left_slope and end_slope <= right_slope:
            visible.add(pos)

        # If tile is blocked, update slopes
        if grid.is_blocked(pos):
            # Previous tile was open
            if row > 1:  # Don't recurse on first row
                _cast_light(
                    grid=grid,
                    origin=origin,
                    radius=radius,
                    visible=visible,
                    octant=octant,
                    start_slope=start_slope,
                    end_slope=right_slope,
                    row=row + 1,
                )
            start_slope = left_slope


def _transform_octant(origin: Position, row: int, col: int, octant: int) -> Position:
    """Transform row/col to grid position based on octant.

    Args:
        origin: Origin position
        row: Row in octant space
        col: Column in octant space
        octant: Octant number (0-7)

    Returns:
        Transformed position
    """
    if octant == 0:
        return Position(origin.x + col, origin.y - row)
    elif octant == 1:
        return Position(origin.x + row, origin.y - col)
    elif octant == 2:
        return Position(origin.x + row, origin.y + col)
    elif octant == 3:
        return Position(origin.x + col, origin.y + row)
    elif octant == 4:
        return Position(origin.x - col, origin.y + row)
    elif octant == 5:
        return Position(origin.x - row, origin.y + col)
    elif octant == 6:
        return Position(origin.x - row, origin.y - col)
    else:  # octant == 7
        return Position(origin.x - col, origin.y - row)


def compute_light_level(
    grid: Grid,
    light_source: Position,
    target: Position,
    max_range: int,
    falloff: float = 1.0,
) -> float:
    """Calculate light level at a position from a light source.

    Args:
        grid: The grid
        light_source: Position of the light source
        target: Position to calculate light level at
        max_range: Maximum range of the light
        falloff: Light falloff rate (1.0 = linear, 2.0 = quadratic)

    Returns:
        Light level from 0.0 (no light) to 1.0 (full brightness)
    """
    # Check if target is within range
    distance = light_source.euclidean_distance(target)
    if distance > max_range:
        return 0.0

    # Check line of sight
    if not has_line_of_sight(grid, light_source, target):
        return 0.0

    # Calculate light level with falloff
    if distance == 0:
        return 1.0

    intensity = 1.0 - (distance / max_range) ** falloff
    return max(0.0, min(1.0, intensity))
