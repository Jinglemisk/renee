"""Schema Registry for managing and querying type definitions.

The SchemaRegistry is a central repository for component, event, and action
schemas, allowing AI agents to introspect the game's type system.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from renee.schema.schema import Schema, FieldDefinition
from renee.schema.loader import load_schemas_from_yaml


class SchemaRegistry:
    """Central registry for component, event, and action schemas.

    The registry allows:
    - Registering schemas from YAML files or Python dataclasses
    - Querying schemas by name
    - Listing schemas by type
    - Validating data against schemas
    - Getting default values
    - JSON export for AI introspection

    Example:
        >>> registry = SchemaRegistry()
        >>> registry.register_from_yaml("schemas/components.yaml")
        >>> schema = registry.get("Health")
        >>> schema.validate({"current": 50, "max": 100})
        (True, [])
        >>> registry.list_schemas(type="component")
        ["Health", ...]
    """

    def __init__(self) -> None:
        """Initialize an empty schema registry."""
        self._schemas: dict[str, Schema] = {}

    def register(self, schema: Schema) -> None:
        """Register a schema.

        Args:
            schema: The schema to register

        Raises:
            ValueError: If a schema with this name is already registered
        """
        if schema.name in self._schemas:
            raise ValueError(f"Schema '{schema.name}' is already registered")
        self._schemas[schema.name] = schema

    def register_component(
        self, component_type: type, name: str | None = None
    ) -> None:
        """Register a component schema from a Python dataclass.

        Args:
            component_type: The dataclass type to register
            name: Optional name override (defaults to class name)

        Example:
            >>> @dataclass
            ... class Health:
            ...     current: int = 100
            ...     max: int = 100
            >>> registry.register_component(Health)
        """
        schema = Schema.from_dataclass(component_type, "component")
        if name:
            schema.name = name
        self.register(schema)

    def register_event(
        self, event_type: type, name: str | None = None
    ) -> None:
        """Register an event schema from a Python dataclass.

        Args:
            event_type: The dataclass type to register
            name: Optional name override (defaults to class name)
        """
        schema = Schema.from_dataclass(event_type, "event")
        if name:
            schema.name = name
        self.register(schema)

    def register_action(
        self, action_type: type, name: str | None = None
    ) -> None:
        """Register an action schema from a Python dataclass.

        Args:
            action_type: The dataclass type to register
            name: Optional name override (defaults to class name)
        """
        schema = Schema.from_dataclass(action_type, "action")
        if name:
            schema.name = name
        self.register(schema)

    def register_from_yaml(self, filepath: str | Path) -> None:
        """Register schemas from a YAML file.

        The YAML file can contain 'components', 'events', and/or 'actions'
        sections, each with schema definitions.

        Args:
            filepath: Path to the YAML file

        Example YAML:
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
        """
        schemas = load_schemas_from_yaml(filepath)
        for schema in schemas:
            self.register(schema)

    def get(self, name: str) -> Schema:
        """Get a schema by name.

        Args:
            name: Name of the schema

        Returns:
            The schema

        Raises:
            KeyError: If no schema with this name exists
        """
        if name not in self._schemas:
            raise KeyError(f"No schema named '{name}' found")
        return self._schemas[name]

    def has(self, name: str) -> bool:
        """Check if a schema exists.

        Args:
            name: Name of the schema

        Returns:
            True if the schema exists, False otherwise
        """
        return name in self._schemas

    def list_schemas(
        self, type: Literal["component", "event", "action"] | None = None
    ) -> list[str]:
        """List all registered schema names, optionally filtered by type.

        Args:
            type: Optional filter by schema type

        Returns:
            List of schema names

        Example:
            >>> registry.list_schemas(type="component")
            ["Health", "Position", "Sprite"]
        """
        if type is None:
            return sorted(self._schemas.keys())
        return sorted(name for name, schema in self._schemas.items() if schema.type == type)

    def validate(self, schema_name: str, data: dict) -> tuple[bool, list[str]]:
        """Validate data against a schema.

        Args:
            schema_name: Name of the schema to validate against
            data: Data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)

        Raises:
            KeyError: If no schema with this name exists
        """
        schema = self.get(schema_name)
        return schema.validate(data)

    def defaults(self, schema_name: str) -> dict:
        """Get default values for a schema.

        Args:
            schema_name: Name of the schema

        Returns:
            Dictionary of field names to default values

        Raises:
            KeyError: If no schema with this name exists
        """
        schema = self.get(schema_name)
        return schema.defaults()

    def to_dict(self) -> dict[str, dict]:
        """Convert all schemas to dictionary representation.

        Returns:
            Dictionary mapping schema names to their dict representations
        """
        return {name: schema.to_dict() for name, schema in self._schemas.items()}

    def to_json(self, indent: int | None = 2) -> str:
        """Export all schemas as JSON.

        This is the primary interface for AI agents to query the type system.

        Args:
            indent: JSON indentation (None for compact output)

        Returns:
            JSON string representation

        Example:
            >>> json_str = registry.to_json()
            >>> # AI agent can now parse and understand all schemas
        """
        return json.dumps(self.to_dict(), indent=indent)

    def clear(self) -> None:
        """Remove all registered schemas.

        Useful for testing or reinitializing the registry.
        """
        self._schemas.clear()

    def __len__(self) -> int:
        """Get the number of registered schemas."""
        return len(self._schemas)

    def __contains__(self, name: str) -> bool:
        """Check if a schema exists (supports 'in' operator)."""
        return name in self._schemas

    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"SchemaRegistry(schemas={len(self._schemas)})"
