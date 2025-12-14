"""Example demonstrating the Action Pipeline system.

This example shows how to:
- Define custom actions
- Register action handlers
- Add validators
- Use pre-rules to validate and modify actions
- Use post-rules to react to completed actions
- Execute actions through the pipeline
"""

from dataclasses import dataclass

from renee.actions import Action, ActionContext, ActionPipeline, ActionResult
from renee.ecs.world import World
from renee.types import EntityId, Position


# Define custom components
@dataclass
class Health:
    """Health component."""
    current: int
    maximum: int


@dataclass
class AttackPower:
    """Attack power component."""
    value: int


@dataclass
class MovementRange:
    """Movement range component."""
    range: int


# Define custom events
@dataclass(frozen=True)
class MovedEvent:
    """Event emitted when an entity moves."""
    entity: EntityId
    from_pos: Position
    to_pos: Position


@dataclass(frozen=True)
class DamageDealtEvent:
    """Event emitted when damage is dealt."""
    attacker: EntityId
    target: EntityId
    damage: int


@dataclass(frozen=True)
class EntityDiedEvent:
    """Event emitted when an entity dies."""
    entity: EntityId


def setup_pipeline() -> ActionPipeline:
    """Set up the action pipeline with handlers and rules."""
    pipeline = ActionPipeline()

    # === MOVE ACTION ===

    def move_validator(action: Action, world: World) -> str | None:
        """Validate move action parameters."""
        if 'entity' not in action.params:
            return "Missing required parameter: entity"
        if 'target' not in action.params:
            return "Missing required parameter: target"

        entity = action.params['entity']
        if not world.entity_exists(entity):
            return f"Entity {entity} does not exist"

        return None

    def check_movement_range(ctx: ActionContext) -> None:
        """Pre-rule: Check if target is within movement range."""
        entity = ctx.action.params['entity']
        target = ctx.action.params['target']

        # Get current position
        if not ctx.world.has_component(entity, Position):
            ctx.cancel("Entity has no position")
            return

        current_pos = ctx.world.get_component(entity, Position)

        # Get movement range
        if not ctx.world.has_component(entity, MovementRange):
            ctx.cancel("Entity cannot move")
            return

        move_range = ctx.world.get_component(entity, MovementRange)
        distance = current_pos.manhattan_distance(target)

        if distance > move_range.range:
            ctx.cancel(f"Target is out of range (distance: {distance}, max: {move_range.range})")

    def move_handler(action: Action, world: World) -> list:
        """Execute move action."""
        entity = action.params['entity']
        target = action.params['target']

        old_pos = world.get_component(entity, Position)
        world.add_component(entity, target)

        return [MovedEvent(entity=entity, from_pos=old_pos, to_pos=target)]

    def log_movement(ctx: ActionContext) -> None:
        """Post-rule: Log movement."""
        entity = ctx.action.params['entity']
        target = ctx.action.params['target']
        print(f"[LOG] Entity {entity} moved to {target}")

    pipeline.register_validator('move', move_validator)
    pipeline.add_pre_rule('move', check_movement_range, priority=10)
    pipeline.register_handler('move', move_handler)
    pipeline.add_post_rule('move', log_movement)

    # === ATTACK ACTION ===

    def attack_validator(action: Action, world: World) -> str | None:
        """Validate attack action parameters."""
        required_params = ['attacker', 'target']
        for param in required_params:
            if param not in action.params:
                return f"Missing required parameter: {param}"

            entity = action.params[param]
            if not world.entity_exists(entity):
                return f"Entity {entity} does not exist"

        return None

    def check_attack_range(ctx: ActionContext) -> None:
        """Pre-rule: Check if target is in range (adjacent)."""
        attacker = ctx.action.params['attacker']
        target = ctx.action.params['target']

        if not ctx.world.has_component(attacker, Position):
            ctx.cancel("Attacker has no position")
            return

        if not ctx.world.has_component(target, Position):
            ctx.cancel("Target has no position")
            return

        attacker_pos = ctx.world.get_component(attacker, Position)
        target_pos = ctx.world.get_component(target, Position)

        # Check if adjacent (distance 1)
        if attacker_pos.manhattan_distance(target_pos) > 1:
            ctx.cancel("Target is not adjacent")

    def calculate_damage(ctx: ActionContext) -> None:
        """Pre-rule: Calculate damage based on attacker's power."""
        attacker = ctx.action.params['attacker']

        if not ctx.world.has_component(attacker, AttackPower):
            ctx.cancel("Attacker has no attack power")
            return

        attack_power = ctx.world.get_component(attacker, AttackPower)
        ctx.modify_param('damage', attack_power.value)

    def attack_handler(action: Action, world: World) -> list:
        """Execute attack action."""
        attacker = action.params['attacker']
        target = action.params['target']
        damage = action.params['damage']

        events = []

        # Apply damage
        if world.has_component(target, Health):
            health = world.get_component(target, Health)
            new_health = Health(
                current=max(0, health.current - damage),
                maximum=health.maximum
            )
            world.add_component(target, new_health)

            events.append(DamageDealtEvent(
                attacker=attacker,
                target=target,
                damage=damage
            ))

            # Check if target died
            if new_health.current == 0:
                events.append(EntityDiedEvent(entity=target))

        return events

    def check_death(ctx: ActionContext) -> None:
        """Post-rule: Destroy entity if it died."""
        target = ctx.action.params['target']

        if ctx.world.has_component(target, Health):
            health = ctx.world.get_component(target, Health)
            if health.current == 0:
                ctx.world.destroy_entity(target)
                print(f"[LOG] Entity {target} was destroyed")

    pipeline.register_validator('attack', attack_validator)
    pipeline.add_pre_rule('attack', check_attack_range, priority=10)
    pipeline.add_pre_rule('attack', calculate_damage, priority=5)
    pipeline.register_handler('attack', attack_handler)
    pipeline.add_post_rule('attack', check_death)

    return pipeline


