"""Event Bus implementation for Renee.

The EventBus is the central hub for event-driven communication.
It handles event emission, subscription, and history tracking.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime
from typing import Any, Callable, TypeVar

from renee.events.event import EventMetadata, _create_metadata
from renee.types import EntityId

# Type for event handler functions
EventHandler = Callable[[Any], None]
T = TypeVar("T")


class EventBus:
    """Central event bus for game events.

    The EventBus manages event emission, subscription, and history.
    It automatically adds metadata to all events and maintains a queryable history.

    Example:
        bus = EventBus()

        # Subscribe to events
        def handle_damage(event: DamageEvent):
            print(f"Entity {event.target} took {event.amount} damage!")

        bus.subscribe(DamageEvent, handle_damage)

        # Emit events
        bus.emit(DamageEvent(source=1, target=2, amount=10))

        # Query history
        recent = bus.query(event_type=DamageEvent, turn=5)
        all_events = bus.get_history()
    """

    def __init__(self, current_turn: int = 0) -> None:
        """Initialize the event bus.

        Args:
            current_turn: The current turn number (used for event metadata).
        """
        self._current_turn = current_turn
        self._history: list[Any] = []
        self._subscribers: dict[type, list[EventHandler]] = defaultdict(list)
        self._wildcard_subscribers: list[EventHandler] = []

    def set_turn(self, turn: int) -> None:
        """Update the current turn number.

        This affects the metadata of newly emitted events.

        Args:
            turn: The new turn number.
        """
        self._current_turn = turn

    def get_turn(self) -> int:
        """Get the current turn number."""
        return self._current_turn

    def emit(self, event: T) -> T:
        """Emit an event to all subscribers and add it to history.

        The event will have metadata automatically added before emission.

        Args:
            event: The event to emit (must be a dataclass).

        Returns:
            The event with metadata added.

        Raises:
            TypeError: If event is not a dataclass.
        """
        if not is_dataclass(event):
            raise TypeError(f"Event must be a dataclass, got {type(event)}")

        # Add metadata to the event
        metadata = _create_metadata(self._current_turn)
        event_with_metadata = replace(event, metadata=metadata)

        # Add to history
        self._history.append(event_with_metadata)

        # Notify type-specific subscribers
        event_type = type(event_with_metadata)
        for handler in self._subscribers.get(event_type, []):
            try:
                handler(event_with_metadata)
            except Exception as e:
                # Log but don't crash - we don't want one handler to break others
                print(f"Error in event handler for {event_type.__name__}: {e}")

        # Notify wildcard subscribers
        for handler in self._wildcard_subscribers:
            try:
                handler(event_with_metadata)
            except Exception as e:
                print(f"Error in wildcard event handler: {e}")

        return event_with_metadata  # type: ignore[return-value]

    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: The type of event to listen for.
            handler: Function to call when events of this type are emitted.
        """
        self._subscribers[event_type].append(handler)  # type: ignore[arg-type]

    def subscribe_all(self, handler: Callable[[Any], None]) -> None:
        """Subscribe to all events (wildcard subscription).

        Args:
            handler: Function to call for any emitted event.
        """
        self._wildcard_subscribers.append(handler)

    def unsubscribe(self, event_type: type[T], handler: Callable[[T], None]) -> bool:
        """Unsubscribe a handler from events of a specific type.

        Args:
            event_type: The type of event to stop listening for.
            handler: The handler function to remove.

        Returns:
            True if the handler was found and removed, False otherwise.
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)  # type: ignore[arg-type]
                return True
            except ValueError:
                return False
        return False

    def unsubscribe_all(self, handler: Callable[[Any], None]) -> bool:
        """Unsubscribe a wildcard handler.

        Args:
            handler: The handler function to remove.

        Returns:
            True if the handler was found and removed, False otherwise.
        """
        try:
            self._wildcard_subscribers.remove(handler)
            return True
        except ValueError:
            return False

    def clear_subscribers(self) -> None:
        """Remove all event subscribers."""
        self._subscribers.clear()
        self._wildcard_subscribers.clear()

    def get_history(self) -> list[Any]:
        """Get the complete event history.

        Returns:
            A copy of the event history list.
        """
        return list(self._history)

    def query(
        self,
        event_type: type[T] | None = None,
        turn: int | None = None,
        entity: EntityId | None = None,
        filter_fn: Callable[[Any], bool] | None = None,
        limit: int | None = None,
    ) -> list[Any]:
        """Query the event history with filters.

        Args:
            event_type: Filter by event type (optional).
            turn: Filter by turn number (optional).
            entity: Filter by entity_id field (if event has one) (optional).
            filter_fn: Custom filter function (optional).
            limit: Maximum number of events to return (optional).

        Returns:
            List of events matching the filters.

        Example:
            # Get all damage events from turn 5
            events = bus.query(event_type=DamageEvent, turn=5)

            # Get recent events with custom filter
            events = bus.query(
                filter_fn=lambda e: e.metadata.timestamp > some_time,
                limit=10
            )
        """
        results = []

        for event in self._history:
            # Type filter
            if event_type is not None and not isinstance(event, event_type):
                continue

            # Turn filter
            if turn is not None and hasattr(event, "metadata"):
                if event.metadata.turn != turn:
                    continue

            # Entity filter (check common entity-related fields)
            if entity is not None:
                entity_found = False
                for field_name in ["entity_id", "source", "target"]:
                    if hasattr(event, field_name):
                        field_value = getattr(event, field_name)
                        if field_value == entity:
                            entity_found = True
                            break
                if not entity_found:
                    continue

            # Custom filter
            if filter_fn is not None and not filter_fn(event):
                continue

            results.append(event)

            # Limit check
            if limit is not None and len(results) >= limit:
                break

        return results

    def clear_history(self) -> None:
        """Clear the event history.

        This is useful for tests or when starting a new game session.
        """
        self._history.clear()

    def event_count(self) -> int:
        """Get the total number of events in history."""
        return len(self._history)

    def to_json(self, indent: int | None = None) -> str:
        """Export event history to JSON.

        Args:
            indent: JSON indentation level (None for compact).

        Returns:
            JSON string representation of event history.

        Note:
            This uses a custom JSON encoder to handle EntityId and datetime.
        """
        return json.dumps(
            [self._event_to_dict(event) for event in self._history],
            indent=indent,
            cls=EventJSONEncoder,
        )

    def _event_to_dict(self, event: Any) -> dict[str, Any]:
        """Convert an event dataclass to a dictionary for JSON serialization."""
        if not is_dataclass(event):
            return {"_raw": str(event)}

        result = asdict(event)
        result["_event_type"] = type(event).__name__

        return result


class EventJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for events.

    Handles special types like EntityId, datetime, and custom dataclasses.
    """

    def default(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable formats."""
        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Handle EntityId (NewType wrapper around int)
        if isinstance(obj, int):
            return obj

        # Handle dataclasses
        if is_dataclass(obj):
            result = asdict(obj)
            result["_type"] = type(obj).__name__
            return result

        # Fall back to default behavior
        return super().default(obj)
