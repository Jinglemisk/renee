"""Demonstration of the Renee Simulation Engine.

This example shows how to:
1. Define a test scenario
2. Run simulations with statistical analysis
3. Compare baseline vs modified configurations
4. Analyze the impact of proposed changes
"""

from dataclasses import dataclass
from renee.ecs.world import World
from renee.types import EntityId
from renee.actions.action import Action
from renee.simulation import (
    Simulator,
    Scenario,
    ImpactAnalyzer,
)
from renee.schema.registry import SchemaRegistry
from renee.rules.engine import RuleEngine


# Define a simple component for this demo
@dataclass
class Health:
    """Health component for entities."""
    current: int
    max: int


@dataclass
class Damage:
    """Damage component for entities."""
    value: int


def create_world() -> World:
    """Factory function to create a fresh world for each simulation run."""
    world = World()
    return world


def setup_basic_combat(world: World) -> None:
    """Set up a basic combat scenario.

    Creates a player and an enemy, both with health.
    """
    # Create player
    player = world.create_entity()
    world.add_component(player, Health(current=100, max=100))
    world.add_component(player, Damage(value=20))
    world.add_tag(player, "player")

    # Create enemy
    enemy = world.create_entity()
    world.add_component(enemy, Health(current=50, max=50))
    world.add_component(enemy, Damage(value=15))
    world.add_tag(enemy, "enemy")


def check_enemy_defeated(world: World) -> bool:
    """Success condition: enemy is defeated.

    Returns True if no entities with 'enemy' tag exist.
    """
    enemies = list(world.query_by_tag("enemy"))
    return len(enemies) == 0


def main():
    """Run the simulation demo."""
    print("=" * 70)
    print("RENEE SIMULATION ENGINE DEMO")
    print("=" * 70)
    print()

    # Create a scenario
    scenario = Scenario(
        name="basic_combat",
        description="Player defeats a single enemy",
        setup=setup_basic_combat,
        actions=[
            # In a real scenario, these would be actual game actions
            # For demo purposes, we're using placeholder actions
            Action(name="attack", params={"attacker": 0, "target": 1}),
        ],
        success_condition=check_enemy_defeated,
        metrics=["damage_dealt", "turns_to_victory"],
        max_turns=10,
        tags=["combat", "basic"]
    )

    print(f"Scenario: {scenario}")
    print()

    # Create simulator
    simulator = Simulator(create_world)

    # Set seed for reproducibility
    simulator.set_seed(42)

    print("Running simulation (100 runs)...")
    result = simulator.run_scenario(scenario, runs=100)

    print()
    print("-" * 70)
    print("SIMULATION RESULTS")
    print("-" * 70)
    print(f"Scenario: {result.scenario}")
    print(f"Total runs: {result.runs}")
    print(f"Successes: {result.successes}")
    print(f"Failures: {result.failures}")
    print(f"Timeouts: {result.timeouts}")
    print(f"Success rate: {result.success_rate():.1f}%")
    print(f"Duration: {result.duration:.2f}s")
    print()

    if result.metrics:
        print("Metrics:")
        for metric_name, summary in result.metrics.items():
            print(f"  {metric_name}:")
            print(f"    Mean: {summary.mean:.2f}")
            print(f"    Std Dev: {summary.std_dev:.2f}")
            print(f"    Range: [{summary.min_val:.2f}, {summary.max_val:.2f}]")
            print(f"    Median: {summary.median:.2f}")
    print()

    # Demonstrate parameter sweep
    print("-" * 70)
    print("PARAMETER SWEEP DEMO")
    print("-" * 70)
    print("Testing different values of enemy health...")

    sweep_result = simulator.sweep_parameter(
        scenario,
        "enemy_health",
        [30, 40, 50, 60, 70],
        runs_per_value=20
    )

    print()
    print(f"Parameter: {sweep_result.parameter_name}")
    for value, sim_result in zip(sweep_result.parameter_values, sweep_result.results):
        print(f"  Value {value}: {sim_result.success_rate():.1f}% success")
    print()

    # Demonstrate impact analysis
    print("-" * 70)
    print("IMPACT ANALYSIS DEMO")
    print("-" * 70)

    # Create necessary components for impact analyzer
    schema_registry = SchemaRegistry()
    rule_engine = RuleEngine()
    world = create_world()

    analyzer = ImpactAnalyzer(schema_registry, rule_engine, world)

    # Analyze a proposed change
    change = {
        "type": "modify_component",
        "target": "Health",
        "field": "max",
        "old_value": 100,
        "new_value": 150
    }

    print(f"Analyzing change: {change}")
    print()

    report = analyzer.analyze_change(change)

    print(report)
    print()
    print(f"Suggestions:")
    for i, suggestion in enumerate(report.suggestions, 1):
        print(f"  {i}. {suggestion}")
    print()

    # Export to JSON
    print("-" * 70)
    print("JSON EXPORT (for AI consumption)")
    print("-" * 70)
    print(result.to_json(indent=2))
    print()

    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
