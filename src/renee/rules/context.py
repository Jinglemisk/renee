"""Action context for rules.

The ActionContext provides rules with access to the action being processed,
the game world, and methods to modify or cancel the action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from renee.ecs.world import World


@dataclass
class Action:
    """Represents an action being processed through the pipeline.

    Attributes:
        name: The action type name (e.g., 'move', 'attack').
        params: Parameters for this action instance.
    """

    name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionContext:
    """Context passed to rules during action processing.

    The context provides:
    - Access to the action being processed
    - Access to the game world
    - Methods to modify or cancel the action
    - Storage for rule-specific data

    Example:
        @pre_rule(action='move', priority=10)
        def check_blocked(ctx: ActionContext):
            entity = ctx.action.params['entity']
            target_pos = ctx.action.params['target_pos']

            if ctx.world.is_blocked(target_pos):
                ctx.cancel("Target position is blocked")
    """

    action: Action
    world: World
    cancelled: bool = False
    cancel_reason: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def cancel(self, reason: str) -> None:
        """Cancel the action from executing.

        This should be called from pre-rules to prevent an action from
        executing. Post-rules should not cancel actions as they run after
        execution has completed.

        Args:
            reason: Human-readable explanation of why the action was cancelled.

        Example:
            if not has_enough_mana(entity):
                ctx.cancel("Not enough mana")
        """
        self.cancelled = True
        self.cancel_reason = reason

    def modify(self, **changes: Any) -> None:
        """Modify action parameters.

        This updates the action's params dictionary with the provided changes.
        Useful for rules that need to adjust action parameters (e.g., applying
        damage modifiers, adjusting move distance).

        Args:
            **changes: Key-value pairs to update in action params.

        Example:
            # Reduce damage by armor value
            ctx.modify(damage=ctx.action.params['damage'] - armor.value)
        """
        self.action.params.update(changes)

    def get_param(self, key: str, default: Any = None) -> Any:
        """Get an action parameter with optional default.

        Args:
            key: Parameter name to retrieve.
            default: Default value if parameter doesn't exist.

        Returns:
            The parameter value or default.
        """
        return self.action.params.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        """Store custom data in the context.

        This allows rules to pass data to other rules in the pipeline.

        Args:
            key: Data key.
            value: Data value.
        """
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Retrieve custom data from the context.

        Args:
            key: Data key.
            default: Default value if key doesn't exist.

        Returns:
            The data value or default.
        """
        return self.data.get(key, default)

    def is_cancelled(self) -> bool:
        """Check if the action has been cancelled.

        Returns:
            True if the action has been cancelled.
        """
        return self.cancelled
