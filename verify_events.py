"""Quick verification script for the event system."""

from dataclasses import dataclass

from renee.events import (
    EventBus,
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
from renee.types import EntityId


@dataclass(frozen=True, slots=True)
class TestEvent:
    value: int
    metadata: EventMetadata = None  # type: ignore[assignment]


def main() -> None:
    print("Verifying Event System Implementation...")

    # Test 1: Create EventBus
    print("\n1. Creating EventBus...")
    bus = EventBus(current_turn=1)
    print(f"   ✓ EventBus created at turn {bus.get_turn()}")

    # Test 2: Emit and receive events
    print("\n2. Testing event emission and subscription...")
    received = []

    def handler(event: TestEvent) -> None:
        received.append(event)

    bus.subscribe(TestEvent, handler)
    bus.emit(TestEvent(value=42))

    assert len(received) == 1
    assert received[0].value == 42
    assert hasattr(received[0], "metadata")
    assert received[0].metadata.turn == 1
    print("   ✓ Event emission and subscription working")

    # Test 3: Query history
    print("\n3. Testing event history queries...")
    bus.emit(TestEvent(value=100))
    bus.set_turn(2)
    bus.emit(TestEvent(value=200))

    all_events = bus.query(event_type=TestEvent)
    assert len(all_events) == 3

    turn_1_events = bus.query(event_type=TestEvent, turn=1)
    assert len(turn_1_events) == 2
    print("   ✓ Event queries working")

    # Test 4: Built-in events
    print("\n4. Testing built-in events...")
    bus.emit(EntityCreatedEvent(entity_id=EntityId(1)))
    bus.emit(EntityDestroyedEvent(entity_id=EntityId(1)))
    bus.emit(TurnStartEvent(turn_number=3))
    bus.emit(GameStartEvent())

    entity_events = bus.query(event_type=EntityCreatedEvent)
    assert len(entity_events) == 1
    print("   ✓ Built-in events working")

    # Test 5: JSON serialization
    print("\n5. Testing JSON export...")
    json_str = bus.to_json()
    assert len(json_str) > 0
    assert "TestEvent" in json_str
    print("   ✓ JSON serialization working")

    # Test 6: Wildcard subscription
    print("\n6. Testing wildcard subscriptions...")
    all_captured = []
    bus.subscribe_all(lambda e: all_captured.append(e))
    bus.emit(TestEvent(value=999))

    assert len(all_captured) == 1
    print("   ✓ Wildcard subscriptions working")

    # Test 7: Event metadata
    print("\n7. Testing event metadata...")
    event = bus.emit(TestEvent(value=123))
    assert event.metadata.event_id is not None
    assert event.metadata.timestamp is not None
    assert event.metadata.turn == 2
    print("   ✓ Event metadata working")

    print("\n" + "=" * 50)
    print("✓ All verification tests passed!")
    print(f"✓ Total events in history: {bus.event_count()}")
    print("=" * 50)


if __name__ == "__main__":
    main()
