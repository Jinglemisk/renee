#!/usr/bin/env python3
"""Example usage of Renee's spatial reasoning system.

This demonstrates the complete spatial API for turn-based games.
"""

from renee.spatial import (
    Grid,
    find_path,
    PathfindingOptions,
    has_line_of_sight,
    compute_field_of_view,
    tiles_in_range,
    tiles_in_cone,
    tiles_in_rectangle,
    entities_at_position,
    entities_in_range,
    DistanceMetric,
)
from renee.types.core import Position
from renee.ecs.world import World


def example_grid_basics():
    """Basic grid operations."""
    print("\n=== Grid Basics ===")

    # Create a 20x20 grid
    grid = Grid(20, 20)

    # Mark some tiles as blocked (walls)
    grid.set_blocked(Position(5, 5), True)
    grid.set_blocked(Position(5, 6), True)
    grid.set_blocked(Position(5, 7), True)

    # Check if tiles are blocked
    print(f"Position(5, 5) blocked: {grid.is_blocked(Position(5, 5))}")
    print(f"Position(6, 5) blocked: {grid.is_blocked(Position(6, 5))}")

    # Set terrain costs for weighted pathfinding
    grid.set_cost(Position(10, 10), 2.0)  # Difficult terrain
    grid.set_cost(Position(11, 10), 3.0)  # Very difficult terrain

    # Store arbitrary data on tiles
    grid.set_tile_data(Position(15, 15), "treasure", "gold coins")
    treasure = grid.get_tile_data(Position(15, 15), "treasure")
    print(f"Found treasure: {treasure}")

    # Get passable neighbors
    neighbors = grid.get_passable_neighbors(Position(5, 5), diagonal=True)
    print(f"Passable neighbors of (5,5): {len(neighbors)}")


def example_pathfinding():
    """Pathfinding examples."""
    print("\n=== Pathfinding ===")

    grid = Grid(20, 20)

    # Create a wall
    for x in range(5, 15):
        grid.set_blocked(Position(x, 10), True)

    # Create a gap in the wall
    grid.set_blocked(Position(10, 10), False)

    # Find path (cardinal directions only)
    start = Position(5, 5)
    goal = Position(5, 15)
    path = find_path(grid, start, goal)

    if path:
        print(f"Path found: {len(path)} steps")
        print(f"First 5 steps: {path[:5]}")
    else:
        print("No path found")

    # Find path with diagonal movement
    options = PathfindingOptions(diagonal=True)
    path_diag = find_path(grid, start, goal, options)
    if path_diag:
        print(f"Diagonal path: {len(path_diag)} steps")

    # Find path with maximum distance constraint
    options_limited = PathfindingOptions(max_distance=10)
    path_limited = find_path(grid, start, Position(19, 19), options_limited)
    if path_limited:
        print(f"Limited range path: {len(path_limited)} steps")
    else:
        print("Goal too far away")


def example_visibility():
    """Line of sight and field of view examples."""
    print("\n=== Visibility ===")

    grid = Grid(30, 30)

    # Place some walls
    for y in range(10, 20):
        grid.set_blocked(Position(15, y), True)

    # Check line of sight
    observer = Position(10, 15)
    target1 = Position(14, 15)  # Before wall
    target2 = Position(16, 15)  # Behind wall

    los1 = has_line_of_sight(grid, observer, target1)
    los2 = has_line_of_sight(grid, observer, target2)

    print(f"Can see target1: {los1}")
    print(f"Can see target2: {los2}")

    # Compute field of view
    fov = compute_field_of_view(grid, observer, radius=8)
    print(f"Tiles visible from observer: {len(fov)}")

    # Check specific tiles
    print(f"(10,15) visible: {Position(10, 15) in fov}")
    print(f"(14,15) visible: {Position(14, 15) in fov}")
    print(f"(16,15) visible: {Position(16, 15) in fov}")


