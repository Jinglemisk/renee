"""Event system for Renee.

The event system provides:
- EventBus for centralized event handling
- Event base class with automatic metadata
- Common built-in events
- Event history and querying

Example:
    from renee.events import EventBus, EntityCreatedEvent

    bus = EventBus()
    bus.subscribe(EntityCreatedEvent, lambda e: print(f"Created {e.entity_id}"))
    bus.emit(EntityCreatedEvent(entity_id=EntityId(1)))
"""

from renee.events.bus import EventBus, EventJSONEncoder
from renee.events.event import (
    Event,
    EventMetadata,
    EntityCreatedEvent,
    EntityDestroyedEvent,
    ComponentAddedEvent,
    ComponentRemovedEvent,
    TurnStartEvent,
    TurnEndEvent,
    GameStartEvent,
    GameEndEvent,
)

__all__ = [
    # Core classes
    "EventBus",
    "Event",
    "EventMetadata",
    "EventJSONEncoder",
    # Built-in events
    "EntityCreatedEvent",
    "EntityDestroyedEvent",
    "ComponentAddedEvent",
    "ComponentRemovedEvent",
    "TurnStartEvent",
    "TurnEndEvent",
    "GameStartEvent",
    "GameEndEvent",
]
