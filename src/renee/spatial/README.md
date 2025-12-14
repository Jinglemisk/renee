# Renee Spatial Module

AI-native spatial reasoning for turn-based games.

## What's Included

- **grid.py**: 2D tile grid with blocking, costs, and tile data
- **pathfinding.py**: A* pathfinding with diagonal movement and weighted terrain
- **visibility.py**: Line-of-sight and field-of-view using shadow casting
- **area.py**: Range, cone, rectangle, and entity query functions

## Quick Example

```python
from renee.spatial import Grid, find_path, has_line_of_sight, tiles_in_range
from renee.types.core import Position

# Create grid and mark obstacles
grid = Grid(20, 20)
grid.set_blocked(Position(5, 5), True)

# Find path
path = find_path(grid, Position(0, 0), Position(10, 10))

# Check visibility
visible = has_line_of_sight(grid, Position(0, 0), Position(10, 10))

# Get area
area = tiles_in_range(Position(5, 5), 3, metric="manhattan")
```

## Why AI-Native?

1. **Introspectable**: All data structures are queryable at runtime
2. **Type-safe**: Full type hints throughout
3. **Text-first**: No binary formats or GUI dependencies
4. **Composable**: Works seamlessly with ECS world and Position components
5. **Well-documented**: Extensive docstrings and examples

## Documentation

See `/docs/SPATIAL.md` for complete documentation.

See `/examples/spatial_example.py` for working examples.

## Features

### Grid System
- Arbitrary grid sizes
- Blocked/passable tiles
- Terrain movement costs
- Arbitrary tile metadata
- Region iteration

### Pathfinding
- A* algorithm
- Cardinal + diagonal movement
- Weighted terrain support
- Maximum distance constraints
- Custom cost functions
- Reachable position queries

### Visibility
- Bresenham's line algorithm
- Shadow casting FOV
- Configurable radius
- Light level calculations
- Occlusion handling

### Area Queries
- Manhattan/Chebyshev/Euclidean distance
- Rectangular areas
- Cone/arc areas (breath weapons, etc.)
- Line queries
- Entity spatial queries
- Nearest entity search

## Design Principles

1. **Position is immutable**: Use frozen dataclass to prevent bugs
2. **Grid is mutable**: Represents changeable world state
3. **Separate concerns**: Grid (terrain) vs World (entities)
4. **No hidden state**: Everything is queryable
5. **Performance conscious**: Efficient algorithms, optional caching hints

## Testing

Run tests:
```bash
python test_spatial.py
```

Run examples:
```bash
python examples/spatial_example.py
```

## Integration with ECS

The spatial module integrates seamlessly with Renee's ECS:

```python
from renee.ecs.world import World
from renee.spatial import entities_in_range
from renee.types.core import Position

world = World()
# ... create entities with Position components

# Find entities near a position
nearby = entities_in_range(world, Position(10, 10), 5)
```

## Common Use Cases

- **Tactical RPGs**: Movement ranges, attack ranges, ability areas
- **Roguelikes**: FOV, pathfinding, dungeon navigation
- **Strategy games**: Zone control, unit movement, vision
- **Board games**: Valid moves, capture areas, line of sight
- **Puzzle games**: Reachability, flood fill, connectivity

## Performance

- Grid operations: O(1)
- Pathfinding: O(n log n) where n is grid size
- FOV: O(visible tiles)
- Area queries: O(area size)
- Entity queries: O(entities) - can be optimized with spatial indexing if needed

## Future Enhancements

Potential additions (not yet implemented):

- Spatial indexing (quadtree, grid hash) for large entity counts
- Flow fields for multi-unit pathfinding
- Jump point search for faster pathfinding
- Influence maps for tactical AI
- Connectivity analysis (flood fill, connected components)

## License

Part of the Renee game framework.
