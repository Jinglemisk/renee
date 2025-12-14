"""Tests for the CLI and REPL functionality."""

import json
from io import StringIO

import pytest

from renee.cli.output import OutputFormatter
from renee.cli.repl import GameREPL, REPLOutput
from renee.ecs.world import World


class TestOutputFormatter:
    """Test the OutputFormatter class."""

    def test_success_json_mode(self, capsys):
        """Test success output in JSON mode."""
        formatter = OutputFormatter(json_mode=True)
        formatter.success("Test message", {"key": "value"})

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["status"] == "success"
        assert output["message"] == "Test message"
        assert output["data"] == {"key": "value"}

    def test_success_human_mode(self, capsys):
        """Test success output in human-readable mode."""
        formatter = OutputFormatter(json_mode=False)
        formatter.success("Test message")

        captured = capsys.readouterr()
        assert "Success: Test message" in captured.out

    def test_error_json_mode(self, capsys):
        """Test error output in JSON mode."""
        formatter = OutputFormatter(json_mode=True)
        formatter.error("Error message", "Details here")

        captured = capsys.readouterr()
        output = json.loads(captured.err)

        assert output["status"] == "error"
        assert output["message"] == "Error message"
        assert output["details"] == "Details here"

    def test_error_human_mode(self, capsys):
        """Test error output in human-readable mode."""
        formatter = OutputFormatter(json_mode=False)
        formatter.error("Error message", "Details here")

        captured = capsys.readouterr()
        assert "Error: Error message" in captured.err
        assert "Details here" in captured.err

    def test_table_json_mode(self, capsys):
        """Test table output in JSON mode."""
        formatter = OutputFormatter(json_mode=True)
        formatter.table(["ID", "Name"], [[1, "Alice"], [2, "Bob"]])

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert len(output) == 2
        assert output[0] == {"ID": 1, "Name": "Alice"}
        assert output[1] == {"ID": 2, "Name": "Bob"}

    def test_table_human_mode(self, capsys):
        """Test table output in human-readable mode."""
        formatter = OutputFormatter(json_mode=False)
        formatter.table(["ID", "Name"], [[1, "Alice"], [2, "Bob"]])

        captured = capsys.readouterr()
        assert "ID" in captured.out
        assert "Name" in captured.out
        assert "Alice" in captured.out
        assert "Bob" in captured.out


class TestREPLOutput:
    """Test the REPLOutput class."""

    def test_format_json_mode(self):
        """Test formatting in JSON mode."""
        output = REPLOutput(json_mode=True)
        result = output.format({"key": "value", "number": 42})

        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_format_human_mode_dict(self):
        """Test formatting dict in human-readable mode."""
        output = REPLOutput(json_mode=False)
        result = output.format({"key": "value", "number": 42})

        assert "key: value" in result
        assert "number: 42" in result

    def test_format_human_mode_list(self):
        """Test formatting list in human-readable mode."""
        output = REPLOutput(json_mode=False)
        result = output.format(["item1", "item2", "item3"])

        assert "[0]: item1" in result
        assert "[1]: item2" in result
        assert "[2]: item3" in result

    def test_error_json_mode(self):
        """Test error formatting in JSON mode."""
        output = REPLOutput(json_mode=True)
        result = output.error("Something went wrong")

        parsed = json.loads(result)
        assert parsed["error"] == "Something went wrong"

    def test_error_human_mode(self):
        """Test error formatting in human-readable mode."""
        output = REPLOutput(json_mode=False)
        result = output.error("Something went wrong")

        assert "Error: Something went wrong" in result

    def test_success_json_mode(self):
        """Test success formatting in JSON mode."""
        output = REPLOutput(json_mode=True)
        result = output.success("Operation completed")

        parsed = json.loads(result)
        assert parsed["success"] == "Operation completed"

    def test_success_human_mode(self):
        """Test success formatting in human-readable mode."""
        output = REPLOutput(json_mode=False)
        result = output.success("Operation completed")

        assert "Success: Operation completed" in result


