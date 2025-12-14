# Rule Engine Quick Reference

## Basic Setup

```python
from renee.rules import RuleEngine, pre_rule, post_rule, set_global_engine

engine = RuleEngine()
set_global_engine(engine)
```

## Define Pre-Rules (Validation/Modification)

```python
@pre_rule(action='move', priority=10)
def check_stunned(ctx):
    entity = ctx.get_param('entity')
    if ctx.world.has_component(entity, Stunned):
        ctx.cancel("Entity is stunned")

@pre_rule(action='attack', priority=15)
def apply_armor(ctx):
    damage = ctx.get_param('damage', 0)
    armor = get_armor_value(ctx)
    ctx.modify(damage=max(0, damage - armor))
```

## Define Post-Rules (Side Effects)

```python
@post_rule(action='attack', priority=20)
def apply_poison(ctx):
    attacker = ctx.get_param('attacker')
    target = ctx.get_param('target')
    if ctx.world.has_component(attacker, PoisonWeapon):
        ctx.world.add_component(target, Poisoned(damage=5))
```

## Execute Rules

```python
from renee.rules import Action, ActionContext

action = Action(name='attack', params={'attacker': 1, 'target': 2, 'damage': 10})
ctx = ActionContext(action=action, world=world)

# Apply pre-rules
engine.apply_rules(ctx, 'pre')

if not ctx.is_cancelled():
    # Execute action
    # ...

    # Apply post-rules
    engine.apply_rules(ctx, 'post')
```

## Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | str or list | `'*'` | Action type(s) to apply to |
| `priority` | int | `0` | Execution order (lower = earlier) |
| `when` | Callable | `None` | Optional condition function |
| `intent` | str | `None` | Natural language description |
| `engine` | RuleEngine | global | Specific engine to use |

## Context Methods

| Method | Description |
|--------|-------------|
| `ctx.cancel(reason)` | Cancel the action |
| `ctx.modify(**changes)` | Update action parameters |
| `ctx.get_param(key, default)` | Get action parameter |
| `ctx.set_data(key, value)` | Store custom data |
| `ctx.get_data(key, default)` | Retrieve custom data |
| `ctx.is_cancelled()` | Check if cancelled |

## Common Patterns

### Multiple Actions
```python
@pre_rule(action=['attack', 'spell'], priority=5)
def check_mana(ctx):
    # Applies to both attack and spell
    pass
```

### Conditional Rules
```python
def has_shield(ctx):
    return ctx.world.has_component(ctx.get_param('target'), Shield)

@pre_rule(action='attack', when=has_shield, priority=15)
def block_with_shield(ctx):
    # Only runs if target has shield
    pass
```

### Wildcard (All Actions)
```python
@post_rule(action='*', priority=100)
def log_all_actions(ctx):
    print(f"Action: {ctx.action.name}")
```

### Data Sharing
```python
@pre_rule(action='attack', priority=10)
def calculate_hit(ctx):
    hit_chance = 0.85
    ctx.set_data('hit_chance', hit_chance)

@pre_rule(action='attack', priority=20)
def apply_hit_check(ctx):
    hit_chance = ctx.get_data('hit_chance', 1.0)
    if random.random() > hit_chance:
        ctx.cancel("Attack missed")
```

## Priority Guidelines

| Range | Purpose |
|-------|---------|
| 0-20 | Early validation (range, resources) |
| 21-40 | Modification (damage, cost adjustments) |
| 41-60 | Complex calculations |
| 61-80 | Final checks |
| 81-100 | Logging and monitoring |

## Engine Methods

```python
# Registration
engine.register(rule)

# Querying
rules = engine.get_rules('attack', 'pre')
all_rules = engine.list_rules()
rule = engine.get_rule('rule_name')

# Statistics
count = engine.rule_count()
summary = engine.get_summary()

# Export
json_str = engine.to_json(indent=2)

# Cleanup
engine.clear()
```

## Complete Example

```python
from renee import World
from renee.rules import RuleEngine, pre_rule, post_rule, set_global_engine
from renee.rules import Action, ActionContext

# Setup
world = World()
engine = RuleEngine()
set_global_engine(engine)

# Define rules
@pre_rule(action='attack', priority=10, intent="Validate attack range")
def check_range(ctx):
    if distance_too_far(ctx):
        ctx.cancel("Out of range")

@pre_rule(action='attack', priority=20, intent="Apply armor reduction")
def apply_armor(ctx):
    damage = ctx.get_param('damage', 0)
    armor = get_armor(ctx)
    ctx.modify(damage=max(0, damage - armor))

@post_rule(action='attack', priority=10, intent="Apply poison effect")
def apply_poison(ctx):
    if has_poison_weapon(ctx):
        apply_poison_to_target(ctx)

# Execute
action = Action(name='attack', params={'attacker': 1, 'target': 2, 'damage': 15})
ctx = ActionContext(action=action, world=world)

engine.apply_rules(ctx, 'pre')
if not ctx.is_cancelled():
    # Perform attack
    final_damage = ctx.get_param('damage')
    # ...
    engine.apply_rules(ctx, 'post')
```

## Tips

1. Use gaps in priority (10, 20, 30) for easier insertion
2. Add intent fields to help AI understand rules
3. Keep pre-rules for validation, post-rules for reactions
4. Don't cancel actions in post-rules
5. Use `when=` for expensive conditions
6. Lower priority = runs earlier
7. Wildcard `'*'` matches all actions
