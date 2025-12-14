# Renee Spatial System

Complete spatial reasoning utilities for turn-based games on 2D tile grids.

## Overview

The spatial module provides:

- **Grid**: 2D tile map with blocking, costs, and arbitrary tile data
- **Pathfinding**: A* pathfinding with support for diagonal movement and weighted terrain
- **Visibility**: Line-of-sight and field-of-view calculations
- **Area Queries**: Range, cone, rectangle, and line area queries
- **Entity Queries**: Spatial queries integrated with the ECS world

## Quick Start

```python
from renee.spatial import Grid, find_path, has_line_of_sight, tiles_in_range
from renee.types.core import Position

# Create a grid
grid = Grid(20, 20)

# Mark obstacles
grid.set_blocked(Position(5, 5), True)

# Find a path
path = find_path(grid, Position(0, 0), Position(10, 10))

# Check visibility
visible = has_line_of_sight(grid, Position(0, 0), Position(10, 10))

# Get tiles in range
area = tiles_in_range(Position(5, 5), 3, metric="manhattan")
```

## Grid System

### Creating a Grid

```python
from renee.spatial import Grid
from renee.types.core import Position

# Create a 20x20 grid with default cost 1.0
grid = Grid(20, 20)

# Create with custom default cost
grid = Grid(30, 30, default_cost=1.5)
```

### Blocking Tiles

```python
# Mark tiles as impassable
grid.set_blocked(Position(5, 5), True)

# Check if blocked
is_blocked = grid.is_blocked(Position(5, 5))  # True

# Blocked tiles are treated as having infinite cost
```

### Terrain Costs

```python
# Set movement cost for weighted pathfinding
grid.set_cost(Position(10, 10), 2.0)  # Difficult terrain
grid.set_cost(Position(11, 10), 0.5)  # Easy terrain

# Get cost
cost = grid.get_cost(Position(10, 10))  # 2.0

# Blocked tiles return infinity
cost = grid.get_cost(Position(5, 5))  # float('inf')
```

### Tile Data

```python
# Store arbitrary data on tiles
grid.set_tile_data(Position(15, 15), "treasure", "gold coins")
grid.set_tile_data(Position(15, 15), "trap", True)

# Retrieve data
treasure = grid.get_tile_data(Position(15, 15), "treasure")  # "gold coins"
trap = grid.get_tile_data(Position(15, 15), "trap")  # True
missing = grid.get_tile_data(Position(15, 15), "foo")  # None

# Clear data
grid.clear_tile_data(Position(15, 15), "trap")
```

### Iteration

```python
# Iterate over all tiles
for tile in grid.iter_tiles():
    print(f"Tile at {tile.position}: blocked={tile.blocked}, cost={tile.cost}")

# Iterate over a region
for tile in grid.iter_region(Position(0, 0), Position(5, 5)):
    print(tile.position)
```

### Utility Methods

```python
# Check bounds
in_bounds = grid.in_bounds(Position(10, 10))  # True
in_bounds = grid.in_bounds(Position(30, 30))  # False

# Get passable neighbors
neighbors = grid.get_passable_neighbors(Position(5, 5), diagonal=False)  # 4-way
neighbors_8 = grid.get_passable_neighbors(Position(5, 5), diagonal=True)  # 8-way

# Reset grid
grid.clear()  # Reset all tiles to default state
grid.clear(default_cost=2.0)  # Reset with new default cost
```

## Pathfinding

### Basic Pathfinding

```python
from renee.spatial import find_path
from renee.types.core import Position

# Find path (cardinal directions only)
path = find_path(grid, Position(0, 0), Position(10, 10))

if path:
    print(f"Path found: {len(path)} steps")
    for pos in path:
        print(pos)
else:
    print("No path exists")
```

### Pathfinding Options

```python
from renee.spatial import PathfindingOptions

# Allow diagonal movement
options = PathfindingOptions(diagonal=True)
path = find_path(grid, start, goal, options)

# Limit search distance
options = PathfindingOptions(max_distance=10)
path = find_path(grid, start, goal, options)

# Custom cost function
def custom_cost(pos: Position, grid: Grid) -> float:
    base_cost = grid.get_cost(pos)
    # Add extra cost for tiles near enemies
    if grid.get_tile_data(pos, "enemy_nearby"):
        return base_cost * 2.0
    return base_cost

options = PathfindingOptions(cost_fn=custom_cost)
path = find_path(grid, start, goal, options)
```

