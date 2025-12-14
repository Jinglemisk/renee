"""Event appliers (reducers) for event-sourced state updates."""

from __future__ import annotations

from typing import Any, Mapping

from renee.actions.types import ActionContext, EventApplier
from renee.errors import SchemaError
from renee.types import EntityId


class EventApplierRegistry:
    def __init__(self) -> None:
        self._appliers: dict[str, EventApplier] = {}

    def register(self, event_type: str, applier: EventApplier) -> None:
        self._appliers[event_type] = applier

    def has(self, event_type: str) -> bool:
        return event_type in self._appliers

    def apply(self, ctx: ActionContext, event_type: str, payload: Mapping[str, Any]) -> None:
        applier = self._appliers.get(event_type)
        if applier is None:
            raise SchemaError(
                "event_applier_missing",
                f"No applier registered for event type: {event_type}",
                hint="Register an applier for this event type, or emit ECS events.",
                context={"event_type": event_type},
            )
        applier(ctx, payload)

    def apply_if_registered(self, ctx: ActionContext, event_type: str, payload: Mapping[str, Any]) -> bool:
        applier = self._appliers.get(event_type)
        if applier is None:
            return False
        applier(ctx, payload)
        return True


def register_default_ecs_appliers(registry: EventApplierRegistry) -> None:
    registry.register("ecs.entity_spawned", _apply_ecs_spawn)
    registry.register("ecs.entity_destroyed", _apply_ecs_destroy)
    registry.register("ecs.component_set", _apply_ecs_component_set)
    registry.register("ecs.component_removed", _apply_ecs_component_removed)
    registry.register("ecs.tag_added", _apply_ecs_tag_added)
    registry.register("ecs.tag_removed", _apply_ecs_tag_removed)
    registry.register("ecs.intent_set", _apply_ecs_intent_set)


def register_default_turn_appliers(registry: EventApplierRegistry) -> None:
    registry.register("turn.sync", _apply_turn_sync)


def _apply_ecs_spawn(ctx: ActionContext, payload: Mapping[str, Any]) -> None:
    entity_raw = payload.get("entity")
    if entity_raw is None:
        entity = ctx.world.create_entity()
    else:
        entity = ctx.world.create_entity_with_id(EntityId(int(entity_raw)))

    components = payload.get("components", {})
    if isinstance(components, Mapping):
        for comp_name, comp_data in components.items():
            component_obj = _instantiate_component(ctx, str(comp_name), comp_data)
            ctx.world.add_component(entity, component_obj)

    for tag in payload.get("tags", []) or []:
        ctx.world.add_tag(entity, str(tag))

    intent = payload.get("intent")
    if isinstance(intent, str):
        ctx.world.set_intent(entity, intent)


def _apply_ecs_destroy(ctx: ActionContext, payload: Mapping[str, Any]) -> None:
    entity = EntityId(int(payload["entity"]))
    ctx.world.destroy_entity(entity)


def _apply_ecs_component_set(ctx: ActionContext, payload: Mapping[str, Any]) -> None:
    entity = EntityId(int(payload["entity"]))
    comp_name = str(payload["component"])
    data = payload.get("data")
    component_obj = _instantiate_component(ctx, comp_name, data)
    ctx.world.add_component(entity, component_obj)


def _apply_ecs_component_removed(ctx: ActionContext, payload: Mapping[str, Any]) -> None:
    if ctx.schemas is None:
        raise SchemaError(
            "schema_registry_missing",
            "Component removal requires a SchemaRegistry to resolve component types.",
            hint="Provide SchemaRegistry to the ActionPipeline.",
        )
    entity = EntityId(int(payload["entity"]))
    comp_name = str(payload["component"])
    comp_type = ctx.schemas.generated_type(comp_name, kind="component")
    ctx.world.remove_component(entity, comp_type)


def _apply_ecs_tag_added(ctx: ActionContext, payload: Mapping[str, Any]) -> None:
    entity = EntityId(int(payload["entity"]))
    ctx.world.add_tag(entity, str(payload["tag"]))


def _apply_ecs_tag_removed(ctx: ActionContext, payload: Mapping[str, Any]) -> None:
    entity = EntityId(int(payload["entity"]))
    ctx.world.remove_tag(entity, str(payload["tag"]))


def _apply_ecs_intent_set(ctx: ActionContext, payload: Mapping[str, Any]) -> None:
    entity = EntityId(int(payload["entity"]))
    ctx.world.set_intent(entity, str(payload["intent"]))


def _instantiate_component(ctx: ActionContext, comp_name: str, data: Any) -> object:
    if isinstance(data, Mapping):
        if ctx.schemas is None:
            raise SchemaError(
                "schema_registry_missing",
                f"Component '{comp_name}' requires SchemaRegistry to instantiate from mapping data.",
                hint="Load component schemas and pass SchemaRegistry to the ActionPipeline.",
            )
        return ctx.schemas.instantiate(comp_name, data, kind="component")
    if data is None:
        raise SchemaError(
            "component_data_missing",
            f"Component '{comp_name}' data is missing.",
            hint="Provide a mapping for component data (e.g., {x: 1, y: 2}).",
        )
    return data


def _apply_turn_sync(ctx: ActionContext, payload: Mapping[str, Any]) -> None:
    if ctx.turns is None:
        raise SchemaError(
            "turn_manager_missing",
            "turn.sync requires an active TurnManager.",
            hint="Initialize TurnManager before replaying turn events.",
        )
    if not isinstance(payload, Mapping):
        raise SchemaError("turn_sync_invalid", "turn.sync payload must be a mapping.")
    new_state = dict(payload)
    new = ctx.turns.from_dict(new_state)
    ctx.turns.players = new.players
    ctx.turns.phases = new.phases
    ctx.turns.current_player_index = new.current_player_index
    ctx.turns.current_phase_index = new.current_phase_index
    ctx.turns.turn_number = new.turn_number
    ctx.turns.round_number = new.round_number
    ctx.turns.auto_advance = new.auto_advance
