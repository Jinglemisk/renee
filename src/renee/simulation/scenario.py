"""Scenario definition for simulation testing.

Scenarios define test conditions, actions to execute, and success criteria
for simulation-based balance testing and validation.
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from renee.ecs.world import World
    from renee.actions.action import Action


@dataclass
class Scenario:
    """Definition of a test scenario for simulation.

    A scenario describes:
    - How to set up the initial game state
    - What actions to execute
    - How to determine success or failure
    - What metrics to measure

    Scenarios can be defined in code or loaded from YAML files.

    Attributes:
        name: Unique scenario identifier
        description: Human-readable description of what this tests
        setup: Function that configures the initial world state
        actions: List of actions to execute in sequence
        success_condition: Function that returns True if scenario succeeded
        metrics: List of metric names to collect during execution
        max_turns: Maximum number of turns before timeout
        tags: Optional tags for organizing scenarios

    Example:
        def setup_combat(world: World) -> None:
            player = world.create_entity()
            world.add_component(player, Health(current=100, max=100))
            enemy = world.create_entity()
            world.add_component(enemy, Health(current=50, max=50))

        scenario = Scenario(
            name="basic_combat",
            description="Player defeats single enemy",
            setup=setup_combat,
            actions=[
                Action(name="attack", params={"attacker": 0, "target": 1}),
            ],
            success_condition=lambda w: not w.entity_exists(1),
            metrics=["damage_dealt", "turns_to_victory"],
            max_turns=10
        )
    """

    name: str
    description: str
    setup: Callable[[World], None]
    actions: list[Action]
    success_condition: Callable[[World], bool]
    metrics: list[str]
    max_turns: int = 100
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate scenario configuration."""
        if not self.name:
            raise ValueError("Scenario name cannot be empty")

        if not callable(self.setup):
            raise ValueError("Scenario setup must be callable")

        if not callable(self.success_condition):
            raise ValueError("Scenario success_condition must be callable")

        if self.max_turns < 1:
            raise ValueError(f"Scenario max_turns must be positive, got {self.max_turns}")

    @classmethod
    def from_yaml(cls, path: str | Path) -> Scenario:
        """Load scenario from YAML file.

        The YAML file should have the following structure:

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

        Args:
            path: Path to the YAML file

        Returns:
            Scenario instance

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If YAML is invalid or missing required fields

        Note:
            This method requires that setup, actions, and success_condition
            functions are defined in importable Python modules. The functions
            are dynamically imported from the specified module and function names.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Scenario file not found: {path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML format in {path}: expected dictionary")

        # Extract required fields
        name = data.get("name")
        if not name:
            raise ValueError(f"Scenario in {path} missing 'name' field")

        description = data.get("description", "")
        max_turns = data.get("max_turns", 100)
        metrics = data.get("metrics", [])
        tags = data.get("tags", [])

        # Load functions from modules
        setup_func = cls._load_function(data.get("setup"), "setup", path)
        actions_func = cls._load_function(data.get("actions"), "actions", path)
        success_func = cls._load_function(data.get("success_condition"), "success_condition", path)

        # Get actions (might be a list or a function that returns a list)
        if callable(actions_func):
            actions = actions_func()
        else:
            actions = actions_func if isinstance(actions_func, list) else []

        return cls(
            name=name,
            description=description,
            setup=setup_func,
            actions=actions,
            success_condition=success_func,
            metrics=metrics,
            max_turns=max_turns,
            tags=tags,
        )

    @staticmethod
    def _load_function(config: dict | None, field_name: str, yaml_path: Path) -> Callable:
        """Load a function from module specification.

        Args:
            config: Dictionary with 'module' and 'function' keys
            field_name: Name of the field being loaded (for error messages)
            yaml_path: Path to YAML file (for error messages)

        Returns:
            The loaded function

        Raises:
            ValueError: If config is invalid or function cannot be loaded
        """
        if not config:
            raise ValueError(f"Scenario in {yaml_path} missing '{field_name}' field")

        if not isinstance(config, dict):
            raise ValueError(
                f"Scenario in {yaml_path} field '{field_name}' must be a dict "
                f"with 'module' and 'function' keys"
            )

        module_name = config.get("module")
        function_name = config.get("function")

        if not module_name or not function_name:
            raise ValueError(
                f"Scenario in {yaml_path} field '{field_name}' must specify "
                f"both 'module' and 'function'"
            )

        try:
            import importlib
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
        except ImportError as e:
            raise ValueError(
                f"Cannot import module '{module_name}' for scenario '{field_name}': {e}"
            ) from e
        except AttributeError as e:
            raise ValueError(
                f"Module '{module_name}' has no function '{function_name}' "
                f"for scenario '{field_name}': {e}"
            ) from e

        if not callable(func):
            raise ValueError(
                f"Loaded '{field_name}' from {module_name}.{function_name} "
                f"is not callable"
            )

        return func

    def to_dict(self) -> dict[str, Any]:
        """Convert scenario to dictionary for JSON serialization.

        Note: Functions (setup, success_condition) cannot be serialized,
        so only metadata is included.

        Returns:
            Dictionary representation of scenario metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "max_turns": self.max_turns,
            "metrics": self.metrics,
            "tags": self.tags,
            "action_count": len(self.actions),
        }

    def validate(self) -> tuple[bool, list[str]]:
        """Validate scenario configuration.

        Checks that all required components are properly configured.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not self.name:
            errors.append("Scenario name is empty")

        if not callable(self.setup):
            errors.append("Setup is not callable")

        if not callable(self.success_condition):
            errors.append("Success condition is not callable")

        if self.max_turns < 1:
            errors.append(f"Invalid max_turns: {self.max_turns}")

        if not isinstance(self.metrics, list):
            errors.append("Metrics must be a list")

        if not isinstance(self.actions, list):
            errors.append("Actions must be a list")

        return len(errors) == 0, errors

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Scenario('{self.name}': {self.description}, "
            f"{len(self.actions)} actions, max {self.max_turns} turns)"
        )


@dataclass
class ScenarioResult:
    """Result of running a scenario once.

    Captures the outcome of a single scenario execution.

    Attributes:
        scenario_name: Name of the scenario that was run
        success: Whether the success condition was met
        timeout: Whether the scenario exceeded max_turns
        turns_elapsed: Number of turns executed
        metrics: Dictionary of collected metric values
        error: Error message if execution failed

    Example:
        result = ScenarioResult(
            scenario_name="basic_combat",
            success=True,
            timeout=False,
            turns_elapsed=5,
            metrics={"damage_dealt": 50, "turns_to_victory": 5},
            error=None
        )
    """

    scenario_name: str
    success: bool
    timeout: bool
    turns_elapsed: int
    metrics: dict[str, float]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "scenario": self.scenario_name,
            "success": self.success,
            "timeout": self.timeout,
            "turns_elapsed": self.turns_elapsed,
            "metrics": self.metrics,
            "error": self.error,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.error:
            return f"ScenarioResult('{self.scenario_name}': ERROR - {self.error})"

        status = "SUCCESS" if self.success else ("TIMEOUT" if self.timeout else "FAILURE")
        return (
            f"ScenarioResult('{self.scenario_name}': {status}, "
            f"{self.turns_elapsed} turns)"
        )