class TestGameREPL:
    """Test the GameREPL class."""

    def test_entity_command(self):
        """Test the entity command."""
        world = World()
        entity = world.create_entity()
        world.add_tag(entity, "player")

        repl = GameREPL(world, json_mode=True)
        result = repl.execute(f"entity {entity}")

        parsed = json.loads(result)
        assert parsed["id"] == entity
        assert "player" in parsed["tags"]

    def test_entities_command(self):
        """Test the entities command."""
        world = World()
        e1 = world.create_entity()
        e2 = world.create_entity()

        repl = GameREPL(world, json_mode=True)
        result = repl.execute("entities")

        parsed = json.loads(result)
        assert parsed["count"] == 2
        assert e1 in parsed["entities"]
        assert e2 in parsed["entities"]

    def test_entities_with_tag(self):
        """Test the entities command with tag filter."""
        world = World()
        e1 = world.create_entity()
        e2 = world.create_entity()
        world.add_tag(e1, "player")
        world.add_tag(e2, "enemy")

        repl = GameREPL(world, json_mode=True)
        result = repl.execute("entities player")

        parsed = json.loads(result)
        assert parsed["count"] == 1
        assert parsed["tag"] == "player"
        assert e1 in parsed["entities"]
        assert e2 not in parsed["entities"]

    def test_destroy_command(self):
        """Test the destroy command."""
        world = World()
        entity = world.create_entity()

        repl = GameREPL(world, json_mode=True)
        result = repl.execute(f"destroy {entity}")

        parsed = json.loads(result)
        assert "success" in parsed
        assert not world.entity_exists(entity)

    def test_snapshot_restore(self):
        """Test snapshot and restore commands."""
        world = World()
        e1 = world.create_entity()
        e2 = world.create_entity()

        repl = GameREPL(world, json_mode=True)

        # Create snapshot
        result = repl.execute("snapshot")
        parsed = json.loads(result)
        snapshot_id = parsed["snapshot_id"]

        # Destroy an entity
        world.destroy_entity(e1)
        assert world.entity_count() == 1

        # Restore snapshot
        result = repl.execute(f"restore {snapshot_id}")
        parsed = json.loads(result)
        assert "success" in parsed

        # Both entities should be back
        assert world.entity_count() == 2
        assert world.entity_exists(e1)
        assert world.entity_exists(e2)

    def test_state_command(self):
        """Test the state command."""
        world = World()
        world.create_entity()
        world.create_entity()
        snapshot_id = world.snapshot()

        repl = GameREPL(world, json_mode=True)
        result = repl.execute("state")

        parsed = json.loads(result)
        assert parsed["entities"]["count"] == 2
        assert parsed["snapshots"]["count"] == 1
        assert snapshot_id in parsed["snapshots"]["ids"]

    def test_help_command(self):
        """Test the help command."""
        world = World()
        repl = GameREPL(world, json_mode=False)
        result = repl.execute("help")

        assert "entity" in result
        assert "entities" in result
        assert "snapshot" in result
        assert "restore" in result

    def test_invalid_command(self):
        """Test invalid command handling."""
        world = World()
        repl = GameREPL(world, json_mode=True)
        result = repl.execute("invalid_command")

        parsed = json.loads(result)
        assert "error" in parsed

    def test_entity_not_found(self):
        """Test entity command with non-existent entity."""
        world = World()
        repl = GameREPL(world, json_mode=True)
        result = repl.execute("entity 999")

        parsed = json.loads(result)
        assert "error" in parsed

    def test_history_command(self):
        """Test the history command."""
        world = World()
        repl = GameREPL(world, json_mode=True)

        # Execute some commands
        repl.execute("entities")
        repl.execute("state")

        # Check history
        result = repl.execute("history")
        parsed = json.loads(result)

        assert parsed["count"] == 3  # entities, state, history
        assert "entities" in parsed["commands"]
        assert "state" in parsed["commands"]
