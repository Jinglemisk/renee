"""REPL (Read-Eval-Print Loop) for interactive game manipulation.

The REPL provides an interactive interface for experimenting with games:
- Inspect entities and components
- Execute actions
- Manipulate world state
- Create and restore snapshots
- Query event history

The REPL supports both human-readable and JSON output modes.
"""

import json
from typing import Any

from renee.ecs.world import World
from renee.types import EntityId


class REPLOutput:
    """Format REPL output based on mode (JSON or human-readable).

    Example:
        >>> output = REPLOutput(json_mode=True)
        >>> output.format({"entity": 42, "tags": ["player"]})
        '{"entity": 42, "tags": ["player"]}'
    """

    def __init__(self, json_mode: bool) -> None:
        """Initialize REPL output formatter.

        Args:
            json_mode: If True, output JSON. If False, output human-readable text.
        """
        self.json_mode = json_mode

    def format(self, data: Any) -> str:
        """Format data for output.

        Args:
            data: Data to format

        Returns:
            Formatted string
        """
        if self.json_mode:
            return json.dumps(data, indent=2, default=str)
        else:
            return self._format_human(data)

    def _format_human(self, data: Any) -> str:
        """Format data in human-readable form.

        Args:
            data: Data to format

        Returns:
            Human-readable string
        """
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=2, default=str)
                    lines.append(f"{key}:")
                    for line in value_str.split("\n"):
                        lines.append(f"  {line}")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            if not data:
                return "(empty list)"
            lines = []
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    item_str = json.dumps(item, indent=2, default=str)
                    lines.append(f"[{i}]:")
                    for line in item_str.split("\n"):
                        lines.append(f"  {line}")
                else:
                    lines.append(f"[{i}]: {item}")
            return "\n".join(lines)
        else:
            return str(data)

    def error(self, message: str) -> str:
        """Format an error message.

        Args:
            message: Error message

        Returns:
            Formatted error string
        """
        if self.json_mode:
            return json.dumps({"error": message}, indent=2)
        else:
            return f"Error: {message}"

    def success(self, message: str) -> str:
        """Format a success message.

        Args:
            message: Success message

        Returns:
            Formatted success string
        """
        if self.json_mode:
            return json.dumps({"success": message}, indent=2)
        else:
            return f"Success: {message}"


