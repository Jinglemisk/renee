"""Tests for the Schema Registry system."""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from renee.schema import SchemaRegistry, Schema, FieldDefinition
from renee.schema.loader import load_schemas_from_yaml, save_schemas_to_yaml


class TestFieldDefinition:
    """Tests for FieldDefinition class."""

    def test_basic_field(self):
        field = FieldDefinition(name="health", type="int", default=100)
        assert field.name == "health"
        assert field.type == "int"
        assert field.default == 100

    def test_field_with_constraints(self):
        field = FieldDefinition(
            name="level",
            type="int",
            default=1,
            constraints={"min": 1, "max": 100},
        )
        assert field.constraints["min"] == 1
        assert field.constraints["max"] == 100

    def test_validate_valid_value(self):
        field = FieldDefinition(name="score", type="int", constraints={"min": 0, "max": 100})
        is_valid, error = field.validate_value(50)
        assert is_valid
        assert error is None

    def test_validate_below_min(self):
        field = FieldDefinition(name="score", type="int", constraints={"min": 0})
        is_valid, error = field.validate_value(-10)
        assert not is_valid
        assert "less than minimum" in error

    def test_validate_above_max(self):
        field = FieldDefinition(name="score", type="int", constraints={"max": 100})
        is_valid, error = field.validate_value(150)
        assert not is_valid
        assert "exceeds maximum" in error

    def test_validate_wrong_type(self):
        field = FieldDefinition(name="name", type="str")
        is_valid, error = field.validate_value(123)
        assert not is_valid
        assert "expected type" in error

    def test_to_dict(self):
        field = FieldDefinition(
            name="health",
            type="int",
            default=100,
            constraints={"min": 0},
            description="Player health points",
        )
        data = field.to_dict()
        assert data["name"] == "health"
        assert data["type"] == "int"
        assert data["default"] == 100
        assert data["constraints"] == {"min": 0}
        assert data["description"] == "Player health points"


class TestSchema:
    """Tests for Schema class."""

    def test_basic_schema(self):
        schema = Schema(name="Health", type="component")
        assert schema.name == "Health"
        assert schema.type == "component"
        assert len(schema.fields) == 0

    def test_schema_with_fields(self):
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int", default=100),
                "max": FieldDefinition("max", "int", default=100),
            },
        )
        assert len(schema.fields) == 2
        assert "current" in schema.fields
        assert "max" in schema.fields

    def test_schema_with_intent(self):
        schema = Schema(
            name="Health",
            type="component",
            intent="Tracks entity hit points",
        )
        assert schema.intent == "Tracks entity hit points"

    def test_schema_with_invariants(self):
        schema = Schema(
            name="Health",
            type="component",
            invariants=["current <= max", "current >= 0"],
        )
        assert len(schema.invariants) == 2

    def test_validate_valid_data(self):
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int", default=100),
                "max": FieldDefinition("max", "int", default=100),
            },
        )
        is_valid, errors = schema.validate({"current": 50, "max": 100})
        assert is_valid
        assert len(errors) == 0

    def test_validate_missing_required_field(self):
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int"),  # No default = required
                "max": FieldDefinition("max", "int", default=100),
            },
        )
        is_valid, errors = schema.validate({"max": 100})
        assert not is_valid
        assert any("Missing required field: current" in e for e in errors)

    def test_validate_unknown_field(self):
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int", default=100),
            },
        )
        is_valid, errors = schema.validate({"current": 50, "unknown": 999})
        assert not is_valid
        assert any("Unknown field: unknown" in e for e in errors)

    def test_defaults(self):
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int", default=100),
                "max": FieldDefinition("max", "int", default=100),
                "bonus": FieldDefinition("bonus", "int"),  # No default
            },
        )
        defaults = schema.defaults()
        assert defaults == {"current": 100, "max": 100}
        assert "bonus" not in defaults

    def test_to_dict(self):
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int", default=100),
            },
            intent="Tracks hit points",
            invariants=["current >= 0"],
        )
        data = schema.to_dict()
        assert data["name"] == "Health"
        assert data["type"] == "component"
        assert "current" in data["fields"]
        assert data["intent"] == "Tracks hit points"
        assert data["invariants"] == ["current >= 0"]

    def test_from_dict(self):
        data = {
            "name": "Health",
            "type": "component",
            "fields": {
                "current": {
                    "type": "int",
                    "default": 100,
                    "constraints": {"min": 0},
                }
            },
            "intent": "Tracks hit points",
        }
        schema = Schema.from_dict(data)
        assert schema.name == "Health"
        assert schema.type == "component"
        assert len(schema.fields) == 1
        assert schema.fields["current"].default == 100
        assert schema.intent == "Tracks hit points"

    def test_from_dataclass(self):
        @dataclass
        class Health:
            """Tracks entity hit points"""
            current: int = 100
            max: int = 100

        schema = Schema.from_dataclass(Health, "component")
        assert schema.name == "Health"
        assert schema.type == "component"
        assert len(schema.fields) == 2
        assert schema.fields["current"].type == "int"
        assert schema.fields["current"].default == 100
        assert "hit points" in schema.intent.lower()


