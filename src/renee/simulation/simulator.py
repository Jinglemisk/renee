"""Simulation engine for AI-assisted balance testing.

The Simulator runs scenarios multiple times with different random seeds,
collecting statistics and enabling comparison of baseline vs modified configurations.
"""

from __future__ import annotations

import copy
import json
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Any, TYPE_CHECKING

from renee.simulation.scenario import Scenario, ScenarioResult
from renee.simulation.statistics import (
    StatisticalSummary,
    ComparisonResult,
    compare_distributions,
)

if TYPE_CHECKING:
    from renee.ecs.world import World
    from renee.actions.action import Action


@dataclass
class SimulationResult:
    """Result of running a scenario multiple times.

    Aggregates statistics across multiple runs to provide insights
    into expected behavior and variability.

    Attributes:
        scenario: Name of the scenario
        runs: Total number of runs executed
        successes: Number of successful runs
        failures: Number of failed runs
        timeouts: Number of runs that exceeded max_turns
        metrics: Statistical summaries for each metric
        events: Aggregated event data (optional)
        duration: Total simulation time in seconds

    Example:
        result = simulator.run_scenario(scenario, runs=100)
        print(f"Success rate: {result.successes / result.runs * 100:.1f}%")
        print(f"Avg damage: {result.metrics['damage_dealt'].mean:.1f}")
    """

    scenario: str
    runs: int
    successes: int
    failures: int
    timeouts: int
    metrics: dict[str, StatisticalSummary]
    events: list[dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0

    def success_rate(self) -> float:
        """Calculate success rate as a percentage.

        Returns:
            Success rate (0-100)
        """
        if self.runs == 0:
            return 0.0
        return (self.successes / self.runs) * 100

    def timeout_rate(self) -> float:
        """Calculate timeout rate as a percentage.

        Returns:
            Timeout rate (0-100)
        """
        if self.runs == 0:
            return 0.0
        return (self.timeouts / self.runs) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "scenario": self.scenario,
            "runs": self.runs,
            "successes": self.successes,
            "failures": self.failures,
            "timeouts": self.timeouts,
            "success_rate": self.success_rate(),
            "timeout_rate": self.timeout_rate(),
            "metrics": {
                name: summary.to_dict()
                for name, summary in self.metrics.items()
            },
            "duration_seconds": self.duration,
        }

    def to_json(self, indent: int | None = 2) -> str:
        """Export as JSON string.

        Args:
            indent: JSON indentation level (None for compact)

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"SimulationResult('{self.scenario}': {self.runs} runs, "
            f"{self.success_rate():.1f}% success, "
            f"{len(self.metrics)} metrics, "
            f"{self.duration:.2f}s)"
        )


@dataclass
class SweepResult:
    """Result of sweeping a parameter across multiple values.

    Used to explore how changing a parameter affects outcomes.

    Attributes:
        scenario: Name of the scenario
        parameter_name: Name of the parameter that was swept
        results: Simulation results for each parameter value
        parameter_values: List of parameter values tested

    Example:
        result = simulator.sweep_parameter(
            scenario,
            "enemy_health",
            [50, 75, 100, 125, 150],
            runs_per_value=50
        )
        for val, sim_result in zip(result.parameter_values, result.results):
            print(f"Health {val}: {sim_result.success_rate():.1f}% success")
    """

    scenario: str
    parameter_name: str
    results: list[SimulationResult]
    parameter_values: list[Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "scenario": self.scenario,
            "parameter_name": self.parameter_name,
            "parameter_values": self.parameter_values,
            "results": [r.to_dict() for r in self.results],
        }

    def to_json(self, indent: int | None = 2) -> str:
        """Export as JSON string.

        Args:
            indent: JSON indentation level (None for compact)

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)


