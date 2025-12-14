"""Basic multiplayer server/client integration test."""

from __future__ import annotations

import time

from renee.actions import ActionPipeline
from renee.ecs import World
from renee.events import EventBus
from renee.multiplayer import MultiplayerClient, MultiplayerServer
from renee.schema import SchemaRegistry
from renee.turns import TurnManager
from renee.types import EntityId, Position


def _registry() -> SchemaRegistry:
    reg = SchemaRegistry()
    reg.load_from_mapping(
        {
            "components": {"Position": {"fields": {"x": "int", "y": "int"}}},
            "actions": {"Spawn": {"fields": {"entity": "EntityId", "x": "int", "y": "int"}}},
        }
    )
    return reg


class TestMultiplayer:
    def test_server_client_event_sync(self) -> None:
        reg = _registry()
        server_world = World()
        server_pipeline = ActionPipeline(
            world=server_world, bus=EventBus(), schemas=reg, turns=TurnManager([EntityId(1)])
        )

        def spawn(ctx) -> None:  # type: ignore[no-untyped-def]
            ctx.queue_event(
                "ecs.entity_spawned",
                {"entity": ctx.params["entity"], "components": {"Position": {"x": ctx.params["x"], "y": ctx.params["y"]}}},
            )

        server_pipeline.register_action("Spawn", spawn)

        server = MultiplayerServer(pipeline=server_pipeline, host="127.0.0.1", port=0)
        server.start()

        client_pipeline = ActionPipeline(world=World(), bus=EventBus(), schemas=reg)
        client = MultiplayerClient(pipeline=client_pipeline, host="127.0.0.1", port=server.port)
        client.connect()

        client.send_action("Spawn", {"entity": 99, "x": 2, "y": 3})

        # Give background thread a moment to apply the event.
        deadline = time.time() + 2.0
        while time.time() < deadline:
            if client_pipeline.world.entity_exists(EntityId(99)):
                break
            time.sleep(0.01)

        assert client_pipeline.world.entity_exists(EntityId(99))
        assert client_pipeline.world.get_component(EntityId(99), Position) == Position(x=2, y=3)

        client.disconnect()
        server.stop()

