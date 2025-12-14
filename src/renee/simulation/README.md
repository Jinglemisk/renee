# Renee Simulation Engine

The Simulation Engine enables AI-assisted balance testing and impact analysis for Renee games.

## Overview

The simulation package provides tools for:

- **Running scenarios** multiple times with statistical analysis
- **Comparing configurations** to see the impact of changes
- **Sweeping parameters** to explore the design space
- **Analyzing impact** of proposed changes before making them
- **Validating changes** against design intents

## Key Components

### Simulator

Runs scenarios multiple times with different random seeds and collects statistics.

```python
from renee.simulation import Simulator, Scenario
from renee.ecs.world import World

def create_world() -> World:
    return World()

simulator = Simulator(create_world)
result = simulator.run_scenario(scenario, runs=100, seed=42)

print(f"Success rate: {result.success_rate():.1f}%")
print(f"Average turns: {result.metrics['turns'].mean:.1f}")
```

### Scenario

Defines test conditions, actions, and success criteria.

```python
from renee.simulation import Scenario
from renee.actions.action import Action

def setup_combat(world: World) -> None:
    # Create entities and components
    player = world.create_entity()
    world.add_component(player, Health(current=100, max=100))
    # ... more setup

scenario = Scenario(
    name="basic_combat",
    description="Player defeats single enemy",
    setup=setup_combat,
    actions=[
        Action(name="attack", params={"attacker": 0, "target": 1}),
    ],
    success_condition=lambda w: check_victory(w),
    metrics=["damage_dealt", "turns_to_victory"],
    max_turns=10
)
```

### StatisticalSummary

Provides statistical analysis of collected values.

```python
from renee.simulation import StatisticalSummary

values = [10, 20, 30, 40, 50]
summary = StatisticalSummary.from_values(values)

print(f"Mean: {summary.mean}")
print(f"Std Dev: {summary.std_dev}")
print(f"Median: {summary.median}")
print(f"Range: [{summary.min_val}, {summary.max_val}]")
```

### ComparisonResult

Compares two distributions statistically.

```python
from renee.simulation import compare_distributions

baseline = [100, 105, 95, 100, 110]
modified = [120, 125, 115, 120, 130]

result = compare_distributions(baseline, modified)

print(f"Difference: {result.difference:.1f}%")
print(f"Significant: {result.significant}")
print(f"P-value: {result.p_value:.4f}")
```

### ImpactAnalyzer

Analyzes the impact of proposed changes.

```python
from renee.simulation import ImpactAnalyzer

analyzer = ImpactAnalyzer(schema_registry, rule_engine, world)

change = {
    "type": "modify_component",
    "target": "Health",
    "field": "max",
    "old_value": 100,
    "new_value": 150
}

report = analyzer.analyze_change(change)

print(f"Risk level: {report.risk_level}")
print(f"Affected rules: {report.affected_rules}")
print(f"Intent violations: {report.intent_violations}")
print(f"Suggestions: {report.suggestions}")
```

## Common Use Cases

### Balance Testing

Run a scenario many times to understand expected behavior:

```python
simulator = Simulator(create_world)
result = simulator.run_scenario(combat_scenario, runs=100)

print(f"Win rate: {result.success_rate():.1f}%")
if result.metrics['turns'].mean > 10:
    print("Warning: Combat takes too long on average")
```

### Comparing Configurations

Compare baseline vs modified to see impact:

```python
baseline_config = {"enemy_damage": 10}
modified_config = {"enemy_damage": 15}

comparison = simulator.compare(
    scenario,
    baseline_config,
    modified_config,
    runs=100
)

for metric, result in comparison.items():
    if result.significant:
        print(f"{metric}: {result.difference:.1f}% change (significant)")
```

### Parameter Sweeping

Explore different parameter values:

```python
result = simulator.sweep_parameter(
    scenario,
    "enemy_health",
    [50, 75, 100, 125, 150],
    runs_per_value=50
)

for val, sim_result in zip(result.parameter_values, result.results):
    print(f"Health {val}: {sim_result.success_rate():.1f}% success")
```

### Impact Analysis

Analyze changes before making them:

```python
analyzer = ImpactAnalyzer(schema_registry, rule_engine, world)

change = {
    "type": "modify_component",
    "target": "Damage",
    "field": "base",
    "old_value": 10,
    "new_value": 20
}

report = analyzer.analyze_change(change)

if report.risk_level == 'high':
    print("Warning: High-risk change detected!")
    print("Affected rules:", report.affected_rules)
    print("Suggestions:", report.suggestions)
```

## Loading Scenarios from YAML

Scenarios can be defined in YAML files:

```yaml
name: "basic_combat"
description: "Player defeats single enemy"
max_turns: 10
tags: ["combat", "basic"]
metrics:
  - "damage_dealt"
  - "turns_to_victory"
setup:
  module: "my_game.scenarios"
  function: "setup_combat"
actions:
  module: "my_game.scenarios"
  function: "get_combat_actions"
success_condition:
  module: "my_game.scenarios"
  function: "check_victory"
```

Load it with:

```python
scenario = Scenario.from_yaml("scenarios/basic_combat.yaml")
```

## JSON Output

All results support JSON export for AI consumption:

```python
# Simulation results
json_str = result.to_json(indent=2)

# Impact reports
json_str = report.to_json(indent=2)

# Statistical summaries
summary_dict = summary.to_dict()
```

## Design Philosophy

The Simulation Engine is designed for AI agents:

1. **Text-first**: All configuration is in YAML or Python, no binary formats
2. **Introspectable**: Query schemas, state, and results at runtime
3. **Statistical**: Provides rigorous statistical analysis, not just averages
4. **Intent-aware**: Validates changes against stated design goals
5. **JSON-friendly**: All output can be exported as JSON

## Examples

See `examples/simulation_demo.py` for a complete working example.

## Statistical Notes

- Statistical comparisons use a two-sample t-test
- Significance threshold is p < 0.05
- Standard deviation uses (n-1) for sample variance
- Percentiles use linear interpolation

For production use with critical balance decisions, consider using `scipy.stats` for more accurate statistical analysis.

## Future Enhancements

Potential improvements for future versions:

- Integration with action pipeline for automatic action execution
- Event-based metric collection from event bus
- Parallel simulation execution for faster results
- Visualization of sweep results and distributions
- Machine learning for automated balance tuning
- Intent validation using LLMs for semantic checking
