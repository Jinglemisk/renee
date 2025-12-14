"""RuleEngine implementation for Renee.

The RuleEngine manages the registration and execution of game rules.
It applies rules in order based on priority and phase (pre/post).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from renee.rules.context import ActionContext
    from renee.rules.rule import Rule


class RuleEngine:
    """Manages registration and execution of game rules.

    The RuleEngine is responsible for:
    - Registering rules from decorators or manual calls
    - Finding rules that apply to specific actions and phases
    - Executing rules in priority order
    - Providing introspection for AI agents

    Example:
        engine = RuleEngine()

        # Register a rule
        engine.register(Rule(
            name="check_range",
            phase="pre",
            priority=10,
            action_types=["attack"],
            handler=lambda ctx: validate_attack_range(ctx),
            intent="Ensure attack is within range"
        ))

        # Get applicable rules
        pre_rules = engine.get_rules("attack", "pre")

        # Apply rules to an action context
        engine.apply_rules(ctx, "pre")
    """

    def __init__(self) -> None:
        """Initialize the rule engine."""
        self._rules: list[Rule] = []

    def register(self, rule: Rule) -> None:
        """Register a rule with the engine.

        Rules are stored and sorted by priority. Lower priority values
        execute first.

        Args:
            rule: The rule to register.

        Example:
            engine.register(Rule(
                name="poison_damage",
                phase="post",
                priority=20,
                action_types=["attack"],
                handler=apply_poison,
                intent="Apply poison damage after successful attack"
            ))
        """
        self._rules.append(rule)
        # Keep rules sorted by priority for efficient execution
        self._rules.sort(key=lambda r: r.priority)

    def unregister(self, rule_name: str) -> bool:
        """Unregister a rule by name.

        Args:
            rule_name: Name of the rule to remove.

        Returns:
            True if rule was found and removed, False otherwise.
        """
        for i, rule in enumerate(self._rules):
            if rule.name == rule_name:
                self._rules.pop(i)
                return True
        return False

    def get_rules(self, action_type: str, phase: str) -> list[Rule]:
        """Get all rules that apply to a specific action type and phase.

        Args:
            action_type: The action type (e.g., 'move', 'attack').
            phase: The execution phase ('pre' or 'post').

        Returns:
            List of applicable rules, sorted by priority.

        Example:
            # Get all pre-rules for attack actions
            attack_pre_rules = engine.get_rules("attack", "pre")
        """
        return [
            rule
            for rule in self._rules
            if rule.phase == phase and rule.applies_to(action_type)
        ]

    def apply_rules(self, ctx: ActionContext, phase: str) -> None:
        """Apply all matching rules to an action context.

        Rules are executed in priority order (lowest priority first).
        If a rule cancels the action (during pre-phase), remaining rules
        are still executed to allow for logging or other side effects.

        Args:
            ctx: The action context to process.
            phase: The execution phase ('pre' or 'post').

        Example:
            ctx = ActionContext(
                action=Action(name="move", params={"entity": 1, "target": (5, 5)}),
                world=world
            )
            engine.apply_rules(ctx, "pre")

            if not ctx.is_cancelled():
                # Execute the action
                pass
        """
        action_type = ctx.action.name
        applicable_rules = self.get_rules(action_type, phase)

        for rule in applicable_rules:
            # Check if rule's condition is met
            if rule.should_execute(ctx):
                try:
                    rule.execute(ctx)
                except Exception as e:
                    # Log but don't crash - allow other rules to execute
                    print(f"Error executing rule '{rule.name}': {e}")

    def list_rules(self, action_type: str | None = None, phase: str | None = None) -> list[Rule]:
        """List all registered rules, optionally filtered.

        Args:
            action_type: Filter by action type (optional).
            phase: Filter by phase (optional).

        Returns:
            List of rules matching the filters.

        Example:
            # List all rules
            all_rules = engine.list_rules()

            # List only attack pre-rules
            attack_pre_rules = engine.list_rules(action_type="attack", phase="pre")
        """
        rules = self._rules

        if action_type is not None:
            rules = [r for r in rules if r.applies_to(action_type)]

        if phase is not None:
            rules = [r for r in rules if r.phase == phase]

        return rules

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

    def clear(self) -> None:
        """Remove all registered rules.

        This is useful for testing or resetting the engine.
        """
        self._rules.clear()

    def rule_count(self) -> int:
        """Get the total number of registered rules.

        Returns:
            Number of rules.
        """
        return len(self._rules)

    def to_json(self, indent: int | None = None) -> str:
        """Export rules to JSON for AI introspection.

        This provides a machine-readable view of all registered rules,
        useful for AI agents to understand game logic.

        Args:
            indent: JSON indentation level (None for compact).

        Returns:
            JSON string representation of all rules.

        Example:
            json_output = engine.to_json(indent=2)
            # AI can parse this to understand what rules exist
        """
        rules_data = {
            "rule_count": len(self._rules),
            "rules": [rule.to_dict() for rule in self._rules],
            "rules_by_phase": {
                "pre": [r.to_dict() for r in self._rules if r.phase == "pre"],
                "post": [r.to_dict() for r in self._rules if r.phase == "post"],
            },
        }
        return json.dumps(rules_data, indent=indent)

    def get_summary(self) -> dict:
        """Get a summary of registered rules.

        Returns:
            Dictionary with rule statistics.

        Example:
            summary = engine.get_summary()
            print(f"Total rules: {summary['total']}")
            print(f"Pre-rules: {summary['pre_rules']}")
            print(f"Post-rules: {summary['post_rules']}")
        """
        pre_rules = [r for r in self._rules if r.phase == "pre"]
        post_rules = [r for r in self._rules if r.phase == "post"]

        action_types = set()
        for rule in self._rules:
            action_types.update(rule.action_types)

        return {
            "total": len(self._rules),
            "pre_rules": len(pre_rules),
            "post_rules": len(post_rules),
            "action_types_covered": sorted(action_types),
            "rules_with_conditions": sum(1 for r in self._rules if r.condition is not None),
            "rules_with_intent": sum(1 for r in self._rules if r.intent is not None),
        }
