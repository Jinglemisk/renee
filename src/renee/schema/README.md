# Schema Registry

The Schema Registry provides runtime-queryable type definitions that allow AI agents to understand game structure.

## Overview

The Schema Registry is a core feature of Renee's AI-native design. It enables:

- **Runtime Introspection**: AI agents can query "what fields does this component have?" and get authoritative answers
- **Type Validation**: Validate data against schemas before use
- **Intent Documentation**: Natural language descriptions of what each schema is meant to accomplish
- **Multiple Sources**: Load schemas from YAML files or Python dataclasses
- **JSON Export**: Export all schemas as JSON for AI consumption

## Quick Start

```python
from renee.schema import SchemaRegistry

# Create a registry
registry = SchemaRegistry()

# Load schemas from YAML
registry.register_from_yaml("schemas/components.yaml")

# Register from Python dataclass
from dataclasses import dataclass

@dataclass
class Position:
    x: int = 0
    y: int = 0

registry.register_component(Position)

# Query schemas
schema = registry.get("Health")
print(schema.intent)  # "Tracks entity hit points"
print(schema.fields)  # dict of FieldDefinition objects

# Validate data
is_valid, errors = schema.validate({"current": 50, "max": 100})

# Get defaults
defaults = schema.defaults()  # {"current": 100, "max": 100}

# List schemas by type
components = registry.list_schemas(type="component")

# Export for AI
json_str = registry.to_json()
```

## YAML Schema Format

Schemas can be defined in YAML files with the following structure:

```yaml
components:
  Health:
    intent: "Tracks entity hit points"
    fields:
      current:
        type: int
        default: 100
        constraints:
          min: 0
        description: "Current hit points"
      max:
        type: int
        default: 100
        constraints:
          min: 1
    invariants:
      - "current <= max"
      - "current >= 0"

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
```

### Field Definition

Each field can have:

- `type` (required): Type name (e.g., `int`, `str`, `Position`)
- `default` (optional): Default value (omit for required fields)
- `constraints` (optional): Validation constraints
  - `min`: Minimum value (for numbers)
  - `max`: Maximum value (for numbers)
  - `min_length`: Minimum length (for strings/lists)
  - `max_length`: Maximum length (for strings/lists)
  - `pattern`: Regex pattern (for strings)
- `description` (optional): Human-readable description

### Schema Attributes

Each schema can have:

- `intent` (optional): Natural language description of purpose
- `fields` (required): Dictionary of field definitions
- `invariants` (optional): List of invariant expressions that must hold

## Python API

### SchemaRegistry

```python
class SchemaRegistry:
    def __init__(self) -> None:
        """Initialize an empty schema registry."""

    def register(self, schema: Schema) -> None:
        """Register a schema."""

    def register_component(self, component_type: type, name: str | None = None) -> None:
        """Register a component schema from a Python dataclass."""

    def register_event(self, event_type: type, name: str | None = None) -> None:
        """Register an event schema from a Python dataclass."""

    def register_action(self, action_type: type, name: str | None = None) -> None:
        """Register an action schema from a Python dataclass."""

    def register_from_yaml(self, filepath: str | Path) -> None:
        """Register schemas from a YAML file."""

    def get(self, name: str) -> Schema:
        """Get a schema by name."""

    def has(self, name: str) -> bool:
        """Check if a schema exists."""

    def list_schemas(self, type: Literal["component", "event", "action"] | None = None) -> list[str]:
        """List all registered schema names, optionally filtered by type."""

    def validate(self, schema_name: str, data: dict) -> tuple[bool, list[str]]:
        """Validate data against a schema."""

    def defaults(self, schema_name: str) -> dict:
        """Get default values for a schema."""

    def to_dict(self) -> dict[str, dict]:
        """Convert all schemas to dictionary representation."""

    def to_json(self, indent: int | None = 2) -> str:
        """Export all schemas as JSON."""

    def clear(self) -> None:
        """Remove all registered schemas."""
```

### Schema

```python
@dataclass
class Schema:
    name: str
    type: Literal["component", "event", "action"]
    fields: dict[str, FieldDefinition]
    intent: str | None = None
    invariants: list[str] = field(default_factory=list)

    def validate(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate data against this schema."""

    def defaults(self) -> dict[str, Any]:
        """Get default values for all fields."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Schema:
        """Create a Schema from a dictionary."""

    @classmethod
    def from_dataclass(cls, dataclass_type: type, schema_type: Literal["component", "event", "action"]) -> Schema:
        """Create a Schema from a Python dataclass."""
```

