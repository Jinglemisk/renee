"""Spatial reasoning utilities for Renee.

Provides grid management, pathfinding, line-of-sight, and area queries
for turn-based games on 2D tile grids.
"""

from renee.spatial.grid import Grid
from renee.spatial.pathfinding import find_path, PathfindingOptions
from renee.spatial.visibility import (
    has_line_of_sight,
    compute_field_of_view,
    tiles_along_line,
)
from renee.spatial.area import (
    tiles_in_range,
    tiles_in_cone,
    tiles_in_rectangle,
    tiles_in_line,
    entities_at_position,
    entities_in_range,
    DistanceMetric,
)

__all__ = [
    # Grid
    "Grid",
    # Pathfinding
    "find_path",
    "PathfindingOptions",
    # Visibility
    "has_line_of_sight",
    "compute_field_of_view",
    "tiles_along_line",
    # Area queries
    "tiles_in_range",
    "tiles_in_cone",
    "tiles_in_rectangle",
    "tiles_in_line",
    "entities_at_position",
    "entities_in_range",
    "DistanceMetric",
]
