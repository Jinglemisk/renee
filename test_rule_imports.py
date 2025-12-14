#!/usr/bin/env python3
"""Quick import verification script for the rule engine."""

import sys

def test_imports():
    """Test that all rule engine imports work correctly."""
    print("Testing rule engine imports...")

    try:
        # Test core imports
        from renee.rules import (
            Rule,
            RuleEngine,
            ActionContext,
            Action,
            rule,
            pre_rule,
            post_rule,
            set_global_engine,
            get_global_engine,
            collect_rules,
            register_module_rules,
        )
        print("  ✓ Core imports successful")

        # Test that we can create instances
        engine = RuleEngine()
        print(f"  ✓ RuleEngine created: {engine}")

        # Test that we can create a rule
        test_rule = Rule(
            name="test",
            phase="pre",
            priority=0,
            action_types=["test"],
            condition=None,
            handler=lambda ctx: None,
        )
        print(f"  ✓ Rule created: {test_rule}")

        # Test registration
        engine.register(test_rule)
        print(f"  ✓ Rule registered: {engine.rule_count()} rules")

        # Test context
        from renee.ecs.world import World
        world = World()
        action = Action(name="test", params={})
        ctx = ActionContext(action=action, world=world)
        print(f"  ✓ ActionContext created: {ctx}")

        # Test decorators
        set_global_engine(engine)

        @pre_rule(action="test", priority=10)
        def test_decorator_rule(ctx):
            pass

        print(f"  ✓ Decorator rule registered: {engine.rule_count()} rules")

        # Test JSON export
        json_output = engine.to_json()
        print(f"  ✓ JSON export successful: {len(json_output)} chars")

        print("\n✓ All imports and basic functionality working!")
        return True

    except Exception as e:
        print(f"\n✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
