"""Simulation Engine for AI-assisted balance testing and impact analysis.

The simulation package provides tools for:
- Running scenarios multiple times with statistical analysis
- Comparing baseline vs modified configurations
- Sweeping parameter ranges to explore design space
- Analyzing the impact of proposed changes
- Validating changes against design intents

Key Components:
    Simulator: Runs scenarios with statistical analysis
    Scenario: Defines test conditions and success criteria
    StatisticalSummary: Aggregates statistics from multiple runs
    ComparisonResult: Compares two distributions
    ImpactAnalyzer: Analyzes impact of proposed changes

Example:
    from renee.simulation import Simulator, Scenario
    from renee.ecs.world import World

    def create_world() -> World:
        return World()

    def setup_combat(world: World) -> None:
        # Set up entities, components, etc.
        pass

    scenario = Scenario(
        name="basic_combat",
        description="Test combat balance",
        setup=setup_combat,
        actions=[],
        success_condition=lambda w: True,
        metrics=["damage_dealt", "turns"],
        max_turns=10
    )

    simulator = Simulator(create_world)
    result = simulator.run_scenario(scenario, runs=100)
    print(f"Success rate: {result.success_rate():.1f}%")

    # Impact analysis
    from renee.simulation import ImpactAnalyzer

    analyzer = ImpactAnalyzer(schema_registry, rule_engine, world)
    report = analyzer.analyze_change({
        "type": "modify_component",
        "target": "Health",
        "field": "max",
        "old_value": 100,
        "new_value": 150
    })
    print(f"Risk level: {report.risk_level}")
"""

from renee.simulation.scenario import Scenario, ScenarioResult
from renee.simulation.statistics import (
    StatisticalSummary,
    ComparisonResult,
    compare_distributions,
)
from renee.simulation.simulator import (
    Simulator,
    SimulationResult,
    SweepResult,
)
from renee.simulation.impact import ImpactAnalyzer, ImpactReport

__all__ = [
    # Scenario
    "Scenario",
    "ScenarioResult",
    # Statistics
    "StatisticalSummary",
    "ComparisonResult",
    "compare_distributions",
    # Simulator
    "Simulator",
    "SimulationResult",
    "SweepResult",
    # Impact Analysis
    "ImpactAnalyzer",
    "ImpactReport",
]
