"""Main CLI entry point for the Renee game framework.

This module provides the primary command-line interface using typer.
All commands support --json output for AI agent parsing.
"""

import sys
from pathlib import Path
from typing import Optional

import typer

from renee.cli.output import OutputFormatter
from renee.cli.repl import GameREPL
from renee.ecs.world import World
from renee.schema.registry import SchemaRegistry

# Global typer app
app = typer.Typer(
    name="renee",
    help="Renee Game Framework CLI - AI-native turn-based game development",
    add_completion=False,
)

# Global state for JSON output flag
_json_output = False
_formatter: Optional[OutputFormatter] = None


def get_formatter() -> OutputFormatter:
    """Get the global output formatter."""
    global _formatter
    if _formatter is None:
        _formatter = OutputFormatter(json_mode=_json_output)
    return _formatter


@app.callback()
def main(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON for machine parsing",
    ),
) -> None:
    """Renee Game Framework CLI.

    An AI-native framework for turn-based games.
    """
    global _json_output, _formatter
    _json_output = json_output
    _formatter = OutputFormatter(json_mode=json_output)


@app.command()
def new(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template to use"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project directory (default: ./name)"),
) -> None:
    """Create a new game project.

    Creates a new Renee game project with the standard directory structure:
    - schemas/ (component, event, action definitions)
    - entities/ (entity templates)
    - systems/ (game logic)
    - rules/ (game rules)
    - scenes/ (levels/maps)
    - assets/ (sprites, sounds, fonts)
    - tests/ (pytest tests)

    Example:
        renee new my-game
        renee new my-game --template=tactics --path=/path/to/project
    """
    formatter = get_formatter()

    try:
        # Determine project path
        if path:
            project_path = Path(path)
        else:
            project_path = Path.cwd() / name

        # Check if directory already exists
        if project_path.exists():
            formatter.error(f"Directory already exists: {project_path}")
            sys.exit(1)

        # Create directory structure
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "schemas").mkdir(exist_ok=True)
        (project_path / "entities").mkdir(exist_ok=True)
        (project_path / "entities" / "_templates").mkdir(exist_ok=True)
        (project_path / "systems").mkdir(exist_ok=True)
        (project_path / "rules").mkdir(exist_ok=True)
        (project_path / "scenes").mkdir(exist_ok=True)
        (project_path / "assets").mkdir(exist_ok=True)
        (project_path / "assets" / "sprites").mkdir(exist_ok=True)
        (project_path / "assets" / "sounds").mkdir(exist_ok=True)
        (project_path / "assets" / "fonts").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)

        # Create basic game.yaml
        game_yaml_content = f"""# Renee Game Project: {name}

name: {name}
version: 0.1.0
template: {template}

# Schema files to load
schemas:
  - schemas/components.yaml
  - schemas/events.yaml
  - schemas/actions.yaml

# Entity template directories
entity_templates:
  - entities/

# Asset directories
assets:
  sprites: assets/sprites
  sounds: assets/sounds
  fonts: assets/fonts
"""
        (project_path / "game.yaml").write_text(game_yaml_content)

        # Create placeholder schema files
        components_yaml = """# Component Schemas
# Define your game's component types here

components:
  Position:
    intent: "2D position on the game grid"
    fields:
      x:
        type: int
        default: 0
      y:
        type: int
        default: 0
"""
        (project_path / "schemas" / "components.yaml").write_text(components_yaml)

        events_yaml = """# Event Schemas
# Define your game's event types here

events:
  EntityMoved:
    intent: "Fired when an entity moves"
    fields:
      entity:
        type: int
      from_x:
        type: int
      from_y:
        type: int
      to_x:
        type: int
      to_y:
        type: int
"""
        (project_path / "schemas" / "events.yaml").write_text(events_yaml)

        actions_yaml = """# Action Schemas
# Define your game's action types here

actions:
  Move:
    intent: "Move an entity to a new position"
    fields:
      entity:
        type: int
      target_x:
        type: int
      target_y:
        type: int
"""
        (project_path / "schemas" / "actions.yaml").write_text(actions_yaml)

        # Create README
        readme_content = f"""# {name}

A Renee game project.

## Structure

- `schemas/` - Type definitions for components, events, and actions
- `entities/` - Entity templates
- `systems/` - Game logic (Python modules)
- `rules/` - Game rules (Python decorators)
- `scenes/` - Level/map definitions
- `assets/` - Game assets (sprites, sounds, fonts)
- `tests/` - pytest test suite

## Commands

- `renee run` - Run the game
- `renee validate` - Validate game files
- `renee repl` - Start interactive REPL
- `renee schema` - Show schema information

## Getting Started

1. Define your components in `schemas/components.yaml`
2. Create entity templates in `entities/`
3. Implement game systems in `systems/`
4. Add game rules in `rules/`
5. Run with `renee run`
"""
        (project_path / "README.md").write_text(readme_content)

        formatter.success(
            f"Created new project: {name}",
            {
                "path": str(project_path),
                "template": template,
            },
        )

    except Exception as e:
        formatter.error(f"Failed to create project: {str(e)}")
        sys.exit(1)


