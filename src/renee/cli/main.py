"""Renee CLI - Main entry point.

Designed for both humans and AI agents:
- `--json` on commands for structured output
- predictable exit codes (0 success, 1 error)

Uses typer for type-safe CLI with automatic help generation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from renee import __version__
from renee.assets import AssetRegistry
from renee.cli.output import OutputFormatter
from renee.cli.repl import GameREPL
from renee.ecs.world import World
from renee.errors import ReneeError
from renee.schema import SchemaRegistry

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


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(__version__)
        raise typer.Exit()


@app.callback()
def main(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON for machine parsing",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Print version and exit",
    ),
) -> None:
    """Renee Game Framework CLI.

    An AI-native framework for turn-based games.
    """
    global _json_output, _formatter
    _json_output = json_output
    _formatter = OutputFormatter(json_mode=json_output)


# ==================== Schema Commands ====================

schemas_app = typer.Typer(help="Schema introspection commands")
app.add_typer(schemas_app, name="schemas")


@schemas_app.command("list")
def schemas_list(
    path: str = typer.Option(..., "--path", help="Schema file (.yaml/.json/.toml)"),
    kind: Optional[str] = typer.Option(
        None, "--kind", help="Filter by kind (component/event/action)"
    ),
) -> None:
    """List schemas in a file."""
    formatter = get_formatter()
    try:
        reg = SchemaRegistry()
        reg.load_from_path(path)
        schemas = reg.list(kind=kind) if kind else reg.list()
        data = {"ok": True, "schemas": schemas}
        _emit(data, formatter)
    except ReneeError as e:
        formatter.renee_error(e)
        raise typer.Exit(1)


@schemas_app.command("show")
def schemas_show(
    path: str = typer.Option(..., "--path", help="Schema file (.yaml/.json/.toml)"),
    kind: str = typer.Option(..., "--kind", help="Schema kind (component/event/action)"),
    name: str = typer.Option(..., "--name", help="Schema name"),
) -> None:
    """Show a specific schema."""
    formatter = get_formatter()
    try:
        reg = SchemaRegistry()
        reg.load_from_path(path)
        data = {"ok": True, "schema": reg.as_json(name, kind=kind)}
        _emit(data, formatter)
    except ReneeError as e:
        formatter.renee_error(e)
        raise typer.Exit(1)


# ==================== Asset Commands ====================

assets_app = typer.Typer(help="Asset management commands")
app.add_typer(assets_app, name="assets")


@assets_app.command("scan")
def assets_scan(
    root: str = typer.Option(..., "--root", help="Assets root directory"),
    manifest: str = typer.Option(
        "assets/manifest.json", "--manifest", help="Output manifest path"
    ),
    constants: str = typer.Option(
        "assets/constants.py", "--constants", help="Output constants module path"
    ),
) -> None:
    """Scan assets directory and generate manifest."""
    formatter = get_formatter()
    try:
        reg = AssetRegistry.scan(root)
        reg.write_manifest(manifest)
        reg.generate_constants(constants)
        data = {
            "ok": True,
            "manifest": manifest,
            "constants": constants,
            "counts": {k: len(v) for k, v in reg.manifest.items()},
        }
        _emit(data, formatter)
    except ReneeError as e:
        formatter.renee_error(e)
        raise typer.Exit(1)


# ==================== Demo Commands ====================

demo_app = typer.Typer(help="Run the built-in grid-walk demo")
app.add_typer(demo_app, name="demo")


@demo_app.command("local")
def demo_local(
    renderer: str = typer.Option(
        "terminal",
        "--renderer",
        help="Renderer type (terminal/pygame/headless)",
    ),
) -> None:
    """Run demo locally."""
    try:
        from renee.examples.grid_walk import run_local

        run_local(renderer=renderer)
    except Exception as e:
        formatter = get_formatter()
        formatter.error(f"Demo failed: {str(e)}")
        raise typer.Exit(1)


@demo_app.command("server")
def demo_server(
    host: str = typer.Option("127.0.0.1", "--host", help="Server host"),
    port: int = typer.Option(8765, "--port", help="Server port"),
) -> None:
    """Run demo server."""
    try:
        from renee.examples.grid_walk import run_server

        run_server(host=host, port=port)
    except Exception as e:
        formatter = get_formatter()
        formatter.error(f"Server failed: {str(e)}")
        raise typer.Exit(1)


@demo_app.command("client")
def demo_client(
    host: str = typer.Option("127.0.0.1", "--host", help="Server host"),
    port: int = typer.Option(8765, "--port", help="Server port"),
    renderer: str = typer.Option(
        "terminal",
        "--renderer",
        help="Renderer type (terminal/pygame)",
    ),
) -> None:
    """Run demo client."""
    try:
        from renee.examples.grid_walk import run_client

        run_client(host=host, port=port, renderer=renderer)
    except Exception as e:
        formatter = get_formatter()
        formatter.error(f"Client failed: {str(e)}")
        raise typer.Exit(1)


# ==================== Impact Commands ====================

impact_app = typer.Typer(help="Impact analysis utilities")
app.add_typer(impact_app, name="impact")


@impact_app.command("schema")
def impact_schema(
    path: str = typer.Option(..., "--path", help="Schema file (.yaml/.json/.toml)"),
    kind: str = typer.Option(..., "--kind", help="Schema kind (component/event/action)"),
    name: str = typer.Option(..., "--name", help="Schema name"),
) -> None:
    """Analyze schema references and impact."""
    formatter = get_formatter()
    try:
        from renee.impact import analyze_schema_impact

        reg = SchemaRegistry()
        reg.load_from_path(path)
        report = analyze_schema_impact(reg, kind=kind, name=name)
        data = {
            "ok": True,
            "impact": {
                "kind": report.kind,
                "name": report.name,
                "referenced_by": report.referenced_by,
            },
        }
        _emit(data, formatter)
    except ReneeError as e:
        formatter.renee_error(e)
        raise typer.Exit(1)


# ==================== Project Commands ====================


@app.command()
def new(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", "--template", "-t", help="Project template"),
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="Project directory (default: ./name)"
    ),
) -> None:
    """Create a new game project.

    Creates a new Renee game project with the standard directory structure.

    Example:
        renee new my-game
        renee new my-game --template=tactics --path=/path/to/project
    """
    formatter = get_formatter()

    try:
        project_path = Path(path) if path else Path.cwd() / name

        if project_path.exists():
            formatter.error(f"Directory already exists: {project_path}")
            raise typer.Exit(1)

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

        # Create game.yaml
        game_yaml = f"""# Renee Game Project: {name}

