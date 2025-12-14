"""Action Pipeline system for Renee.

The Action Pipeline handles the flow: Request → Validation → Pre-Rules → Execution → Post-Rules → Events

This module provides:
- Action: Base class for all actions
- ActionContext: Context passed to rules during processing
- ActionResult: Result of action execution
- ActionPipeline: Main pipeline for processing actions

Example:
    # Create pipeline
    pipeline = ActionPipeline()

    # Register handler
    def move_handler(action: Action, world: World) -> list[Event]:
        entity = action.params['entity']
        target = action.params['target']
        world.add_component(entity, target)
        return [MovedEvent(entity=entity, to=target)]

    pipeline.register_handler('move', move_handler)

    # Add pre-rule
    def check_range(ctx: ActionContext) -> None:
        entity = ctx.action.params['entity']
        target = ctx.action.params['target']
        pos = ctx.world.get_component(entity, Position)
        if pos.manhattan_distance(target) > 5:
            ctx.cancel("Target is out of range")

    pipeline.add_pre_rule('move', check_range)

    # Execute action
    action = Action('move', {'entity': e1, 'target': Position(5, 5)})
    result = pipeline.execute(action, world)

    if result.success:
        for event in result.events:
            event_bus.emit(event)
"""

from renee.actions.action import Action, ActionContext
from renee.actions.pipeline import ActionPipeline
from renee.actions.result import ActionResult

__all__ = [
    "Action",
    "ActionContext",
    "ActionPipeline",
    "ActionResult",
]
