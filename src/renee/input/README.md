# Input System

The Input System maps raw input (keyboard, mouse, controller) to logical game actions.

## Core Components

### InputState
Tracks the current state of all input devices:
- Keyboard keys (pressed, just pressed, just released)
- Mouse (position, buttons, scroll)
- Controller (buttons, axes)

### InputBindings
Maps raw inputs to logical actions:
- Define actions like "move_up", "attack", "confirm"
- Bind multiple inputs to the same action
- Save/load from YAML configuration files

### InputHandler
Processes input updates and provides a high-level API:
- Compute frame events (just pressed/released)
- Query action states
- Get directional input
- Convert mouse to grid coordinates

## Quick Start

```python
from renee.input import InputHandler, InputState

# Create handler with default bindings
handler = InputHandler()

# Game loop
while running:
    # Get raw input from your backend (pygame, etc.)
    raw_state = InputState(
        keys_pressed={"w", "d"},
        mouse_position=(100, 200)
    )

    # Update handler
    handler.update(raw_state)

    # Query actions
    if handler.is_action_just_pressed("confirm"):
        print("Player confirmed!")

    # Get direction
    direction = handler.get_direction()
    if direction:
        player_pos = player_pos + direction
```

## Custom Bindings

```python
from renee.input import InputBindings, InputHandler

# Create custom bindings
bindings = InputBindings()
bindings.bind("attack", keys=["space", "j"], mouse=[1])
bindings.bind("defend", keys=["shift", "k"])
bindings.bind("special", keys=["e"], mouse=[3])

# Use custom bindings
handler = InputHandler(bindings=bindings)
```

## YAML Configuration

```yaml
bindings:
  attack:
    keys: [space, j]
    mouse: [1]
    controller: [a, x]

  defend:
    keys: [shift, k]
    controller: [b]

  move_up:
    keys: [w, up]
```

```python
from renee.input import InputBindings

# Load from YAML
bindings = InputBindings.from_yaml("input_config.yaml")

# Save to YAML
bindings.to_yaml("input_config.yaml")
```

## Default Bindings

The system includes sensible defaults:
- `up`, `down`, `left`, `right` - WASD and arrow keys
- `confirm` - Return and Space
- `cancel` - Escape
- `select` - Left mouse button
- `context_menu` - Right mouse button

## API Reference

### InputState

```python
# Check key state
state.is_key_pressed("w")          # Currently pressed
state.is_key_just_pressed("space") # Just pressed this frame
state.is_key_just_released("a")    # Just released this frame

# Check mouse state
state.is_mouse_pressed(1)          # Button 1 (left) pressed
state.is_mouse_just_clicked(1)     # Just clicked this frame

# Convert mouse to grid
grid_pos = state.get_mouse_grid_pos(tile_size=32)
```

### InputBindings

```python
# Bind actions
bindings.bind("jump", keys=["space"], mouse=[2])
bindings.unbind("jump")

# Query actions
bindings.is_action_pressed("jump", state)
bindings.is_action_just_pressed("jump", state)

# Get actions
action = bindings.get_action(state)        # First active action
actions = bindings.get_all_actions(state)  # All active actions

# Introspection
binding = bindings.get_binding("jump")
all_actions = bindings.all_actions()
```

### InputHandler

```python
# Update
handler.update(raw_state)

# Query actions
handler.is_action_pressed("attack")
handler.is_action_just_pressed("jump")
handler.get_all_pressed_actions()

# Direction input
direction = handler.get_direction()  # Position(-1, 0) for left

# Mouse
pos = handler.get_mouse_position()
grid_pos = handler.get_mouse_grid_position(tile_size=32)

# Cleanup
handler.clear_state()
```

## Examples

See:
- `examples/input_system_demo.py` - Comprehensive demonstrations
- `examples/input_bindings.yaml` - Sample configuration file
- `tests/test_input.py` - Unit tests showing usage patterns

## Design Philosophy

The Input System follows Renee's AI-native principles:

1. **Text-first**: YAML configs, no binary formats
2. **Introspectable**: Query all bindings and state at runtime
3. **Type-safe**: Full type hints for IDE support
4. **Logical actions**: Abstract from specific keys/buttons
5. **Frame-aware**: Tracks just pressed/released for precise input

This makes it easy for AI agents to:
- Read and modify input configurations
- Query current input state
- Generate test cases
- Debug input issues
