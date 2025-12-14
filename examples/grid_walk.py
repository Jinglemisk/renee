#!/usr/bin/env python3
"""Simple Grid Walk Demo - Move a player with WASD keys.

This is the simplest possible visual demo of the Renee framework.
"""

from dataclasses import dataclass
from renee.ecs.world import World
from renee.types import Position
from renee.render import PygameRenderer, ClearCommand, DrawRectCommand, DrawTextCommand

# Grid settings
TILE_SIZE = 32
GRID_W = 20
GRID_H = 15
WINDOW_W = TILE_SIZE * GRID_W
WINDOW_H = TILE_SIZE * GRID_H

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
GRAY = (40, 40, 40)
RED = (200, 0, 0)


@dataclass
class Player:
    """Marker component for the player entity."""
    pass


@dataclass
class Wall:
    """Marker component for wall entities."""
    pass


def create_world() -> World:
    """Create the game world with player and walls."""
    world = World()

    # Create player at center
    player = world.create_entity()
    world.add_component(player, Position(GRID_W // 2, GRID_H // 2))
    world.add_component(player, Player())
    world.add_tag(player, "player")

    # Create some walls
    walls = [
        (5, 5), (5, 6), (5, 7), (5, 8),
        (10, 3), (11, 3), (12, 3), (13, 3),
        (15, 10), (15, 11), (15, 12),
        (3, 12), (4, 12), (5, 12), (6, 12),
    ]
    for wx, wy in walls:
        wall = world.create_entity()
        world.add_component(wall, Position(wx, wy))
        world.add_component(wall, Wall())
        world.add_tag(wall, "wall")

    return world


def get_player_pos(world: World) -> Position:
    """Get the player's current position."""
    for entity_id in world.query(Player, Position):
        return world.get_component(entity_id, Position)
    return Position(0, 0)


def is_blocked(world: World, pos: Position) -> bool:
    """Check if a position is blocked by a wall or out of bounds."""
    # Check bounds
    if pos.x < 0 or pos.x >= GRID_W or pos.y < 0 or pos.y >= GRID_H:
        return True

    # Check walls
    for entity_id in world.query(Wall, Position):
        wall_pos = world.get_component(entity_id, Position)
        if wall_pos.x == pos.x and wall_pos.y == pos.y:
            return True

    return False


def move_player(world: World, dx: int, dy: int) -> None:
    """Move the player by delta if not blocked."""
    for entity_id in world.query(Player, Position):
        current = world.get_component(entity_id, Position)
        new_pos = Position(current.x + dx, current.y + dy)

        if not is_blocked(world, new_pos):
            world.add_component(entity_id, new_pos)


def render_game(world: World) -> list:
    """Generate render commands for the current game state."""
    commands = []

    # Clear screen
    commands.append(ClearCommand(color=BLACK))

    # Draw grid lines
    for x in range(GRID_W + 1):
        commands.append(DrawRectCommand(
            x=x * TILE_SIZE, y=0, width=1, height=WINDOW_H, color=GRAY
        ))
    for y in range(GRID_H + 1):
        commands.append(DrawRectCommand(
            x=0, y=y * TILE_SIZE, width=WINDOW_W, height=1, color=GRAY
        ))

    # Draw walls
    for entity_id in world.query(Wall, Position):
        pos = world.get_component(entity_id, Position)
        commands.append(DrawRectCommand(
            x=pos.x * TILE_SIZE + 2,
            y=pos.y * TILE_SIZE + 2,
            width=TILE_SIZE - 4,
            height=TILE_SIZE - 4,
            color=RED,
            layer=1
        ))

    # Draw player
    player_pos = get_player_pos(world)
    commands.append(DrawRectCommand(
        x=player_pos.x * TILE_SIZE + 4,
        y=player_pos.y * TILE_SIZE + 4,
        width=TILE_SIZE - 8,
        height=TILE_SIZE - 8,
        color=GREEN,
        layer=2
    ))

    # Draw instructions
    commands.append(DrawTextCommand(
        text="WASD to move | ESC to quit",
        x=10, y=WINDOW_H - 25,
        size=20, color=WHITE,
        layer=3
    ))

    return commands


def main():
    """Main game loop."""
    print("=" * 50)
    print("RENEE GRID WALK DEMO")
    print("=" * 50)
    print("Controls: WASD to move, ESC or close window to quit")
    print()

    # Create world
    world = create_world()

    # Create renderer
    renderer = PygameRenderer()
    renderer.initialize({
        "width": WINDOW_W,
        "height": WINDOW_H,
        "title": "Renee Grid Walk Demo",
        "fps": 60,
    })

    print("Game window opened!")

    # Game loop
    while renderer.is_running():
        # Get input
        input_state = renderer.get_input()

        # Check for quit
        if "escape" in input_state.keys_just_pressed:
            break

        # Handle movement (only on key press, not hold)
        if "w" in input_state.keys_just_pressed or "up" in input_state.keys_just_pressed:
            move_player(world, 0, -1)
        if "s" in input_state.keys_just_pressed or "down" in input_state.keys_just_pressed:
            move_player(world, 0, 1)
        if "a" in input_state.keys_just_pressed or "left" in input_state.keys_just_pressed:
            move_player(world, -1, 0)
        if "d" in input_state.keys_just_pressed or "right" in input_state.keys_just_pressed:
            move_player(world, 1, 0)

        # Render
        commands = render_game(world)
        renderer.render(commands)

    # Cleanup
    renderer.shutdown()
    print("Game closed.")


if __name__ == "__main__":
    main()
