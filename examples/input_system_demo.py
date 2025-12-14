"""Demo of the Input System for Renee.

This example shows how to:
1. Create and configure input bindings
2. Process input states
3. Map inputs to logical actions
4. Handle directional input
5. Save/load bindings from YAML
"""

import tempfile
from pathlib import Path

from renee.input import InputState, InputBindings, InputHandler, DEFAULT_BINDINGS
from renee.types import Position


def demo_basic_input():
    """Demonstrate basic input handling."""
    print("=== Basic Input Handling ===\n")

    # Create a handler with default bindings
    handler = InputHandler()

    # Simulate first frame: no input
    state1 = InputState()
    handler.update(state1)
    print(f"Frame 1 - Direction: {handler.get_direction()}")

    # Simulate second frame: player presses 'W' to move up
    state2 = InputState(keys_pressed={"w"})
    handler.update(state2)
    print(f"Frame 2 - Direction: {handler.get_direction()}")
    print(f"         Up action pressed: {handler.is_action_pressed('up')}")
    print(f"         Up action just pressed: {handler.is_action_just_pressed('up')}")

    # Simulate third frame: player holds 'W' and presses 'D' for diagonal movement
    state3 = InputState(keys_pressed={"w", "d"})
    handler.update(state3)
    print(f"Frame 3 - Direction: {handler.get_direction()}")
    print(f"         Right action just pressed: {handler.is_action_just_pressed('right')}")

    # Simulate fourth frame: player presses Space to confirm
    state4 = InputState(keys_pressed={"space"})
    handler.update(state4)
    print(f"Frame 4 - Confirm pressed: {handler.is_action_just_pressed('confirm')}")
    print()


def demo_custom_bindings():
    """Demonstrate custom input bindings."""
    print("=== Custom Input Bindings ===\n")

    # Create custom bindings for a game
    bindings = InputBindings()
    bindings.bind("attack", keys=["j", "space"], mouse=[1])
    bindings.bind("defend", keys=["k"])
    bindings.bind("special", keys=["l"], mouse=[3])
    bindings.bind("jump", keys=["w", "up"])

    handler = InputHandler(bindings=bindings)

    # Simulate player pressing 'J' to attack
    state1 = InputState(keys_pressed={"j"})
    handler.update(state1)
    print(f"Player presses 'J': Attack action = {handler.is_action_just_pressed('attack')}")

    # Simulate player left-clicking to attack
    state2 = InputState(mouse_buttons={1}, mouse_just_clicked={1})
    handler.update(state2)
    print(f"Player left-clicks: Attack action = {handler.is_action_just_pressed('attack')}")

    # Simulate player pressing multiple actions
    state3 = InputState(keys_pressed={"j", "k"})
    handler.update(state3)
    actions = handler.get_all_pressed_actions()
    print(f"Player presses 'J' + 'K': Active actions = {actions}")
    print()


def demo_mouse_input():
    """Demonstrate mouse input handling."""
    print("=== Mouse Input Handling ===\n")

    handler = InputHandler()

    # Simulate mouse movement and click
    state1 = InputState(
        mouse_position=(320, 240),
        mouse_buttons={1},
        mouse_just_clicked={1}
    )
    handler.update(state1)

    print(f"Mouse position: {handler.get_mouse_position()}")
    print(f"Mouse grid position (32px tiles): {handler.get_mouse_grid_position(32)}")
    print(f"Left click action: {handler.is_action_just_pressed('select')}")

    # Simulate mouse scroll
    state2 = InputState(mouse_scroll=5)
    handler.update(state2)
    print(f"Mouse scroll delta: {handler.get_state().mouse_scroll}")
    print()


def demo_yaml_bindings():
    """Demonstrate saving and loading bindings from YAML."""
    print("=== YAML Bindings ===\n")

    # Create custom bindings
    bindings = InputBindings()
    bindings.bind("move_up", keys=["w", "up"])
    bindings.bind("move_down", keys=["s", "down"])
    bindings.bind("move_left", keys=["a", "left"])
    bindings.bind("move_right", keys=["d", "right"])
    bindings.bind("primary_action", keys=["return"], mouse=[1])
    bindings.bind("secondary_action", keys=["backspace"], mouse=[3])

    # Save to temporary YAML file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = f.name

    try:
        bindings.to_yaml(temp_path)
        print(f"Saved bindings to: {temp_path}")

        # Read and display the YAML
        with open(temp_path, "r") as f:
            yaml_content = f.read()
        print("\nYAML content:")
        print(yaml_content)

        # Load bindings from YAML
        loaded_bindings = InputBindings.from_yaml(temp_path)
        print(f"Loaded {len(loaded_bindings.all_actions())} actions from YAML")

        # Verify loaded bindings work
        handler = InputHandler(bindings=loaded_bindings)
        state = InputState(keys_pressed={"w"})
        handler.update(state)
        print(f"Testing loaded bindings - move_up pressed: {handler.is_action_pressed('move_up')}")
    finally:
        Path(temp_path).unlink(missing_ok=True)

    print()


def demo_game_loop_simulation():
    """Simulate a simple game loop with input handling."""
    print("=== Game Loop Simulation ===\n")

    handler = InputHandler()
    player_pos = Position(5, 5)

    print(f"Starting position: {player_pos}")
    print("Simulating player movement:\n")

    # Frame 1: Player presses 'W' to move up
    state1 = InputState(keys_pressed={"w"})
    handler.update(state1)
    if handler.is_action_just_pressed("up"):
        direction = handler.get_direction()
        if direction:
            player_pos = player_pos + direction
            print(f"Frame 1: Moved up -> {player_pos}")

    # Frame 2: Player holds 'W' and presses 'D' to move up-right
    state2 = InputState(keys_pressed={"w", "d"})
    handler.update(state2)
    if handler.is_action_just_pressed("right"):
        direction = handler.get_direction()
        if direction:
            player_pos = player_pos + direction
            print(f"Frame 2: Moved up-right -> {player_pos}")

    # Frame 3: Player releases 'W', continues moving right
    state3 = InputState(keys_pressed={"d"})
    handler.update(state3)
    direction = handler.get_direction()
    if direction:
        player_pos = player_pos + direction
        print(f"Frame 3: Moved right -> {player_pos}")

    # Frame 4: Player presses Space to confirm action
    state4 = InputState(keys_pressed={"space"})
    handler.update(state4)
    if handler.is_action_just_pressed("confirm"):
        print(f"Frame 4: Action confirmed at position {player_pos}")

    print(f"\nFinal position: {player_pos}")
    print()


def demo_default_bindings():
    """Show the default bindings configuration."""
    print("=== Default Bindings ===\n")

    print("Available default actions:")
    for action in DEFAULT_BINDINGS.all_actions():
        binding = DEFAULT_BINDINGS.get_binding(action)
        if binding:
            parts = []
            if binding.keys:
                parts.append(f"Keys: {', '.join(binding.keys)}")
            if binding.mouse_buttons:
                parts.append(f"Mouse: {', '.join(map(str, binding.mouse_buttons))}")
            if binding.controller_buttons:
                parts.append(f"Controller: {', '.join(binding.controller_buttons)}")
            print(f"  {action}: {' | '.join(parts)}")
    print()


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("Renee Input System Demo")
    print("="*60 + "\n")

    demo_default_bindings()
    demo_basic_input()
    demo_custom_bindings()
    demo_mouse_input()
    demo_yaml_bindings()
    demo_game_loop_simulation()

    print("="*60)
    print("Demo complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
