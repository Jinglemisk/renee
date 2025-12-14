"""Simple REPL with optional JSON output.

The REPL is intentionally minimal and engine-focused. Games can build richer
tools on top of these primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable, Mapping

from renee.actions import ActionPipeline
from renee.ecs import WorldSnapshot
from renee.errors import ReneeError
from renee.types import EntityId


@dataclass
class _SnapshotBundle:
    world: WorldSnapshot
    turns: dict[str, Any] | None


class Repl:
    def __init__(self, *, pipeline: ActionPipeline, json_mode: bool = False) -> None:
        self.pipeline = pipeline
        self.json_mode = json_mode
        self._snapshots: dict[int, _SnapshotBundle] = {}
        self._next_snapshot_id = 1

    def run(self) -> None:
        self._print({"type": "repl_ready", "help": "Type 'help'."})
        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                return
            if not line:
                continue
            if line in {"quit", "exit"}:
                return
            try:
                self._dispatch(line)
            except ReneeError as e:
                self._print({"type": "error", "error": e.to_dict()})
            except Exception as e:  # noqa: BLE001
                self._print({"type": "error", "error": {"code": "repl_error", "message": str(e)}})

    def _dispatch(self, line: str) -> None:
        parts = line.split(maxsplit=2)
        cmd = parts[0]
        args = parts[1:]

        if cmd == "help":
            self._print(
                {
                    "type": "help",
                    "commands": [
                        "entities",
                        "show <entity_id>",
                        "turn",
                        "events [n]",
                        "snapshot",
                        "rollback <snapshot_id>",
                        "action <name> <json_params>",
                        "quit",
                    ],
                }
            )
            return

        if cmd == "entities":
            ents = [int(e) for e in self.pipeline.world.all_entities()]
            self._print({"type": "entities", "entities": ents})
            return

        if cmd == "show":
            if not args:
                raise ReneeError("usage", "show requires an entity id", hint="show 1")
            eid = EntityId(int(args[0]))
            comps = {}
            for t, v in self.pipeline.world.get_all_components(eid).items():
                comps[t.__name__] = _jsonable(v)
            self._print(
                {
                    "type": "entity",
                    "id": int(eid),
                    "tags": sorted(self.pipeline.world.tags(eid)),
                    "intent": self.pipeline.world.get_intent(eid),
                    "components": comps,
                }
            )
            return

        if cmd == "turn":
            turns = self.pipeline.turns
            if turns is None:
                self._print({"type": "turn", "enabled": False})
                return
            self._print(
                {
                    "type": "turn",
                    "enabled": True,
                    "current_player": int(turns.current_player()),
                    "phase": turns.current_phase().name,
                    "turn_number": turns.turn_number,
                    "round_number": turns.round_number,
                }
            )
            return

        if cmd == "events":
            n = int(args[0]) if args else 10
            history = self.pipeline.bus.history()
            tail = history[-n:]
            self._print(
                {
                    "type": "events",
                    "events": [
                        {"type": e.type, "payload": _jsonable(dict(e.payload)), "meta": e.meta.__dict__}
                        for e in tail
                    ],
                }
            )
            return

        if cmd == "snapshot":
            sid = self._next_snapshot_id
            self._next_snapshot_id += 1
            turns_state = None if self.pipeline.turns is None else self.pipeline.turns.to_dict()
            self._snapshots[sid] = _SnapshotBundle(world=self.pipeline.world.snapshot(), turns=turns_state)
            self._print({"type": "snapshot", "id": sid})
            return

        if cmd == "rollback":
            if not args:
                raise ReneeError("usage", "rollback requires a snapshot id", hint="rollback 1")
            sid = int(args[0])
            if sid not in self._snapshots:
                raise ReneeError("snapshot_not_found", f"Snapshot not found: {sid}")
            bundle = self._snapshots[sid]
            self.pipeline.world.restore(bundle.world)
            if bundle.turns is not None and self.pipeline.turns is not None:
                self.pipeline.apply_event("turn.sync", bundle.turns, strict=True)
            self._print({"type": "rollback", "id": sid})
            return

        if cmd == "action":
            if len(args) < 2:
                raise ReneeError("usage", "action requires a name and JSON params", hint="action Move {\"dx\":1,\"dy\":0}")
            name = args[0]
            params = json.loads(args[1])
            actor = None if self.pipeline.turns is None else self.pipeline.turns.current_player()
            result = self.pipeline.execute(name, actor=actor, params=params)
            self._print(
                {
                    "type": "action_result",
                    "ok": result.ok,
                    "cancelled": result.cancelled,
                    "reason": result.cancel_reason,
                    "events": [{"type": e.type, "payload": _jsonable(dict(e.payload))} for e in result.events],
                }
            )
            return

        raise ReneeError("unknown_command", f"Unknown command: {cmd}", hint="Type 'help' for commands.")

    def _print(self, obj: Mapping[str, Any]) -> None:
        if self.json_mode:
            print(json.dumps(obj, indent=2, sort_keys=True))
        else:
            print(obj)


def run_repl(*, pipeline: ActionPipeline, json_mode: bool = False) -> None:
    Repl(pipeline=pipeline, json_mode=json_mode).run()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "__dataclass_fields__"):
        return {k: _jsonable(getattr(value, k)) for k in value.__dataclass_fields__.keys()}
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return str(value)