class TestSchemaRegistry:
    """Tests for SchemaRegistry class."""

    def test_empty_registry(self):
        registry = SchemaRegistry()
        assert len(registry) == 0
        assert registry.list_schemas() == []

    def test_register_schema(self):
        registry = SchemaRegistry()
        schema = Schema(name="Health", type="component")
        registry.register(schema)
        assert len(registry) == 1
        assert "Health" in registry

    def test_register_duplicate_raises_error(self):
        registry = SchemaRegistry()
        schema = Schema(name="Health", type="component")
        registry.register(schema)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(schema)

    def test_register_component(self):
        @dataclass
        class Health:
            current: int = 100
            max: int = 100

        registry = SchemaRegistry()
        registry.register_component(Health)
        assert "Health" in registry
        assert registry.get("Health").type == "component"

    def test_register_event(self):
        @dataclass
        class DamageEvent:
            entity_id: int
            amount: int

        registry = SchemaRegistry()
        registry.register_event(DamageEvent)
        assert "DamageEvent" in registry
        assert registry.get("DamageEvent").type == "event"

    def test_register_action(self):
        @dataclass
        class MoveAction:
            entity_id: int
            x: int
            y: int

        registry = SchemaRegistry()
        registry.register_action(MoveAction)
        assert "MoveAction" in registry
        assert registry.get("MoveAction").type == "action"

    def test_get_schema(self):
        registry = SchemaRegistry()
        schema = Schema(name="Health", type="component")
        registry.register(schema)
        retrieved = registry.get("Health")
        assert retrieved.name == "Health"

    def test_get_missing_schema_raises_error(self):
        registry = SchemaRegistry()
        with pytest.raises(KeyError, match="No schema named"):
            registry.get("NonExistent")

    def test_has_schema(self):
        registry = SchemaRegistry()
        schema = Schema(name="Health", type="component")
        registry.register(schema)
        assert registry.has("Health")
        assert not registry.has("NonExistent")

    def test_list_schemas(self):
        registry = SchemaRegistry()
        registry.register(Schema(name="Health", type="component"))
        registry.register(Schema(name="Sprite", type="component"))
        registry.register(Schema(name="DamageEvent", type="event"))

        all_schemas = registry.list_schemas()
        assert len(all_schemas) == 3
        assert "Health" in all_schemas

        components = registry.list_schemas(type="component")
        assert len(components) == 2
        assert "Health" in components
        assert "Sprite" in components
        assert "DamageEvent" not in components

        events = registry.list_schemas(type="event")
        assert len(events) == 1
        assert "DamageEvent" in events

    def test_validate(self):
        registry = SchemaRegistry()
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int", default=100),
            },
        )
        registry.register(schema)

        is_valid, errors = registry.validate("Health", {"current": 50})
        assert is_valid

        is_valid, errors = registry.validate("Health", {"invalid": 123})
        assert not is_valid

    def test_defaults(self):
        registry = SchemaRegistry()
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int", default=100),
                "max": FieldDefinition("max", "int", default=100),
            },
        )
        registry.register(schema)

        defaults = registry.defaults("Health")
        assert defaults == {"current": 100, "max": 100}

    def test_to_dict(self):
        registry = SchemaRegistry()
        registry.register(Schema(name="Health", type="component"))
        registry.register(Schema(name="DamageEvent", type="event"))

        data = registry.to_dict()
        assert "Health" in data
        assert "DamageEvent" in data
        assert data["Health"]["type"] == "component"

    def test_to_json(self):
        registry = SchemaRegistry()
        registry.register(Schema(name="Health", type="component"))

        json_str = registry.to_json()
        data = json.loads(json_str)
        assert "Health" in data

    def test_clear(self):
        registry = SchemaRegistry()
        registry.register(Schema(name="Health", type="component"))
        assert len(registry) == 1

        registry.clear()
        assert len(registry) == 0


