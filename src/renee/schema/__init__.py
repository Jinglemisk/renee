"""Schema Registry for runtime-queryable type definitions.

The Schema Registry allows AI agents to understand game structure by
providing introspectable component, event, and action schemas.
"""

from renee.schema.registry import SchemaRegistry
from renee.schema.schema import Schema, FieldDefinition

__all__ = [
    "SchemaRegistry",
    "Schema",
    "FieldDefinition",
]
