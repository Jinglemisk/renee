"""Python-decorator rule engine (no custom DSL).

Rules are Python functions decorated with @rule. The engine executes them
in priority order (higher priority first) during action processing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol, TYPE_CHECKING

RulePhase = Literal["pre", "post"]

if TYPE_CHECKING:  # pragma: no cover
    from renee.actions.types import ActionContext


class RuleFn(Protocol):
    def __call__(self, ctx: "ActionContext") -> Any: ...


RulePredicate = Callable[["ActionContext"], bool]


@dataclass(frozen=True, slots=True)
class Rule:
    """A game rule that runs during action processing.

    Attributes:
        name: Unique rule identifier.
        phase: When the rule runs ("pre" or "post").
        priority: Execution order (higher = earlier).
        fn: The rule function.
        when: Optional predicate for conditional execution.
        intent: Optional natural language description of the rule's purpose.
        action_types: Optional list of action types this rule applies to.
                     If None or empty, applies to all actions.
    """
    name: str
    phase: RulePhase
    priority: int
    fn: RuleFn
    when: RulePredicate | None = None
    intent: str | None = None
    action_types: tuple[str, ...] = field(default_factory=tuple)

    def applies(self, ctx: "ActionContext") -> bool:
        """Check if this rule applies to the given context."""
        # Check action type filter
        if self.action_types and ctx.action not in self.action_types:
            return False
        # Check predicate
        return True if self.when is None else bool(self.when(ctx))

    def to_dict(self) -> dict[str, Any]:
        """Convert rule to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "phase": self.phase,
            "priority": self.priority,
            "intent": self.intent,
            "action_types": list(self.action_types) if self.action_types else [],
            "has_condition": self.when is not None,
        }


def rule(
    *,
    phase: RulePhase = "pre",
    priority: int = 0,
    when: RulePredicate | None = None,
    intent: str | None = None,
    actions: tuple[str, ...] | list[str] | None = None,
) -> Callable[[RuleFn], RuleFn]:
    """Decorator to mark a function as a rule.

    Args:
        phase: When the rule runs ("pre" or "post"). Default: "pre".
        priority: Execution order. Higher = earlier. Default: 0.
        when: Optional predicate for conditional execution.
        intent: Optional description of the rule's purpose.
        actions: Optional list of action types this rule applies to.

    Example:
        @rule(phase="pre", priority=10, intent="Ensure target is within range")
        def check_range(ctx: ActionContext) -> None:
            if distance > max_range:
                ctx.cancel("Target is out of range")

        @rule(phase="post", actions=("resolve",), intent="Apply action effects")
        def apply_effects(ctx: ActionContext) -> None:
            # Only runs after "resolve" actions
            pass
    """
    action_types = tuple(actions) if actions else ()

    def decorator(fn: RuleFn) -> RuleFn:
        r = Rule(
            name=getattr(fn, "__name__", "rule"),
            phase=phase,
            priority=priority,
            fn=fn,
            when=when,
            intent=intent,
            action_types=action_types,
        )
        setattr(fn, "__renee_rule__", r)
        return fn

    return decorator


class RuleEngine:
    """Stores and executes pre/post rules in priority order.

    The RuleEngine manages the registration and execution of game rules.
    Rules can be registered either as Rule objects or as decorated functions.

    Example:
        engine = RuleEngine()

        @rule(phase="pre", priority=10, intent="Check range")
        def check_range(ctx):
            if too_far:
                ctx.cancel("Out of range")

        engine.register(check_range)

        # Or register directly
        engine.register(Rule(
            name="check_health",
            phase="pre",
            priority=5,
            fn=lambda ctx: ...,
            intent="Ensure entity has enough health"
        ))
    """

    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def register(self, rule_or_fn: Rule | RuleFn) -> None:
        """Register a rule with the engine.

        Args:
            rule_or_fn: A Rule object or a function decorated with @rule.

        Raises:
            TypeError: If the argument is not a Rule or decorated function.
        """
        if isinstance(rule_or_fn, Rule):
            self._rules.append(rule_or_fn)
            return
        r = getattr(rule_or_fn, "__renee_rule__", None)
        if not isinstance(r, Rule):
            raise TypeError("Expected a Rule or a function decorated with @rule")
        self._rules.append(r)

    def unregister(self, name: str) -> bool:
        """Unregister a rule by name.

        Args:
            name: Name of the rule to remove.

        Returns:
            True if rule was found and removed, False otherwise.
        """
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                return True
        return False

    def get_rule(self, name: str) -> Rule | None:
        """Get a specific rule by name.

        Args:
            name: The rule name.

        Returns:
            The rule if found, None otherwise.
        """
        for rule in self._rules:
            if rule.name == name:
                return rule
        return None

    def rules(self, *, phase: RulePhase | None = None, action: str | None = None) -> list[Rule]:
        """List rules, optionally filtered by phase and/or action.

        Args:
            phase: Filter by phase ("pre" or "post").
            action: Filter by action type.

        Returns:
            List of matching rules.
        """
        result = self._rules
        if phase is not None:
            result = [r for r in result if r.phase == phase]
        if action is not None:
            result = [r for r in result if not r.action_types or action in r.action_types]
        return list(result)

    def run(self, ctx: "ActionContext", *, phase: RulePhase) -> None:
        """Execute all rules for a given phase.

        Rules are executed in priority order (higher priority first).
        If a pre-rule cancels the action, remaining rules are skipped.

        Args:
            ctx: The action context.
            phase: The phase to run ("pre" or "post").
        """
        # Higher priority first; stable sort keeps registration order for ties.
        ordered = sorted(
            (r for r in self._rules if r.phase == phase),
            key=lambda r: r.priority,
            reverse=True,
        )
        for r in ordered:
            if ctx.cancelled and phase == "pre":
                return
            if r.applies(ctx):
                r.fn(ctx)

    def clear(self) -> None:
        """Remove all registered rules."""
        self._rules.clear()

    def rule_count(self) -> int:
        """Get the total number of registered rules."""
        return len(self._rules)

    # ==================== Introspection ====================

    def to_json(self, indent: int | None = None) -> str:
        """Export rules to JSON for AI introspection.

        Args:
            indent: JSON indentation level (None for compact).

        Returns:
            JSON string representation of all rules.
        """
        rules_data = {
            "rule_count": len(self._rules),
            "rules": [r.to_dict() for r in self._rules],
            "rules_by_phase": {
                "pre": [r.to_dict() for r in self._rules if r.phase == "pre"],
                "post": [r.to_dict() for r in self._rules if r.phase == "post"],
            },
        }
        return json.dumps(rules_data, indent=indent)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of registered rules.

        Returns:
            Dictionary with rule statistics.
        """
        pre_rules = [r for r in self._rules if r.phase == "pre"]
        post_rules = [r for r in self._rules if r.phase == "post"]

        action_types: set[str] = set()
        for rule in self._rules:
            action_types.update(rule.action_types)

        return {
            "total": len(self._rules),
            "pre_rules": len(pre_rules),
            "post_rules": len(post_rules),
            "action_types_covered": sorted(action_types),
            "rules_with_conditions": sum(1 for r in self._rules if r.when is not None),
            "rules_with_intent": sum(1 for r in self._rules if r.intent is not None),
        }

