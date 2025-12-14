"""Tests for the Rule Engine.

This module tests the core rule engine functionality including:
- Rule registration and execution
- Rule decorators (@pre_rule, @post_rule)
- Action context and modification
- Rule priority ordering
- Conditional rules
"""

import json

import pytest

from renee.ecs.world import World
from renee.rules import (
    Action,
    ActionContext,
    Rule,
    RuleEngine,
    post_rule,
    pre_rule,
    set_global_engine,
)
from renee.types import EntityId


class TestRule:
    """Test the Rule class."""

    def test_rule_creation(self):
        """Test basic rule creation."""

        def handler(ctx):
            pass

        rule = Rule(
            name="test_rule",
            phase="pre",
            priority=10,
            action_types=["move"],
            condition=None,
            handler=handler,
            intent="Test rule",
        )

        assert rule.name == "test_rule"
        assert rule.phase == "pre"
        assert rule.priority == 10
        assert rule.action_types == ["move"]
        assert rule.intent == "Test rule"

    def test_rule_invalid_phase(self):
        """Test that invalid phase raises error."""
        with pytest.raises(ValueError, match="phase must be"):

            Rule(
                name="bad_rule",
                phase="invalid",
                priority=0,
                action_types=["move"],
                condition=None,
                handler=lambda ctx: None,
            )

    def test_rule_applies_to(self):
        """Test rule action type matching."""
        rule = Rule(
            name="move_rule",
            phase="pre",
            priority=0,
            action_types=["move"],
            condition=None,
            handler=lambda ctx: None,
        )

        assert rule.applies_to("move")
        assert not rule.applies_to("attack")

    def test_rule_wildcard_applies_to_all(self):
        """Test wildcard rule applies to all actions."""
        rule = Rule(
            name="wildcard_rule",
            phase="pre",
            priority=0,
            action_types=["*"],
            condition=None,
            handler=lambda ctx: None,
        )

        assert rule.applies_to("move")
        assert rule.applies_to("attack")
        assert rule.applies_to("any_action")

    def test_rule_multiple_action_types(self):
        """Test rule with multiple action types."""
        rule = Rule(
            name="combat_rule",
            phase="pre",
            priority=0,
            action_types=["attack", "defend"],
            condition=None,
            handler=lambda ctx: None,
        )

        assert rule.applies_to("attack")
        assert rule.applies_to("defend")
        assert not rule.applies_to("move")

    def test_rule_to_dict(self):
        """Test rule serialization to dict."""
        rule = Rule(
            name="test_rule",
            phase="pre",
            priority=10,
            action_types=["move"],
            condition=lambda ctx: True,
            handler=lambda ctx: None,
            intent="Test intent",
        )

        rule_dict = rule.to_dict()
        assert rule_dict["name"] == "test_rule"
        assert rule_dict["phase"] == "pre"
        assert rule_dict["priority"] == 10
        assert rule_dict["action_types"] == ["move"]
        assert rule_dict["has_condition"] is True
        assert rule_dict["intent"] == "Test intent"


class TestActionContext:
    """Test the ActionContext class."""

    def test_context_creation(self):
        """Test basic context creation."""
        world = World()
        action = Action(name="move", params={"entity": 1, "target": (5, 5)})
        ctx = ActionContext(action=action, world=world)

        assert ctx.action.name == "move"
        assert ctx.world is world
        assert not ctx.is_cancelled()

    def test_context_cancel(self):
        """Test action cancellation."""
        world = World()
        action = Action(name="move", params={})
        ctx = ActionContext(action=action, world=world)

        ctx.cancel("Blocked")
        assert ctx.is_cancelled()
        assert ctx.cancel_reason == "Blocked"

    def test_context_modify(self):
        """Test action parameter modification."""
        world = World()
        action = Action(name="attack", params={"damage": 10})
        ctx = ActionContext(action=action, world=world)

        ctx.modify(damage=15)
        assert ctx.action.params["damage"] == 15

    def test_context_get_param(self):
        """Test getting action parameters."""
        world = World()
        action = Action(name="attack", params={"damage": 10})
        ctx = ActionContext(action=action, world=world)

        assert ctx.get_param("damage") == 10
        assert ctx.get_param("missing") is None
        assert ctx.get_param("missing", default=5) == 5

    def test_context_data_storage(self):
        """Test custom data storage in context."""
        world = World()
        action = Action(name="move", params={})
        ctx = ActionContext(action=action, world=world)

        ctx.set_data("key1", "value1")
        ctx.set_data("key2", 42)

        assert ctx.get_data("key1") == "value1"
        assert ctx.get_data("key2") == 42
        assert ctx.get_data("missing") is None
        assert ctx.get_data("missing", default="default") == "default"