class Simulator:
    """Simulation engine for running scenarios with statistics.

    The Simulator executes scenarios multiple times with different random seeds,
    collecting metrics and providing statistical analysis of outcomes.

    Example:
        def create_world() -> World:
            return World()

        simulator = Simulator(create_world)
        result = simulator.run_scenario(scenario, runs=100, seed=42)
        print(f"Success rate: {result.success_rate():.1f}%")
    """

    def __init__(self, world_factory: Callable[[], World]) -> None:
        """Initialize the simulator.

        Args:
            world_factory: Function that creates fresh World instances.
                          Called once per simulation run.

        Example:
            def create_game_world() -> World:
                world = World()
                # Register components, rules, etc.
                return world

            simulator = Simulator(create_game_world)
        """
        self.world_factory = world_factory
        self._rng = random.Random()
        self._seed: int | None = None

    def set_seed(self, seed: int) -> None:
        """Set the RNG seed for reproducible simulations.

        Args:
            seed: Random seed value

        Example:
            simulator.set_seed(42)
            result = simulator.run_scenario(scenario, runs=100)
            # Results will be identical on repeated runs
        """
        self._seed = seed
        self._rng.seed(seed)

    def run_scenario(
        self,
        scenario: Scenario,
        runs: int = 100,
        seed: int | None = None
    ) -> SimulationResult:
        """Run a scenario multiple times and collect statistics.

        Args:
            scenario: The scenario to run
            runs: Number of times to run the scenario
            seed: Optional random seed (overrides set_seed)

        Returns:
            SimulationResult with aggregated statistics

        Example:
            result = simulator.run_scenario(combat_scenario, runs=100)
            print(f"Average turns: {result.metrics['turns'].mean:.1f}")
        """
        if seed is not None:
            self.set_seed(seed)

        start_time = time.time()

        successes = 0
        failures = 0
        timeouts = 0

        # Collect metric values across all runs
        metric_values: dict[str, list[float]] = {
            metric: [] for metric in scenario.metrics
        }

        for run_idx in range(runs):
            # Create fresh world for this run
            world = self.world_factory()

            # Set up random seed for this run
            run_seed = self._rng.randint(0, 2**31 - 1) if self._seed is not None else None
            if run_seed is not None:
                random.seed(run_seed)

            # Run the scenario
            result = self._run_single(scenario, world)

            # Update counters
            if result.success:
                successes += 1
            elif result.timeout:
                timeouts += 1
            else:
                failures += 1

            # Collect metrics
            for metric_name in scenario.metrics:
                if metric_name in result.metrics:
                    metric_values[metric_name].append(result.metrics[metric_name])

        # Calculate statistical summaries
        metrics = {}
        for metric_name, values in metric_values.items():
            if values:
                metrics[metric_name] = StatisticalSummary.from_values(values)

        duration = time.time() - start_time

        return SimulationResult(
            scenario=scenario.name,
            runs=runs,
            successes=successes,
            failures=failures,
            timeouts=timeouts,
            metrics=metrics,
            duration=duration,
        )

    def compare(
        self,
        scenario: Scenario,
        baseline: dict[str, Any],
        modified: dict[str, Any],
        runs: int = 100
    ) -> dict[str, ComparisonResult]:
        """Compare baseline vs modified configuration.

        Runs the scenario with two different configurations and
        statistically compares the results.

        Args:
            scenario: The scenario to run
            baseline: Baseline configuration parameters
            modified: Modified configuration parameters
            runs: Number of runs for each configuration

        Returns:
            Dictionary mapping metric names to ComparisonResults

        Example:
            baseline = {"enemy_damage": 10}
            modified = {"enemy_damage": 15}
            comparison = simulator.compare(
                scenario,
                baseline,
                modified,
                runs=100
            )
            for metric, result in comparison.items():
                print(f"{metric}: {result}")
        """
        # This is a simplified implementation
        # In a full implementation, you would:
        # 1. Apply baseline config to world before setup
        # 2. Run scenario with baseline
        # 3. Apply modified config to world before setup
        # 4. Run scenario with modified
        # 5. Compare metric distributions

        # For now, we'll run the scenario twice and compare
        # (assuming config changes are applied in scenario setup)
        baseline_result = self.run_scenario(scenario, runs=runs)
        modified_result = self.run_scenario(scenario, runs=runs)

        # Compare each metric
        comparisons = {}
        for metric_name in scenario.metrics:
            if metric_name in baseline_result.metrics and metric_name in modified_result.metrics:
                baseline_summary = baseline_result.metrics[metric_name]
                modified_summary = modified_result.metrics[metric_name]

                # We need raw values for comparison, but we only have summaries
                # Generate approximate distributions from summaries for demonstration
                baseline_values = self._approximate_distribution(baseline_summary)
                modified_values = self._approximate_distribution(modified_summary)

                comparison = compare_distributions(baseline_values, modified_values)
                comparisons[metric_name] = comparison

        return comparisons

    def sweep_parameter(
        self,
        scenario: Scenario,
        param_name: str,
        values: list[Any],
        runs_per_value: int = 50
    ) -> SweepResult:
        """Test multiple values of a parameter.

        Runs the scenario with different parameter values to explore
        the impact of that parameter.

        Args:
            scenario: The scenario to run
            param_name: Name of the parameter to sweep
            values: List of parameter values to test
            runs_per_value: Number of runs for each value

        Returns:
            SweepResult with results for each parameter value

        Example:
            result = simulator.sweep_parameter(
                scenario,
                "enemy_health",
                [50, 100, 150, 200],
                runs_per_value=50
            )
            # Analyze how enemy health affects success rate
        """
        results = []

        for value in values:
            # Note: In a full implementation, you would modify the scenario
            # to use this parameter value. For now, we just run as-is.
            # The scenario setup function should read from a shared config.

            result = self.run_scenario(scenario, runs=runs_per_value)
            results.append(result)

        return SweepResult(
            scenario=scenario.name,
            parameter_name=param_name,
            results=results,
            parameter_values=values,
        )

    def _run_single(self, scenario: Scenario, world: World) -> ScenarioResult:
        """Run a scenario once.

        Args:
            scenario: The scenario to run
            world: Pre-created world instance

        Returns:
            ScenarioResult for this run
        """
        try:
            # Set up the scenario
            scenario.setup(world)

            # Execute actions
            turns = 0
            for turn_idx in range(scenario.max_turns):
                turns = turn_idx + 1

                # Check success condition
                if scenario.success_condition(world):
                    # Success!
                    metrics = self._collect_metrics(scenario, world, turns)
                    return ScenarioResult(
                        scenario_name=scenario.name,
                        success=True,
                        timeout=False,
                        turns_elapsed=turns,
                        metrics=metrics,
                    )

                # Execute actions for this turn
                if turn_idx < len(scenario.actions):
                    action = scenario.actions[turn_idx]
                    # In a full implementation, you would execute the action
                    # through the action pipeline here
                    # For now, we'll just acknowledge it
                    pass

            # Timeout - max turns exceeded
            metrics = self._collect_metrics(scenario, world, turns)
            return ScenarioResult(
                scenario_name=scenario.name,
                success=False,
                timeout=True,
                turns_elapsed=turns,
                metrics=metrics,
            )

        except Exception as e:
            # Error during execution
            return ScenarioResult(
                scenario_name=scenario.name,
                success=False,
                timeout=False,
                turns_elapsed=0,
                metrics={},
                error=str(e),
            )

    def _collect_metrics(
        self,
        scenario: Scenario,
        world: World,
        turns: int
    ) -> dict[str, float]:
        """Collect metric values from the world state.

        Args:
            scenario: The scenario being run
            world: Current world state
            turns: Number of turns elapsed

        Returns:
            Dictionary mapping metric names to values

        Note:
            This is a simplified implementation. In a full system,
            metrics would be collected from events, world state,
            or custom metric collectors.
        """
        metrics = {}

        # Add default metrics
        metrics["turns"] = float(turns)
        metrics["entities"] = float(world.entity_count())

        # Scenario-specific metrics would be collected here
        # based on the metric names in scenario.metrics

        return metrics

    def _approximate_distribution(self, summary: StatisticalSummary) -> list[float]:
        """Approximate a distribution from statistical summary.

        This generates synthetic data that roughly matches the summary statistics.
        Used when we need raw values but only have summary statistics.

        Args:
            summary: Statistical summary

        Returns:
            List of approximately distributed values

        Note:
            This is an approximation and should not be used for critical
            statistical analysis. Ideally, keep raw values during simulation.
        """
        # Generate values using normal distribution approximation
        values = []
        for _ in range(summary.count):
            # Generate value from normal distribution
            value = random.gauss(summary.mean, summary.std_dev)
            # Clamp to observed min/max
            value = max(summary.min_val, min(summary.max_val, value))
            values.append(value)

        return values
