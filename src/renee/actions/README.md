# Action Pipeline

The Action Pipeline handles the flow: Request → Validation → Pre-Rules → Execution → Post-Rules → Events

## Overview

The Action Pipeline is a core system in Renee that processes all game actions (movement, attacks, item usage, etc.) through a structured pipeline with validation, rule processing, and event generation.

## Core Components

### Action (`action.py`)

Represents a request to perform a game operation.

```python
from renee.actions import Action
from renee.types import EntityId, Position

# Create an action
action = Action(
    name='move',
    params={'entity': player_id, 'target': Position(5, 5)},
    source=player_id
)
```

**Attributes:**
- `name: str` - Action type name (e.g., 'move', 'attack', 'use_item')
- `params: dict[str, Any]` - Action parameters (entity, target, amount, etc.)
- `source: EntityId | None` - Entity performing the action (optional)

### ActionContext (`action.py`)

Context passed to rules during action processing. Provides access to the action, world state, and methods to cancel or modify the action.

```python
from renee.actions import ActionContext

def validate_range(ctx: ActionContext) -> None:
    entity = ctx.action.params['entity']
    target = ctx.action.params['target']

    pos = ctx.world.get_component(entity, Position)
    if pos.manhattan_distance(target) > 5:
        ctx.cancel("Target is out of range")
```

**Attributes:**
- `action: Action` - The action being processed
- `world: World` - Reference to the game world
- `phase: str` - Current pipeline phase ('pre' or 'post')
- `cancelled: bool` - Whether the action has been cancelled
- `cancel_reason: str | None` - Reason for cancellation
- `modified_params: dict[str, Any]` - Parameters modified by rules

**Methods:**
- `cancel(reason: str)` - Cancel the action with a reason
- `modify_param(key: str, value: Any)` - Modify an action parameter
- `get_param(key: str, default: Any = None)` - Get parameter (modified or original)

### ActionResult (`result.py`)

Result of executing an action through the pipeline.

```python
from renee.actions import ActionResult

result = pipeline.execute(action, world)

if result.success:
    for event in result.events:
        event_bus.emit(event)
elif result.cancelled:
    print(f"Cancelled: {result.cancel_reason}")
else:
    print(f"Error: {result.error}")
```

**Attributes:**
- `success: bool` - Whether the action completed successfully
- `action: Action` - The action that was executed
- `cancelled: bool` - Whether the action was cancelled by rules
- `cancel_reason: str | None` - Reason for cancellation
- `error: str | None` - Error message if execution failed
- `events: list[Any]` - Events generated during execution

**Factory Methods:**
- `success_result(action, events)` - Create successful result
- `cancelled_result(action, reason)` - Create cancelled result
- `error_result(action, error)` - Create error result

### ActionPipeline (`pipeline.py`)

Main pipeline for processing actions through validation, rules, and execution.

```python
from renee.actions import ActionPipeline, Action, ActionContext

pipeline = ActionPipeline()

# Register handler
def move_handler(action: Action, world: World) -> list[Event]:
    entity = action.params['entity']
    target = action.params['target']
    world.add_component(entity, target)
    return [MovedEvent(entity=entity, to=target)]

pipeline.register_handler('move', move_handler)

# Add pre-rule
def check_range(ctx: ActionContext) -> None:
    # Validation logic
    pass

pipeline.add_pre_rule('move', check_range, priority=10)

# Execute action
result = pipeline.execute(action, world)
```

**Methods:**

#### `register_handler(action_name: str, handler: Callable)`
Register an action handler that executes the action and returns events.

**Handler signature:** `(Action, World) -> list[Event]`

#### `register_validator(action_name: str, validator: Callable)`
Register a validator that checks action parameters before execution.

**Validator signature:** `(Action, World) -> str | None` (returns error string or None)

#### `add_pre_rule(action_name: str, rule: Callable, priority: int = 0)`
Add a pre-execution rule that can cancel or modify the action.

**Rule signature:** `(ActionContext) -> None`

Rules with higher priority run first.

#### `add_post_rule(action_name: str, rule: Callable, priority: int = 0)`
Add a post-execution rule that reacts to completed actions.

**Rule signature:** `(ActionContext) -> None`

#### `execute(action: Action, world: World) -> ActionResult`
Execute an action through the pipeline.

## Pipeline Stages

The pipeline processes actions through six stages:

1. **Handler Check** - Verify a handler is registered for this action type
2. **Validation** - Run validator to check parameters (if registered)
3. **Pre-Rules** - Execute pre-rules in priority order (can cancel/modify)
4. **Execution** - Run handler to perform action effects (if not cancelled)
5. **Post-Rules** - Execute post-rules in priority order (react to action)
6. **Return Result** - Return ActionResult with success state and events

```
Request → Validation → Pre-Rules → Execution → Post-Rules → Events
          ↓             ↓           ↓           ↓
        Error?      Cancelled?   Error?    (No cancel)
```

## Usage Example

See `/examples/action_pipeline_example.py` for a complete working example.

### Basic Handler Registration

```python
from renee.actions import ActionPipeline, Action
from renee.ecs.world import World
from renee.types import Position

pipeline = ActionPipeline()

def move_handler(action: Action, world: World) -> list:
    entity = action.params['entity']
    target = action.params['target']

    old_pos = world.get_component(entity, Position)
    world.add_component(entity, target)

    return [MovedEvent(entity=entity, from_pos=old_pos, to_pos=target)]

pipeline.register_handler('move', move_handler)
```

### Adding Validation

```python
def move_validator(action: Action, world: World) -> str | None:
    if 'entity' not in action.params:
        return "Missing required parameter: entity"
    if 'target' not in action.params:
        return "Missing required parameter: target"

    entity = action.params['entity']
    if not world.entity_exists(entity):
        return f"Entity {entity} does not exist"

    return None

pipeline.register_validator('move', move_validator)
```

