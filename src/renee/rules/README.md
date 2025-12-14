# Renee Rule Engine

The Rule Engine provides Python decorators for defining game logic. Rules intercept actions in the action pipeline, allowing validation, modification, cancellation, and side effects.

## Overview

Rules are Python functions decorated with `@pre_rule` or `@post_rule` that execute before or after game actions. This allows you to:

- **Validate** actions before they execute (e.g., check if entity has enough mana)
- **Modify** action parameters (e.g., apply damage modifiers)
- **Cancel** invalid actions (e.g., prevent stunned entity from moving)
- **React** to completed actions (e.g., apply poison after attack)

## Quick Start

```python
from renee.rules import RuleEngine, pre_rule, post_rule, set_global_engine
from renee.rules import ActionContext

# Create and configure engine
engine = RuleEngine()
set_global_engine(engine)

# Define a pre-rule for validation
@pre_rule(action='move', priority=10, intent="Prevent movement if stunned")
def check_stunned(ctx: ActionContext) -> None:
    entity = ctx.get_param('entity')
    if ctx.world.has_component(entity, Stunned):
        ctx.cancel("Entity is stunned")

# Define a post-rule for side effects
@post_rule(action='attack', priority=20, intent="Apply poison damage")
def apply_poison(ctx: ActionContext) -> None:
    attacker = ctx.get_param('attacker')
    target = ctx.get_param('target')
    if ctx.world.has_component(attacker, PoisonWeapon):
        ctx.world.add_component(target, Poisoned(damage=5))
```

## Core Concepts

### Rules

A `Rule` is a game logic unit that runs at a specific phase (pre/post) with a defined priority:

```python
from renee.rules import Rule

rule = Rule(
    name="check_range",
    phase="pre",
    priority=10,
    action_types=["attack"],
    condition=lambda ctx: True,  # Optional
    handler=lambda ctx: validate_range(ctx),
    intent="Ensure attack is within range"
)
```

**Attributes:**

- `name`: Human-readable identifier
- `phase`: `'pre'` (before action) or `'post'` (after action)
- `priority`: Execution order (lower = earlier)
- `action_types`: List of action names, or `['*']` for all
- `condition`: Optional function to check if rule should run
- `handler`: The rule's logic
- `intent`: Natural language description (for AI agents)

### Action Context

The `ActionContext` is passed to every rule handler and provides:

```python
@dataclass
class ActionContext:
    action: Action          # The action being processed
    world: World           # Access to game state
    cancelled: bool        # Whether action has been cancelled
    cancel_reason: str     # Why action was cancelled
    data: dict             # Custom data storage

    def cancel(self, reason: str) -> None:
        """Cancel the action"""

    def modify(self, **changes) -> None:
        """Modify action parameters"""

    def get_param(self, key: str, default=None) -> Any:
        """Get action parameter"""

    def set_data(self, key: str, value: Any) -> None:
        """Store custom data"""

    def get_data(self, key: str, default=None) -> Any:
        """Retrieve custom data"""
```

### RuleEngine

The `RuleEngine` manages rule registration and execution:

```python
engine = RuleEngine()

# Register a rule
engine.register(rule)

# Get applicable rules
rules = engine.get_rules(action_type='attack', phase='pre')

# Apply rules to a context
engine.apply_rules(ctx, phase='pre')

# List all rules
all_rules = engine.list_rules()

# Export to JSON (for AI introspection)
json_str = engine.to_json(indent=2)
```

## Decorators

### `@pre_rule`

Pre-rules execute **before** the action handler. Use them for:

- Validation
- Parameter modification
- Action cancellation

```python
@pre_rule(action='attack', priority=10, intent="Validate attack range")
def check_range(ctx: ActionContext) -> None:
    attacker_pos = ctx.world.get_component(ctx.get_param('attacker'), Position)
    target_pos = ctx.world.get_component(ctx.get_param('target'), Position)

    if attacker_pos.manhattan_distance(target_pos) > 1:
        ctx.cancel("Target out of range")
```

**Parameters:**

- `action`: Action type(s) - string or list (default: `'*'`)
- `priority`: Execution order - lower runs first (default: `0`)
- `when`: Optional condition function
- `intent`: Natural language description
- `engine`: Specific RuleEngine to use (default: global)

### `@post_rule`

Post-rules execute **after** the action completes. Use them for:

- Side effects
- Event emission
- State updates

```python
@post_rule(action='attack', priority=20, intent="Apply poison on hit")
def apply_poison(ctx: ActionContext) -> None:
    attacker = ctx.get_param('attacker')
    target = ctx.get_param('target')

    if ctx.world.has_component(attacker, PoisonWeapon):
        poison = ctx.world.get_component(attacker, PoisonWeapon)
        ctx.world.add_component(target, Poisoned(damage=poison.damage))
```

### `@rule`

Base decorator for explicit phase control:

```python
@rule(phase='pre', action='move', priority=10)
def my_rule(ctx: ActionContext) -> None:
    pass
```

## Common Patterns

### Multiple Action Types

Apply the same rule to multiple actions:

```python
@pre_rule(action=['attack', 'spell'], priority=5)
def check_mana(ctx: ActionContext) -> None:
    caster = ctx.get_param('caster')
    cost = ctx.get_param('mana_cost', 0)

    mana = ctx.world.get_component(caster, Mana)
    if mana.current < cost:
        ctx.cancel("Not enough mana")
```

