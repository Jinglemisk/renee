# Renee Event System

The Event Bus provides a centralized, type-safe event system for the Renee game framework. It enables decoupled communication between game systems through event emission and subscription.

## Features

- **Automatic Metadata**: All events receive unique IDs, timestamps, and turn numbers
- **Type-Safe Subscriptions**: Subscribe to specific event types with proper typing
- **Queryable History**: Filter events by type, turn, entity, or custom criteria
- **JSON Serialization**: Export event history for debugging and replay
- **Wildcard Subscriptions**: Listen to all events with a single handler
- **Error Resilience**: Handler exceptions don't break the event bus

## Quick Start

### 1. Define Events

Events are simple dataclasses with a metadata field:

```python
from dataclasses import dataclass
from renee.events import EventMetadata
from renee.types import EntityId

@dataclass(frozen=True, slots=True)
class DamageEvent:
    source: EntityId
    target: EntityId
    amount: int
    metadata: EventMetadata = None  # type: ignore[assignment]
```

### 2. Create Event Bus

```python
from renee.events import EventBus

bus = EventBus(current_turn=1)
```

### 3. Subscribe to Events

```python
def handle_damage(event: DamageEvent) -> None:
    print(f"Entity {event.target} took {event.amount} damage!")

bus.subscribe(DamageEvent, handle_damage)
```

### 4. Emit Events

```python
bus.emit(DamageEvent(
    source=EntityId(1),
    target=EntityId(2),
    amount=15
))
```

## Usage Patterns

### Type-Specific Handlers

```python
bus.subscribe(DamageEvent, handle_damage)
bus.subscribe(HealEvent, handle_heal)
bus.subscribe(LevelUpEvent, handle_level_up)
```

### Wildcard Subscriptions

Listen to all events:

```python
def log_event(event: object) -> None:
    print(f"Event: {type(event).__name__}")

bus.subscribe_all(log_event)
```

### Querying History

Query by event type:

```python
damage_events = bus.query(event_type=DamageEvent)
```

Query by turn:

```python
turn_5_events = bus.query(turn=5)
```

Query by entity:

```python
# Gets events where entity appears in source, target, or entity_id fields
entity_events = bus.query(entity=EntityId(1))
```

Query with custom filter:

```python
high_damage = bus.query(
    event_type=DamageEvent,
    filter_fn=lambda e: e.amount > 50
)
```

Combined filters:

```python
results = bus.query(
    event_type=DamageEvent,
    turn=5,
    entity=EntityId(1),
    filter_fn=lambda e: e.amount > 10,
    limit=10
)
```

### Managing Subscriptions

Unsubscribe specific handler:

```python
bus.unsubscribe(DamageEvent, handle_damage)
```

Clear all subscribers:

```python
bus.clear_subscribers()
```

### Turn Management

Update current turn:

```python
bus.set_turn(5)
```

Get current turn:

```python
current = bus.get_turn()
```

### History Management

Get all events:

```python
history = bus.get_history()
```

Count events:

```python
count = bus.event_count()
```

Clear history:

```python
bus.clear_history()
```

### JSON Export

Export for debugging or replay:

```python
json_str = bus.to_json(indent=2)
```

## Built-in Events

The event system includes common game events:

- `EntityCreatedEvent` - Entity creation
- `EntityDestroyedEvent` - Entity destruction
- `ComponentAddedEvent` - Component added to entity
- `ComponentRemovedEvent` - Component removed from entity
- `TurnStartEvent` - Turn begins
- `TurnEndEvent` - Turn ends
- `GameStartEvent` - Game starts
- `GameEndEvent` - Game ends

## Event Metadata

All events automatically receive metadata:

```python
event = bus.emit(DamageEvent(...))

print(event.metadata.event_id)    # Unique UUID
print(event.metadata.timestamp)   # When event was emitted
print(event.metadata.turn)        # Turn number when emitted
```

## Design Guidelines

### Events Should Be Immutable

Always use `frozen=True` on event dataclasses:

```python
@dataclass(frozen=True, slots=True)
class MyEvent:
    ...
```

### Events Are Facts, Not Commands

Events represent things that **have happened**, not requests for things to happen:

- Good: `DamageDealtEvent`, `EntityDiedEvent`
- Bad: `DealDamageCommand`, `KillEntityRequest`

