"""Action pipeline implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from renee.actions.appliers import (
    EventApplierRegistry,
    register_default_ecs_appliers,
    register_default_turn_appliers,
)
from renee.actions.types import ActionContext, ActionHandler, ActionResult
from renee.errors import SchemaError
from renee.events import Event, EventBus
from renee.rules import RuleEngine
from renee.schema import SchemaRegistry
from renee.turns import TurnManager
from renee.types import EntityId


@dataclass(frozen=True, slots=True)
class ActionSpec:
    name: str
    handler: ActionHandler
    schema: str | None = None


class ActionPipeline:
    def __init__(
        self,
        *,
        world: Any,
        bus: EventBus | None = None,
        schemas: SchemaRegistry | None = None,
        rules: RuleEngine | None = None,
        turns: TurnManager | None = None,
        appliers: EventApplierRegistry | None = None,
    ) -> None:
        from renee.ecs import World

        if not isinstance(world, World):
            raise TypeError("ActionPipeline.world must be a renee.ecs.World")
        self.world = world
        self.bus = EventBus() if bus is None else bus
        self.schemas = schemas
        self.rules = RuleEngine() if rules is None else rules
        self.turns = turns

        self.appliers = EventApplierRegistry() if appliers is None else appliers
        register_default_ecs_appliers(self.appliers)
        register_default_turn_appliers(self.appliers)

        self._actions: dict[str, ActionSpec] = {}

    def register_action(self, name: str, handler: ActionHandler, *, schema: str | None = None) -> None:
        if name in self._actions:
            raise SchemaError(
                "action_already_registered",
                f"Action already registered: {name}",
                hint="Use a unique action name.",
            )
        self._actions[name] = ActionSpec(name=name, handler=handler, schema=schema or name)

    def execute(
        self,
        action: str,
        *,
        actor: EntityId | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> ActionResult:
        if action not in self._actions:
            raise SchemaError(
                "action_not_registered",
                f"Unknown action: {action}",
                hint="Register the action handler with ActionPipeline.register_action().",
                context={"action": action, "known": sorted(self._actions.keys())},
            )
        spec = self._actions[action]
        raw_params = dict(params or {})

        # Turn validation.
        if self.turns is not None and actor is not None and not self.turns.is_players_turn(actor):
            ctx = ActionContext(
                action=action,
                actor=actor,
                params=raw_params,
                world=self.world,
                bus=self.bus,
                schemas=self.schemas,
                turns=self.turns,
            )
            ctx.cancel("It is not this player's turn.")
            cancel_event = self.bus.emit(
                "action_cancelled",
                {"action": action, "actor": actor, "params": ctx.params, "reason": ctx.cancel_reason},
                turn=ctx.current_turn(),
                actor=actor,
            )
            return ActionResult(
                action=action,
                actor=actor,
                ok=False,
                cancelled=True,
                cancel_reason=ctx.cancel_reason,
                params=ctx.params,
                events=(cancel_event,),
            )

        typed_params = self._coerce_params(spec, raw_params)
        ctx = ActionContext(
            action=action,
            actor=actor,
            params=typed_params,
            world=self.world,
            bus=self.bus,
            schemas=self.schemas,
            turns=self.turns,
        )
        turn_at_start = ctx.current_turn()

        # Pre-rules may cancel or modify parameters.
        self.rules.run(ctx, phase="pre")

        emitted: list[Event] = []
        if not ctx.cancelled:
            emitted.extend(self._flush_events(ctx, turn=turn_at_start))
            spec.handler(ctx)
            emitted.extend(self._flush_events(ctx, turn=turn_at_start))
            self.rules.run(ctx, phase="post")
            emitted.extend(self._flush_events(ctx, turn=turn_at_start))

        if ctx.cancelled:
            emitted.append(
                self.bus.emit(
                    "action_cancelled",
                    {"action": action, "actor": actor, "params": ctx.params, "reason": ctx.cancel_reason},
                    turn=turn_at_start,
                    actor=actor,
                )
            )
            return ActionResult(
                action=action,
                actor=actor,
                ok=False,
                cancelled=True,
                cancel_reason=ctx.cancel_reason,
                params=ctx.params,
                events=tuple(emitted),
            )

        completion = self.bus.emit(
            "action_completed",
            {"action": action, "actor": actor, "params": ctx.params},
            turn=turn_at_start,
            actor=actor,
        )
        emitted.append(completion)

        if self.turns is not None:
            self.turns.on_action_completed()
            emitted.append(
                self.bus.emit(
                    "turn.sync",
                    self.turns.to_dict(),
                    turn=self.turns.turn_number,
                    actor=actor,
                )
            )

        return ActionResult(
            action=action,
            actor=actor,
            ok=True,
            cancelled=False,
            cancel_reason=None,
            params=ctx.params,
            events=tuple(emitted),
        )

    def apply_event(self, event_type: str, payload: Mapping[str, Any], *, strict: bool = True) -> bool:
        """Apply an event to state without running rules/handlers (replay/sync).

        Returns True if the event was applied.
        """

        ctx = ActionContext(
            action="__replay__",
            actor=None,
            params={},
            world=self.world,
            bus=self.bus,
            schemas=self.schemas,
            turns=self.turns,
        )
        if strict:
            self.appliers.apply(ctx, event_type, payload)
            return True
        return self.appliers.apply_if_registered(ctx, event_type, payload)

    def _coerce_params(self, spec: ActionSpec, raw: dict[str, Any]) -> dict[str, Any]:
        if self.schemas is None or spec.schema is None:
            return raw
        # If the schema exists, instantiate then convert to dict of typed values.
        try:
            typed = self.schemas.instantiate(spec.schema, raw, kind="action")
        except SchemaError:
            raise
        fields = getattr(typed, "__dataclass_fields__", {})
        return {name: getattr(typed, name) for name in fields.keys()}

    def _flush_events(self, ctx: ActionContext, *, turn: int | None) -> list[Event]:
        events: list[Event] = []
        for spec in ctx.drain_events():
            self.appliers.apply(ctx, spec.type, spec.payload)
            events.append(self.bus.emit(spec.type, spec.payload, turn=turn, actor=ctx.actor))
        return events
