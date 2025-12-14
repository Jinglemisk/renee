"""Example demonstrating the Schema Registry.

This example shows how to:
1. Define schemas in YAML
2. Register schemas from Python dataclasses
3. Query and introspect schemas
4. Validate data against schemas
5. Export schemas for AI consumption
"""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from renee.schema import SchemaRegistry


def main():
    """Run the Schema Registry example."""
    print("=" * 70)
    print("Renee Schema Registry Example")
    print("=" * 70)
    print()

    # Create a registry
    registry = SchemaRegistry()

    # Example 1: Define schemas in YAML
    print("1. Loading schemas from YAML")
    print("-" * 70)

    yaml_content = """
components:
  Health:
    intent: "Tracks entity hit points with regeneration"
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
        description: "Maximum hit points"
      regen_rate:
        type: int
        default: 0
        constraints:
          min: 0
        description: "HP regenerated per turn"
    invariants:
      - "current <= max"
      - "current >= 0"

  Position:
    intent: "Entity location on 2D grid"
    fields:
      x:
        type: int
        default: 0
      y:
        type: int
        default: 0

events:
  DamageEvent:
    intent: "Emitted when entity takes damage"
    fields:
      entity_id:
        type: EntityId
        description: "Entity that took damage"
      amount:
        type: int
        constraints:
          min: 0
        description: "Amount of damage dealt"
      source_id:
        type: EntityId
        default: null
        description: "Entity that caused the damage (optional)"
"""

    # Save to temporary file and load
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        registry.register_from_yaml(temp_path)
        print(f"Loaded {len(registry)} schemas from YAML")
        print()
    finally:
        Path(temp_path).unlink()

    # Example 2: Register from Python dataclass
    print("2. Registering schemas from Python dataclasses")
    print("-" * 70)

    @dataclass
    class Sprite:
        """Visual representation of an entity"""
        image: str = "default.png"
        scale: float = 1.0
        rotation: float = 0.0

    @dataclass
    class MoveAction:
        """Move an entity to a new position"""
        entity_id: int
        target_x: int
        target_y: int

    registry.register_component(Sprite)
    registry.register_action(MoveAction)
    print(f"Registered Sprite component and MoveAction")
    print(f"Total schemas: {len(registry)}")
    print()

    # Example 3: Query schemas
    print("3. Querying schemas")
    print("-" * 70)

    # List all component schemas
    components = registry.list_schemas(type="component")
    print(f"Components: {', '.join(components)}")

    # List all event schemas
    events = registry.list_schemas(type="event")
    print(f"Events: {', '.join(events)}")

    # List all action schemas
    actions = registry.list_schemas(type="action")
    print(f"Actions: {', '.join(actions)}")
    print()

    # Example 4: Introspect a schema
    print("4. Introspecting the Health schema")
    print("-" * 70)

    health = registry.get("Health")
    print(f"Name: {health.name}")
    print(f"Type: {health.type}")
    print(f"Intent: {health.intent}")
    print()
    print("Fields:")
    for field_name, field_def in health.fields.items():
        print(f"  {field_name}:")
        print(f"    Type: {field_def.type}")
        if field_def.default is not None:
            print(f"    Default: {field_def.default}")
        if field_def.constraints:
            print(f"    Constraints: {field_def.constraints}")
        if field_def.description:
            print(f"    Description: {field_def.description}")
    print()
    print(f"Invariants: {health.invariants}")
    print()

    # Example 5: Get default values
    print("5. Getting default values")
    print("-" * 70)

    health_defaults = registry.defaults("Health")
    print(f"Health defaults: {health_defaults}")

    sprite_defaults = registry.defaults("Sprite")
    print(f"Sprite defaults: {sprite_defaults}")
    print()

    # Example 6: Validate data
    print("6. Validating data against schemas")
    print("-" * 70)

    # Valid data
    valid_health = {"current": 75, "max": 100, "regen_rate": 5}
    is_valid, errors = registry.validate("Health", valid_health)
    print(f"Validating {valid_health}")
    print(f"  Valid: {is_valid}")
    print()

    # Invalid data (current > max)
    invalid_health = {"current": 150, "max": 100, "regen_rate": 5}
    is_valid, errors = registry.validate("Health", invalid_health)
    print(f"Validating {invalid_health}")
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {errors}")
    print()

    # Missing required field
    incomplete_move = {"entity_id": 42, "target_x": 10}
    is_valid, errors = registry.validate("MoveAction", incomplete_move)
    print(f"Validating {incomplete_move}")
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {errors}")
    print()

    # Example 7: Export for AI consumption
    print("7. Exporting schemas for AI agents")
    print("-" * 70)

    # Export all schemas as JSON
    json_output = registry.to_json(indent=2)

    # Show a snippet
    print("Sample JSON output (DamageEvent):")
    all_schemas = json.loads(json_output)
    damage_event = all_schemas["DamageEvent"]
    print(json.dumps({"DamageEvent": damage_event}, indent=2))
    print()

    # AI-friendly queries
    print("AI can now ask questions like:")
    print("  - 'What components are available?'")
    print(f"    Answer: {registry.list_schemas(type='component')}")
    print()
    print("  - 'What fields does Position have?'")
    pos_fields = list(registry.get("Position").fields.keys())
    print(f"    Answer: {pos_fields}")
    print()
    print("  - 'What is the purpose of Health?'")
    print(f"    Answer: {registry.get('Health').intent}")
    print()

    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
