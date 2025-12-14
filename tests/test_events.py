"""Tests for the event system."""

import json
from dataclasses import dataclass
from datetime import datetime

import pytest

from renee.events import (
    EventBus,
    Event,
    EventMetadata,
    EntityCreatedEvent,
    EntityDestroyedEvent,
    TurnStartEvent,
    GameStartEvent,
)
from renee.types import EntityId


@dataclass(frozen=True, slots=True)
class DamageEvent:
    """Test event for damage dealing."""

    source: EntityId
    target: EntityId
    amount: int
    metadata: EventMetadata = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class HealEvent:
    """Test event for healing."""

    target: EntityId
    amount: int
    metadata: EventMetadata = None  # type: ignore[assignment]


class TestEventBus:
    """Test suite for EventBus."""

    def test_emit_adds_metadata(self) -> None:
        """Test that emitting an event adds metadata."""
        bus = EventBus(current_turn=5)
        event = DamageEvent(source=EntityId(1), target=EntityId(2), amount=10)

        emitted = bus.emit(event)

        assert hasattr(emitted, "metadata")
        assert emitted.metadata.turn == 5
        assert isinstance(emitted.metadata.event_id, str)
        assert isinstance(emitted.metadata.timestamp, datetime)

    def test_emit_adds_to_history(self) -> None:
        """Test that emitted events are added to history."""
        bus = EventBus()
        event = DamageEvent(source=EntityId(1), target=EntityId(2), amount=10)

        bus.emit(event)

        history = bus.get_history()
        assert len(history) == 1
        assert history[0].amount == 10

    def test_subscribe_and_emit(self) -> None:
        """Test subscribing to and receiving events."""
        bus = EventBus()
        received_events = []

        def handler(event: DamageEvent) -> None:
            received_events.append(event)

        bus.subscribe(DamageEvent, handler)
        event = DamageEvent(source=EntityId(1), target=EntityId(2), amount=10)
        bus.emit(event)

        assert len(received_events) == 1
        assert received_events[0].amount == 10

    def test_multiple_subscribers(self) -> None:
        """Test that multiple subscribers receive events."""
        bus = EventBus()
        received1 = []
        received2 = []

        bus.subscribe(DamageEvent, lambda e: received1.append(e))
        bus.subscribe(DamageEvent, lambda e: received2.append(e))

        event = DamageEvent(source=EntityId(1), target=EntityId(2), amount=10)
        bus.emit(event)

        assert len(received1) == 1
        assert len(received2) == 1

    def test_type_specific_subscription(self) -> None:
        """Test that subscribers only receive events of their type."""
        bus = EventBus()
        damage_events = []
        heal_events = []

        bus.subscribe(DamageEvent, lambda e: damage_events.append(e))
        bus.subscribe(HealEvent, lambda e: heal_events.append(e))

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(HealEvent(target=EntityId(2), amount=5))

        assert len(damage_events) == 1
        assert len(heal_events) == 1
        assert damage_events[0].amount == 10
        assert heal_events[0].amount == 5

    def test_wildcard_subscription(self) -> None:
        """Test wildcard subscription receives all events."""
        bus = EventBus()
        all_events = []

        bus.subscribe_all(lambda e: all_events.append(e))

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(HealEvent(target=EntityId(2), amount=5))

        assert len(all_events) == 2

    def test_unsubscribe(self) -> None:
        """Test unsubscribing from events."""
        bus = EventBus()
        received = []

        def handler(event: DamageEvent) -> None:
            received.append(event)

        bus.subscribe(DamageEvent, handler)
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

        assert len(received) == 1

        # Unsubscribe and emit again
        result = bus.unsubscribe(DamageEvent, handler)
        assert result is True
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

        assert len(received) == 1  # Still only 1

    def test_unsubscribe_wildcard(self) -> None:
        """Test unsubscribing from wildcard events."""
        bus = EventBus()
        received = []

        def handler(event: Any) -> None:
            received.append(event)

        bus.subscribe_all(handler)
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

        assert len(received) == 1

        # Unsubscribe and emit again
        result = bus.unsubscribe_all(handler)
        assert result is True
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

        assert len(received) == 1  # Still only 1

    def test_clear_subscribers(self) -> None:
        """Test clearing all subscribers."""
        bus = EventBus()
        received = []

        bus.subscribe(DamageEvent, lambda e: received.append(e))
        bus.subscribe_all(lambda e: received.append(e))

        bus.clear_subscribers()
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

        assert len(received) == 0

    def test_query_by_type(self) -> None:
        """Test querying events by type."""
        bus = EventBus()

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(HealEvent(target=EntityId(2), amount=5))
        bus.emit(DamageEvent(source=EntityId(3), target=EntityId(4), amount=20))

        damage_events = bus.query(event_type=DamageEvent)
        assert len(damage_events) == 2
        assert all(isinstance(e, DamageEvent) for e in damage_events)

    def test_query_by_turn(self) -> None:
        """Test querying events by turn number."""
        bus = EventBus(current_turn=1)
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

        bus.set_turn(2)
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=20))

        bus.set_turn(3)
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=30))

        turn_2_events = bus.query(turn=2)
        assert len(turn_2_events) == 1
        assert turn_2_events[0].amount == 20

    def test_query_by_entity(self) -> None:
        """Test querying events by entity ID."""
        bus = EventBus()

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(DamageEvent(source=EntityId(3), target=EntityId(2), amount=20))
        bus.emit(HealEvent(target=EntityId(2), amount=5))

        # Query by target entity
        entity_2_events = bus.query(entity=EntityId(2))
        assert len(entity_2_events) == 3  # All events involve entity 2

    def test_query_with_filter(self) -> None:
        """Test querying with a custom filter function."""
        bus = EventBus()

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=50))
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=5))

        # Get damage events with amount > 20
        high_damage = bus.query(
            event_type=DamageEvent, filter_fn=lambda e: e.amount > 20
        )

        assert len(high_damage) == 1
        assert high_damage[0].amount == 50

    def test_query_with_limit(self) -> None:
        """Test querying with a result limit."""
        bus = EventBus()

        for i in range(10):
            bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=i))

        limited = bus.query(event_type=DamageEvent, limit=5)
        assert len(limited) == 5

    def test_query_combined_filters(self) -> None:
        """Test querying with multiple filters combined."""
        bus = EventBus(current_turn=1)

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=50))

        bus.set_turn(2)
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=30))

        # Get high damage events from turn 1
        results = bus.query(
            event_type=DamageEvent, turn=1, filter_fn=lambda e: e.amount > 20
        )

        assert len(results) == 1
        assert results[0].amount == 50
        assert results[0].metadata.turn == 1

    def test_clear_history(self) -> None:
        """Test clearing event history."""
        bus = EventBus()

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(HealEvent(target=EntityId(2), amount=5))

        assert bus.event_count() == 2

        bus.clear_history()
        assert bus.event_count() == 0
        assert len(bus.get_history()) == 0

    def test_set_and_get_turn(self) -> None:
        """Test setting and getting the current turn."""
        bus = EventBus(current_turn=5)
        assert bus.get_turn() == 5

        bus.set_turn(10)
        assert bus.get_turn() == 10

        event = bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        assert event.metadata.turn == 10

    def test_event_count(self) -> None:
        """Test event count tracking."""
        bus = EventBus()
        assert bus.event_count() == 0

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        assert bus.event_count() == 1

        bus.emit(HealEvent(target=EntityId(2), amount=5))
        assert bus.event_count() == 2

    def test_to_json(self) -> None:
        """Test JSON serialization of event history."""
        bus = EventBus(current_turn=1)

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(EntityCreatedEvent(entity_id=EntityId(3)))

        json_str = bus.to_json()
        parsed = json.loads(json_str)

        assert len(parsed) == 2
        assert parsed[0]["_event_type"] == "DamageEvent"
        assert parsed[0]["amount"] == 10
        assert parsed[1]["_event_type"] == "EntityCreatedEvent"

    def test_built_in_events(self) -> None:
        """Test that built-in events work correctly."""
        bus = EventBus()

        bus.emit(EntityCreatedEvent(entity_id=EntityId(1)))
        bus.emit(EntityDestroyedEvent(entity_id=EntityId(1)))
        bus.emit(TurnStartEvent(turn_number=1))
        bus.emit(GameStartEvent())

        assert bus.event_count() == 4

        created = bus.query(event_type=EntityCreatedEvent)
        assert len(created) == 1
        assert created[0].entity_id == EntityId(1)

    def test_emit_non_dataclass_raises(self) -> None:
        """Test that emitting a non-dataclass raises an error."""
        bus = EventBus()

        with pytest.raises(TypeError):
            bus.emit("not a dataclass")  # type: ignore[arg-type]

    def test_handler_exception_doesnt_break_bus(self) -> None:
        """Test that exceptions in handlers don't break the event bus."""
        bus = EventBus()
        received = []

        def bad_handler(event: DamageEvent) -> None:
            raise ValueError("Handler error!")

        def good_handler(event: DamageEvent) -> None:
            received.append(event)

        bus.subscribe(DamageEvent, bad_handler)
        bus.subscribe(DamageEvent, good_handler)

        # This should not raise, even though bad_handler raises
        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

        # Good handler should still receive the event
        assert len(received) == 1

    def test_event_history_is_immutable_copy(self) -> None:
        """Test that get_history returns a copy, not the internal list."""
        bus = EventBus()

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))

        history1 = bus.get_history()
        history2 = bus.get_history()

        assert history1 is not history2
        assert history1 == history2

    def test_multiple_event_types_same_bus(self) -> None:
        """Test that a single bus can handle many different event types."""
        bus = EventBus()

        bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=10))
        bus.emit(HealEvent(target=EntityId(2), amount=5))
        bus.emit(EntityCreatedEvent(entity_id=EntityId(3)))
        bus.emit(TurnStartEvent(turn_number=1))

        assert bus.event_count() == 4

        # Each type should be queryable
        assert len(bus.query(event_type=DamageEvent)) == 1
        assert len(bus.query(event_type=HealEvent)) == 1
        assert len(bus.query(event_type=EntityCreatedEvent)) == 1
        assert len(bus.query(event_type=TurnStartEvent)) == 1
