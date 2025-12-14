"""YAML schema loading utilities.

This module provides functionality to load schema definitions from YAML files
and convert them into Schema objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml

from renee.schema.schema import Schema, FieldDefinition


def load_schemas_from_yaml(filepath: str | Path) -> list[Schema]:
    """Load schemas from a YAML file.

    The YAML file can contain 'components', 'events', and/or 'actions'
    sections, each with schema definitions.

    Args:
        filepath: Path to the YAML file

    Returns:
        List of Schema objects

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the YAML is malformed or invalid

    Example YAML structure:
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
            invariants:
              - "current <= max"

        events:
          DamageEvent:
            intent: "Emitted when entity takes damage"
            fields:
              entity_id:
                type: EntityId
              amount:
                type: int
                constraints:
                  min: 0

        actions:
          MoveAction:
            fields:
              entity_id:
                type: EntityId
              target:
                type: Position
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {filepath}: {e}") from e

    if not data:
        return []

    schemas: list[Schema] = []

    # Load components
    if "components" in data:
        for name, schema_def in data["components"].items():
            schema = _parse_schema(name, "component", schema_def)
            schemas.append(schema)

    # Load events
    if "events" in data:
        for name, schema_def in data["events"].items():
            schema = _parse_schema(name, "event", schema_def)
            schemas.append(schema)

    # Load actions
    if "actions" in data:
        for name, schema_def in data["actions"].items():
            schema = _parse_schema(name, "action", schema_def)
            schemas.append(schema)

    return schemas


def _parse_schema(
    name: str,
    schema_type: Literal["component", "event", "action"],
    schema_def: dict[str, Any],
) -> Schema:
    """Parse a schema definition from YAML data.

    Args:
        name: Schema name
        schema_type: Type of schema
        schema_def: Dictionary containing schema definition

    Returns:
        Schema object

    Raises:
        ValueError: If the schema definition is invalid
    """
    if not isinstance(schema_def, dict):
        raise ValueError(f"Schema '{name}' must be a dictionary, got {type(schema_def)}")

    # Extract fields
    fields_data = schema_def.get("fields", {})
    if not isinstance(fields_data, dict):
        raise ValueError(f"Schema '{name}' fields must be a dictionary")

    fields: dict[str, FieldDefinition] = {}
    for field_name, field_def in fields_data.items():
        fields[field_name] = _parse_field(field_name, field_def)

    # Extract optional attributes
    intent = schema_def.get("intent")
    if intent is not None and not isinstance(intent, str):
        raise ValueError(f"Schema '{name}' intent must be a string")

    invariants = schema_def.get("invariants", [])
    if not isinstance(invariants, list):
        raise ValueError(f"Schema '{name}' invariants must be a list")

    return Schema(
        name=name,
        type=schema_type,
        fields=fields,
        intent=intent,
        invariants=invariants,
    )


def _parse_field(name: str, field_def: dict[str, Any]) -> FieldDefinition:
    """Parse a field definition from YAML data.

    Args:
        name: Field name
        field_def: Dictionary containing field definition

    Returns:
        FieldDefinition object

    Raises:
        ValueError: If the field definition is invalid
    """
    if not isinstance(field_def, dict):
        raise ValueError(f"Field '{name}' must be a dictionary, got {type(field_def)}")

    # Type is required
    field_type = field_def.get("type")
    if not field_type:
        raise ValueError(f"Field '{name}' must have a 'type' attribute")
    if not isinstance(field_type, str):
        raise ValueError(f"Field '{name}' type must be a string")

    # Default is optional
    default = field_def.get("default")

    # Constraints are optional
    constraints = field_def.get("constraints", {})
    if not isinstance(constraints, dict):
        raise ValueError(f"Field '{name}' constraints must be a dictionary")

    # Description is optional
    description = field_def.get("description")
    if description is not None and not isinstance(description, str):
        raise ValueError(f"Field '{name}' description must be a string")

    return FieldDefinition(
        name=name,
        type=field_type,
        default=default,
        constraints=constraints,
        description=description,
    )


def save_schemas_to_yaml(
    schemas: list[Schema],
    filepath: str | Path,
    schema_type: Literal["component", "event", "action"] | None = None,
) -> None:
    """Save schemas to a YAML file.

    Args:
        schemas: List of schemas to save
        filepath: Path to save to
        schema_type: Optional filter - only save schemas of this type

    Example:
        >>> schemas = [health_schema, damage_schema]
        >>> save_schemas_to_yaml(schemas, "schemas/components.yaml", schema_type="component")
    """
    # Filter schemas if type specified
    if schema_type:
        schemas = [s for s in schemas if s.type == schema_type]

    # Group by type
    grouped: dict[str, dict[str, Any]] = {
        "components": {},
        "events": {},
        "actions": {},
    }

    for schema in schemas:
        schema_dict = schema.to_dict()
        # Remove 'name' and 'type' from the dict as they're in the structure
        schema_dict.pop("name", None)
        schema_dict.pop("type", None)

        if schema.type == "component":
            grouped["components"][schema.name] = schema_dict
        elif schema.type == "event":
            grouped["events"][schema.name] = schema_dict
        elif schema.type == "action":
            grouped["actions"][schema.name] = schema_dict

    # Remove empty sections
    grouped = {k: v for k, v in grouped.items() if v}

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(grouped, f, default_flow_style=False, sort_keys=False)
