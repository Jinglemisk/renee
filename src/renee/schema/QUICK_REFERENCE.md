# Schema Registry Quick Reference

## Import

```python
from renee.schema import SchemaRegistry, Schema, FieldDefinition
```

## Create Registry

```python
registry = SchemaRegistry()
```

## Register Schemas

### From YAML

```python
registry.register_from_yaml("schemas/components.yaml")
```

### From Dataclass

```python
from dataclasses import dataclass

@dataclass
class Health:
    """Tracks entity hit points"""
    current: int = 100
    max: int = 100

registry.register_component(Health)
registry.register_event(DamageEvent)
registry.register_action(MoveAction)
```

### Manually

```python
schema = Schema(
    name="Health",
    type="component",
    fields={
        "current": FieldDefinition("current", "int", default=100),
        "max": FieldDefinition("max", "int", default=100),
    },
    intent="Tracks entity hit points",
)
registry.register(schema)
```

## Query Schemas

### Get Schema

```python
schema = registry.get("Health")
print(schema.intent)  # "Tracks entity hit points"
print(schema.fields)  # dict of FieldDefinition
```

### Check Existence

```python
if registry.has("Health"):
    # ...

if "Health" in registry:
    # ...
```

### List Schemas

```python
all_schemas = registry.list_schemas()
components = registry.list_schemas(type="component")
events = registry.list_schemas(type="event")
actions = registry.list_schemas(type="action")
```

## Validate Data

```python
is_valid, errors = registry.validate("Health", {"current": 50, "max": 100})
if not is_valid:
    print(f"Errors: {errors}")
```

## Get Defaults

```python
defaults = registry.defaults("Health")
# {"current": 100, "max": 100}
```

## Export

### To Dict

```python
schemas_dict = registry.to_dict()
```

### To JSON

```python
json_str = registry.to_json()
json_compact = registry.to_json(indent=None)
```

## YAML Schema Format

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
        description: "Current HP"
      max:
        type: int
        default: 100
        constraints:
          min: 1
    invariants:
      - "current <= max"
```

## Field Constraints

- `min`: Minimum value (numbers)
- `max`: Maximum value (numbers)
- `min_length`: Minimum length (strings/lists)
- `max_length`: Maximum length (strings/lists)
- `pattern`: Regex pattern (strings)

## Field Types

Built-in: `int`, `str`, `float`, `bool`, `list`, `dict`

Custom: `EntityId`, `Position`, `AssetRef`, etc.

## Common Patterns

### Component with Constraints

```python
@dataclass
class Health:
    current: int = 100
    max: int = 100

registry.register_component(Health)
```

### Event with Multiple Fields

```python
@dataclass
class DamageEvent:
    entity_id: int
    amount: int
    source_id: int | None = None

registry.register_event(DamageEvent)
```

### Action with Required Fields

```python
@dataclass
class MoveAction:
    entity_id: int
    target_x: int
    target_y: int

registry.register_action(MoveAction)
```

## Utility Methods

```python
len(registry)        # Number of schemas
registry.clear()     # Remove all schemas
str(registry)        # String representation
```

## Error Handling

```python
try:
    schema = registry.get("NonExistent")
except KeyError as e:
    print(f"Schema not found: {e}")

try:
    registry.register(duplicate_schema)
except ValueError as e:
    print(f"Already registered: {e}")
```

## AI Agent Workflow

```python
# 1. What components exist?
components = registry.list_schemas(type="component")

# 2. What fields does Health have?
health = registry.get("Health")
fields = list(health.fields.keys())

# 3. What's the purpose?
intent = health.intent

# 4. What are the defaults?
defaults = health.defaults()

# 5. Validate my data
is_valid, errors = health.validate(my_data)

# 6. Get full JSON for analysis
json_data = registry.to_json()
```