### Movement Cost

```python
from renee.spatial.pathfinding import get_movement_cost

# Calculate total cost to reach destination
cost = get_movement_cost(grid, Position(0, 0), Position(10, 10))
if cost is not None:
    print(f"Total movement cost: {cost}")
```

### Reachable Positions

```python
from renee.spatial.pathfinding import get_reachable_positions

# Get all positions reachable within movement budget
reachable = get_reachable_positions(grid, Position(5, 5), max_cost=10.0)

for pos, cost in reachable.items():
    print(f"{pos}: {cost} movement cost")
```

## Visibility

### Line of Sight

```python
from renee.spatial import has_line_of_sight

# Check if two positions can see each other
observer = Position(0, 0)
target = Position(10, 10)

can_see = has_line_of_sight(grid, observer, target)

# Don't check if start/end are blocked
can_see = has_line_of_sight(grid, observer, target, ignore_start=True, ignore_end=True)
```

### Field of View

```python
from renee.spatial import compute_field_of_view

# Get all visible tiles from a position
observer = Position(10, 10)
fov = compute_field_of_view(grid, observer, radius=8)

# Check if specific tile is visible
if Position(15, 15) in fov:
    print("Tile is visible!")

# Number of visible tiles
print(f"Can see {len(fov)} tiles")
```

### Tiles Along Line

```python
from renee.spatial import tiles_along_line

# Get all tiles along a line (Bresenham's algorithm)
line = tiles_along_line(Position(0, 0), Position(10, 10))

for pos in line:
    print(pos)
```

### Light Levels

```python
from renee.spatial.visibility import compute_light_level

# Calculate light intensity at a position
light_source = Position(10, 10)
target = Position(15, 15)

# Linear falloff
intensity = compute_light_level(grid, light_source, target, max_range=10, falloff=1.0)

# Quadratic falloff (more realistic)
intensity = compute_light_level(grid, light_source, target, max_range=10, falloff=2.0)

print(f"Light intensity: {intensity:.2f}")  # 0.0 to 1.0
```

## Area Queries

### Tiles in Range

```python
from renee.spatial import tiles_in_range, DistanceMetric

# Manhattan distance (taxicab, 4-way)
tiles = tiles_in_range(Position(10, 10), 3, DistanceMetric.MANHATTAN)

# Chebyshev distance (chessboard, 8-way)
tiles = tiles_in_range(Position(10, 10), 3, DistanceMetric.CHEBYSHEV)

# Euclidean distance (straight-line)
tiles = tiles_in_range(Position(10, 10), 3, DistanceMetric.EUCLIDEAN)

# Can also use strings
tiles = tiles_in_range(Position(10, 10), 3, "manhattan")
```

### Rectangular Area

```python
from renee.spatial import tiles_in_rectangle

# Get all tiles in rectangle
corner1 = Position(5, 5)
corner2 = Position(10, 10)
tiles = tiles_in_rectangle(corner1, corner2)

# Works regardless of corner order
tiles = tiles_in_rectangle(Position(10, 10), Position(5, 5))
```

### Cone/Arc Area

```python
from renee.spatial import tiles_in_cone

# Get tiles in a cone (e.g., breath weapon, cone of fire)
origin = Position(10, 10)
direction = Position(15, 10)  # Point east
tiles = tiles_in_cone(origin, direction, angle_degrees=90, distance=5)

# 180-degree arc (half circle)
tiles = tiles_in_cone(origin, direction, angle_degrees=180, distance=8)
```

### Line Area

```python
from renee.spatial import tiles_in_line

# Get all tiles along a line
tiles = tiles_in_line(Position(0, 0), Position(10, 10))
```

## Entity Queries

Integrate spatial queries with the ECS world to find entities by position.

### Entities at Position

```python
from renee.spatial import entities_at_position
from renee.ecs.world import World
from renee.types.core import Position

world = World()

# Create entities with positions
# ... (create entities and add Position components)

# Find all entities at a specific position
entities = entities_at_position(world, Position(10, 10))
```

