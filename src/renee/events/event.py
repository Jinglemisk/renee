"""Base Event class and common event types for Renee.

Events are immutable dataclasses with automatic metadata.
All game events should inherit from Event or be plain dataclasses.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from renee.types import EntityId


@dataclass(frozen=True, slots=True)
class EventMetadata:
    """Metadata automatically added to all events."""

    event_id: str
    timestamp: datetime
    turn: int


def _default_metadata() -> EventMetadata:
    """Create placeholder metadata (will be replaced by EventBus.emit())."""
    return EventMetadata(event_id="", timestamp=datetime.min, turn=-1)


@dataclass(frozen=True, slots=True)
class Event:
    """Base class for all game events.

    Events are immutable records of things that happened in the game.
    They carry automatic metadata (id, timestamp, turn) and custom data.

    Subclass this to create custom events, or use plain dataclasses.
    """

    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


# Common built-in events


@dataclass(frozen=True, slots=True)
class EntityCreatedEvent:
    """Emitted when an entity is created."""

    entity_id: EntityId
    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


@dataclass(frozen=True, slots=True)
class EntityDestroyedEvent:
    """Emitted when an entity is destroyed."""

    entity_id: EntityId
    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


@dataclass(frozen=True, slots=True)
class ComponentAddedEvent:
    """Emitted when a component is added to an entity."""

    entity_id: EntityId
    component_type: str
    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


@dataclass(frozen=True, slots=True)
class ComponentRemovedEvent:
    """Emitted when a component is removed from an entity."""

    entity_id: EntityId
    component_type: str
    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


@dataclass(frozen=True, slots=True)
class TurnStartEvent:
    """Emitted when a new turn starts."""

    turn_number: int
    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


@dataclass(frozen=True, slots=True)
class TurnEndEvent:
    """Emitted when a turn ends."""

    turn_number: int
    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


@dataclass(frozen=True, slots=True)
class GameStartEvent:
    """Emitted when the game starts."""

    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


@dataclass(frozen=True, slots=True)
class GameEndEvent:
    """Emitted when the game ends."""

    reason: str
    metadata: EventMetadata = field(default_factory=_default_metadata, repr=False)


def _generate_event_id() -> str:
    """Generate a unique event ID."""
    return str(uuid.uuid4())


def _create_metadata(turn: int) -> EventMetadata:
    """Create event metadata with current timestamp and turn number."""
    return EventMetadata(
        event_id=_generate_event_id(),
        timestamp=datetime.now(),
        turn=turn,
    )