class TestYAMLLoader:
    """Tests for YAML loading functionality."""

    def test_load_from_yaml(self):
        yaml_content = """
components:
  Health:
    intent: "Tracks entity hit points"
    fields:
      current:
        type: int
        default: 100
        constraints:
          min: 0
      max:
        type: int
        default: 100
        constraints:
          min: 1
    invariants:
      - "current <= max"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            schemas = load_schemas_from_yaml(temp_path)
            assert len(schemas) == 1
            assert schemas[0].name == "Health"
            assert schemas[0].type == "component"
            assert schemas[0].intent == "Tracks entity hit points"
            assert len(schemas[0].fields) == 2
            assert schemas[0].fields["current"].constraints["min"] == 0
            assert len(schemas[0].invariants) == 1
        finally:
            Path(temp_path).unlink()

    def test_load_multiple_types(self):
        yaml_content = """
components:
  Health:
    fields:
      current:
        type: int
        default: 100

events:
  DamageEvent:
    fields:
      amount:
        type: int

actions:
  MoveAction:
    fields:
      target_x:
        type: int
      target_y:
        type: int
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            schemas = load_schemas_from_yaml(temp_path)
            assert len(schemas) == 3
            types = {s.type for s in schemas}
            assert types == {"component", "event", "action"}
        finally:
            Path(temp_path).unlink()

    def test_register_from_yaml(self):
        yaml_content = """
components:
  Health:
    fields:
      current:
        type: int
        default: 100
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry = SchemaRegistry()
            registry.register_from_yaml(temp_path)
            assert "Health" in registry
            assert registry.get("Health").fields["current"].default == 100
        finally:
            Path(temp_path).unlink()

    def test_save_schemas_to_yaml(self):
        schema = Schema(
            name="Health",
            type="component",
            fields={
                "current": FieldDefinition("current", "int", default=100),
            },
            intent="Tracks hit points",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            save_schemas_to_yaml([schema], temp_path)
            loaded = load_schemas_from_yaml(temp_path)
            assert len(loaded) == 1
            assert loaded[0].name == "Health"
            assert loaded[0].intent == "Tracks hit points"
        finally:
            Path(temp_path).unlink()


class TestIntegration:
    """Integration tests demonstrating full workflow."""

    def test_full_workflow(self):
        """Test the complete workflow from the user's example."""
        # Create registry
        registry = SchemaRegistry()

        # Define a component with YAML
        yaml_content = """
components:
  Health:
    intent: "Tracks entity hit points"
    fields:
      current:
        type: int
        default: 100
        constraints:
          min: 0
      max:
        type: int
        default: 100
        constraints:
          min: 1
    invariants:
      - "current <= max"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Register from YAML
            registry.register_from_yaml(temp_path)

            # Register from dataclass
            @dataclass
            class Position:
                x: int = 0
                y: int = 0

            registry.register_component(Position)

            # Get schema
            schema = registry.get("Health")
            assert schema.fields is not None
            assert schema.intent == "Tracks entity hit points"

            # Validate data
            is_valid, errors = schema.validate({"current": 50, "max": 100})
            assert is_valid

            # Get defaults
            defaults = schema.defaults()
            assert defaults == {"current": 100, "max": 100}

            # List schemas
            components = registry.list_schemas(type="component")
            assert "Health" in components
            assert "Position" in components

            # Export to JSON
            json_str = registry.to_json()
            data = json.loads(json_str)
            assert "Health" in data
            assert "Position" in data

        finally:
            Path(temp_path).unlink()

    def test_ai_querying_workflow(self):
        """Demonstrate how an AI agent would query the registry."""
        registry = SchemaRegistry()

        # Set up some schemas
        @dataclass
        class Health:
            """Tracks entity hit points"""
            current: int = 100
            max: int = 100

        @dataclass
        class Sprite:
            """Visual representation"""
            image: str = "default.png"
            scale: float = 1.0

        registry.register_component(Health)
        registry.register_component(Sprite)

        # AI asks: "What components are available?"
        components = registry.list_schemas(type="component")
        assert set(components) == {"Health", "Sprite"}

        # AI asks: "What fields does Health have?"
        health_schema = registry.get("Health")
        field_names = list(health_schema.fields.keys())
        assert set(field_names) == {"current", "max"}

        # AI asks: "What's the default value for Health?"
        defaults = health_schema.defaults()
        assert defaults == {"current": 100, "max": 100}

        # AI asks: "What's the purpose of Health?"
        assert "hit points" in health_schema.intent.lower()

        # AI asks: "Give me all schema info as JSON"
        json_data = json.loads(registry.to_json())
        assert len(json_data) == 2