### FieldDefinition

```python
@dataclass
class FieldDefinition:
    name: str
    type: str
    default: Any = None
    constraints: dict[str, Any] = field(default_factory=dict)
    description: str | None = None

    def validate_value(self, value: Any) -> tuple[bool, str | None]:
        """Validate a value against this field's constraints."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
```

## AI-Native Design

The Schema Registry embodies several AI-native principles:

### 1. Everything is Introspectable

AI agents don't need to guess what fields exist or what types they are. They can query:

```python
# What components exist?
components = registry.list_schemas(type="component")

# What fields does Health have?
health = registry.get("Health")
field_names = list(health.fields.keys())

# What constraints apply to a field?
current_field = health.fields["current"]
constraints = current_field.constraints  # {"min": 0}
```

### 2. Intent Fields Connect Design to Implementation

The `intent` field bridges high-level design goals and low-level implementation:

```python
health = registry.get("Health")
print(health.intent)  # "Tracks entity hit points"

# AI can compare:
# - What the intent says (track hit points)
# - What the implementation does (current/max fields with constraints)
# - Whether they align
```

### 3. Machine-Readable, Human-Friendly

Schemas export to clean JSON that both AI and humans can understand:

```json
{
  "Health": {
    "name": "Health",
    "type": "component",
    "intent": "Tracks entity hit points",
    "fields": {
      "current": {
        "name": "current",
        "type": "int",
        "default": 100,
        "constraints": {"min": 0}
      }
    }
  }
}
```

## Use Cases

### 1. AI Code Generation

When generating component code, AI can query valid schemas:

```python
# AI queries: "What are valid component names?"
components = registry.list_schemas(type="component")

# AI queries: "What fields does Position need?"
position = registry.get("Position")
fields = position.fields
```

### 2. Validation and Error Prevention

Before creating entities, validate component data:

```python
component_data = {"current": 50, "max": 100}
is_valid, errors = registry.validate("Health", component_data)

if not is_valid:
    print(f"Invalid data: {errors}")
```

### 3. Documentation Generation

Generate documentation from schemas:

```python
for schema_name in registry.list_schemas():
    schema = registry.get(schema_name)
    print(f"## {schema.name}")
    if schema.intent:
        print(f"{schema.intent}")
    print("\nFields:")
    for field_name, field_def in schema.fields.items():
        print(f"- {field_name} ({field_def.type}): {field_def.description}")
```

### 4. Interactive REPL

In a REPL, developers and AI can explore schemas:

```python
>>> registry.list_schemas(type="component")
['Health', 'Position', 'Sprite']

>>> registry.get("Health").intent
'Tracks entity hit points'

>>> registry.defaults("Health")
{'current': 100, 'max': 100}
```

## Examples

See `examples/schema_example.py` for a complete working example demonstrating:

- Loading schemas from YAML
- Registering from dataclasses
- Querying and introspection
- Validation
- JSON export
- AI-friendly queries

Run the example:

```bash
python examples/schema_example.py
```

## Testing

Comprehensive tests are available in `tests/test_schema.py`:

```bash
pytest tests/test_schema.py -v
```

## Design Decisions

### Why Separate from Pydantic Models?

While Pydantic provides excellent validation, the Schema Registry adds:

1. **Runtime Introspection**: Query schemas without instantiating objects
2. **Intent Documentation**: Natural language design goals
3. **Multiple Sources**: Load from YAML or Python
4. **AI-Optimized Export**: JSON format designed for AI consumption
5. **Game-Specific Semantics**: Component/Event/Action distinction

### Why Support Both YAML and Python?

- **YAML**: Great for data-first definitions, easy to edit, version control friendly
- **Python**: Great for code-first definitions, type safety, IDE support

Supporting both gives developers flexibility to choose the right tool for each use case.

## Future Enhancements

Potential future additions:

- [ ] Schema versioning and migration
- [ ] Cross-schema validation (invariants across multiple schemas)
- [ ] Schema inheritance/composition
- [ ] Auto-generation of Pydantic models from schemas
- [ ] CLI commands for schema introspection
- [ ] Schema visualization (diagrams)
