"""Shared types for the action pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from renee.ecs import World
from renee.events import Event, EventBus
from renee.schema import SchemaRegistry
from renee.turns import TurnManager
from renee.types import EntityId


@dataclass(frozen=True, slots=True)
class EventSpec:
    type: str
    payload: Mapping[str, Any]


@dataclass
class ActionContext:
    action: str
    actor: EntityId | None
    params: dict[str, Any]
    world: World
    bus: EventBus
    schemas: SchemaRegistry | None = None
    turns: TurnManager | None = None

    cancelled: bool = False
    cancel_reason: str | None = None

    emitted: list[Event] = field(default_factory=list)
    _queue: list[EventSpec] = field(default_factory=list, repr=False)

    def cancel(self, reason: str) -> None:
        self.cancelled = True
        self.cancel_reason = reason

    def modify(self, **changes: Any) -> None:
        self.params.update(changes)

    def queue_event(self, event_type: str, payload: Mapping[str, Any]) -> None:
        self._queue.append(EventSpec(type=event_type, payload=dict(payload)))

    def drain_events(self) -> list[EventSpec]:
        events = list(self._queue)
        self._queue.clear()
        return events

    def current_turn(self) -> int | None:
        return None if self.turns is None else self.turns.turn_number


ActionHandler = Callable[[ActionContext], None]
EventApplier = Callable[[ActionContext, Mapping[str, Any]], None]


@dataclass(frozen=True, slots=True)
class ActionResult:
    action: str
    actor: EntityId | None
    ok: bool
    cancelled: bool
    cancel_reason: str | None
    params: Mapping[str, Any]
    events: tuple[Event, ...]

