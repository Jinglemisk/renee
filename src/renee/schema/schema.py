"""Schema and FieldDefinition classes for type definitions.

These classes represent the structure of components, events, and actions,
allowing runtime introspection and validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


@dataclass(slots=True)
class FieldDefinition:
    """Definition of a single field in a schema.

    Attributes:
        name: Field name
        type: Python type name (e.g., 'int', 'str', 'Position')
        default: Default value for the field (None if required)
        constraints: Optional constraints (e.g., min, max, pattern)
        description: Optional human-readable description
    """

    name: str
    type: str
    default: Any = None
    constraints: dict[str, Any] = field(default_factory=dict)
    description: str | None = None

    def validate_value(self, value: Any) -> tuple[bool, str | None]:
        """Validate a value against this field's constraints.

        Args:
            value: The value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check type compatibility (basic check)
        if value is None and self.default is None:
            return False, f"Field '{self.name}' is required"

        # Type validation
        type_validators = {
            "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "str": lambda v: isinstance(v, str),
            "bool": lambda v: isinstance(v, bool),
            "list": lambda v: isinstance(v, list),
            "dict": lambda v: isinstance(v, dict),
        }

        validator = type_validators.get(self.type)
        if validator and not validator(value):
            return False, f"Field '{self.name}' expected type {self.type}, got {type(value).__name__}"

        # Constraint validation
        if "min" in self.constraints:
            if value < self.constraints["min"]:
                return False, f"Field '{self.name}' value {value} is less than minimum {self.constraints['min']}"

        if "max" in self.constraints:
            if value > self.constraints["max"]:
                return False, f"Field '{self.name}' value {value} exceeds maximum {self.constraints['max']}"

        if "min_length" in self.constraints:
            if len(value) < self.constraints["min_length"]:
                return False, f"Field '{self.name}' length {len(value)} is less than minimum {self.constraints['min_length']}"

        if "max_length" in self.constraints:
            if len(value) > self.constraints["max_length"]:
                return False, f"Field '{self.name}' length {len(value)} exceeds maximum {self.constraints['max_length']}"

        if "pattern" in self.constraints:
            import re
            if not re.match(self.constraints["pattern"], str(value)):
                return False, f"Field '{self.name}' does not match pattern {self.constraints['pattern']}"

        return True, None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.constraints:
            result["constraints"] = self.constraints
        if self.description:
            result["description"] = self.description
        return result


@dataclass(slots=True)
class Schema:
    """Schema definition for a component, event, or action.

    Attributes:
        name: Schema name (e.g., 'Health', 'DamageEvent')
        type: Schema type ('component', 'event', or 'action')
        fields: Dictionary of field definitions keyed by field name
        intent: Optional natural language description of purpose
        invariants: Optional list of invariant expressions that must hold
    """

    name: str
    type: Literal["component", "event", "action"]
    fields: dict[str, FieldDefinition] = field(default_factory=dict)
    intent: str | None = None
    invariants: list[str] = field(default_factory=list)

    def validate(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate data against this schema.

        Args:
            data: Dictionary of field values

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: list[str] = []

        # Check for missing required fields
        for field_name, field_def in self.fields.items():
            if field_name not in data and field_def.default is None:
                errors.append(f"Missing required field: {field_name}")

        # Check for unknown fields
        for key in data.keys():
            if key not in self.fields:
                errors.append(f"Unknown field: {key}")

        # Validate each field value
        for field_name, value in data.items():
            if field_name in self.fields:
                is_valid, error = self.fields[field_name].validate_value(value)
                if not is_valid and error:
                    errors.append(error)

        # TODO: Validate invariants (would require expression evaluation)
        # For now, we just note them but don't validate them

        return len(errors) == 0, errors

    def defaults(self) -> dict[str, Any]:
        """Get default values for all fields.

        Returns:
            Dictionary of field names to default values
        """
        return {
            field_name: field_def.default
            for field_name, field_def in self.fields.items()
            if field_def.default is not None
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for JSON serialization.

        Returns:
            Dictionary representation of this schema
        """
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "fields": {name: field_def.to_dict() for name, field_def in self.fields.items()},
        }
        if self.intent:
            result["intent"] = self.intent
        if self.invariants:
            result["invariants"] = self.invariants
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Schema:
        """Create a Schema from a dictionary.

        Args:
            data: Dictionary containing schema definition

        Returns:
            Schema instance
        """
        fields_data = data.get("fields", {})
        fields = {
            name: FieldDefinition(
                name=name,
                type=field_data.get("type", "str"),
                default=field_data.get("default"),
                constraints=field_data.get("constraints", {}),
                description=field_data.get("description"),
            )
            for name, field_data in fields_data.items()
        }

        return cls(
            name=data["name"],
            type=data["type"],
            fields=fields,
            intent=data.get("intent"),
            invariants=data.get("invariants", []),
        )

    @classmethod
    def from_dataclass(cls, dataclass_type: type, schema_type: Literal["component", "event", "action"]) -> Schema:
        """Create a Schema from a Python dataclass.

        Args:
            dataclass_type: The dataclass type to introspect
            schema_type: Type of schema ('component', 'event', or 'action')

        Returns:
            Schema instance
        """
        import dataclasses
        import typing

        if not dataclasses.is_dataclass(dataclass_type):
            raise ValueError(f"{dataclass_type.__name__} is not a dataclass")

        fields: dict[str, FieldDefinition] = {}

        for dc_field in dataclasses.fields(dataclass_type):
            # Get type name
            type_hint = dc_field.type
            type_name = cls._get_type_name(type_hint)

            # Get default value
            default_value = None
            if dc_field.default is not dataclasses.MISSING:
                default_value = dc_field.default
            elif dc_field.default_factory is not dataclasses.MISSING:
                default_value = dc_field.default_factory()

            fields[dc_field.name] = FieldDefinition(
                name=dc_field.name,
                type=type_name,
                default=default_value,
                constraints={},
                description=None,
            )

        # Extract intent from docstring if available
        intent = None
        if dataclass_type.__doc__:
            intent = dataclass_type.__doc__.strip()

        return cls(
            name=dataclass_type.__name__,
            type=schema_type,
            fields=fields,
            intent=intent,
            invariants=[],
        )

    @staticmethod
    def _get_type_name(type_hint: Any) -> str:
        """Extract a readable type name from a type hint.

        Args:
            type_hint: The type hint to process

        Returns:
            String representation of the type
        """
        import typing

        # Handle basic types
        if type_hint in (int, float, str, bool):
            return type_hint.__name__

        # Handle typing constructs
        origin = typing.get_origin(type_hint)
        if origin is not None:
            if origin is list:
                return "list"
            elif origin is dict:
                return "dict"
            elif origin is tuple:
                return "tuple"
            elif origin is typing.Union:
                # For Optional[X] or Union[X, Y], get the first non-None type
                args = typing.get_args(type_hint)
                for arg in args:
                    if arg is not type(None):
                        return Schema._get_type_name(arg)
                return "Any"

        # For custom types, use the name
        if hasattr(type_hint, "__name__"):
            return type_hint.__name__

        # Fallback
        return str(type_hint)