### Adding Pre-Rules

```python
def check_movement_range(ctx: ActionContext) -> None:
    """Check if target is within movement range."""
    entity = ctx.action.params['entity']
    target = ctx.action.params['target']

    pos = ctx.world.get_component(entity, Position)
    move_range = ctx.world.get_component(entity, MovementRange)

    distance = pos.manhattan_distance(target)
    if distance > move_range.range:
        ctx.cancel(f"Out of range (distance: {distance}, max: {move_range.range})")

pipeline.add_pre_rule('move', check_movement_range, priority=10)
```

### Modifying Parameters

```python
def apply_damage_reduction(ctx: ActionContext) -> None:
    """Reduce damage based on target's armor."""
    target = ctx.action.params['target']
    damage = ctx.action.params['damage']

    if ctx.world.has_component(target, Armor):
        armor = ctx.world.get_component(target, Armor)
        reduced_damage = max(0, damage - armor.value)
        ctx.modify_param('damage', reduced_damage)

pipeline.add_pre_rule('attack', apply_damage_reduction, priority=5)
```

### Adding Post-Rules

```python
def check_death(ctx: ActionContext) -> None:
    """Destroy entity if health reaches zero."""
    target = ctx.action.params['target']

    if ctx.world.has_component(target, Health):
        health = ctx.world.get_component(target, Health)
        if health.current == 0:
            ctx.world.destroy_entity(target)

pipeline.add_post_rule('attack', check_death)
```

### Executing Actions

```python
# Create action
action = Action('move', {
    'entity': player_id,
    'target': Position(5, 5)
})

# Execute through pipeline
result = pipeline.execute(action, world)

# Handle result
if result.success:
    print(f"Action succeeded!")
    for event in result.events:
        event_bus.emit(event)
elif result.cancelled:
    print(f"Action cancelled: {result.cancel_reason}")
else:
    print(f"Action failed: {result.error}")
```

## Design Patterns

### Separation of Concerns

- **Validators**: Check parameter validity (required fields, types, existence)
- **Pre-Rules**: Check business logic (range, costs, conditions)
- **Handlers**: Execute action effects (modify world state)
- **Post-Rules**: React to completed actions (side effects, cleanup)

### Priority System

Rules execute in priority order (highest first):

```python
pipeline.add_pre_rule('attack', check_range, priority=10)      # Runs first
pipeline.add_pre_rule('attack', check_mana, priority=5)        # Runs second
pipeline.add_pre_rule('attack', apply_buffs, priority=0)       # Runs third
```

This allows you to control execution order for dependent logic.

### Cancellation

Pre-rules can cancel actions to prevent execution:

```python
def check_mana(ctx: ActionContext) -> None:
    caster = ctx.action.params['caster']
    cost = ctx.action.params['mana_cost']

    mana = ctx.world.get_component(caster, Mana)
    if mana.current < cost:
        ctx.cancel("Not enough mana")
```

Once cancelled, the handler and remaining pre-rules are skipped.

### Parameter Modification

Pre-rules can modify parameters that the handler will see:

```python
def critical_hit(ctx: ActionContext) -> None:
    """20% chance to double damage."""
    import random
    if random.random() < 0.2:
        damage = ctx.action.params['damage']
        ctx.modify_param('damage', damage * 2)
        ctx.modify_param('critical', True)
```

## Testing

See `/tests/test_actions.py` for comprehensive test examples.

```python
import pytest
from renee.actions import Action, ActionPipeline, ActionResult
from renee.ecs.world import World

def test_action_execution():
    pipeline = ActionPipeline()
    world = World()

    def handler(action: Action, world: World) -> list:
        return []

    pipeline.register_handler('test', handler)

    action = Action('test', {})
    result = pipeline.execute(action, world)

    assert result.success
```

## Error Handling

The pipeline catches and reports errors at each stage:

- **Validation errors**: Returned as `error` in result
- **Pre-rule errors**: Caught and returned as `error`
- **Handler errors**: Caught and returned as `error`
- **Post-rule errors**: Logged but don't fail the action

```python
result = pipeline.execute(action, world)

if not result.success:
    if result.cancelled:
        # Action was cancelled by a rule
        print(f"Cancelled: {result.cancel_reason}")
    else:
        # Validation or execution error
        print(f"Error: {result.error}")
```

## Integration with Other Systems

### Event Bus Integration

```python
result = pipeline.execute(action, world)

if result.success:
    for event in result.events:
        event_bus.emit(event)
```

### Turn Manager Integration

```python
def execute_player_action(action: Action) -> bool:
    result = pipeline.execute(action, world)

    if result.success:
        for event in result.events:
            event_bus.emit(event)
        turn_manager.end_turn()
        return True
    else:
        print(f"Invalid action: {result.cancel_reason or result.error}")
        return False
```

## Best Practices

1. **Validators for Schema** - Use validators for parameter checking
2. **Pre-Rules for Logic** - Use pre-rules for business logic validation
3. **Handlers for Effects** - Keep handlers focused on state changes
4. **Post-Rules for Reactions** - Use post-rules for side effects
5. **Priorities for Dependencies** - Use priorities when rules depend on each other
6. **Clear Error Messages** - Provide descriptive cancellation reasons
7. **Return Relevant Events** - Generate events for all significant state changes
8. **Test Each Stage** - Write tests for validators, rules, and handlers separately

## Future Extensions

Potential enhancements to the Action Pipeline:

- Action queueing and batching
- Undo/redo support via action history
- Action cost calculation (mana, AP, resources)
- Conditional execution (if-then actions)
- Action templates and composition
- Network synchronization for multiplayer
- Replay system integration
