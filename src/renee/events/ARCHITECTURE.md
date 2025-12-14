# Event System Architecture

## Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                      EventBus                           │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Subscribers  │  │   History    │  │   Metadata   │ │
│  │              │  │              │  │   Generator  │ │
│  │ Dict[type,   │  │ List[Event]  │  │              │ │
│  │ List[Handler]]│  │              │  │ turn: int    │ │
│  │              │  │              │  │              │ │
│  │ Wildcard:    │  │              │  │              │ │
│  │ List[Handler]│  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                   │                   │
         │ emit()            │ query()           │ set_turn()
         ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                    Event Lifecycle                      │
│                                                         │
│  1. Event Created (dataclass)                          │
│  2. Metadata Added (id, timestamp, turn)               │
│  3. Added to History                                   │
│  4. Handlers Notified (type-specific + wildcard)       │
│  5. Available for Query                                │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Event Emission Flow

```
User Code
   │
   │ emit(DamageEvent(...))
   ▼
EventBus.emit()
   │
   ├─► 1. Validate event is dataclass
   │
   ├─► 2. Generate metadata
   │      - Unique ID (UUID)
   │      - Current timestamp
   │      - Current turn number
   │
   ├─► 3. Create event with metadata
   │      event_with_metadata = replace(event, metadata=metadata)
   │
   ├─► 4. Add to history
   │      _history.append(event_with_metadata)
   │
   ├─► 5. Notify type-specific subscribers
   │      for handler in _subscribers[DamageEvent]:
   │         handler(event_with_metadata)
   │
   ├─► 6. Notify wildcard subscribers
   │      for handler in _wildcard_subscribers:
   │         handler(event_with_metadata)
   │
   └─► 7. Return event with metadata
```

### Subscription Flow

```
User Code
   │
   │ subscribe(DamageEvent, handle_damage)
   ▼
EventBus.subscribe()
   │
   └─► Store in _subscribers dict
       _subscribers[DamageEvent].append(handle_damage)

User Code
   │
   │ subscribe_all(log_all)
   ▼
EventBus.subscribe_all()
   │
   └─► Store in wildcard list
       _wildcard_subscribers.append(log_all)
```

### Query Flow

```
User Code
   │
   │ query(event_type=DamageEvent, turn=5, entity=EntityId(1))
   ▼
EventBus.query()
   │
   ├─► Iterate through _history
   │
   ├─► Apply filters:
   │   │
   │   ├─► Type filter: isinstance(event, event_type)?
   │   │
   │   ├─► Turn filter: event.metadata.turn == turn?
   │   │
   │   ├─► Entity filter: entity in [event.entity_id, event.source, event.target]?
   │   │
   │   └─► Custom filter: filter_fn(event)?
   │
   ├─► Collect matching events
   │
   └─► Return results (up to limit)
```

## Class Structure

### EventMetadata

```python
@dataclass(frozen=True, slots=True)
class EventMetadata:
    event_id: str      # Unique identifier
    timestamp: datetime # When event was emitted
    turn: int          # Turn number when emitted
```

### Event Base Class

```python
@dataclass(frozen=True, slots=True)
class Event:
    metadata: EventMetadata = field(init=False, repr=False)
```

### EventBus

```python
class EventBus:
    _current_turn: int
    _history: list[Any]
    _subscribers: dict[type, list[EventHandler]]
    _wildcard_subscribers: list[EventHandler]
```

## Storage Model

### Subscribers Storage

```
_subscribers = {
    DamageEvent: [handle_damage, log_damage, update_stats],
    HealEvent: [handle_heal],
    LevelUpEvent: [handle_level_up, show_animation],
    ...
}

_wildcard_subscribers = [
    log_all_events,
    debug_logger,
    event_recorder,
]
```

### History Storage

```
_history = [
    DamageEvent(source=1, target=2, amount=10, metadata=...),
    HealEvent(target=2, amount=5, metadata=...),
    LevelUpEvent(entity_id=1, new_level=2, metadata=...),
    DamageEvent(source=2, target=1, amount=12, metadata=...),
    ...
]
```

## Event Processing

### Handler Execution Order

1. Type-specific handlers (in registration order)
2. Wildcard handlers (in registration order)

### Error Handling

```
for handler in handlers:
    try:
        handler(event)
    except Exception as e:
        # Log error but continue processing
        print(f"Error in handler: {e}")
        # Other handlers still execute
```

This ensures one failing handler doesn't break the entire event system.

## Memory Management

### Event History Growth

```
Turn 1:  [e1, e2, e3]                    # 3 events
Turn 2:  [e1, e2, e3, e4, e5]           # 5 events
Turn 3:  [e1, e2, e3, e4, e5, e6, e7]   # 7 events
...
Turn N:  [e1 ... eX]                     # X events total

Memory usage grows linearly with total events
```

### Cleanup Strategies

