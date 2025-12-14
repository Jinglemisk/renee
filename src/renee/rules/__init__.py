"""Rule Engine for Renee.

The Rule Engine provides Python decorators for defining game logic.
Rules intercept actions in the action pipeline, allowing validation,
modification, cancellation, and side effects.

Example:
    from renee.rules import RuleEngine, pre_rule, post_rule, set_global_engine

    # Set up engine
    engine = RuleEngine()
    set_global_engine(engine)

    # Define pre-rule for validation
    @pre_rule(action='move', priority=10, intent="Prevent movement if stunned")
    def check_stunned(ctx):
        entity = ctx.get_param('entity')
        if ctx.world.has_component(entity, Stunned):
            ctx.cancel("Entity is stunned")

    # Define post-rule for side effects
    @post_rule(action='attack', priority=20, intent="Apply poison damage")
    def apply_poison(ctx):
        attacker = ctx.get_param('attacker')
        target = ctx.get_param('target')
        if ctx.world.has_component(attacker, PoisonWeapon):
            poison = ctx.world.get_component(attacker, PoisonWeapon)
            ctx.world.add_component(target, Poisoned(damage=poison.damage))

    # Apply rules to an action context
    from renee.rules import ActionContext, Action

    ctx = ActionContext(
        action=Action(name="move", params={"entity": 1, "target": (5, 5)}),
        world=world
    )
    engine.apply_rules(ctx, "pre")

    if not ctx.is_cancelled():
        # Execute the action
        pass
"""

from renee.rules.context import Action, ActionContext
from renee.rules.decorators import (
    collect_rules,
    get_global_engine,
    post_rule,
    pre_rule,
    register_module_rules,
    rule,
    set_global_engine,
)
from renee.rules.engine import RuleEngine
from renee.rules.rule import Rule

__all__ = [
    # Core classes
    "Rule",
    "RuleEngine",
    "ActionContext",
    "Action",
    # Decorators
    "rule",
    "pre_rule",
    "post_rule",
    # Global engine management
    "set_global_engine",
    "get_global_engine",
    # Utilities
    "collect_rules",
    "register_module_rules",
]
