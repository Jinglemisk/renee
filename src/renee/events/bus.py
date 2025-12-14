"""Event bus with history for event-sourced gameplay."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import time
from typing import Any, Callable, DefaultDict, Iterable, Mapping

from renee.types import EntityId


@dataclass(frozen=True, slots=True)
class EventMeta:
    id: int
    timestamp: float
    turn: int | None = None
    actor: EntityId | None = None


@dataclass(frozen=True, slots=True)
class Event:
    type: str
    payload: Mapping[str, Any]
    meta: EventMeta


EventHandler = Callable[[Event], None]


class EventBus:
    """Publish/subscribe event bus with queryable history."""

    def __init__(self) -> None:
        self._handlers: DefaultDict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []
        self._next_id: int = 1

    def on(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Use `"*"` to receive all events.
        """

        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(
        self,
        event_type: str,
        payload: Mapping[str, Any],
        *,
        turn: int | None = None,
        actor: EntityId | None = None,
    ) -> Event:
        meta = EventMeta(id=self._next_id, timestamp=time.time(), turn=turn, actor=actor)
        self._next_id += 1
        event = Event(type=event_type, payload=dict(payload), meta=meta)
        self._history.append(event)

        # Specific handlers
        for handler in list(self._handlers.get(event_type, [])):
            handler(event)

        # Wildcard handlers
        for handler in list(self._handlers.get("*", [])):
            handler(event)

        return event

    def clear_history(self) -> None:
        self._history.clear()

    def history(
        self,
        *,
        event_type: str | None = None,
        turn: int | None = None,
        actor: EntityId | None = None,
        since_id: int | None = None,
        until_id: int | None = None,
        predicate: Callable[[Event], bool] | None = None,
    ) -> list[Event]:
        events: Iterable[Event] = self._history

        if since_id is not None:
            events = (e for e in events if e.meta.id >= since_id)
        if until_id is not None:
            events = (e for e in events if e.meta.id <= until_id)
        if event_type is not None:
            events = (e for e in events if e.type == event_type)
        if turn is not None:
            events = (e for e in events if e.meta.turn == turn)
        if actor is not None:
            events = (e for e in events if e.meta.actor == actor)
        if predicate is not None:
            events = (e for e in events if predicate(e))

        return list(events)

