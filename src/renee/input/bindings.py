"""Input bindings for Renee.

Maps raw inputs to logical actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

from renee.input.state import InputState


@dataclass
class Binding:
    """Maps inputs to a logical action.

    Actions are logical game operations like 'move_up', 'attack', 'confirm'.
    Multiple inputs can trigger the same action.
    """

    action: str  # Logical action name like "move_up", "attack", "confirm"
    keys: list[str] = field(default_factory=list)
    mouse_buttons: list[int] = field(default_factory=list)
    controller_buttons: list[str] = field(default_factory=list)


class InputBindings:
    """Manages mapping between raw inputs and logical actions."""

    def __init__(self) -> None:
        self._bindings: dict[str, Binding] = {}

    def bind(
        self,
        action: str,
        keys: list[str] | None = None,
        mouse: list[int] | None = None,
        controller: list[str] | None = None,
    ) -> None:
        """Create or update a binding.

        Args:
            action: Logical action name.
            keys: List of keyboard keys that trigger this action.
            mouse: List of mouse button numbers that trigger this action.
            controller: List of controller button names that trigger this action.
        """
        if action in self._bindings:
            # Update existing binding
            binding = self._bindings[action]
            if keys is not None:
                binding.keys = keys
            if mouse is not None:
                binding.mouse_buttons = mouse
            if controller is not None:
                binding.controller_buttons = controller
        else:
            # Create new binding
            self._bindings[action] = Binding(
                action=action,
                keys=keys or [],
                mouse_buttons=mouse or [],
                controller_buttons=controller or [],
            )

    def unbind(self, action: str) -> None:
        """Remove a binding.

        Args:
            action: Logical action name to unbind.
        """
        if action in self._bindings:
            del self._bindings[action]

    def get_action(self, state: InputState) -> str | None:
        """Get the first action triggered by current input state.

        Args:
            state: Current input state.

        Returns:
            The first matching action name, or None if no action is triggered.
        """
        for action, binding in self._bindings.items():
            if self._is_binding_active(binding, state):
                return action
        return None

    def get_all_actions(self, state: InputState) -> list[str]:
        """Get all actions currently triggered.

        Args:
            state: Current input state.

        Returns:
            List of all matching action names.
        """
        actions = []
        for action, binding in self._bindings.items():
            if self._is_binding_active(binding, state):
                actions.append(action)
        return actions

    def is_action_pressed(self, action: str, state: InputState) -> bool:
        """Check if an action is currently pressed.

        Args:
            action: Logical action name.
            state: Current input state.

        Returns:
            True if the action is currently active.
        """
        if action not in self._bindings:
            return False
        return self._is_binding_active(self._bindings[action], state)

    def is_action_just_pressed(self, action: str, state: InputState) -> bool:
        """Check if an action was just pressed this frame.

        Args:
            action: Logical action name.
            state: Current input state.

        Returns:
            True if the action was just activated.
        """
        if action not in self._bindings:
            return False
        binding = self._bindings[action]

        # Check if any bound key was just pressed
        for key in binding.keys:
            if state.is_key_just_pressed(key):
                return True

        # Check if any bound mouse button was just clicked
        for button in binding.mouse_buttons:
            if state.is_mouse_just_clicked(button):
                return True

        return False

    def _is_binding_active(self, binding: Binding, state: InputState) -> bool:
        """Check if a binding is currently active.

        Args:
            binding: The binding to check.
            state: Current input state.

        Returns:
            True if any input in the binding is currently active.
        """
        # Check keyboard keys
        for key in binding.keys:
            if state.is_key_pressed(key):
                return True

        # Check mouse buttons
        for button in binding.mouse_buttons:
            if state.is_mouse_pressed(button):
                return True

        # Check controller buttons
        for button in binding.controller_buttons:
            if button in state.controller_buttons:
                return True

        return False

    @classmethod
    def from_yaml(cls, path: str) -> InputBindings:
        """Load bindings from YAML config.

        YAML format:
        ```yaml
        bindings:
          move_up:
            keys: [w, up]
          attack:
            keys: [space]
            mouse: [1]
        ```

        Args:
            path: Path to YAML file.

        Returns:
            New InputBindings instance loaded from the file.
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        bindings = cls()
        if not data or "bindings" not in data:
            return bindings

        for action, inputs in data["bindings"].items():
            bindings.bind(
                action=action,
                keys=inputs.get("keys", []),
                mouse=inputs.get("mouse", []),
                controller=inputs.get("controller", []),
            )

        return bindings

    def to_yaml(self, path: str) -> None:
        """Save bindings to YAML.

        Args:
            path: Path to save the YAML file.
        """
        data: dict[str, Any] = {"bindings": {}}

        for action, binding in self._bindings.items():
            action_data: dict[str, Any] = {}
            if binding.keys:
                action_data["keys"] = binding.keys
            if binding.mouse_buttons:
                action_data["mouse"] = binding.mouse_buttons
            if binding.controller_buttons:
                action_data["controller"] = binding.controller_buttons
            data["bindings"][action] = action_data

        with open(path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def get_binding(self, action: str) -> Binding | None:
        """Get the binding for an action.

        Args:
            action: Logical action name.

        Returns:
            The binding for the action, or None if not found.
        """
        return self._bindings.get(action)

    def all_actions(self) -> list[str]:
        """Get all registered action names.

        Returns:
            List of all action names.
        """
        return list(self._bindings.keys())


# Default bindings preset for standard game controls
DEFAULT_BINDINGS = InputBindings()
DEFAULT_BINDINGS.bind("up", keys=["w", "up"])
DEFAULT_BINDINGS.bind("down", keys=["s", "down"])
DEFAULT_BINDINGS.bind("left", keys=["a", "left"])
DEFAULT_BINDINGS.bind("right", keys=["d", "right"])
DEFAULT_BINDINGS.bind("confirm", keys=["return", "space"])
DEFAULT_BINDINGS.bind("cancel", keys=["escape"])
DEFAULT_BINDINGS.bind("select", mouse=[1])  # Left mouse button
DEFAULT_BINDINGS.bind("context_menu", mouse=[3])  # Right mouse button