### Conditional Rules

Use `when` parameter for conditional execution:

```python
def has_shield(ctx: ActionContext) -> bool:
    target = ctx.get_param('target')
    return ctx.world.has_component(target, Shield)

@pre_rule(action='attack', when=has_shield, priority=15)
def block_with_shield(ctx: ActionContext) -> None:
    target = ctx.get_param('target')
    shield = ctx.world.get_component(target, Shield)

    damage = ctx.get_param('damage', 0)
    ctx.modify(damage=max(0, damage - shield.reduction))
```

### Wildcard Rules

Apply to all actions using `'*'`:

```python
@post_rule(action='*', priority=100)
def log_all_actions(ctx: ActionContext) -> None:
    print(f"Action executed: {ctx.action.name}")
```

### Priority Ordering

Lower priority executes first:

```python
@pre_rule(action='attack', priority=5)
def validate_range(ctx):
    """Runs first"""
    pass

@pre_rule(action='attack', priority=10)
def apply_modifiers(ctx):
    """Runs second"""
    pass

@pre_rule(action='attack', priority=15)
def calculate_final_damage(ctx):
    """Runs third"""
    pass
```

### Sharing Data Between Rules

Use context data storage:

```python
@pre_rule(action='attack', priority=10)
def calculate_hit_chance(ctx: ActionContext) -> None:
    # Calculate and store
    hit_chance = calculate_chance(ctx)
    ctx.set_data('hit_chance', hit_chance)

@pre_rule(action='attack', priority=20)
def apply_hit_check(ctx: ActionContext) -> None:
    # Retrieve stored data
    hit_chance = ctx.get_data('hit_chance', 1.0)
    if not roll_success(hit_chance):
        ctx.cancel("Attack missed")
```

### Modifying Action Parameters

```python
@pre_rule(action='attack', priority=10)
def apply_strength_bonus(ctx: ActionContext) -> None:
    attacker = ctx.get_param('attacker')
    strength = ctx.world.get_component(attacker, Strength)

    damage = ctx.get_param('damage', 0)
    ctx.modify(damage=damage + strength.bonus)
```

## Integration with Action Pipeline

Rules are designed to integrate with the Action Pipeline (Phase 2.1):

```python
# Typical action pipeline flow:
def execute_action(action_name: str, **params):
    # 1. Create context
    ctx = ActionContext(
        action=Action(name=action_name, params=params),
        world=world
    )

    # 2. Apply pre-rules
    engine.apply_rules(ctx, 'pre')

    # 3. Check if cancelled
    if ctx.is_cancelled():
        return ActionResult(success=False, reason=ctx.cancel_reason)

    # 4. Execute action handler
    result = action_handlers[action_name](ctx)

    # 5. Apply post-rules
    engine.apply_rules(ctx, 'post')

    return result
```

## AI-Native Features

### Intent Fields

Rules support natural language `intent` fields that AI agents can use to understand game logic:

```python
@pre_rule(
    action='move',
    priority=10,
    intent="Prevent movement if entity is stunned, rooted, or paralyzed"
)
def check_movement_status(ctx: ActionContext) -> None:
    # Implementation
    pass
```

### JSON Export

Export rules for AI introspection:

```python
json_output = engine.to_json(indent=2)
# AI can parse this to understand:
# - What rules exist
# - When they execute
# - What they do (via intent field)
```

### Rule Discovery

Collect rules from modules:

```python
from renee.rules import collect_rules, register_module_rules
import my_game.combat_rules

# Collect all rules in module
rules = collect_rules(my_game.combat_rules)

# Or register them all at once
count = register_module_rules(engine, my_game.combat_rules)
```

## Best Practices

1. **Use descriptive names**: Rule names should clearly indicate their purpose
2. **Add intent fields**: Help AI agents understand rule logic
3. **Keep priority gaps**: Use 10, 20, 30 instead of 1, 2, 3 for easier insertion
4. **Pre-rules validate, post-rules react**: Don't cancel actions in post-rules
5. **Low priority for validation**: Check basic constraints early (priority 0-20)
6. **High priority for logging**: Log actions after all modifications (priority 90+)
7. **Test rule interactions**: Multiple rules can modify the same action

## Examples

See `/examples/rule_engine_demo.py` for a complete working example demonstrating:

- Pre-rule validation (range checks, status effects)
- Pre-rule modification (armor reduction, critical hits)
- Post-rule side effects (poison application, damage dealing)
- Wildcard rules (action logging)
- Action cancellation
- Priority ordering

## API Reference

### Classes

- `Rule`: Rule definition dataclass
- `RuleEngine`: Rule registration and execution manager
- `ActionContext`: Context passed to rule handlers
- `Action`: Action being processed

### Decorators

- `@pre_rule`: Pre-action rule decorator
- `@post_rule`: Post-action rule decorator
- `@rule`: Base rule decorator

### Functions

- `set_global_engine(engine)`: Set global engine for decorators
- `get_global_engine()`: Get current global engine
- `collect_rules(module)`: Collect rules from a module
- `register_module_rules(engine, module)`: Bulk register module rules

## Related Documentation

- **Phase 2.1**: Action Pipeline Specification (not yet written)
- **DESIGN.md**: Overall framework architecture
- **ROADMAP.md**: Development roadmap and timeline
