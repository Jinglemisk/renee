"""Tests for action pipeline and rules."""

import pytest

from renee.actions import ActionPipeline
from renee.ecs import World
from renee.events import EventBus
from renee.rules import RuleEngine, rule
from renee.schema import SchemaRegistry
from renee.types import EntityId, Position
from renee.turns import TurnManager


def _registry() -> SchemaRegistry:
    reg = SchemaRegistry()
    reg.load_from_mapping(
        {
            "components": {"Position": {"fields": {"x": "int", "y": "int"}}},
            "actions": {
                "Spawn": {"fields": {"entity": "EntityId", "x": "int", "y": "int"}},
                "Move": {"fields": {"entity": "EntityId", "to": "Position"}},
            },
        }
    )
    return reg


class TestActionPipeline:
    def test_action_emits_and_applies_ecs_events(self) -> None:
        reg = _registry()
        world = World()
        bus = EventBus()
        pipeline = ActionPipeline(world=world, bus=bus, schemas=reg)

        def spawn(ctx) -> None:  # type: ignore[no-untyped-def]
            ctx.queue_event(
                "ecs.entity_spawned",
                {
                    "entity": ctx.params["entity"],
                    "components": {"Position": {"x": ctx.params["x"], "y": ctx.params["y"]}},
                    "tags": ["player"],
                },
            )

        pipeline.register_action("Spawn", spawn)
        result = pipeline.execute("Spawn", actor=EntityId(1), params={"entity": 10, "x": 2, "y": 3})

        assert result.ok
        assert world.entity_exists(EntityId(10))
        assert world.get_component(EntityId(10), reg.generated_type("Position", kind="component")) == reg.instantiate(
            "Position", {"x": 2, "y": 3}, kind="component"
        )
        assert [e.type for e in bus.history()] == ["ecs.entity_spawned", "action_completed"]

    def test_pre_rule_can_cancel(self) -> None:
        reg = _registry()
        world = World()
        bus = EventBus()
        rules = RuleEngine()

        @rule(phase="pre")
        def no_negative_x(ctx) -> None:  # type: ignore[no-untyped-def]
            if ctx.params.get("x", 0) < 0:
                ctx.cancel("x must be >= 0")

        rules.register(no_negative_x)
        pipeline = ActionPipeline(world=world, bus=bus, schemas=reg, rules=rules)

        def spawn(ctx) -> None:  # type: ignore[no-untyped-def]
            ctx.queue_event("ecs.entity_spawned", {"entity": ctx.params["entity"], "components": {}})

        pipeline.register_action("Spawn", spawn)
        result = pipeline.execute("Spawn", actor=EntityId(1), params={"entity": 1, "x": -1, "y": 0})
        assert result.cancelled
        assert "x must be" in (result.cancel_reason or "")
        assert world.entity_count() == 0

    def test_turn_validation_cancels(self) -> None:
        reg = _registry()
        world = World()
        bus = EventBus()
        turns = TurnManager([EntityId(1), EntityId(2)])
        pipeline = ActionPipeline(world=world, bus=bus, schemas=reg, turns=turns)

        def move(ctx) -> None:  # type: ignore[no-untyped-def]
            ctx.queue_event(
                "ecs.component_set",
                {"entity": ctx.params["entity"], "component": "Position", "data": {"x": 0, "y": 0}},
            )

        # Seed an entity so Move can work.
        world.create_entity_with_id(EntityId(99))
        world.add_component(EntityId(99), Position(x=1, y=1))

        pipeline.register_action("Move", move)
        result = pipeline.execute("Move", actor=EntityId(2), params={"entity": 99, "to": {"x": 0, "y": 0}})
        assert result.cancelled
        assert bus.history(event_type="action_cancelled")

    def test_missing_action_registration_raises(self) -> None:
        pipeline = ActionPipeline(world=World())
        with pytest.raises(Exception):
            pipeline.execute("Unknown")