class TestRuleEngine:
    """Test the RuleEngine class."""

    def test_engine_creation(self):
        """Test basic engine creation."""
        engine = RuleEngine()
        assert engine.rule_count() == 0

    def test_register_rule(self):
        """Test rule registration."""
        engine = RuleEngine()
        rule = Rule(
            name="test_rule",
            phase="pre",
            priority=0,
            action_types=["move"],
            condition=None,
            handler=lambda ctx: None,
        )

        engine.register(rule)
        assert engine.rule_count() == 1

    def test_get_rules_by_action_and_phase(self):
        """Test getting rules by action type and phase."""
        engine = RuleEngine()

        rule1 = Rule(
            name="move_pre",
            phase="pre",
            priority=0,
            action_types=["move"],
            condition=None,
            handler=lambda ctx: None,
        )
        rule2 = Rule(
            name="move_post",
            phase="post",
            priority=0,
            action_types=["move"],
            condition=None,
            handler=lambda ctx: None,
        )
        rule3 = Rule(
            name="attack_pre",
            phase="pre",
            priority=0,
            action_types=["attack"],
            condition=None,
            handler=lambda ctx: None,
        )

        engine.register(rule1)
        engine.register(rule2)
        engine.register(rule3)

        move_pre = engine.get_rules("move", "pre")
        assert len(move_pre) == 1
        assert move_pre[0].name == "move_pre"

        move_post = engine.get_rules("move", "post")
        assert len(move_post) == 1
        assert move_post[0].name == "move_post"

        attack_pre = engine.get_rules("attack", "pre")
        assert len(attack_pre) == 1
        assert attack_pre[0].name == "attack_pre"

    def test_apply_rules(self):
        """Test applying rules to a context."""
        engine = RuleEngine()
        world = World()
        executed = []

        def handler1(ctx):
            executed.append("rule1")

        def handler2(ctx):
            executed.append("rule2")

        rule1 = Rule(
            name="rule1",
            phase="pre",
            priority=0,
            action_types=["move"],
            condition=None,
            handler=handler1,
        )
        rule2 = Rule(
            name="rule2",
            phase="pre",
            priority=1,
            action_types=["move"],
            condition=None,
            handler=handler2,
        )

        engine.register(rule1)
        engine.register(rule2)

        action = Action(name="move", params={})
        ctx = ActionContext(action=action, world=world)
        engine.apply_rules(ctx, "pre")

        assert executed == ["rule1", "rule2"]

    def test_rule_priority_ordering(self):
        """Test that rules execute in priority order."""
        engine = RuleEngine()
        world = World()
        execution_order = []

        def make_handler(name):
            def handler(ctx):
                execution_order.append(name)

            return handler

        # Register rules out of priority order
        engine.register(
            Rule(
                name="priority_30",
                phase="pre",
                priority=30,
                action_types=["move"],
                condition=None,
                handler=make_handler("30"),
            )
        )
        engine.register(
            Rule(
                name="priority_10",
                phase="pre",
                priority=10,
                action_types=["move"],
                condition=None,
                handler=make_handler("10"),
            )
        )
        engine.register(
            Rule(
                name="priority_20",
                phase="pre",
                priority=20,
                action_types=["move"],
                condition=None,
                handler=make_handler("20"),
            )
        )

        action = Action(name="move", params={})
        ctx = ActionContext(action=action, world=world)
        engine.apply_rules(ctx, "pre")

        # Should execute in priority order: 10, 20, 30
        assert execution_order == ["10", "20", "30"]

    def test_rule_with_condition(self):
        """Test conditional rule execution."""
        engine = RuleEngine()
        world = World()
        executed = []

        def condition(ctx):
            return ctx.get_param("should_run", False)

        def handler(ctx):
            executed.append("executed")

        rule = Rule(
            name="conditional_rule",
            phase="pre",
            priority=0,
            action_types=["move"],
            condition=condition,
            handler=handler,
        )

        engine.register(rule)

        # Test with condition False
        action1 = Action(name="move", params={"should_run": False})
        ctx1 = ActionContext(action=action1, world=world)
        engine.apply_rules(ctx1, "pre")
        assert executed == []

        # Test with condition True
        action2 = Action(name="move", params={"should_run": True})
        ctx2 = ActionContext(action=action2, world=world)
        engine.apply_rules(ctx2, "pre")
        assert executed == ["executed"]

    def test_action_cancellation(self):
        """Test that rules can cancel actions."""
        engine = RuleEngine()
        world = World()

        def cancel_rule(ctx):
            ctx.cancel("Action not allowed")

        rule = Rule(
            name="cancel_rule",
            phase="pre",
            priority=0,
            action_types=["move"],
            condition=None,
            handler=cancel_rule,
        )

        engine.register(rule)

        action = Action(name="move", params={})
        ctx = ActionContext(action=action, world=world)
        engine.apply_rules(ctx, "pre")

        assert ctx.is_cancelled()
        assert ctx.cancel_reason == "Action not allowed"

    def test_action_modification(self):
        """Test that rules can modify action parameters."""
        engine = RuleEngine()
        world = World()

        def modify_rule(ctx):
            damage = ctx.get_param("damage", 0)
            ctx.modify(damage=damage * 2)

        rule = Rule(
            name="double_damage",
            phase="pre",
            priority=0,
            action_types=["attack"],
            condition=None,
            handler=modify_rule,
        )

        engine.register(rule)

        action = Action(name="attack", params={"damage": 10})
        ctx = ActionContext(action=action, world=world)
        engine.apply_rules(ctx, "pre")

        assert ctx.get_param("damage") == 20

    def test_to_json(self):
        """Test JSON serialization of rules."""
        engine = RuleEngine()

        rule1 = Rule(
            name="rule1",
            phase="pre",
            priority=10,
            action_types=["move"],
            condition=None,
            handler=lambda ctx: None,
            intent="Test rule 1",
        )
        rule2 = Rule(
            name="rule2",
            phase="post",
            priority=20,
            action_types=["attack"],
            condition=None,
            handler=lambda ctx: None,
        )

        engine.register(rule1)
        engine.register(rule2)

        json_str = engine.to_json()
        data = json.loads(json_str)

        assert data["rule_count"] == 2
        assert len(data["rules"]) == 2
        assert len(data["rules_by_phase"]["pre"]) == 1
        assert len(data["rules_by_phase"]["post"]) == 1

    def test_list_rules(self):
        """Test listing rules with filters."""
        engine = RuleEngine()

        engine.register(
            Rule(
                name="move_pre",
                phase="pre",
                priority=0,
                action_types=["move"],
                condition=None,
                handler=lambda ctx: None,
            )
        )
        engine.register(
            Rule(
                name="attack_pre",
                phase="pre",
                priority=0,
                action_types=["attack"],
                condition=None,
                handler=lambda ctx: None,
            )
        )
        engine.register(
            Rule(
                name="move_post",
                phase="post",
                priority=0,
                action_types=["move"],
                condition=None,
                handler=lambda ctx: None,
            )
        )

        all_rules = engine.list_rules()
        assert len(all_rules) == 3

        pre_rules = engine.list_rules(phase="pre")
        assert len(pre_rules) == 2

        move_rules = engine.list_rules(action_type="move")
        assert len(move_rules) == 2

        move_pre = engine.list_rules(action_type="move", phase="pre")
        assert len(move_pre) == 1

    def test_get_summary(self):
        """Test getting rule engine summary."""
        engine = RuleEngine()

        engine.register(
            Rule(
                name="rule1",
                phase="pre",
                priority=0,
                action_types=["move"],
                condition=lambda ctx: True,
                handler=lambda ctx: None,
                intent="Test intent",
            )
        )
        engine.register(
            Rule(
                name="rule2",
                phase="post",
                priority=0,
                action_types=["attack"],
                condition=None,
                handler=lambda ctx: None,
            )
        )

        summary = engine.get_summary()
        assert summary["total"] == 2
        assert summary["pre_rules"] == 1
        assert summary["post_rules"] == 1
        assert "move" in summary["action_types_covered"]
        assert "attack" in summary["action_types_covered"]
        assert summary["rules_with_conditions"] == 1
        assert summary["rules_with_intent"] == 1


