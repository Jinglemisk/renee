"""Rule class definition for Renee.

Rules are game logic that run before or after actions, allowing validation,
modification, cancellation, and side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from renee.rules.context import ActionContext


@dataclass
class Rule:
    """A game rule that intercepts actions in the action pipeline.

    Rules can run before actions (pre-rules) to validate or modify them,
    or after actions (post-rules) to apply side effects or react to changes.

    Attributes:
        name: Human-readable name for the rule.
        phase: When the rule executes ('pre' or 'post').
        priority: Execution order (lower values run first).
        action_types: Which action types this rule applies to ('*' for all).
        condition: Optional function to check if rule should run.
        handler: The rule's logic.
        intent: Optional natural language description of rule's purpose.

    Example:
        Rule(
            name="check_stunned",
            phase="pre",
            priority=10,
            action_types=["move"],
            condition=lambda ctx: ctx.world.has_component(ctx.entity, Stunned),
            handler=lambda ctx: ctx.cancel("Entity is stunned"),
            intent="Prevent movement if entity is stunned"
        )
    """

    name: str
    phase: str  # 'pre' or 'post'
    priority: int  # Lower = earlier execution
    action_types: list[str]  # Which actions this applies to ('*' for all)
    condition: Callable[[ActionContext], bool] | None  # When rule applies
    handler: Callable[[ActionContext], None]  # What rule does
    intent: str | None = None  # Natural language description

    def __post_init__(self) -> None:
        """Validate rule configuration."""
        if self.phase not in ("pre", "post"):
            raise ValueError(f"Rule phase must be 'pre' or 'post', got '{self.phase}'")

        if not self.action_types:
            raise ValueError("Rule must specify at least one action type")

        if not callable(self.handler):
            raise ValueError("Rule handler must be callable")

        if self.condition is not None and not callable(self.condition):
            raise ValueError("Rule condition must be callable or None")

    def applies_to(self, action_type: str) -> bool:
        """Check if this rule applies to a given action type.

        Args:
            action_type: The action type to check.

        Returns:
            True if this rule should be evaluated for this action type.
        """
        return "*" in self.action_types or action_type in self.action_types

    def should_execute(self, ctx: ActionContext) -> bool:
        """Check if this rule should execute for a given context.

        Args:
            ctx: The action context.

        Returns:
            True if the rule's condition is met (or no condition exists).
        """
        if self.condition is None:
            return True
        return self.condition(ctx)

    def execute(self, ctx: ActionContext) -> None:
        """Execute this rule's handler.

        Args:
            ctx: The action context to process.
        """
        self.handler(ctx)

    def to_dict(self) -> dict:
        """Convert rule to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the rule.
        """
        return {
            "name": self.name,
            "phase": self.phase,
            "priority": self.priority,
            "action_types": self.action_types,
            "has_condition": self.condition is not None,
            "intent": self.intent,
        }