def main():
    """Run the example."""
    print("=== Action Pipeline Example ===\n")

    # Create world
    world = World()

    # Create entities
    player = world.create_entity()
    world.add_component(player, Position(0, 0))
    world.add_component(player, Health(current=100, maximum=100))
    world.add_component(player, AttackPower(value=25))
    world.add_component(player, MovementRange(range=3))

    enemy = world.create_entity()
    world.add_component(enemy, Position(5, 0))
    world.add_component(enemy, Health(current=50, maximum=50))
    world.add_component(enemy, AttackPower(value=15))
    world.add_component(enemy, MovementRange(range=2))

    print(f"Player: {player} at {world.get_component(player, Position)}")
    print(f"Enemy: {enemy} at {world.get_component(enemy, Position)}")
    print()

    # Set up pipeline
    pipeline = setup_pipeline()

    # Example 1: Successful move
    print("=== Example 1: Move within range ===")
    action = Action('move', {'entity': player, 'target': Position(2, 0)})
    result = pipeline.execute(action, world)

    if result.success:
        print(f"✓ Move successful")
        print(f"  Player now at: {world.get_component(player, Position)}")
        print(f"  Events: {result.events}")
    else:
        print(f"✗ Move failed: {result.cancel_reason or result.error}")
    print()

    # Example 2: Move out of range (should be cancelled)
    print("=== Example 2: Move out of range ===")
    action = Action('move', {'entity': player, 'target': Position(10, 10)})
    result = pipeline.execute(action, world)

    if result.success:
        print(f"✓ Move successful")
    else:
        print(f"✗ Move cancelled: {result.cancel_reason or result.error}")
    print()

    # Example 3: Move closer to enemy
    print("=== Example 3: Move closer to enemy ===")
    action = Action('move', {'entity': player, 'target': Position(4, 0)})
    result = pipeline.execute(action, world)

    if result.success:
        print(f"✓ Move successful")
        print(f"  Player now at: {world.get_component(player, Position)}")
    print()

    # Example 4: Attack enemy (adjacent)
    print("=== Example 4: Attack enemy ===")
    action = Action('attack', {'attacker': player, 'target': enemy})
    result = pipeline.execute(action, world)

    if result.success:
        print(f"✓ Attack successful")
        enemy_health = world.get_component(enemy, Health)
        print(f"  Enemy health: {enemy_health.current}/{enemy_health.maximum}")
        print(f"  Events: {result.events}")
    else:
        print(f"✗ Attack failed: {result.cancel_reason or result.error}")
    print()

    # Example 5: Attack again to kill enemy
    print("=== Example 5: Attack enemy again ===")
    action = Action('attack', {'attacker': player, 'target': enemy})
    result = pipeline.execute(action, world)

    if result.success:
        print(f"✓ Attack successful")
        if world.entity_exists(enemy):
            enemy_health = world.get_component(enemy, Health)
            print(f"  Enemy health: {enemy_health.current}/{enemy_health.maximum}")
        else:
            print(f"  Enemy destroyed!")
        print(f"  Events: {result.events}")
    print()

    # Example 6: Attack non-existent enemy (should fail)
    print("=== Example 6: Attack non-existent enemy ===")
    action = Action('attack', {'attacker': player, 'target': enemy})
    result = pipeline.execute(action, world)

    if result.success:
        print(f"✓ Attack successful")
    else:
        print(f"✗ Attack failed: {result.cancel_reason or result.error}")
    print()

    print("=== Example Complete ===")


if __name__ == '__main__':
    main()