### Entities in Range

```python
from renee.spatial import entities_in_range, DistanceMetric

# Find entities within range
nearby = entities_in_range(
    world,
    Position(10, 10),
    range_val=5,
    metric=DistanceMetric.MANHATTAN
)

# Returns dict mapping entity IDs to their positions
for entity_id, pos in nearby.items():
    print(f"Entity {entity_id} at {pos}")
```

### Entities in Cone

```python
from renee.spatial.area import entities_in_cone

# Find entities in cone area
in_cone = entities_in_cone(
    world,
    origin=Position(10, 10),
    direction=Position(15, 10),
    angle_degrees=90,
    distance=8
)
```

### Entities in Rectangle

```python
from renee.spatial.area import entities_in_rectangle

# Find entities in rectangular area
in_rect = entities_in_rectangle(
    world,
    Position(5, 5),
    Position(15, 15)
)
```

### Nearest Entity

```python
from renee.spatial.area import nearest_entity

# Find closest entity to a position
result = nearest_entity(
    world,
    Position(10, 10),
    max_range=20,
    metric=DistanceMetric.EUCLIDEAN
)

if result:
    entity_id, pos, distance = result
    print(f"Nearest entity {entity_id} at {pos}, distance {distance}")
```

## Common Patterns

### Tactical Movement

```python
# Calculate all reachable positions for a unit
unit_pos = world.get_component(unit, Position)
movement_points = 5

reachable = get_reachable_positions(grid, unit_pos, max_cost=movement_points)

# Filter for positions not occupied by enemies
valid_moves = {}
for pos, cost in reachable.items():
    entities = entities_at_position(world, pos)
    if not any(world.has_tag(e, "enemy") for e in entities):
        valid_moves[pos] = cost
```

### Attack Range

```python
# Find all enemies in attack range
attacker_pos = world.get_component(attacker, Position)
attack_range = 5

targets = {}
for entity_id in world.query_by_tag("enemy"):
    enemy_pos = world.get_component(entity_id, Position)
    distance = attacker_pos.manhattan_distance(enemy_pos)

    if distance <= attack_range and has_line_of_sight(grid, attacker_pos, enemy_pos):
        targets[entity_id] = enemy_pos
```

### Area of Effect

```python
# Apply damage to all entities in explosion radius
explosion_center = Position(15, 15)
explosion_radius = 3

affected = entities_in_range(
    world,
    explosion_center,
    explosion_radius,
    DistanceMetric.EUCLIDEAN
)

for entity_id, pos in affected.items():
    # Calculate damage based on distance
    distance = explosion_center.euclidean_distance(pos)
    damage_multiplier = 1.0 - (distance / explosion_radius)

    # Apply damage...
```

### Stealth and Detection

```python
# Check if guard can see player
guard_pos = world.get_component(guard, Position)
player_pos = world.get_component(player, Position)

# Compute guard's field of view
guard_fov = compute_field_of_view(grid, guard_pos, radius=8)

# Check if player is visible
if player_pos in guard_fov:
    # Player detected!
    print("Alert!")
```

### Zone Control

```python
# Find all tiles controlled by friendly units
controlled_tiles = set()

for entity_id in world.query_by_tag("friendly"):
    pos = world.get_component(entity_id, Position)
    influence_area = tiles_in_range(pos, 3, DistanceMetric.CHEBYSHEV)
    controlled_tiles.update(influence_area)

# Check if position is in controlled zone
if Position(10, 10) in controlled_tiles:
    print("This tile is controlled by friendlies")
```

## Performance Tips

1. **Cache FOV**: Field-of-view calculations are expensive. Cache results and only recompute when needed.

2. **Use appropriate distance metrics**:
   - Manhattan: Fastest, good for grid-based movement
   - Chebyshev: Fast, good for 8-way movement
   - Euclidean: Slower, but more accurate for circular areas

3. **Limit search space**: Use `max_distance` in pathfinding options to avoid expensive searches.

4. **Batch queries**: When checking multiple entities, consider using area queries instead of individual distance checks.

5. **Reachable positions**: Use `get_reachable_positions()` instead of repeated pathfinding calls when showing movement options.

