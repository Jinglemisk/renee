# Renee Development Timeline

## 2025-12-13

**Phase 0 + Phase 1.1 + Phase 1.3: Project Setup, Types, ECS Core**

- Created `pyproject.toml` with dependencies (pydantic, pyyaml, pytest, mypy, ruff)
- Implemented semantic types in `src/renee/types/core.py`:
  - `EntityId` — NewType wrapper for entity references
  - `Position` — immutable dataclass with vector math (`+`, `-`, manhattan/chebyshev distance)
- Implemented ECS World in `src/renee/ecs/world.py`:
  - Entity lifecycle: `create_entity()`, `destroy_entity()`, `entity_exists()`
  - Component operations: `add_component()`, `remove_component()`, `get_component()`, `has_component()`, `get_component_or_none()`
  - Queries: `query(*component_types)`, `all_entities()`, `get_all_components()`
  - Entity-centric storage model (dict[entity_id, dict[type, component]])
  - Non-reusing entity IDs to avoid ABA problem
- Created package structure with `__init__.py` exports
- Wrote 29 tests covering types and ECS operations (all passing)
