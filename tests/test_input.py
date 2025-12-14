"""Tests for the input system."""

import tempfile
from pathlib import Path

import pytest

from renee.input import InputState, InputBindings, InputHandler, DEFAULT_BINDINGS
from renee.types import Position


class TestInputState:
    """Tests for InputState class."""

    def test_init_default(self):
        """Test default initialization."""
        state = InputState()
        assert len(state.keys_pressed) == 0
        assert len(state.keys_just_pressed) == 0
        assert len(state.keys_just_released) == 0
        assert state.mouse_position == (0, 0)
        assert len(state.mouse_buttons) == 0
        assert state.mouse_scroll == 0

    def test_is_key_pressed(self):
        """Test key press detection."""
        state = InputState(keys_pressed={"w", "a"})
        assert state.is_key_pressed("w")
        assert state.is_key_pressed("a")
        assert not state.is_key_pressed("s")

    def test_is_key_just_pressed(self):
        """Test key just pressed detection."""
        state = InputState(keys_just_pressed={"space"})
        assert state.is_key_just_pressed("space")
        assert not state.is_key_just_pressed("w")

    def test_is_mouse_pressed(self):
        """Test mouse button press detection."""
        state = InputState(mouse_buttons={1, 3})
        assert state.is_mouse_pressed(1)
        assert state.is_mouse_pressed(3)
        assert not state.is_mouse_pressed(2)

    def test_get_mouse_grid_pos(self):
        """Test mouse to grid position conversion."""
        state = InputState(mouse_position=(100, 150))
        grid_pos = state.get_mouse_grid_pos(tile_size=32)
        assert grid_pos == Position(3, 4)

    def test_clear_frame_events(self):
        """Test clearing of frame events."""
        state = InputState(
            keys_just_pressed={"w"},
            keys_just_released={"s"},
            mouse_just_clicked={1},
            mouse_scroll=5,
        )
        state.clear_frame_events()
        assert len(state.keys_just_pressed) == 0
        assert len(state.keys_just_released) == 0
        assert len(state.mouse_just_clicked) == 0
        assert state.mouse_scroll == 0


class TestInputBindings:
    """Tests for InputBindings class."""

    def test_init(self):
        """Test initialization."""
        bindings = InputBindings()
        assert len(bindings.all_actions()) == 0

    def test_bind_action(self):
        """Test binding an action."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space"])
        assert "jump" in bindings.all_actions()

    def test_bind_multiple_inputs(self):
        """Test binding multiple inputs to one action."""
        bindings = InputBindings()
        bindings.bind("move_up", keys=["w", "up"], mouse=[2])
        binding = bindings.get_binding("move_up")
        assert binding is not None
        assert "w" in binding.keys
        assert "up" in binding.keys
        assert 2 in binding.mouse_buttons

    def test_unbind_action(self):
        """Test unbinding an action."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space"])
        bindings.unbind("jump")
        assert "jump" not in bindings.all_actions()

    def test_is_action_pressed(self):
        """Test action press detection."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space"])

        state = InputState(keys_pressed={"space"})
        assert bindings.is_action_pressed("jump", state)

        state = InputState(keys_pressed={"w"})
        assert not bindings.is_action_pressed("jump", state)

    def test_is_action_just_pressed(self):
        """Test action just pressed detection."""
        bindings = InputBindings()
        bindings.bind("attack", keys=["space"], mouse=[1])

        # Test with key just pressed
        state = InputState(keys_just_pressed={"space"})
        assert bindings.is_action_just_pressed("attack", state)

        # Test with mouse just clicked
        state = InputState(mouse_just_clicked={1})
        assert bindings.is_action_just_pressed("attack", state)

        # Test with no just pressed input
        state = InputState(keys_pressed={"space"})
        assert not bindings.is_action_just_pressed("attack", state)

    def test_get_action(self):
        """Test getting first active action."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space"])
        bindings.bind("move", keys=["w"])

        state = InputState(keys_pressed={"space"})
        action = bindings.get_action(state)
        assert action == "jump"

    def test_get_all_actions(self):
        """Test getting all active actions."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space"])
        bindings.bind("move", keys=["w"])

        state = InputState(keys_pressed={"space", "w"})
        actions = bindings.get_all_actions(state)
        assert "jump" in actions
        assert "move" in actions

    def test_yaml_roundtrip(self):
        """Test saving and loading bindings from YAML."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space", "w"])
        bindings.bind("attack", keys=["e"], mouse=[1])
        bindings.bind("move", controller=["dpad_up"])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            # Save to YAML
            bindings.to_yaml(temp_path)

            # Load from YAML
            loaded = InputBindings.from_yaml(temp_path)

            # Verify
            jump = loaded.get_binding("jump")
            assert jump is not None
            assert "space" in jump.keys
            assert "w" in jump.keys

            attack = loaded.get_binding("attack")
            assert attack is not None
            assert "e" in attack.keys
            assert 1 in attack.mouse_buttons

            move = loaded.get_binding("move")
            assert move is not None
            assert "dpad_up" in move.controller_buttons
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_default_bindings(self):
        """Test that default bindings are set up correctly."""
        assert DEFAULT_BINDINGS.get_binding("up") is not None
        assert DEFAULT_BINDINGS.get_binding("down") is not None
        assert DEFAULT_BINDINGS.get_binding("left") is not None
        assert DEFAULT_BINDINGS.get_binding("right") is not None
        assert DEFAULT_BINDINGS.get_binding("confirm") is not None
        assert DEFAULT_BINDINGS.get_binding("cancel") is not None