class TestRuleDecorators:
    """Test rule decorators."""

    def test_pre_rule_decorator(self):
        """Test @pre_rule decorator."""
        engine = RuleEngine()
        set_global_engine(engine)

        @pre_rule(action="move", priority=10, intent="Test pre-rule")
        def test_rule(ctx):
            ctx.set_data("executed", True)

        assert engine.rule_count() == 1
        rule = engine.get_rule("test_rule")
        assert rule is not None
        assert rule.phase == "pre"
        assert rule.priority == 10
        assert rule.intent == "Test pre-rule"

    def test_post_rule_decorator(self):
        """Test @post_rule decorator."""
        engine = RuleEngine()
        set_global_engine(engine)

        @post_rule(action="attack", priority=20, intent="Test post-rule")
        def test_rule(ctx):
            pass

        assert engine.rule_count() == 1
        rule = engine.get_rule("test_rule")
        assert rule is not None
        assert rule.phase == "post"
        assert rule.priority == 20

    def test_decorator_with_multiple_actions(self):
        """Test decorator with multiple action types."""
        engine = RuleEngine()
        set_global_engine(engine)

        @pre_rule(action=["move", "attack"], priority=5)
        def multi_action_rule(ctx):
            pass

        rule = engine.get_rule("multi_action_rule")
        assert rule is not None
        assert rule.applies_to("move")
        assert rule.applies_to("attack")

    def test_decorator_with_condition(self):
        """Test decorator with when condition."""
        engine = RuleEngine()
        set_global_engine(engine)

        def condition(ctx):
            return ctx.get_param("enabled", False)

        @pre_rule(action="move", when=condition)
        def conditional_rule(ctx):
            ctx.set_data("executed", True)

        world = World()

        # Test with condition False
        action1 = Action(name="move", params={"enabled": False})
        ctx1 = ActionContext(action=action1, world=world)
        engine.apply_rules(ctx1, "pre")
        assert ctx1.get_data("executed") is None

        # Test with condition True
        action2 = Action(name="move", params={"enabled": True})
        ctx2 = ActionContext(action=action2, world=world)
        engine.apply_rules(ctx2, "pre")
        assert ctx2.get_data("executed") is True

    def test_decorator_with_specific_engine(self):
        """Test decorator registration with specific engine."""
        engine1 = RuleEngine()
        engine2 = RuleEngine()
        set_global_engine(engine1)

        @pre_rule(action="move", engine=engine2)
        def specific_engine_rule(ctx):
            pass

        # Should register with engine2, not global engine1
        assert engine1.rule_count() == 0
        assert engine2.rule_count() == 1


