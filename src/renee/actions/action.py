"""Action and ActionContext classes for the Action Pipeline.

Actions represent player/system requests that flow through the pipeline.
ActionContext provides a mutable context passed to rules during processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from renee.types import EntityId

if TYPE_CHECKING:
    from renee.ecs.world import World


@dataclass
class Action:
    """Base class for all actions.

    Actions represent requests to perform game operations (move, attack, etc.).
    They flow through the pipeline: validation → pre-rules → execution → post-rules.

    Attributes:
        name: Action type name (e.g., 'move', 'attack', 'use_item')
        params: Action parameters (entity, target, amount, etc.)
        source: Entity performing the action (optional)

    Example:
        action = Action(
            name='move',
            params={'entity': player_id, 'target': Position(5, 5)},
            source=player_id
        )
    """

    name: str
    params: dict[str, Any]
    source: EntityId | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Action name cannot be empty")
        if not isinstance(self.params, dict):
            raise TypeError(f"Action params must be dict, got {type(self.params)}")


@dataclass
class ActionContext:
    """Context passed to rules during action processing.

    Rules can use this context to:
    - Inspect action parameters
    - Access world state
    - Modify action parameters
    - Cancel the action with a reason

    Attributes:
        action: The action being processed
        world: Reference to the World
        phase: Current pipeline phase ('pre' or 'post')
        cancelled: Whether the action has been cancelled
        cancel_reason: Reason for cancellation (if cancelled)
        modified_params: Parameters modified by rules

    Example:
        def validate_movement(ctx: ActionContext) -> None:
            entity = ctx.action.params['entity']
            if not ctx.world.entity_exists(entity):
                ctx.cancel("Entity does not exist")
    """

    action: Action
    world: World
    phase: str
    cancelled: bool = False
    cancel_reason: str | None = None
    modified_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.phase not in ('pre', 'post'):
            raise ValueError(f"Invalid phase: {self.phase}. Must be 'pre' or 'post'")

    def cancel(self, reason: str) -> None:
        """Cancel the action with a reason.

        Args:
            reason: Human-readable explanation of why the action was cancelled.

        Example:
            ctx.cancel("Target is out of range")
        """
        self.cancelled = True
        self.cancel_reason = reason

    def modify_param(self, key: str, value: Any) -> None:
        """Modify an action parameter.

        Modified parameters override the original action parameters.

        Args:
            key: Parameter name to modify
            value: New parameter value

        Example:
            # Reduce damage by half
            original_damage = ctx.action.params['damage']
            ctx.modify_param('damage', original_damage // 2)
        """
        self.modified_params[key] = value

    def get_param(self, key: str, default: Any = None) -> Any:
        """Get an action parameter, checking modified params first.

        Args:
            key: Parameter name to retrieve
            default: Default value if parameter not found

        Returns:
            The parameter value (modified if available, otherwise original)

        Example:
            damage = ctx.get_param('damage', 0)
        """
        if key in self.modified_params:
            return self.modified_params[key]
        return self.action.params.get(key, default)
