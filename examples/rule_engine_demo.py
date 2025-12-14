"""Rule Engine Demo for Renee Framework.

This example demonstrates how to use the Rule Engine to implement
game logic using Python decorators.

The example shows:
- Creating a RuleEngine
- Defining rules with decorators
- Pre-rules for validation and modification
- Post-rules for side effects
- Conditional rules
- Priority ordering
- Integration with ECS World
"""

from dataclasses import dataclass

from renee.ecs.world import World
from renee.rules import (
    Action,
    ActionContext,
    RuleEngine,
    post_rule,
    pre_rule,
    set_global_engine,
)
from renee.types import EntityId, Position


# Define some game components
@dataclass
class Health:
    """Health component."""

    current: int
    max: int


@dataclass
class Armor:
    """Armor component that reduces incoming damage."""

    value: int


@dataclass
class Stunned:
    """Status effect that prevents actions."""

    duration: int


@dataclass
class Poisoned:
    """Status effect that applies damage over time."""

    damage: int
    duration: int


@dataclass
class PoisonWeapon:
    """Component for weapons that apply poison."""

    poison_damage: int
    poison_duration: int


def main():
    """Run the rule engine demo."""
    print("=" * 60)
    print("Renee Rule Engine Demo")
    print("=" * 60)
    print()

    # Create the rule engine and set it as global
    engine = RuleEngine()
    set_global_engine(engine)

    # Create a world with some entities
    world = World()

    # Create player entity
    player = world.create_entity()
    world.add_component(player, Position(x=0, y=0))
    world.add_component(player, Health(current=100, max=100))
    world.add_component(player, PoisonWeapon(poison_damage=5, poison_duration=3))

    # Create enemy entity
    enemy = world.create_entity()
    world.add_component(enemy, Position(x=1, y=0))
    world.add_component(enemy, Health(current=50, max=50))
    world.add_component(enemy, Armor(value=10))

    print(f"Created player entity: {player}")
    print(f"Created enemy entity: {enemy}")
    print()

    # Define rules using decorators
    print("Defining game rules...")
    print()

    @pre_rule(action="move", priority=10, intent="Prevent movement if stunned")
    def check_stunned(ctx: ActionContext) -> None:
        """Prevent stunned entities from moving."""
        entity = ctx.get_param("entity")
        if ctx.world.has_component(entity, Stunned):
            ctx.cancel("Entity is stunned and cannot move")
            print(f"  [RULE] check_stunned: Entity {entity} is stunned!")

    @pre_rule(action="attack", priority=5, intent="Validate attack range")
    def check_attack_range(ctx: ActionContext) -> None:
        """Ensure attacker is within range of target."""
        attacker = ctx.get_param("attacker")
        target = ctx.get_param("target")

        attacker_pos = ctx.world.get_component(attacker, Position)
        target_pos = ctx.world.get_component(target, Position)

        distance = attacker_pos.manhattan_distance(target_pos)
        max_range = ctx.get_param("range", 1)

        if distance > max_range:
            ctx.cancel(f"Target out of range (distance: {distance}, max: {max_range})")
            print(f"  [RULE] check_attack_range: Attack cancelled - out of range!")
        else:
            print(f"  [RULE] check_attack_range: Range OK (distance: {distance})")

    @pre_rule(action="attack", priority=10, intent="Apply armor reduction to damage")
    def apply_armor(ctx: ActionContext) -> None:
        """Reduce damage based on target's armor."""
        target = ctx.get_param("target")
        damage = ctx.get_param("damage", 0)

        if ctx.world.has_component(target, Armor):
            armor = ctx.world.get_component(target, Armor)
            new_damage = max(0, damage - armor.value)
            ctx.modify(damage=new_damage)
            print(
                f"  [RULE] apply_armor: Damage reduced from {damage} to {new_damage} (armor: {armor.value})"
            )
        else:
            print(f"  [RULE] apply_armor: No armor, damage unchanged ({damage})")

    @pre_rule(action="attack", priority=15, intent="Apply critical hit multiplier")
    def apply_critical(ctx: ActionContext) -> None:
        """Double damage on critical hits."""
        is_critical = ctx.get_param("critical", False)
        if is_critical:
            damage = ctx.get_param("damage", 0)
            ctx.modify(damage=damage * 2)
            print(f"  [RULE] apply_critical: CRITICAL HIT! Damage doubled to {damage * 2}")

    @post_rule(action="attack", priority=10, intent="Apply poison from weapon")
    def apply_poison_weapon(ctx: ActionContext) -> None:
        """Apply poison status if attacker has poison weapon."""
        attacker = ctx.get_param("attacker")
        target = ctx.get_param("target")

        if ctx.world.has_component(attacker, PoisonWeapon):
            poison_weapon = ctx.world.get_component(attacker, PoisonWeapon)

            # Add poison component to target
            if ctx.world.has_component(target, Poisoned):
                # Refresh existing poison
                existing = ctx.world.get_component(target, Poisoned)
                ctx.world.add_component(
                    target,
                    Poisoned(
                        damage=max(existing.damage, poison_weapon.poison_damage),
                        duration=poison_weapon.poison_duration,
                    ),
                )
                print(f"  [RULE] apply_poison_weapon: Refreshed poison on entity {target}")
            else:
                # Apply new poison
                ctx.world.add_component(
                    target,
                    Poisoned(
                        damage=poison_weapon.poison_damage,
                        duration=poison_weapon.poison_duration,
                    ),
                )
                print(
                    f"  [RULE] apply_poison_weapon: Applied poison to entity {target} ({poison_weapon.poison_damage} damage)"
                )

    @post_rule(action="attack", priority=20, intent="Apply damage to target health")
    def apply_damage(ctx: ActionContext) -> None:
        """Reduce target's health by the final damage amount."""
        target = ctx.get_param("target")
        damage = ctx.get_param("damage", 0)

        if ctx.world.has_component(target, Health):
            health = ctx.world.get_component(target, Health)
            new_health = max(0, health.current - damage)
            ctx.world.add_component(target, Health(current=new_health, max=health.max))
            print(
                f"  [RULE] apply_damage: Entity {target} took {damage} damage ({health.current} -> {new_health} HP)"
            )

    @post_rule(action="*", priority=100, intent="Log all actions")
    def log_action(ctx: ActionContext) -> None:
        """Log all completed actions."""
        print(f"  [RULE] log_action: Action '{ctx.action.name}' completed")

    # Show registered rules
    print(f"Registered {engine.rule_count()} rules")
    print()

    summary = engine.get_summary()
    print("Rule Summary:")
    print(f"  Total rules: {summary['total']}")
    print(f"  Pre-rules: {summary['pre_rules']}")
    print(f"  Post-rules: {summary['post_rules']}")
    print(f"  Action types covered: {', '.join(summary['action_types_covered'])}")
    print()

    # Scenario 1: Normal attack
    print("-" * 60)
    print("Scenario 1: Normal Attack")
    print("-" * 60)
    print()

    action = Action(
        name="attack",
        params={
            "attacker": player,
            "target": enemy,
            "damage": 20,
            "range": 1,
            "critical": False,
        },
    )
    ctx = ActionContext(action=action, world=world)

    print("Executing attack action...")
    print()
    print("Pre-rules:")
    engine.apply_rules(ctx, "pre")
    print()

    if not ctx.is_cancelled():
        print("Action execution phase (not cancelled)")
        print()
        print("Post-rules:")
        engine.apply_rules(ctx, "post")
        print()

        # Show final state
        enemy_health = world.get_component(enemy, Health)
        enemy_poisoned = world.get_component_or_none(enemy, Poisoned)
        print(f"Final state:")
        print(f"  Enemy health: {enemy_health.current}/{enemy_health.max}")
        if enemy_poisoned:
            print(
                f"  Enemy poisoned: {enemy_poisoned.damage} damage for {enemy_poisoned.duration} turns"
            )
    else:
        print(f"Action cancelled: {ctx.cancel_reason}")

    print()

    # Scenario 2: Critical hit
    print("-" * 60)
    print("Scenario 2: Critical Hit Attack")
    print("-" * 60)
    print()

    # Reset enemy health
    world.add_component(enemy, Health(current=50, max=50))

    action = Action(
        name="attack",
        params={
            "attacker": player,
            "target": enemy,
            "damage": 15,
            "range": 1,
            "critical": True,  # Critical hit!
        },
    )
    ctx = ActionContext(action=action, world=world)

    print("Executing critical attack...")
    print()
    print("Pre-rules:")
    engine.apply_rules(ctx, "pre")
    print()

    if not ctx.is_cancelled():
        print("Action execution phase (not cancelled)")
        print()
        print("Post-rules:")
        engine.apply_rules(ctx, "post")
        print()

        enemy_health = world.get_component(enemy, Health)
        print(f"Final state:")
        print(f"  Enemy health: {enemy_health.current}/{enemy_health.max}")

    print()

    # Scenario 3: Out of range attack (cancelled)
    print("-" * 60)
    print("Scenario 3: Out of Range Attack (Should Cancel)")
    print("-" * 60)
    print()

    # Move enemy far away
    world.add_component(enemy, Position(x=10, y=10))

    action = Action(
        name="attack",
        params={
            "attacker": player,
            "target": enemy,
            "damage": 20,
            "range": 1,
        },
    )
    ctx = ActionContext(action=action, world=world)

    print("Executing out-of-range attack...")
    print()
    print("Pre-rules:")
    engine.apply_rules(ctx, "pre")
    print()

    if ctx.is_cancelled():
        print(f"Action cancelled: {ctx.cancel_reason}")
    else:
        print("Action execution phase (not cancelled)")
        print("Post-rules:")
        engine.apply_rules(ctx, "post")

    print()

    # Scenario 4: Stunned entity trying to move (cancelled)
    print("-" * 60)
    print("Scenario 4: Stunned Entity Movement (Should Cancel)")
    print("-" * 60)
    print()

    # Stun the player
    world.add_component(player, Stunned(duration=2))

    action = Action(name="move", params={"entity": player, "target": Position(x=1, y=1)})
    ctx = ActionContext(action=action, world=world)

    print("Executing move action on stunned entity...")
    print()
    print("Pre-rules:")
    engine.apply_rules(ctx, "pre")
    print()

    if ctx.is_cancelled():
        print(f"Action cancelled: {ctx.cancel_reason}")
    else:
        print("Action execution phase (not cancelled)")

    print()

    # Show JSON output for AI introspection
    print("-" * 60)
    print("JSON Export (for AI agents)")
    print("-" * 60)
    print()
    print(engine.to_json(indent=2))


if __name__ == "__main__":
    main()