class TestIntegrationScenarios:
    """Test complete rule engine scenarios."""

    def test_combat_rules_example(self):
        """Test a realistic combat rules scenario."""
        engine = RuleEngine()
        world = World()

        # Create entities
        attacker = world.create_entity()
        defender = world.create_entity()

        # Track execution
        results = []

        # Pre-rule: Check range
        def check_range(ctx):
            results.append("check_range")

        # Pre-rule: Apply damage modifiers
        def apply_modifiers(ctx):
            results.append("apply_modifiers")
            damage = ctx.get_param("damage", 0)
            ctx.modify(damage=damage + 5)  # Bonus damage

        # Post-rule: Apply poison
        def apply_poison(ctx):
            results.append("apply_poison")

        # Post-rule: Log attack
        def log_attack(ctx):
            results.append("log_attack")

        engine.register(
            Rule(
                name="check_range",
                phase="pre",
                priority=10,
                action_types=["attack"],
                condition=None,
                handler=check_range,
            )
        )
        engine.register(
            Rule(
                name="apply_modifiers",
                phase="pre",
                priority=20,
                action_types=["attack"],
                condition=None,
                handler=apply_modifiers,
            )
        )
        engine.register(
            Rule(
                name="apply_poison",
                phase="post",
                priority=10,
                action_types=["attack"],
                condition=None,
                handler=apply_poison,
            )
        )
        engine.register(
            Rule(
                name="log_attack",
                phase="post",
                priority=20,
                action_types=["attack"],
                condition=None,
                handler=log_attack,
            )
        )

        # Execute attack action
        action = Action(
            name="attack",
            params={"attacker": attacker, "defender": defender, "damage": 10},
        )
        ctx = ActionContext(action=action, world=world)

        # Apply pre-rules
        engine.apply_rules(ctx, "pre")
        assert results == ["check_range", "apply_modifiers"]
        assert ctx.get_param("damage") == 15  # Modified by apply_modifiers

        # (Action would execute here)

        # Apply post-rules
        engine.apply_rules(ctx, "post")
        assert results == ["check_range", "apply_modifiers", "apply_poison", "log_attack"]
