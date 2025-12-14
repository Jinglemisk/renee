"""Demo of the Renee Event Bus system.

This example shows how to:
1. Define custom events as dataclasses
2. Create an EventBus instance
3. Subscribe handlers to events
4. Emit events
5. Query event history
6. Use wildcard subscriptions
"""

from dataclasses import dataclass

from renee.events import EventBus, EventMetadata, EntityCreatedEvent, TurnStartEvent
from renee.types import EntityId


# Define custom game events as dataclasses
@dataclass(frozen=True, slots=True)
class DamageEvent:
    """Event for damage dealing."""

    source: EntityId
    target: EntityId
    amount: int
    damage_type: str = "physical"
    metadata: EventMetadata = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class HealEvent:
    """Event for healing."""

    target: EntityId
    amount: int
    healer: EntityId | None = None
    metadata: EventMetadata = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class LevelUpEvent:
    """Event for entity leveling up."""

    entity_id: EntityId
    new_level: int
    metadata: EventMetadata = None  # type: ignore[assignment]


def main() -> None:
    """Run the event system demo."""
    print("=== Renee Event Bus Demo ===\n")

    # Create event bus
    bus = EventBus(current_turn=1)
    print(f"Created EventBus at turn {bus.get_turn()}")

    # Subscribe to specific events
    print("\n--- Subscribing to events ---")

    def handle_damage(event: DamageEvent) -> None:
        print(
            f"  [DAMAGE] Entity {event.source} dealt {event.amount} "
            f"{event.damage_type} damage to {event.target}"
        )

    def handle_heal(event: HealEvent) -> None:
        healer_text = f" by {event.healer}" if event.healer else ""
        print(f"  [HEAL] Entity {event.target} healed for {event.amount}{healer_text}")

    def handle_level_up(event: LevelUpEvent) -> None:
        print(f"  [LEVEL UP] Entity {event.entity_id} is now level {event.new_level}!")

    bus.subscribe(DamageEvent, handle_damage)
    bus.subscribe(HealEvent, handle_heal)
    bus.subscribe(LevelUpEvent, handle_level_up)

    # Wildcard subscription to log all events
    event_log = []

    def log_all_events(event: object) -> None:
        event_log.append(event)

    bus.subscribe_all(log_all_events)

    # Emit some events
    print("\n--- Turn 1: Combat begins ---")
    bus.emit(EntityCreatedEvent(entity_id=EntityId(1)))
    bus.emit(EntityCreatedEvent(entity_id=EntityId(2)))
    bus.emit(
        DamageEvent(
            source=EntityId(1), target=EntityId(2), amount=15, damage_type="fire"
        )
    )
    bus.emit(HealEvent(target=EntityId(2), amount=5))

    # Advance to next turn
    bus.set_turn(2)
    print(f"\n--- Turn 2: The battle continues ---")
    bus.emit(TurnStartEvent(turn_number=2))
    bus.emit(
        DamageEvent(
            source=EntityId(2), target=EntityId(1), amount=12, damage_type="physical"
        )
    )
    bus.emit(DamageEvent(source=EntityId(1), target=EntityId(2), amount=20))
    bus.emit(LevelUpEvent(entity_id=EntityId(1), new_level=2))

    # Query event history
    print("\n--- Event History Query ---")
    print(f"Total events: {bus.event_count()}")
    print(f"Events logged by wildcard: {len(event_log)}")

    # Query by type
    damage_events = bus.query(event_type=DamageEvent)
    print(f"\nDamage events: {len(damage_events)}")
    for event in damage_events:
        print(
            f"  Turn {event.metadata.turn}: {event.source} -> {event.target} "
            f"({event.amount} {event.damage_type} damage)"
        )

    # Query by turn
    turn_1_events = bus.query(turn=1)
    print(f"\nTurn 1 events: {len(turn_1_events)}")

    # Query by entity
    entity_1_events = bus.query(entity=EntityId(1))
    print(f"\nEvents involving Entity 1: {len(entity_1_events)}")

    # Query with custom filter
    high_damage = bus.query(event_type=DamageEvent, filter_fn=lambda e: e.amount > 15)
    print(f"\nHigh damage events (>15): {len(high_damage)}")
    for event in high_damage:
        print(f"  {event.amount} damage")

    # Export to JSON
    print("\n--- JSON Export ---")
    json_output = bus.to_json(indent=2)
    print("Event history exported to JSON:")
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)

    # Demonstrate metadata
    print("\n--- Event Metadata ---")
    last_event = bus.get_history()[-1]
    print(f"Last event type: {type(last_event).__name__}")
    print(f"Event ID: {last_event.metadata.event_id}")
    print(f"Turn: {last_event.metadata.turn}")
    print(f"Timestamp: {last_event.metadata.timestamp}")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
