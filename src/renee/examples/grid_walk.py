"""A tiny turn-based grid-walk demo.

Demonstrates:
- schema registry (components/actions)
- ECS world and snapshotting
- action pipeline with ECS events
- turn sync via multiplayer layer
- renderer-agnostic render commands (terminal/pygame)
"""

from __future__ import annotations

import time
from typing import Any

from renee.actions import ActionPipeline
from renee.ecs import World
from renee.events import EventBus
from renee.multiplayer import MultiplayerClient, MultiplayerServer
from renee.rendering import Clear, DrawText, HeadlessRenderer, PygameRenderer, TerminalRenderer
from renee.schema import SchemaRegistry
from renee.turns import Phase, TurnManager
from renee.types import EntityId, Position


GRID_W = 20
GRID_H = 10


def build_demo() -> tuple[ActionPipeline, SchemaRegistry]:
    schemas = SchemaRegistry()
    schemas.load_from_mapping(
        {
            "components": {
                "Position": {"fields": {"x": "int", "y": "int"}},
                "Name": {"fields": {"value": "str"}},
            },
            "actions": {
                "Move": {"fields": {"dx": "int", "dy": "int"}},
            },
        }
    )

    world = World()
    bus = EventBus()
    turns = TurnManager(
        [EntityId(1), EntityId(2)],
        phases=[Phase("main", traits=frozenset({"single_action"}))],
        auto_advance=True,
    )
    pipeline = ActionPipeline(world=world, bus=bus, schemas=schemas, turns=turns)

    # Create two players with fixed IDs matching turn order.
    p1 = world.create_entity_with_id(EntityId(1))
    world.add_component(p1, Position(x=2, y=2))
    world.add_component(p1, schemas.instantiate("Name", {"value": "1"}, kind="component"))

    p2 = world.create_entity_with_id(EntityId(2))
    world.add_component(p2, Position(x=6, y=2))
    world.add_component(p2, schemas.instantiate("Name", {"value": "2"}, kind="component"))

    def move(ctx) -> None:  # type: ignore[no-untyped-def]
        if ctx.actor is None:
            ctx.cancel("Move requires an actor.")
            return
        dx = int(ctx.params["dx"])
        dy = int(ctx.params["dy"])
        if abs(dx) + abs(dy) != 1:
            ctx.cancel("Move must be cardinal (dx/dy of length 1).")
            return

        pos = ctx.world.get_component(ctx.actor, Position)
        nxt = Position(pos.x + dx, pos.y + dy)
        if not (0 <= nxt.x < GRID_W and 0 <= nxt.y < GRID_H):
            ctx.cancel("Out of bounds.")
            return

        ctx.queue_event(
            "ecs.component_set",
            {
                "entity": ctx.actor,
                "component": "Position",
                "data": {"x": nxt.x, "y": nxt.y},
            },
        )

    pipeline.register_action("Move", move)
    return pipeline, schemas


def render_commands(pipeline: ActionPipeline, schemas: SchemaRegistry) -> list[dict[str, Any]]:
    world = pipeline.world
    turns = pipeline.turns
    name_type = schemas.generated_type("Name", kind="component")

    grid = [["." for _ in range(GRID_W)] for _ in range(GRID_H)]
    for e in world.query(Position):
        pos = world.get_component(e, Position)
        label = str(int(e))
        if world.has_component(e, name_type):
            label = world.get_component(e, name_type).value  # type: ignore[attr-defined]
        grid[pos.y][pos.x] = label[:1]

    cmds: list[Any] = [Clear()]
    for y, row in enumerate(grid):
        cmds.append(DrawText("".join(row), x=0, y=y, size=16))

    if turns is not None:
        cmds.append(
            DrawText(
                f"Turn {turns.turn_number} | Player {int(turns.current_player())}",
                x=0,
                y=GRID_H + 1,
                size=16,
            )
        )
    cmds.append(DrawText("Arrows/WASD: move | Q: quit", x=0, y=GRID_H + 2, size=16))
    return [c.to_dict() if hasattr(c, "to_dict") else c for c in cmds]