name: {name}
version: 0.1.0
template: {template}

schemas:
  - schemas/components.yaml
  - schemas/events.yaml
  - schemas/actions.yaml

entity_templates:
  - entities/

assets:
  sprites: assets/sprites
  sounds: assets/sounds
  fonts: assets/fonts
"""
        (project_path / "game.yaml").write_text(game_yaml)

        # Create placeholder schema files
        (project_path / "schemas" / "components.yaml").write_text(
            """# Component Schemas
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
        )

        (project_path / "schemas" / "events.yaml").write_text(
            """# Event Schemas
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
        )

        (project_path / "schemas" / "actions.yaml").write_text(
            """# Action Schemas
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
        )

        formatter.success(
            f"Created new project: {name}",
            {"path": str(project_path), "template": template},
        )

    except Exception as e:
        formatter.error(f"Failed to create project: {str(e)}")
        raise typer.Exit(1)


@app.command()
def validate(
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
) -> None:
    """Validate game files against schemas.

    Checks all YAML files in the project for valid syntax and schema conformance.
    """
    formatter = get_formatter()
    formatter.error("Not yet implemented")
    raise typer.Exit(1)


@app.command()
def repl(
    project: str = typer.Option(".", "--project", "-p", help="Project directory"),
    demo: bool = typer.Option(False, "--demo", help="Use built-in demo world"),
    json_mode: bool = typer.Option(False, "--json-mode", help="REPL JSON output mode"),
) -> None:
    """Start interactive REPL.

    Opens an interactive Read-Eval-Print Loop for game manipulation.

    Example:
        renee repl
        renee repl --demo --json-mode
    """
    if demo:
        # Use the demo pipeline
        try:
            from renee.examples.grid_walk import build_demo

            pipeline, _schemas = build_demo()
            # Use the pipeline's world for the REPL
            game_repl = GameREPL(pipeline.world, json_mode=json_mode)
            game_repl.run()
        except Exception as e:
            formatter = get_formatter()
            formatter.error(f"Demo REPL failed: {str(e)}")
            raise typer.Exit(1)
    else:
        # Create a basic world for the REPL
        world = World()
        game_repl = GameREPL(world, json_mode=json_mode)
        game_repl.run()


@app.command()
def query(
    entity: Optional[int] = typer.Option(None, "--entity", "-e", help="Entity ID"),
    component: Optional[str] = typer.Option(None, "--component", "-c", help="Component type"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Entity tag"),
) -> None:
    """Query game state.

    Query entities, components, and tags in a running game.
    """
    formatter = get_formatter()
    formatter.error("Not yet implemented - use the REPL instead")
    raise typer.Exit(1)


@app.command()
def simulate(
    scenario: str = typer.Argument(..., help="Scenario file to simulate"),
    runs: int = typer.Option(100, "--runs", "-n", help="Number of simulation runs"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed"),
) -> None:
    """Run simulation for balance testing.

    Runs a scenario multiple times with different random seeds.
    """
    formatter = get_formatter()
    formatter.error("Not yet implemented")
    raise typer.Exit(1)


# ==================== Helper Functions ====================


def _emit(data: dict, formatter: OutputFormatter) -> None:
    """Emit data in the appropriate format."""
    if _json_output:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        # Human-readable fallback
        if "schema" in data:
            print(json.dumps(data["schema"], indent=2, sort_keys=True))
        else:
            print(json.dumps(data, indent=2, sort_keys=True))


def cli_main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli_main()