def example_area_queries():
    """Area query examples."""
    print("\n=== Area Queries ===")

    # Tiles in range (Manhattan distance)
    center = Position(10, 10)
    tiles_manhattan = tiles_in_range(center, 3, DistanceMetric.MANHATTAN)
    print(f"Tiles in Manhattan range 3: {len(tiles_manhattan)}")

    # Tiles in range (Chebyshev distance - king's move)
    tiles_chebyshev = tiles_in_range(center, 3, DistanceMetric.CHEBYSHEV)
    print(f"Tiles in Chebyshev range 3: {len(tiles_chebyshev)}")

    # Rectangular area
    corner1 = Position(5, 5)
    corner2 = Position(10, 10)
    rect_tiles = tiles_in_rectangle(corner1, corner2)
    print(f"Tiles in rectangle: {len(rect_tiles)}")

    # Cone/arc area (e.g., for breath weapon or cone of fire)
    origin = Position(10, 10)
    direction = Position(15, 10)  # Point east
    cone_tiles = tiles_in_cone(origin, direction, angle_degrees=90, distance=5)
    print(f"Tiles in 90° cone: {len(cone_tiles)}")


def example_entity_queries():
    """Entity query examples."""
    print("\n=== Entity Queries ===")

    # Create world and entities
    world = World()

    # Create some entities with positions
    player = world.create_entity()
    world.add_component(player, Position(10, 10))

    enemy1 = world.create_entity()
    world.add_component(enemy1, Position(12, 10))

    enemy2 = world.create_entity()
    world.add_component(enemy2, Position(10, 15))

    enemy3 = world.create_entity()
    world.add_component(enemy3, Position(20, 20))

    # Find entities at specific position
    at_pos = entities_at_position(world, Position(10, 10))
    print(f"Entities at (10,10): {len(at_pos)}")

    # Find entities in range
    nearby = entities_in_range(world, Position(10, 10), 5, DistanceMetric.MANHATTAN)
    print(f"Entities within range 5: {len(nearby)}")

    # Find entities in cone (e.g., for area-of-effect abilities)
    in_cone = tiles_in_cone(
        Position(10, 10),
        Position(15, 10),  # Point east
        angle_degrees=90,
        distance=10,
    )
    print(f"Tiles in cone: {len(in_cone)}")


def example_tactical_combat():
    """Complete tactical combat example."""
    print("\n=== Tactical Combat Example ===")

    # Setup arena
    grid = Grid(25, 25)

    # Create pillars (blocking terrain)
    pillars = [
        Position(8, 8),
        Position(16, 8),
        Position(8, 16),
        Position(16, 16),
    ]
    for pillar in pillars:
        grid.set_blocked(pillar, True)

    # Create entities
    world = World()

    archer = world.create_entity()
    world.add_component(archer, Position(5, 5))

    enemy = world.create_entity()
    world.add_component(enemy, Position(20, 20))

    # Check if archer can see enemy
    archer_pos = world.get_component(archer, Position)
    enemy_pos = world.get_component(enemy, Position)

    can_see = has_line_of_sight(grid, archer_pos, enemy_pos)
    print(f"Archer can see enemy: {can_see}")

    # Calculate movement range
    movement_range = 5
    reachable = tiles_in_range(archer_pos, movement_range, DistanceMetric.MANHATTAN)
    print(f"Archer can move to {len(reachable)} tiles")

    # Find path to get closer to enemy
    # Try to get within attack range (7 tiles)
    attack_range_tiles = tiles_in_range(enemy_pos, 7, DistanceMetric.EUCLIDEAN)
    # Find closest tile in attack range that archer can reach
    for tile in reachable:
        if tile in attack_range_tiles:
            path = find_path(grid, archer_pos, tile)
            if path:
                print(f"Found path to attack position: {len(path)} steps to {tile}")
                break

    # Get archer's field of view
    fov = compute_field_of_view(grid, archer_pos, radius=10)
    print(f"Archer can see {len(fov)} tiles")

    # Check if enemy is in vision
    if enemy_pos in fov:
        print("Enemy is visible!")

    # Simulate area attack (fireball)
    fireball_center = Position(20, 20)
    affected_area = tiles_in_range(fireball_center, 2, DistanceMetric.EUCLIDEAN)
    affected_entities = []
    for entity_id in world.all_entities():
        pos = world.get_component_or_none(entity_id, Position)
        if pos and pos in affected_area:
            affected_entities.append(entity_id)
    print(f"Fireball would hit {len(affected_entities)} entities")


def main():
    """Run all examples."""
    print("=" * 60)
    print("RENEE SPATIAL SYSTEM EXAMPLES")
    print("=" * 60)

    example_grid_basics()
    example_pathfinding()
    example_visibility()
    example_area_queries()
    example_entity_queries()
    example_tactical_combat()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
