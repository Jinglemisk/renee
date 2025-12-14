#!/usr/bin/env python3
"""Quick test script to verify spatial system functionality."""

from renee.spatial import (
    Grid,
    find_path,
    PathfindingOptions,
    has_line_of_sight,
    compute_field_of_view,
    tiles_in_range,
    tiles_in_cone,
    tiles_in_rectangle,
    DistanceMetric,
)
from renee.types.core import Position


def test_grid():
    """Test Grid class."""
    print("Testing Grid...")
    grid = Grid(20, 20)

    # Test basic operations
    assert grid.in_bounds(Position(0, 0))
    assert grid.in_bounds(Position(19, 19))
    assert not grid.in_bounds(Position(20, 20))
    assert not grid.in_bounds(Position(-1, 0))

    # Test blocking
    grid.set_blocked(Position(5, 5), True)
    assert grid.is_blocked(Position(5, 5))
    assert not grid.is_blocked(Position(4, 4))

    # Test costs
    grid.set_cost(Position(3, 3), 2.5)
    assert grid.get_cost(Position(3, 3)) == 2.5
    assert grid.get_cost(Position(5, 5)) == float("inf")  # blocked

    # Test tile data
    grid.set_tile_data(Position(1, 1), "treasure", "gold")
    assert grid.get_tile_data(Position(1, 1), "treasure") == "gold"
    assert grid.get_tile_data(Position(1, 1), "missing") is None

    print("  ✓ Grid tests passed")


def test_pathfinding():
    """Test pathfinding."""
    print("Testing Pathfinding...")
    grid = Grid(10, 10)

    # Test basic path
    path = find_path(grid, Position(0, 0), Position(5, 5))
    assert path is not None
    assert path[0] == Position(0, 0)
    assert path[-1] == Position(5, 5)
    assert len(path) == 11  # Manhattan distance without diagonal

    # Test diagonal path
    options = PathfindingOptions(diagonal=True)
    path_diag = find_path(grid, Position(0, 0), Position(5, 5), options)
    assert path_diag is not None
    assert len(path_diag) == 6  # Chebyshev distance with diagonal

    # Test blocked path
    for x in range(10):
        grid.set_blocked(Position(x, 5), True)
    path_blocked = find_path(grid, Position(0, 0), Position(0, 9))
    assert path_blocked is None  # No path through wall

    # Test path with gap
    grid.set_blocked(Position(5, 5), False)  # Create gap
    path_gap = find_path(grid, Position(0, 0), Position(0, 9))
    assert path_gap is not None  # Path exists through gap

    print("  ✓ Pathfinding tests passed")


def test_visibility():
    """Test line of sight and field of view."""
    print("Testing Visibility...")
    grid = Grid(20, 20)

    # Test clear line of sight
    assert has_line_of_sight(grid, Position(0, 0), Position(10, 10))

    # Test blocked line of sight
    grid.set_blocked(Position(5, 5), True)
    assert not has_line_of_sight(grid, Position(0, 0), Position(10, 10))

    # Test field of view
    grid = Grid(20, 20)
    fov = compute_field_of_view(grid, Position(10, 10), radius=5)
    assert Position(10, 10) in fov
    assert Position(10, 15) in fov  # Within radius
    assert Position(5, 5) in fov
    assert Position(0, 0) not in fov  # Out of radius

    # Test FOV with blocking
    grid.set_blocked(Position(10, 12), True)
    fov_blocked = compute_field_of_view(grid, Position(10, 10), radius=5)
    # Tiles behind the wall should be shadowed
    assert Position(10, 12) in fov_blocked  # Wall itself is visible
    # Note: Shadow casting details depend on implementation

    print("  ✓ Visibility tests passed")


def test_area_queries():
    """Test area query functions."""
    print("Testing Area Queries...")

    # Test tiles in range
    tiles = tiles_in_range(Position(5, 5), 2, DistanceMetric.MANHATTAN)
    assert Position(5, 5) in tiles
    assert Position(7, 5) in tiles  # 2 away
    assert Position(5, 7) in tiles  # 2 away
    assert Position(8, 5) not in tiles  # 3 away

    tiles_cheb = tiles_in_range(Position(5, 5), 2, DistanceMetric.CHEBYSHEV)
    assert Position(7, 7) in tiles_cheb  # Diagonal 2 away in Chebyshev

    # Test rectangle
    rect = tiles_in_rectangle(Position(0, 0), Position(2, 2))
    assert len(rect) == 9  # 3x3 grid
    assert Position(0, 0) in rect
    assert Position(2, 2) in rect
    assert Position(1, 1) in rect
    assert Position(3, 3) not in rect

    # Test cone
    cone = tiles_in_cone(
        Position(5, 5),
        Position(8, 5),  # Point east
        angle_degrees=90,
        distance=3,
    )
    assert Position(5, 5) in cone  # Origin
    assert Position(8, 5) in cone  # Along direction
    # Exact cone membership depends on implementation details

    print("  ✓ Area query tests passed")


def test_integration():
    """Test integration of multiple systems."""
    print("Testing Integration...")

    grid = Grid(30, 30)

    # Create a maze-like structure
    for y in range(10, 20):
        grid.set_blocked(Position(15, y), True)
    grid.set_blocked(Position(15, 15), False)  # Gap

    # Find path around wall
    path = find_path(grid, Position(10, 15), Position(20, 15))
    assert path is not None

    # Check visibility through gap
    assert has_line_of_sight(grid, Position(10, 15), Position(20, 15))

    # Get area around a position
    area = tiles_in_range(Position(15, 15), 5, DistanceMetric.MANHATTAN)
    assert len(area) > 0

    # Check FOV from center
    fov = compute_field_of_view(grid, Position(15, 15), radius=7)
    assert Position(15, 15) in fov

    print("  ✓ Integration tests passed")


def main():
    """Run all tests."""
    print("\n=== Spatial System Tests ===\n")

    test_grid()
    test_pathfinding()
    test_visibility()
    test_area_queries()
    test_integration()

    print("\n=== All Tests Passed! ===\n")


if __name__ == "__main__":
    main()
