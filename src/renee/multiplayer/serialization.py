"""Serialization helpers for multiplayer messages."""

from __future__ import annotations

import dataclasses
from typing import Any, Mapping

from renee.events import Event
from renee.types import EntityId, Probability
from renee.ecs import World
from renee.schema import SchemaRegistry


def to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Probability):
        return float(value)
    if dataclasses.is_dataclass(value):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, set):
        return [to_jsonable(v) for v in sorted(value, key=str)]
    # Fallback: string repr.
    return str(value)


def event_to_dict(event: Event) -> dict[str, Any]:
    return {
        "type": event.type,
        "payload": to_jsonable(dict(event.payload)),
        "meta": {
            "id": event.meta.id,
            "timestamp": event.meta.timestamp,
            "turn": event.meta.turn,
            "actor": to_jsonable(event.meta.actor),
        },
    }


def world_to_dict(world: World) -> dict[str, Any]:
    snap = world.snapshot()
    entities: list[dict[str, Any]] = []
    for e in world.all_entities():
        comps: dict[str, Any] = {}
        for comp_type, comp_val in world.get_all_components(e).items():
            comps[comp_type.__name__] = to_jsonable(comp_val)
        entities.append(
            {
                "id": int(e),
                "components": comps,
                "tags": sorted(world.tags(e)),
                "intent": world.get_intent(e),
            }
        )
    return {"next_id": snap.next_id, "entities": entities}


def world_from_dict(data: Mapping[str, Any], *, schemas: SchemaRegistry | None = None) -> World:
    world = World()
    entities = data.get("entities", [])
    if not isinstance(entities, list):
        return world
    for ent in entities:
        if not isinstance(ent, Mapping):
            continue
        eid = world.create_entity_with_id(EntityId(int(ent.get("id", 0))))
        for tag in ent.get("tags", []) or []:
            world.add_tag(eid, str(tag))
        intent = ent.get("intent")
        if isinstance(intent, str):
            world.set_intent(eid, intent)
        comps = ent.get("components", {}) or {}
        if isinstance(comps, Mapping):
            for comp_name, comp_data in comps.items():
                if isinstance(comp_data, Mapping) and schemas is not None:
                    component_obj = schemas.instantiate(str(comp_name), comp_data, kind="component")
                else:
                    component_obj = comp_data
                world.add_component(eid, component_obj)
    return world