class TestInputHandler:
    """Tests for InputHandler class."""

    def test_init_default_bindings(self):
        """Test initialization with default bindings."""
        handler = InputHandler()
        assert handler.bindings == DEFAULT_BINDINGS

    def test_init_custom_bindings(self):
        """Test initialization with custom bindings."""
        bindings = InputBindings()
        handler = InputHandler(bindings=bindings)
        assert handler.bindings == bindings

    def test_update_computes_just_pressed(self):
        """Test that update computes just_pressed keys."""
        handler = InputHandler()

        # First frame: no keys pressed
        state1 = InputState(keys_pressed=set())
        handler.update(state1)

        # Second frame: 'w' is pressed
        state2 = InputState(keys_pressed={"w"})
        handler.update(state2)

        current = handler.get_state()
        assert "w" in current.keys_just_pressed

    def test_update_computes_just_released(self):
        """Test that update computes just_released keys."""
        handler = InputHandler()

        # First frame: 'w' pressed
        state1 = InputState(keys_pressed={"w"})
        handler.update(state1)

        # Second frame: 'w' released
        state2 = InputState(keys_pressed=set())
        handler.update(state2)

        current = handler.get_state()
        assert "w" in current.keys_just_released

    def test_is_action_pressed(self):
        """Test action press detection."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space"])
        handler = InputHandler(bindings=bindings)

        state = InputState(keys_pressed={"space"})
        handler.update(state)

        assert handler.is_action_pressed("jump")
        assert not handler.is_action_pressed("move")

    def test_is_action_just_pressed(self):
        """Test action just pressed detection."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space"])
        handler = InputHandler(bindings=bindings)

        # First frame: no input
        state1 = InputState(keys_pressed=set())
        handler.update(state1)

        # Second frame: space pressed
        state2 = InputState(keys_pressed={"space"})
        handler.update(state2)

        assert handler.is_action_just_pressed("jump")

    def test_get_direction_single(self):
        """Test getting single direction."""
        handler = InputHandler()

        state = InputState(keys_pressed={"w"})
        handler.update(state)

        direction = handler.get_direction()
        assert direction == Position(0, -1)  # Up

    def test_get_direction_diagonal(self):
        """Test getting diagonal direction."""
        handler = InputHandler()

        state = InputState(keys_pressed={"w", "d"})
        handler.update(state)

        direction = handler.get_direction()
        assert direction == Position(1, -1)  # Up-right

    def test_get_direction_none(self):
        """Test getting direction when no directional input."""
        handler = InputHandler()

        state = InputState(keys_pressed={"space"})
        handler.update(state)

        direction = handler.get_direction()
        assert direction is None

    def test_get_mouse_position(self):
        """Test getting mouse position."""
        handler = InputHandler()

        state = InputState(mouse_position=(100, 200))
        handler.update(state)

        pos = handler.get_mouse_position()
        assert pos == (100, 200)

    def test_get_mouse_grid_position(self):
        """Test getting mouse grid position."""
        handler = InputHandler()

        state = InputState(mouse_position=(100, 200))
        handler.update(state)

        grid_pos = handler.get_mouse_grid_position(tile_size=32)
        assert grid_pos == Position(3, 6)

    def test_get_all_pressed_actions(self):
        """Test getting all pressed actions."""
        bindings = InputBindings()
        bindings.bind("jump", keys=["space"])
        bindings.bind("move", keys=["w"])
        handler = InputHandler(bindings=bindings)

        state = InputState(keys_pressed={"space", "w"})
        handler.update(state)

        actions = handler.get_all_pressed_actions()
        assert "jump" in actions
        assert "move" in actions

    def test_clear_state(self):
        """Test clearing input state."""
        handler = InputHandler()

        state = InputState(keys_pressed={"w"}, mouse_position=(100, 100))
        handler.update(state)

        handler.clear_state()

        current = handler.get_state()
        assert len(current.keys_pressed) == 0
        assert current.mouse_position == (0, 0)
