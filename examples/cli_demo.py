"""Demo of the Renee CLI and REPL functionality.

This script demonstrates:
1. Creating a world
2. Using the REPL programmatically
3. Executing REPL commands
4. Working with entities and snapshots
"""

from renee.cli.repl import GameREPL
from renee.ecs.world import World


def demo_repl_json_mode():
    """Demonstrate REPL in JSON mode."""
    print("=" * 60)
    print("REPL Demo - JSON Mode")
    print("=" * 60)
    print()

    # Create a world
    world = World()

    # Create some entities
    player = world.create_entity()
    world.add_tag(player, "player")

    enemy1 = world.create_entity()
    world.add_tag(enemy1, "enemy")

    enemy2 = world.create_entity()
    world.add_tag(enemy2, "enemy")

    # Create REPL in JSON mode
    repl = GameREPL(world, json_mode=True)

    # Execute some commands
    print("Command: entities")
    print(repl.execute("entities"))
    print()

    print("Command: entities player")
    print(repl.execute("entities player"))
    print()

    print("Command: entities enemy")
    print(repl.execute("entities enemy"))
    print()

    print(f"Command: entity {player}")
    print(repl.execute(f"entity {player}"))
    print()

    print("Command: state")
    print(repl.execute("state"))
    print()

    print("Command: snapshot")
    snapshot_result = repl.execute("snapshot")
    print(snapshot_result)
    print()

    # Parse snapshot ID from result
    import json
    snapshot_data = json.loads(snapshot_result)
    snapshot_id = snapshot_data["snapshot_id"]

    print(f"Command: destroy {enemy1}")
    print(repl.execute(f"destroy {enemy1}"))
    print()

    print("Command: entities (after destroying one enemy)")
    print(repl.execute("entities"))
    print()

    print(f"Command: restore {snapshot_id}")
    print(repl.execute(f"restore {snapshot_id}"))
    print()

    print("Command: entities (after restore)")
    print(repl.execute("entities"))
    print()


def demo_repl_human_mode():
    """Demonstrate REPL in human-readable mode."""
    print("=" * 60)
    print("REPL Demo - Human-Readable Mode")
    print("=" * 60)
    print()

    # Create a world with some entities
    world = World()

    player = world.create_entity()
    world.add_tag(player, "player")
    world.add_tag(player, "alive")

    npc1 = world.create_entity()
    world.add_tag(npc1, "npc")
    world.add_tag(npc1, "merchant")

    npc2 = world.create_entity()
    world.add_tag(npc2, "npc")
    world.add_tag(npc2, "guard")

    # Create REPL in human-readable mode
    repl = GameREPL(world, json_mode=False)

    # Execute some commands
    commands = [
        "entities",
        f"entity {player}",
        "entities npc",
        "state",
        "help",
    ]

    for cmd in commands:
        print(f">>> {cmd}")
        result = repl.execute(cmd)
        print(result)
        print()


def demo_output_formatter():
    """Demonstrate the OutputFormatter."""
    from renee.cli.output import OutputFormatter

    print("=" * 60)
    print("OutputFormatter Demo")
    print("=" * 60)
    print()

    # JSON mode
    print("JSON Mode:")
    print("-" * 40)
    formatter = OutputFormatter(json_mode=True)

    formatter.success("Entity created", {"id": 42, "type": "player"})
    print()

    formatter.error("Invalid action", "Entity does not exist")
    print()

    formatter.table(
        ["ID", "Type", "HP"],
        [
            [1, "Player", 100],
            [2, "Enemy", 50],
            [3, "NPC", 30],
        ],
    )
    print()

    # Human-readable mode
    print("\nHuman-Readable Mode:")
    print("-" * 40)
    formatter = OutputFormatter(json_mode=False)

    formatter.success("Entity created", {"id": 42, "type": "player"})
    print()

    formatter.info("Current turn", {"turn": 5, "player": "Alice"})
    print()

    formatter.table(
        ["ID", "Type", "HP"],
        [
            [1, "Player", 100],
            [2, "Enemy", 50],
            [3, "NPC", 30],
        ],
    )
    print()

    formatter.list_items(["Position", "Health", "Sprite"], "Available Components")
    print()


if __name__ == "__main__":
    demo_output_formatter()
    print("\n\n")
    demo_repl_json_mode()
    print("\n\n")
    demo_repl_human_mode()