## Architecture Notes

### Why Position from ECS?

The Position type is defined in `renee.types.core` and serves as both:
- A spatial coordinate type
- An ECS component for entity positioning

This design allows spatial queries to seamlessly integrate with the ECS world.

### Grid vs World

- **Grid**: Manages tile-level data (blocking, costs, terrain)
- **World**: Manages entities and their components

These are separate concerns. A grid defines the static environment, while the world manages dynamic entities moving through it.

### Pathfinding Algorithm

The implementation uses A* with:
- Configurable heuristics (Manhattan vs Chebyshev)
- Support for weighted terrain costs
- Early termination with max distance
- Custom cost functions

### Visibility Algorithm

Field-of-view uses recursive shadow casting:
- Efficient O(n) where n is visible tiles
- Accurate shadow occlusion
- Works with any blocking terrain configuration

## Examples

See `/examples/spatial_example.py` for complete working examples of all spatial features.

## API Reference

### Grid Class

```python
Grid(width: int, height: int, default_cost: float = 1.0)
```

Methods:
- `in_bounds(pos: Position) -> bool`
- `is_blocked(pos: Position) -> bool`
- `set_blocked(pos: Position, blocked: bool) -> None`
- `get_cost(pos: Position) -> float`
- `set_cost(pos: Position, cost: float) -> None`
- `get_tile_data(pos: Position, key: str, default: Any = None) -> Any`
- `set_tile_data(pos: Position, key: str, value: Any) -> None`
- `clear_tile_data(pos: Position, key: str) -> None`
- `get_tile(pos: Position) -> Tile | None`
- `iter_tiles() -> Iterator[Tile]`
- `iter_region(top_left: Position, bottom_right: Position) -> Iterator[Tile]`
- `get_passable_neighbors(pos: Position, diagonal: bool = False) -> list[Position]`
- `clear(default_cost: float | None = None) -> None`

### Pathfinding Functions

```python
find_path(
    grid: Grid,
    start: Position,
    goal: Position,
    options: PathfindingOptions | None = None
) -> list[Position] | None

get_movement_cost(
    grid: Grid,
    start: Position,
    end: Position,
    options: PathfindingOptions | None = None
) -> float | None

get_reachable_positions(
    grid: Grid,
    start: Position,
    max_cost: float,
    diagonal: bool = False
) -> dict[Position, float]
```

### Visibility Functions

```python
has_line_of_sight(
    grid: Grid,
    start: Position,
    end: Position,
    ignore_start: bool = True,
    ignore_end: bool = True
) -> bool

compute_field_of_view(
    grid: Grid,
    origin: Position,
    radius: int,
    include_origin: bool = True
) -> set[Position]

tiles_along_line(start: Position, end: Position) -> list[Position]

compute_light_level(
    grid: Grid,
    light_source: Position,
    target: Position,
    max_range: int,
    falloff: float = 1.0
) -> float
```

### Area Query Functions

```python
tiles_in_range(
    center: Position,
    range_val: int,
    metric: DistanceMetric | str = DistanceMetric.MANHATTAN
) -> set[Position]

tiles_in_rectangle(corner1: Position, corner2: Position) -> set[Position]

tiles_in_cone(
    origin: Position,
    direction: Position,
    angle_degrees: float,
    distance: int
) -> set[Position]

tiles_in_line(start: Position, end: Position) -> list[Position]
```

### Entity Query Functions

```python
entities_at_position(world: World, pos: Position) -> list[EntityId]

entities_in_range(
    world: World,
    center: Position,
    range_val: int,
    metric: DistanceMetric | str = DistanceMetric.MANHATTAN
) -> dict[EntityId, Position]

entities_in_cone(
    world: World,
    origin: Position,
    direction: Position,
    angle_degrees: float,
    distance: int
) -> dict[EntityId, Position]

entities_in_rectangle(
    world: World,
    corner1: Position,
    corner2: Position
) -> dict[EntityId, Position]

nearest_entity(
    world: World,
    center: Position,
    max_range: int | None = None,
    metric: DistanceMetric | str = DistanceMetric.EUCLIDEAN
) -> tuple[EntityId, Position, float] | None
```