@app.command()
def run(
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
    headless: bool = typer.Option(False, "--headless", help="Run without graphics"),
) -> None:
    """Run a game.

    Loads the game from the specified project directory and starts it.

    Example:
        renee run
        renee run --project=/path/to/game --headless
    """
    formatter = get_formatter()
    formatter.error("Not yet implemented")
    sys.exit(1)


@app.command()
def validate(
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
) -> None:
    """Validate game files against schemas.

    Checks all YAML files in the project for:
    - Valid YAML syntax
    - Schema conformance
    - Intent field presence
    - Reference integrity

    Example:
        renee validate
        renee validate --project=/path/to/game
    """
    formatter = get_formatter()
    formatter.error("Not yet implemented")
    sys.exit(1)


@app.command()
def schema(
    name: Optional[str] = typer.Argument(None, help="Schema name to show"),
    list_all: bool = typer.Option(False, "--list", "-l", help="List all schemas"),
    schema_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by type (component/event/action)",
    ),
) -> None:
    """Show or list schemas.

    Without arguments, lists all available schemas.
    With a name argument, shows details for that schema.

    Example:
        renee schema --list
        renee schema Health
        renee schema --list --type=component --json
    """
    formatter = get_formatter()

    # For now, create an empty registry
    # In a real implementation, this would load from the project
    registry = SchemaRegistry()

    if list_all or name is None:
        # List schemas
        if schema_type:
            if schema_type not in ("component", "event", "action"):
                formatter.error(f"Invalid type: {schema_type}. Must be component, event, or action.")
                sys.exit(1)
            schemas = registry.list_schemas(type=schema_type)  # type: ignore
        else:
            schemas = registry.list_schemas()

        if _json_output:
            formatter.dict_output({"schemas": schemas})
        else:
            if schema_type:
                formatter.list_items(schemas, f"{schema_type.capitalize()} Schemas")
            else:
                formatter.list_items(schemas, "All Schemas")

    else:
        # Show specific schema
        try:
            schema_obj = registry.get(name)
            formatter.dict_output(schema_obj.to_dict(), f"Schema: {name}")
        except KeyError:
            formatter.error(f"Schema not found: {name}")
            sys.exit(1)


@app.command()
def query(
    entity: Optional[int] = typer.Option(None, "--entity", "-e", help="Query specific entity"),
    component: Optional[str] = typer.Option(None, "--component", "-c", help="Filter by component"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
) -> None:
    """Query game state.

    Query entities, components, and tags in a running game.

    Example:
        renee query --entity=42
        renee query --tag=player
        renee query --component=Health --json
    """
    formatter = get_formatter()
    formatter.error("Not yet implemented")
    sys.exit(1)


@app.command()
def simulate(
    scenario: str = typer.Argument(..., help="Scenario file to simulate"),
    runs: int = typer.Option(100, "--runs", "-n", help="Number of simulation runs"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed for reproducibility"),
) -> None:
    """Run simulation for balance testing.

    Runs a scenario multiple times with different random seeds and outputs
    statistical analysis of the results.

    Example:
        renee simulate scenarios/combat.yaml --runs=1000
        renee simulate scenarios/combat.yaml --runs=100 --seed=42 --json
    """
    formatter = get_formatter()
    formatter.error("Not yet implemented")
    sys.exit(1)


@app.command()
def impact(
    change: str = typer.Argument(..., help="Description of proposed change"),
) -> None:
    """Analyze impact of a proposed change.

    Shows what breaks when you make a change, with intent validation.

    Output includes:
    - Affected files
    - Affected rules
    - Intent violations
    - Simulation results (before/after)

    Example:
        renee impact "increase sword damage from 10 to 15"
        renee impact "add cooldown to fireball spell" --json
    """
    formatter = get_formatter()
    formatter.error("Not yet implemented")
    sys.exit(1)


@app.command()
def repl(
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
    json_mode: bool = typer.Option(False, "--json-mode", help="REPL JSON output mode"),
) -> None:
    """Start interactive REPL.

    Opens an interactive Read-Eval-Print Loop for game manipulation.

    Available REPL commands:
    - entity <id> - Show entity details
    - entities [tag] - List entities
    - spawn <template> - Create entity
    - destroy <id> - Remove entity
    - component <entity> <type> - Get component
    - set <entity> <component> <json> - Set component
    - state - Show world state
    - snapshot - Create snapshot
    - restore <id> - Restore snapshot
    - help - Show help
    - exit - Exit REPL

    Example:
        renee repl
        renee repl --project=/path/to/game --json-mode
    """
    # Create a basic world for the REPL
    # In a real implementation, this would load from the project
    world = World()

    # Start REPL
    game_repl = GameREPL(world, json_mode=json_mode)
    game_repl.run()


def cli_main() -> None:
    """Main entry point for the CLI.

    This is the function that gets called when 'renee' is run from the command line.
    """
    app()


if __name__ == "__main__":
    cli_main()