```python
# Strategy 1: Periodic clear
if bus.event_count() > MAX_EVENTS:
    bus.clear_history()

# Strategy 2: Rolling window
old_events = bus.query(filter_fn=lambda e: e.metadata.turn < current_turn - WINDOW)
# Remove old events (custom implementation)

# Strategy 3: Selective retention
important = bus.query(event_type=CriticalEvent)
bus.clear_history()
for event in important:
    # Re-add important events
```

## Threading Considerations

The current implementation is **not thread-safe**. For multi-threaded use:

```python
import threading

class ThreadSafeEventBus(EventBus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()

    def emit(self, event):
        with self._lock:
            return super().emit(event)

    def subscribe(self, event_type, handler):
        with self._lock:
            return super().subscribe(event_type, handler)

    # ... lock other methods similarly
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| `emit()` | O(n) | n = number of subscribers for that type |
| `subscribe()` | O(1) | Append to list |
| `unsubscribe()` | O(n) | n = subscribers for that type |
| `query()` | O(m) | m = total events in history |
| `get_history()` | O(m) | Creates copy of history |
| `clear_history()` | O(1) | List clear operation |

### Space Complexity

| Component | Complexity | Notes |
|-----------|------------|-------|
| History | O(m) | m = total events emitted |
| Subscribers | O(s * h) | s = event types, h = handlers per type |
| Per Event | O(1) | Fixed size dataclass + metadata |

### Optimization Opportunities

For hot paths or large-scale games:

1. **Index history by turn/type**
   ```python
   _history_by_turn: dict[int, list[Event]] = defaultdict(list)
   _history_by_type: dict[type, list[Event]] = defaultdict(list)
   ```

2. **Lazy metadata generation**
   ```python
   # Only generate UUID when needed
   metadata.event_id = lambda: str(uuid.uuid4())
   ```

3. **Event pooling**
   ```python
   # Reuse event objects for frequently emitted events
   _event_pool: dict[type, list[Event]] = {}
   ```

## Integration Points

### With ECS World

```python
class World:
    def __init__(self, event_bus: EventBus | None = None):
        self.event_bus = event_bus or EventBus()

    def create_entity(self) -> EntityId:
        entity_id = self._create_entity_internal()
        self.event_bus.emit(EntityCreatedEvent(entity_id=entity_id))
        return entity_id
```

### With Game Loop

```python
def game_loop(world: World, bus: EventBus):
    turn = 1
    bus.set_turn(turn)
    bus.emit(GameStartEvent())

    while not game_over:
        bus.emit(TurnStartEvent(turn_number=turn))

        # Run game systems...

        bus.emit(TurnEndEvent(turn_number=turn))
        turn += 1
        bus.set_turn(turn)

    bus.emit(GameEndEvent(reason="victory"))
```

### With Serialization

```python
# Save game state
game_state = {
    "turn": bus.get_turn(),
    "events": bus.to_json(),
    "world": world.to_json(),
}

# Replay events
for event_data in saved_events:
    event = deserialize_event(event_data)
    bus.emit(event)
```

## Design Patterns Used

1. **Observer Pattern**: Subscribers observe event emissions
2. **Singleton Pattern**: Typically one EventBus per game instance
3. **Immutable Data**: Events are frozen dataclasses
4. **Metadata Pattern**: Automatic enrichment of events
5. **Strategy Pattern**: Custom filter functions for queries

## Extension Points

### Custom Event Types

```python
@dataclass(frozen=True, slots=True)
class CustomEvent:
    custom_field: str
    metadata: EventMetadata = None  # type: ignore[assignment]
```

### Custom Queries

```python
def find_combat_chain(bus: EventBus, starting_entity: EntityId):
    """Custom query to trace combat interactions."""
    events = bus.query(
        filter_fn=lambda e: (
            hasattr(e, 'source') and
            (e.source == starting_entity or e.target == starting_entity)
        )
    )
    return events
```

### Custom Handlers

```python
class EventLogger:
    def __init__(self, bus: EventBus):
        bus.subscribe_all(self.log_event)

    def log_event(self, event: Any) -> None:
        with open("event.log", "a") as f:
            f.write(f"{event.metadata.timestamp}: {type(event).__name__}\n")
```

## Testing Strategy

The event system supports multiple testing approaches:

### Unit Testing
```python
def test_damage_event():
    bus = EventBus()
    received = []
    bus.subscribe(DamageEvent, lambda e: received.append(e))
    bus.emit(DamageEvent(...))
    assert len(received) == 1
```

### Integration Testing
```python
def test_combat_system():
    world = World()
    bus = EventBus()
    combat = CombatSystem(world, bus)

    bus.emit(AttackEvent(...))
    assert bus.query(event_type=DamageEvent)
```

### Replay Testing
```python
def test_replay():
    # Record events
    events = bus.get_history()

    # Create new bus and replay
    new_bus = EventBus()
    for event in events:
        new_bus.emit(event)

    assert new_bus.get_history() == events
```