def run_local(*, renderer: str = "terminal") -> None:
    pipeline, schemas = build_demo()
    if renderer == "pygame":
        r = PygameRenderer()
        r.initialize({"width": 800, "height": 600, "title": "Renee Grid Walk", "scale": 20})
        try:
            while True:
                inp = r.get_input()
                if inp.quit_requested:
                    return
                dx, dy = _movement_from_keys(inp.keys_pressed)
                if (dx, dy) != (0, 0) and pipeline.turns is not None:
                    pipeline.execute("Move", actor=pipeline.turns.current_player(), params={"dx": dx, "dy": dy})
                if "q" in inp.keys_pressed or "escape" in inp.keys_pressed:
                    return

                cmds = render_commands(pipeline, schemas)
                r.render(cmds)
        finally:
            r.shutdown()

    if renderer == "headless":
        r2 = HeadlessRenderer()
        r2.initialize()
        r2.render(render_commands(pipeline, schemas))
        return

    r3 = TerminalRenderer(width=GRID_W, height=GRID_H + 3)
    r3.initialize()
    while True:
        r3.render(render_commands(pipeline, schemas))
        if pipeline.turns is None:
            return
        line = input(f"Player {int(pipeline.turns.current_player())} move (w/a/s/d, q): ").strip().lower()
        if line in {"q", "quit", "exit"}:
            return
        dx, dy = _movement_from_text(line)
        if (dx, dy) == (0, 0):
            continue
        pipeline.execute("Move", actor=pipeline.turns.current_player(), params={"dx": dx, "dy": dy})


def run_server(*, host: str = "127.0.0.1", port: int = 8765) -> None:
    pipeline, _schemas = build_demo()
    server = MultiplayerServer(pipeline=pipeline, host=host, port=port)
    server.start()
    print(f"Server listening on {host}:{server.port} (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        server.stop()


def run_client(*, host: str = "127.0.0.1", port: int = 8765, renderer: str = "terminal") -> None:
    pipeline, schemas = build_demo()
    client = MultiplayerClient(pipeline=pipeline, host=host, port=port)
    client.connect()

    if renderer == "pygame":
        r = PygameRenderer()
        r.initialize({"width": 800, "height": 600, "title": "Renee Grid Walk (Client)", "scale": 20})
        try:
            while True:
                inp = r.get_input()
                if inp.quit_requested:
                    return
                dx, dy = _movement_from_keys(inp.keys_pressed)
                if (dx, dy) != (0, 0):
                    client.send_action("Move", {"dx": dx, "dy": dy})
                if "q" in inp.keys_pressed or "escape" in inp.keys_pressed:
                    return
                if client.last_error is not None:
                    raise client.last_error

                r.render(render_commands(pipeline, schemas))
        finally:
            r.shutdown()

    r3 = TerminalRenderer(width=GRID_W, height=GRID_H + 3)
    r3.initialize()
    while True:
        r3.render(render_commands(pipeline, schemas))
        if client.last_error is not None:
            raise client.last_error
        line = input("Move (w/a/s/d, q): ").strip().lower()
        if line in {"q", "quit", "exit"}:
            client.disconnect()
            return
        dx, dy = _movement_from_text(line)
        if (dx, dy) == (0, 0):
            continue
        client.send_action("Move", {"dx": dx, "dy": dy})


def _movement_from_keys(keys: set[str]) -> tuple[int, int]:
    if "left" in keys or "a" in keys:
        return (-1, 0)
    if "right" in keys or "d" in keys:
        return (1, 0)
    if "up" in keys or "w" in keys:
        return (0, -1)
    if "down" in keys or "s" in keys:
        return (0, 1)
    return (0, 0)


def _movement_from_text(text: str) -> tuple[int, int]:
    if not text:
        return (0, 0)
    if text[0] == "a":
        return (-1, 0)
    if text[0] == "d":
        return (1, 0)
    if text[0] == "w":
        return (0, -1)
    if text[0] == "s":
        return (0, 1)
    return (0, 0)
