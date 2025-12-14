# Event System Quick Reference

## Imports

```python
from renee.events import EventBus, EventMetadata
from renee.types import EntityId
from dataclasses import dataclass
```

## Define Events

```python
@dataclass(frozen=True, slots=True)
class MyEvent:
    field1: int
    field2: str
    metadata: EventMetadata = None  # type: ignore[assignment]
```

## Create EventBus

```python
bus = EventBus()                    # Default turn 0
bus = EventBus(current_turn=1)      # Start at turn 1
```

## Subscribe to Events

```python
# Type-specific
def handler(event: MyEvent) -> None:
    print(event.field1)

bus.subscribe(MyEvent, handler)

# Lambda
bus.subscribe(MyEvent, lambda e: print(e.field1))

# Wildcard (all events)
bus.subscribe_all(lambda e: print(type(e).__name__))
```

## Emit Events

```python
event = bus.emit(MyEvent(field1=42, field2="hello"))

# Event now has metadata
print(event.metadata.event_id)      # UUID
print(event.metadata.timestamp)     # datetime
print(event.metadata.turn)          # int
```

## Unsubscribe

```python
bus.unsubscribe(MyEvent, handler)           # Type-specific
bus.unsubscribe_all(handler)                # Wildcard
bus.clear_subscribers()                     # All subscribers
```

## Query History

```python
# All events
all_events = bus.get_history()

# By type
damage = bus.query(event_type=DamageEvent)

# By turn
turn_5 = bus.query(turn=5)

# By entity (checks source, target, entity_id fields)
entity_1 = bus.query(entity=EntityId(1))

# Custom filter
high_damage = bus.query(
    event_type=DamageEvent,
    filter_fn=lambda e: e.amount > 50
)

# Combined filters with limit
results = bus.query(
    event_type=DamageEvent,
    turn=5,
    entity=EntityId(1),
    filter_fn=lambda e: e.amount > 10,
    limit=10
)
```

## History Management

```python
count = bus.event_count()           # Number of events
bus.clear_history()                 # Clear all events
```

## Turn Management

```python
bus.set_turn(5)                     # Update turn
current = bus.get_turn()            # Get current turn
```

## JSON Export

```python
json_str = bus.to_json()            # Compact
json_str = bus.to_json(indent=2)    # Pretty-printed
```

## Built-in Events

```python
from renee.events import (
    EntityCreatedEvent,
    EntityDestroyedEvent,
    ComponentAddedEvent,
    ComponentRemovedEvent,
    TurnStartEvent,
    TurnEndEvent,
    GameStartEvent,
    GameEndEvent,
)

bus.emit(EntityCreatedEvent(entity_id=EntityId(1)))
bus.emit(TurnStartEvent(turn_number=1))
bus.emit(GameStartEvent())
```

## Common Patterns

### Combat Event Chain

```python
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

def on_attack(event: AttackEvent) -> None:
    damage = calculate_damage(event.attacker, event.defender)
    bus.emit(DamageEvent(
        source=event.attacker,
        target=event.defender,
        amount=damage
    ))

bus.subscribe(AttackEvent, on_attack)
```

### Event Logger

```python
def log_event(event: object) -> None:
    if hasattr(event, 'metadata'):
        print(f"[Turn {event.metadata.turn}] {type(event).__name__}")

bus.subscribe_all(log_event)
```

### Turn System

```python
def start_turn(turn: int) -> None:
    bus.set_turn(turn)
    bus.emit(TurnStartEvent(turn_number=turn))
    # ... run turn logic ...
    bus.emit(TurnEndEvent(turn_number=turn))

start_turn(1)
```

### Event Statistics

```python
def get_event_stats(bus: EventBus) -> dict:
    history = bus.get_history()
    return {
        "total": len(history),
        "by_type": {
            event_type.__name__: len(bus.query(event_type=event_type))
            for event_type in set(type(e) for e in history)
        },
        "by_turn": {
            turn: len(bus.query(turn=turn))
            for turn in set(e.metadata.turn for e in history)
        }
    }
```

### Conditional Subscriptions

```python
class ConditionalHandler:
    def __init__(self, bus: EventBus, condition: callable):
        self.condition = condition
        bus.subscribe_all(self.handle)

    def handle(self, event: object) -> None:
        if self.condition(event):
            print(f"Condition met for {type(event).__name__}")

# Only log high-damage events
handler = ConditionalHandler(
    bus,
    lambda e: isinstance(e, DamageEvent) and e.amount > 50
)
```

## Type Hints

```python
from typing import Callable, Any

EventHandler = Callable[[Any], None]

def create_logger() -> EventHandler:
    def log(event: Any) -> None:
        print(event)
    return log

bus.subscribe_all(create_logger())
```

## Testing

```python
def test_my_event():
    bus = EventBus()
    received = []

    bus.subscribe(MyEvent, lambda e: received.append(e))
    bus.emit(MyEvent(field1=42, field2="test"))

    assert len(received) == 1
    assert received[0].field1 == 42
    assert hasattr(received[0], 'metadata')
```

## Common Event Fields

```python
# Entity reference events
entity_id: EntityId         # The primary entity

# Source/target events
source: EntityId            # Who caused it
target: EntityId            # Who received it

# Value events
amount: int                 # Damage, healing, experience, etc.
value: Any                  # Generic value

# Type classification
event_type: str             # Category or type
damage_type: str           # Physical, fire, ice, etc.

# Optional context
reason: str                # Why it happened
metadata: EventMetadata    # Automatic (always present after emit)
```

## Error Handling

```python
# Handlers can fail without breaking the bus
def risky_handler(event: MyEvent) -> None:
    if event.field1 < 0:
        raise ValueError("Negative value!")
    # This won't crash the event bus

bus.subscribe(MyEvent, risky_handler)
bus.emit(MyEvent(field1=-1, field2="test"))  # Error logged, other handlers run
```

## Performance Tips

```python
# ❌ Avoid: Heavy work in handlers
def slow_handler(event: MyEvent) -> None:
    recalculate_entire_game_state()  # Too slow!

# ✅ Better: Defer heavy work
work_queue = []
def fast_handler(event: MyEvent) -> None:
    work_queue.append(event)  # Process later

# ❌ Avoid: Querying in handlers (can cause O(n²))
def bad_handler(event: MyEvent) -> None:
    all_events = bus.query(event_type=MyEvent)  # Slow!

# ✅ Better: Cache or batch queries
event_cache = []
def good_handler(event: MyEvent) -> None:
    event_cache.append(event)  # Process batch later
```

## Naming Conventions

```python
# Events: Past tense or present perfect
DamageDealtEvent        # ✅ Past tense
EntityDiedEvent         # ✅ Past tense
ItemPickedUpEvent       # ✅ Past perfect

DealDamageEvent         # ❌ Sounds like a command
KillEntityEvent         # ❌ Sounds like a command

# Handlers: Descriptive action
def handle_damage(event)    # ✅
def on_entity_death(event)  # ✅
def process_pickup(event)   # ✅
```
