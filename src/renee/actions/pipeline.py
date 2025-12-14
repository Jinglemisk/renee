"""Action Pipeline for processing game actions.

The pipeline handles the flow: Request → Validation → Pre-Rules → Execution → Post-Rules → Events
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from renee.actions.action import Action, ActionContext
from renee.actions.result import ActionResult
from renee.ecs.world import World


# Type aliases for clarity
ActionHandler = Callable[[Action, World], list[Any]]  # Returns list of events
ActionValidator = Callable[[Action, World], str | None]  # Returns error string or None
ActionRule = Callable[[ActionContext], None]


@dataclass
class _RuleEntry:
    """Internal: Rule with priority for ordering."""
    rule: ActionRule
    priority: int = 0


class ActionPipeline:
    """Pipeline for processing game actions.

    Actions flow through these stages:
    1. Parameter validation (schema check)
    2. Pre-rules (can cancel or modify)
    3. Handler execution (if not cancelled)
    4. Post-rules (react to completed action)
    5. Return result with events

    Usage:
        pipeline = ActionPipeline()

        # Register handler
        def move_handler(action: Action, world: World) -> list[Event]:
            entity = action.params['entity']
            target = action.params['target']
            world.add_component(entity, target)
            return [MovedEvent(entity=entity, to=target)]

        pipeline.register_handler('move', move_handler)

        # Execute action
        action = Action('move', {'entity': e1, 'target': Position(5, 5)})
        result = pipeline.execute(action, world)
    """

    def __init__(self) -> None:
        # Action handlers: name -> handler function
        self._handlers: dict[str, ActionHandler] = {}

        # Validators: name -> validator function
        self._validators: dict[str, ActionValidator] = {}

        # Pre-rules: name -> list of (rule, priority)
        self._pre_rules: dict[str, list[_RuleEntry]] = {}

        # Post-rules: name -> list of (rule, priority)
        self._post_rules: dict[str, list[_RuleEntry]] = {}

    def register_handler(self, action_name: str, handler: ActionHandler) -> None:
        """Register an action handler.

        The handler is called during the execution phase if the action is not cancelled.
        It should perform the action's effects and return a list of events.

        Args:
            action_name: Name of the action type (e.g., 'move', 'attack')
            handler: Function that executes the action and returns events

        Example:
            def attack_handler(action: Action, world: World) -> list[Event]:
                attacker = action.params['attacker']
                target = action.params['target']
                damage = action.params['damage']
                # ... apply damage ...
                return [DamageDealtEvent(attacker=attacker, target=target, amount=damage)]

            pipeline.register_handler('attack', attack_handler)
        """
        if not action_name:
            raise ValueError("Action name cannot be empty")
        self._handlers[action_name] = handler

    def register_validator(self, action_name: str, validator: ActionValidator) -> None:
        """Register an action validator.

        The validator is called during the validation phase before any rules.
        It should return None if valid, or an error string if invalid.

        Args:
            action_name: Name of the action type
            validator: Function that validates action parameters

        Example:
            def move_validator(action: Action, world: World) -> str | None:
                if 'entity' not in action.params:
                    return "Missing required parameter: entity"
                if 'target' not in action.params:
                    return "Missing required parameter: target"
                return None

            pipeline.register_validator('move', move_validator)
        """
        if not action_name:
            raise ValueError("Action name cannot be empty")
        self._validators[action_name] = validator

    def add_pre_rule(self, action_name: str, rule: ActionRule, priority: int = 0) -> None:
        """Add a pre-execution rule for an action.

        Pre-rules run before the action handler. They can:
        - Cancel the action
        - Modify action parameters
        - Access world state

        Rules with higher priority run first.

        Args:
            action_name: Name of the action type
            rule: Function that processes the action context
            priority: Priority for execution order (higher = earlier, default 0)

        Example:
            def check_range(ctx: ActionContext) -> None:
                entity = ctx.action.params['entity']
                target = ctx.action.params['target']
                pos = ctx.world.get_component(entity, Position)
                if pos.manhattan_distance(target) > 5:
                    ctx.cancel("Target is out of range")

            pipeline.add_pre_rule('move', check_range, priority=10)
        """
        if not action_name:
            raise ValueError("Action name cannot be empty")
        if action_name not in self._pre_rules:
            self._pre_rules[action_name] = []
        self._pre_rules[action_name].append(_RuleEntry(rule=rule, priority=priority))
        # Sort by priority (highest first)
        self._pre_rules[action_name].sort(key=lambda x: -x.priority)

    def add_post_rule(self, action_name: str, rule: ActionRule, priority: int = 0) -> None:
        """Add a post-execution rule for an action.

        Post-rules run after the action handler completes successfully.
        They can react to the completed action but cannot cancel it.

        Rules with higher priority run first.

        Args:
            action_name: Name of the action type
            rule: Function that processes the action context
            priority: Priority for execution order (higher = earlier, default 0)

        Example:
            def log_movement(ctx: ActionContext) -> None:
                entity = ctx.action.params['entity']
                target = ctx.action.params['target']
                print(f"Entity {entity} moved to {target}")

            pipeline.add_post_rule('move', log_movement)
        """
        if not action_name:
            raise ValueError("Action name cannot be empty")
        if action_name not in self._post_rules:
            self._post_rules[action_name] = []
        self._post_rules[action_name].append(_RuleEntry(rule=rule, priority=priority))
        # Sort by priority (highest first)
        self._post_rules[action_name].sort(key=lambda x: -x.priority)

    def execute(self, action: Action, world: World) -> ActionResult:
        """Execute an action through the pipeline.

        Pipeline stages:
        1. Check if handler exists
        2. Validate parameters
        3. Run pre-rules (can cancel/modify)
        4. Execute handler (if not cancelled)
        5. Run post-rules
        6. Return result with events

        Args:
            action: The action to execute
            world: The game world

        Returns:
            ActionResult containing success state, events, or error information

        Example:
            action = Action('move', {'entity': player, 'target': Position(5, 5)})
            result = pipeline.execute(action, world)

            if result.success:
                for event in result.events:
                    event_bus.emit(event)
            else:
                print(f"Action failed: {result.cancel_reason or result.error}")
        """
        # Stage 1: Check if handler exists
        if action.name not in self._handlers:
            return ActionResult.error_result(
                action=action,
                error=f"No handler registered for action: {action.name}"
            )

        # Stage 2: Validate parameters
        if action.name in self._validators:
            validator = self._validators[action.name]
            error = validator(action, world)
            if error:
                return ActionResult.error_result(action=action, error=error)

        # Stage 3: Run pre-rules
        context = ActionContext(action=action, world=world, phase='pre')
        if action.name in self._pre_rules:
            for entry in self._pre_rules[action.name]:
                try:
                    entry.rule(context)
                except Exception as e:
                    return ActionResult.error_result(
                        action=action,
                        error=f"Pre-rule error: {type(e).__name__}: {e}"
                    )

                # Check if cancelled
                if context.cancelled:
                    return ActionResult.cancelled_result(
                        action=action,
                        reason=context.cancel_reason or "Action cancelled by pre-rule"
                    )

        # Apply modified parameters to action
        if context.modified_params:
            action.params.update(context.modified_params)

        # Stage 4: Execute handler
        try:
            handler = self._handlers[action.name]
            events = handler(action, world)
        except Exception as e:
            return ActionResult.error_result(
                action=action,
                error=f"Handler error: {type(e).__name__}: {e}"
            )

        # Stage 5: Run post-rules
        post_context = ActionContext(action=action, world=world, phase='post')
        if action.name in self._post_rules:
            for entry in self._post_rules[action.name]:
                try:
                    entry.rule(post_context)
                except Exception as e:
                    # Post-rules can't cancel, but we log errors
                    # In a real system, might want to emit error event
                    print(f"Warning: Post-rule error: {type(e).__name__}: {e}")

        # Stage 6: Return success result
        return ActionResult.success_result(action=action, events=events or [])