class GameREPL:
    """Interactive REPL for game manipulation.

    The REPL provides commands for:
    - Entity inspection and manipulation
    - Component queries and modifications
    - Action execution
    - Snapshot/restore
    - Event history queries
    - Turn management

    Example:
        >>> world = World()
        >>> repl = GameREPL(world, json_mode=False)
        >>> repl.run()
        renee> entity 0
        Entity: 0
        Components: ...
    """

    def __init__(self, world: World, json_mode: bool = False) -> None:
        """Initialize the REPL.

        Args:
            world: The game world to interact with
            json_mode: If True, output JSON. If False, output human-readable text.
        """
        self.world = world
        self.json_mode = json_mode
        self.output = REPLOutput(json_mode)
        self.history: list[str] = []
        self.running = True

    def run(self) -> None:
        """Start the REPL loop.

        Runs until user exits with 'exit' or 'quit' command.
        """
        if not self.json_mode:
            print("Renee REPL - Interactive Game Manipulation")
            print("Type 'help' for available commands, 'exit' to quit")
            print()

        while self.running:
            try:
                if self.json_mode:
                    prompt = ""
                else:
                    prompt = "renee> "

                # Read command
                try:
                    command = input(prompt).strip()
                except EOFError:
                    # Handle Ctrl+D
                    self.running = False
                    break

                if not command:
                    continue

                # Execute and print result (execute() records to history)
                result = self.execute(command)
                if result:
                    print(result)

            except KeyboardInterrupt:
                # Handle Ctrl+C
                if not self.json_mode:
                    print("\nUse 'exit' to quit")
                continue
            except Exception as e:
                print(self.output.error(f"Unexpected error: {str(e)}"))

    def execute(self, command: str) -> str:
        """Execute a REPL command and return result.

        Args:
            command: Command string to execute

        Returns:
            Result string (formatted based on json_mode)
        """
        if not command:
            return ""

        # Record in history before executing
        self.history.append(command)

        # Parse command
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]

        # Dispatch to command handlers
        try:
            if cmd in ("exit", "quit"):
                self.running = False
                return self.output.success("Goodbye!")

            elif cmd == "help":
                return self._cmd_help(args)

            elif cmd == "entity":
                return self._cmd_entity(args)

            elif cmd == "entities":
                return self._cmd_entities(args)

            elif cmd == "spawn":
                return self._cmd_spawn(args)

            elif cmd == "destroy":
                return self._cmd_destroy(args)

            elif cmd == "component":
                return self._cmd_component(args)

            elif cmd == "set":
                return self._cmd_set(args)

            elif cmd == "query":
                return self._cmd_query(args)

            elif cmd == "state":
                return self._cmd_state(args)

            elif cmd == "snapshot":
                return self._cmd_snapshot(args)

            elif cmd == "restore":
                return self._cmd_restore(args)

            elif cmd == "history":
                return self._cmd_history(args)

            else:
                return self.output.error(f"Unknown command: {cmd}. Type 'help' for available commands.")

        except Exception as e:
            return self.output.error(f"Command failed: {str(e)}")

    def _cmd_help(self, args: list[str]) -> str:
        """Show help information."""
        help_text = """
Available commands:

Entity Management:
  entity <id>              Show entity details
  entities [tag]           List all entities (optionally filtered by tag)
  spawn <template>         Create entity from template
  destroy <id>             Remove entity

Component Operations:
  component <entity> <type>      Get component from entity
  set <entity> <component> <json>  Set component on entity
  query <component1> [...]       Query entities with components

World State:
  state                    Show world state summary
  snapshot [name]          Create state snapshot (optional name)
  restore <id>             Restore to snapshot

Other:
  history                  Show command history
  help                     Show this help
  exit/quit                Exit REPL
"""
        if self.json_mode:
            return json.dumps({"help": help_text.strip()}, indent=2)
        return help_text

    def _cmd_entity(self, args: list[str]) -> str:
        """Show entity details."""
        if not args:
            return self.output.error("Usage: entity <id>")

        try:
            entity_id = EntityId(int(args[0]))
        except ValueError:
            return self.output.error(f"Invalid entity ID: {args[0]}")

        if not self.world.entity_exists(entity_id):
            return self.output.error(f"Entity {entity_id} does not exist")

        # Get entity info
        components = self.world.get_all_components(entity_id)
        tags = self.world.get_tags(entity_id)

        # Format component data
        component_data = {}
        for comp_type, comp_value in components.items():
            comp_name = comp_type.__name__
            # Try to convert to dict if possible
            if hasattr(comp_value, "__dict__"):
                component_data[comp_name] = vars(comp_value)
            else:
                component_data[comp_name] = comp_value

        data = {
            "id": int(entity_id),
            "components": component_data,
            "tags": list(tags),
        }

        return self.output.format(data)

    def _cmd_entities(self, args: list[str]) -> str:
        """List all entities, optionally filtered by tag."""
        if args:
            # Filter by tag
            tag = args[0]
            entities = list(self.world.query_by_tag(tag))
            data = {
                "tag": tag,
                "count": len(entities),
                "entities": [int(e) for e in entities],
            }
        else:
            # All entities
            entities = list(self.world.all_entities())
            data = {
                "count": len(entities),
                "entities": [int(e) for e in entities],
            }

        return self.output.format(data)

    def _cmd_spawn(self, args: list[str]) -> str:
        """Create entity from template."""
        if not args:
            return self.output.error("Usage: spawn <template>")

        template_name = args[0]

        try:
            entity_id = self.world.spawn_from_template(template_name)
            data = {
                "entity": int(entity_id),
                "template": template_name,
            }
            return self.output.format(data)
        except KeyError as e:
            return self.output.error(str(e))

    def _cmd_destroy(self, args: list[str]) -> str:
        """Remove entity."""
        if not args:
            return self.output.error("Usage: destroy <id>")

        try:
            entity_id = EntityId(int(args[0]))
        except ValueError:
            return self.output.error(f"Invalid entity ID: {args[0]}")

        try:
            self.world.destroy_entity(entity_id)
            return self.output.success(f"Destroyed entity {entity_id}")
        except KeyError as e:
            return self.output.error(str(e))

    def _cmd_component(self, args: list[str]) -> str:
        """Get component from entity."""
        if len(args) < 2:
            return self.output.error("Usage: component <entity> <type>")

        try:
            entity_id = EntityId(int(args[0]))
        except ValueError:
            return self.output.error(f"Invalid entity ID: {args[0]}")

        component_type_name = args[1]

        # Get all components and find by name
        try:
            components = self.world.get_all_components(entity_id)
            for comp_type, comp_value in components.items():
                if comp_type.__name__ == component_type_name:
                    if hasattr(comp_value, "__dict__"):
                        data = vars(comp_value)
                    else:
                        data = comp_value
                    return self.output.format(data)

            return self.output.error(
                f"Entity {entity_id} does not have component '{component_type_name}'"
            )
        except KeyError as e:
            return self.output.error(str(e))

    def _cmd_set(self, args: list[str]) -> str:
        """Set component on entity."""
        if len(args) < 3:
            return self.output.error("Usage: set <entity> <component> <json>")

        try:
            entity_id = EntityId(int(args[0]))
        except ValueError:
            return self.output.error(f"Invalid entity ID: {args[0]}")

        component_type_name = args[1]
        json_data = " ".join(args[2:])

        try:
            component_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return self.output.error(f"Invalid JSON: {e}")

        # For now, just store as dict
        # In a real implementation, you'd want to instantiate the proper component type
        if not self.world.entity_exists(entity_id):
            return self.output.error(f"Entity {entity_id} does not exist")

        # Create a simple component class dynamically
        class DynamicComponent:
            def __init__(self, data: dict[str, Any]):
                self.__dict__.update(data)

        DynamicComponent.__name__ = component_type_name
        component = DynamicComponent(component_data)

        self.world.add_component(entity_id, component)
        return self.output.success(
            f"Set component '{component_type_name}' on entity {entity_id}"
        )

    def _cmd_query(self, args: list[str]) -> str:
        """Query entities with components."""
        if not args:
            return self.output.error("Usage: query <component1> [component2 ...]")

        # This is simplified - in a real implementation, you'd need to resolve
        # component type names to actual types
        return self.output.error("Query by component type not yet implemented")

    def _cmd_state(self, args: list[str]) -> str:
        """Show world state summary."""
        entities = list(self.world.all_entities())
        snapshots = self.world.list_snapshots()

        data = {
            "entities": {
                "count": len(entities),
                "ids": [int(e) for e in entities],
            },
            "snapshots": {
                "count": len(snapshots),
                "ids": snapshots,
            },
        }

        return self.output.format(data)

    def _cmd_snapshot(self, args: list[str]) -> str:
        """Create state snapshot."""
        # Optional name argument
        name = args[0] if args else None
        snapshot_id = self.world.save_snapshot(name)
        data = {
            "snapshot_id": snapshot_id,
        }
        return self.output.format(data)

    def _cmd_restore(self, args: list[str]) -> str:
        """Restore to snapshot."""
        if not args:
            return self.output.error("Usage: restore <id>")

        snapshot_id = args[0]

        try:
            self.world.load_snapshot(snapshot_id)
            return self.output.success(f"Restored to snapshot {snapshot_id}")
        except KeyError as e:
            return self.output.error(str(e))

    def _cmd_history(self, args: list[str]) -> str:
        """Show command history."""
        if not self.history:
            return self.output.format({"history": []})

        data = {
            "count": len(self.history),
            "commands": self.history,
        }
        return self.output.format(data)