### Keep Events Simple

Events should be data containers, not behavior:

```python
# Good
@dataclass(frozen=True, slots=True)
class DamageEvent:
    source: EntityId
    target: EntityId
    amount: int

# Bad
@dataclass(frozen=True, slots=True)
class DamageEvent:
    source: EntityId
    target: EntityId

    def calculate_damage(self) -> int:
        # Don't put logic in events!
        ...
```

### Entity References

When events involve entities, use common field names:

- `entity_id` - The primary entity
- `source` - The entity causing the event
- `target` - The entity affected by the event

This enables entity-based query filtering.

## Performance Considerations

### History Growth

The event history grows unbounded by default. For long-running games:

```python
# Clear old events periodically
if bus.event_count() > 10000:
    bus.clear_history()

# Or keep only recent turns
old_events = bus.query(filter_fn=lambda e: e.metadata.turn < current_turn - 10)
# Remove old events (custom implementation needed)
```

### Query Performance

Queries are O(n) over the history. For hot paths:

- Use specific filters to reduce work
- Cache query results when possible
- Consider custom indexing for frequent queries

### Handler Performance

Event handlers run synchronously. Keep them fast:

```python
# Good
def handle_damage(event: DamageEvent) -> None:
    stats.record_damage(event.amount)

# Bad
def handle_damage(event: DamageEvent) -> None:
    # Don't do heavy work in handlers!
    recalculate_entire_game_state()
```

## Integration with ECS

The event system complements the ECS (Entity-Component-System):

```python
from renee.ecs import World
from renee.events import EventBus, EntityCreatedEvent

world = World()
bus = EventBus()

# Emit events when entities are created
entity = world.create_entity()
bus.emit(EntityCreatedEvent(entity_id=entity))

# Components can react to events
def on_damage(event: DamageEvent) -> None:
    health = world.get_component(event.target, Health)
    health.current -= event.amount
    world.add_component(event.target, health)

bus.subscribe(DamageEvent, on_damage)
```

## Testing

The event system is designed for testability:

```python
def test_damage_system():
    bus = EventBus()
    received = []

    bus.subscribe(DamageEvent, lambda e: received.append(e))
    bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

    assert len(received) == 1
    assert received[0].amount == 10
```

## Example: Combat System

```python
from dataclasses import dataclass
from renee.events import EventBus, EventMetadata
from renee.types import EntityId

@dataclass(frozen=True, slots=True)
class AttackEvent:
    attacker: EntityId
    defender: EntityId
    metadata: EventMetadata = None  # type: ignore[assignment]

@dataclass(frozen=True, slots=True)
class DamageEvent:
    source: EntityId
    target: EntityId
    amount: int
    metadata: EventMetadata = None  # type: ignore[assignment]

@dataclass(frozen=True, slots=True)
class DeathEvent:
    entity_id: EntityId
    killed_by: EntityId | None = None
    metadata: EventMetadata = None  # type: ignore[assignment]

bus = EventBus()

# Combat system logic
def on_attack(event: AttackEvent) -> None:
    # Calculate damage
    damage = calculate_damage(event.attacker, event.defender)
    bus.emit(DamageEvent(
        source=event.attacker,
        target=event.defender,
        amount=damage
    ))

def on_damage(event: DamageEvent) -> None:
    # Apply damage to health
    health = get_health(event.target)
    health -= event.amount
    set_health(event.target, health)

    # Check for death
    if health <= 0:
        bus.emit(DeathEvent(
            entity_id=event.target,
            killed_by=event.source
        ))

def on_death(event: DeathEvent) -> None:
    # Clean up dead entity
    remove_entity(event.entity_id)

    # Award experience to killer
    if event.killed_by:
        award_exp(event.killed_by, 100)

# Wire up the system
bus.subscribe(AttackEvent, on_attack)
bus.subscribe(DamageEvent, on_damage)
bus.subscribe(DeathEvent, on_death)

# Trigger combat
bus.emit(AttackEvent(attacker=EntityId(1), defender=EntityId(2)))
```

## See Also

- [examples/event_system_demo.py](../../../examples/event_system_demo.py) - Full working example
- [tests/test_events.py](../../../tests/test_events.py) - Comprehensive test suite
- [DESIGN.md](../../../DESIGN.md) - Overall architecture
