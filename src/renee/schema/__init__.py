"""Schema registry and validation.

Schemas are runtime-queryable definitions for components, actions, and events.
They are typically loaded from YAML at boundaries and used to validate and
instantiate fast runtime dataclasses.
"""

from renee.schema.registry import (
    SchemaDefinition,
    SchemaField,
    SchemaKind,
    SchemaRegistry,
    ValidationIssue,
    ValidationReport,
)

__all__ = [
    "SchemaDefinition",
    "SchemaField",
    "SchemaKind",
    "SchemaRegistry",
    "ValidationIssue",
    "ValidationReport",
]

