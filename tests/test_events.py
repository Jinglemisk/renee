"""Tests for event bus."""

from __future__ import annotations

from renee.events import EventBus
from renee.types import EntityId


class TestEventBus:
    def test_emit_and_history(self) -> None:
        bus = EventBus()
        bus.emit("hello", {"x": 1}, turn=0, actor=EntityId(1))
        bus.emit("hello", {"x": 2}, turn=1, actor=EntityId(2))
        bus.emit("other", {"x": 3}, turn=1, actor=EntityId(1))

        assert len(bus.history()) == 3
        assert len(bus.history(event_type="hello")) == 2
        assert len(bus.history(turn=1)) == 2
        assert len(bus.history(actor=EntityId(1))) == 2
        assert [e.payload["x"] for e in bus.history(event_type="hello")] == [1, 2]

    def test_subscribe(self) -> None:
        bus = EventBus()
        seen: list[str] = []

        bus.on("hello", lambda e: seen.append(f"hello:{e.payload['x']}"))
        bus.emit("hello", {"x": 1})
        bus.emit("other", {"x": 2})
        bus.emit("hello", {"x": 3})

        assert seen == ["hello:1", "hello:3"]

