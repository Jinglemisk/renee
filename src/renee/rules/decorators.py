"""Rule decorators for Renee.

Decorators provide a convenient way to define game rules using Python functions.
Rules can be registered with a global engine or a specific engine instance.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

from renee.rules.rule import Rule

if TYPE_CHECKING:
    from renee.rules.context import ActionContext
    from renee.rules.engine import RuleEngine

# Global rule engine for decorator registration
_global_engine: RuleEngine | None = None


def set_global_engine(engine: RuleEngine) -> None:
    """Set the global rule engine used by decorators.

    Args:
        engine: The RuleEngine instance to use globally.

    Example:
        engine = RuleEngine()
        set_global_engine(engine)

        # Now decorators will register with this engine
        @pre_rule(action='move', priority=10)
        def check_blocked(ctx):
            pass
    """
    global _global_engine
    _global_engine = engine


def get_global_engine() -> RuleEngine | None:
    """Get the current global rule engine.

    Returns:
        The global RuleEngine or None if not set.
    """
    return _global_engine


def rule(
    phase: str,
    action: str | list[str] = "*",
    priority: int = 0,
    when: Callable[[ActionContext], bool] | None = None,
    intent: str | None = None,
    engine: RuleEngine | None = None,
) -> Callable[[Callable[[ActionContext], None]], Callable[[ActionContext], None]]:
    """Decorator to register a function as a game rule.

    This is the base decorator that both @pre_rule and @post_rule use internally.
    You can use it directly for more explicit control over the phase.

    Args:
        phase: When the rule executes ('pre' or 'post').
        action: Action type(s) this rule applies to (default: '*' for all).
        priority: Execution order, lower runs first (default: 0).
        when: Optional condition function that must return True for rule to execute.
        intent: Optional natural language description of rule's purpose.
        engine: Specific RuleEngine to register with (default: global engine).

    Returns:
        Decorator function.

    Example:
        @rule(phase='pre', action='attack', priority=10, intent="Validate range")
        def check_range(ctx: ActionContext) -> None:
            attacker_pos = ctx.world.get_component(ctx.get_param('attacker'), Position)
            target_pos = ctx.world.get_component(ctx.get_param('target'), Position)
            if attacker_pos.manhattan_distance(target_pos) > 1:
                ctx.cancel("Target out of range")
    """

    def decorator(func: Callable[[ActionContext], None]) -> Callable[[ActionContext], None]:
        # Normalize action types to list
        action_types = [action] if isinstance(action, str) else action

        # Create the rule
        rule_obj = Rule(
            name=func.__name__,
            phase=phase,
            priority=priority,
            action_types=action_types,
            condition=when,
            handler=func,
            intent=intent or func.__doc__,
        )

        # Register with specified or global engine
        target_engine = engine or _global_engine
        if target_engine is not None:
            target_engine.register(rule_obj)
        else:
            # Store rule on function for later registration
            if not hasattr(func, "_renee_rules"):
                func._renee_rules = []  # type: ignore[attr-defined]
            func._renee_rules.append(rule_obj)  # type: ignore[attr-defined]

        @wraps(func)
        def wrapper(ctx: ActionContext) -> None:
            return func(ctx)

        # Attach rule object to wrapper for introspection
        wrapper._renee_rule = rule_obj  # type: ignore[attr-defined]

        return wrapper

    return decorator


def pre_rule(
    action: str | list[str] = "*",
    priority: int = 0,
    when: Callable[[ActionContext], bool] | None = None,
    intent: str | None = None,
    engine: RuleEngine | None = None,
) -> Callable[[Callable[[ActionContext], None]], Callable[[ActionContext], None]]:
    """Decorator for pre-action rules.

    Pre-rules execute before the action handler. They can:
    - Validate action parameters
    - Modify action parameters
    - Cancel the action
    - Add logging or side effects

    Args:
        action: Action type(s) this rule applies to (default: '*' for all).
        priority: Execution order, lower runs first (default: 0).
        when: Optional condition function that must return True for rule to execute.
        intent: Optional natural language description of rule's purpose.
        engine: Specific RuleEngine to register with (default: global engine).

    Returns:
        Decorator function.

    Example:
        @pre_rule(action='move', priority=10, intent="Prevent movement if stunned")
        def check_stunned(ctx: ActionContext) -> None:
            entity = ctx.get_param('entity')
            if ctx.world.has_component(entity, Stunned):
                ctx.cancel("Entity is stunned")

        @pre_rule(action=['attack', 'spell'], priority=5)
        def check_mana(ctx: ActionContext) -> None:
            caster = ctx.get_param('caster')
            cost = ctx.get_param('mana_cost', 0)
            mana = ctx.world.get_component(caster, Mana)
            if mana.current < cost:
                ctx.cancel("Not enough mana")
    """
    return rule(
        phase="pre",
        action=action,
        priority=priority,
        when=when,
        intent=intent,
        engine=engine,
    )


def post_rule(
    action: str | list[str] = "*",
    priority: int = 0,
    when: Callable[[ActionContext], bool] | None = None,
    intent: str | None = None,
    engine: RuleEngine | None = None,
) -> Callable[[Callable[[ActionContext], None]], Callable[[ActionContext], None]]:
    """Decorator for post-action rules.

    Post-rules execute after the action handler completes successfully.
    They can:
    - React to completed actions
    - Apply side effects
    - Emit events
    - Update derived state

    Note: Post-rules should NOT cancel actions (they've already executed).

    Args:
        action: Action type(s) this rule applies to (default: '*' for all).
        priority: Execution order, lower runs first (default: 0).
        when: Optional condition function that must return True for rule to execute.
        intent: Optional natural language description of rule's purpose.
        engine: Specific RuleEngine to register with (default: global engine).

    Returns:
        Decorator function.

    Example:
        @post_rule(action='attack', priority=20, intent="Apply poison damage")
        def apply_poison(ctx: ActionContext) -> None:
            attacker = ctx.get_param('attacker')
            target = ctx.get_param('target')
            if ctx.world.has_component(attacker, PoisonWeapon):
                poison = ctx.world.get_component(attacker, PoisonWeapon)
                ctx.world.add_component(target, Poisoned(damage=poison.damage))

        @post_rule(action='*', priority=100, intent="Log all actions")
        def log_action(ctx: ActionContext) -> None:
            print(f"Action executed: {ctx.action.name}")
    """
    return rule(
        phase="post",
        action=action,
        priority=priority,
        when=when,
        intent=intent,
        engine=engine,
    )


def collect_rules(module: Any) -> list[Rule]:
    """Collect all rules defined in a module using decorators.

    This scans a module for functions with attached rule objects and
    returns them. Useful for bulk registration.

    Args:
        module: Python module to scan.

    Returns:
        List of Rule objects found in the module.

    Example:
        import my_game.rules
        rules = collect_rules(my_game.rules)
        for rule in rules:
            engine.register(rule)
    """
    rules = []
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, "_renee_rule"):
            rules.append(obj._renee_rule)
    return rules


def register_module_rules(engine: RuleEngine, module: Any) -> int:
    """Register all rules from a module with an engine.

    Args:
        engine: RuleEngine to register rules with.
        module: Python module containing rule-decorated functions.

    Returns:
        Number of rules registered.

    Example:
        import my_game.combat_rules
        count = register_module_rules(engine, my_game.combat_rules)
        print(f"Registered {count} combat rules")
    """
    rules = collect_rules(module)
    for rule in rules:
        engine.register(rule)
    return len(rules)
