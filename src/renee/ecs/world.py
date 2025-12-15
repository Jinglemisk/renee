"""Entity-Component-System World implementation.

The World is the container for all entities and their components.
It provides the core ECS operations: create, destroy, add, remove, get, query.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator, TypeVar

from renee.events import EventBus
from renee.types import EntityId

T = TypeVar("T")

SpawnHook = Callable[[EntityId], None]
DestroyHook = Callable[[EntityId], None]
ComponentHook = Callable[[EntityId, type, Any], None]
ComponentRemoveHook = Callable[[EntityId, type], None]


@dataclass(frozen=True, slots=True)
class WorldSnapshot:
    """A complete snapshot of World state for rollback."""

    next_id: int
    entities: frozenset[EntityId]
    components: dict[EntityId, dict[type, object]]
    tags: dict[EntityId, set[str]]
    intents: dict[EntityId, str]


class World:
    """The ECS World - container for all entities and components.

    Entities are just IDs (integers). Components are data attached to entities.
    The World manages the lifecycle and storage of both.

    Storage model: Entity-centric (dict[entity_id, dict[component_type, component]])
    This optimizes for "get all components of entity" over "get all entities with component".

    Example:
        world = World()
        player = world.create_entity()
        world.add_component(player, Position(x=0, y=0))
        pos = world.get_component(player, Position)
    """

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        self._next_id: int = 0
        self._entities: set[EntityId] = set()
        self._components: dict[EntityId, dict[type, object]] = {}
        self._tags: dict[EntityId, set[str]] = {}
        self._intents: dict[EntityId, str] = {}

        # Hooks
        self._on_spawn: list[SpawnHook] = []
        self._on_destroy: list[DestroyHook] = []
        self._on_component_added: list[ComponentHook] = []
        self._on_component_removed: list[ComponentRemoveHook] = []

        # Event bus integration
        self._bus = event_bus

        # Entity templates (from renee-claude)
        self._templates: dict[str, dict[str, Any]] = {}

        # Named snapshots (from renee-claude)
        self._snapshots: dict[str, WorldSnapshot] = {}

    def create_entity(self) -> EntityId:
        """Create a new entity and return its ID.

        Entity IDs are never reused to avoid the ABA problem
        (old references pointing to new entities).
        """
        eid = EntityId(self._next_id)
        self._next_id += 1
        self._entities.add(eid)
        self._components[eid] = {}
        self._tags[eid] = set()
        return eid

    def create_entity_with_id(self, entity: EntityId) -> EntityId:
        """Create an entity with an explicit ID (useful for multiplayer sync)."""

        if entity in self._entities:
            raise KeyError(f"Entity {entity} already exists")
        self._entities.add(entity)
        self._components[entity] = {}
        self._tags[entity] = set()
        self._next_id = max(self._next_id, int(entity) + 1)
        return entity

    def spawn(
        self,
        components: Iterable[object] = (),
        *,
        tags: Iterable[str] = (),
        intent: str | None = None,
    ) -> EntityId:
        """Create an entity with initial components/tags/intent and call hooks."""

        eid = self.create_entity()
        for component in components:
            self.add_component(eid, component)
        for tag in tags:
            self.add_tag(eid, tag)
        if intent is not None:
            self.set_intent(eid, intent)
        self._emit_lifecycle("entity_spawned", eid)
        for hook in list(self._on_spawn):
            hook(eid)
        return eid

    def destroy_entity(self, entity: EntityId) -> None:
        """Remove an entity and all its components.

        Raises:
            KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        self._emit_lifecycle("entity_destroyed", entity)
        for hook in list(self._on_destroy):
            hook(entity)
        self._entities.discard(entity)
        del self._components[entity]
        del self._tags[entity]
        self._intents.pop(entity, None)

    def entity_exists(self, entity: EntityId) -> bool:
        """Check if an entity exists."""
        return entity in self._entities

    def on_spawn(self, hook: SpawnHook) -> None:
        self._on_spawn.append(hook)

    def on_destroy(self, hook: DestroyHook) -> None:
        self._on_destroy.append(hook)

    def add_component(self, entity: EntityId, component: object) -> None:
        """Attach a component to an entity.

        If the entity already has a component of this type, it is replaced.

        Raises:
            KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        component_type = type(component)
        self._components[entity][component_type] = component
        # Call component added hooks
        for hook in self._on_component_added:
            hook(entity, component_type, component)

    def remove_component(self, entity: EntityId, component_type: type) -> None:
        """Remove a component from an entity.

        Raises:
            KeyError: If entity does not exist or does not have the component.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        if component_type not in self._components[entity]:
            raise KeyError(f"Entity {entity} does not have component {component_type.__name__}")
        del self._components[entity][component_type]
        # Call component removed hooks
        for hook in self._on_component_removed:
            hook(entity, component_type)

    def get_component(self, entity: EntityId, component_type: type[T]) -> T:
        """Get a component from an entity.

        Raises:
            KeyError: If entity does not exist or does not have the component.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        if component_type not in self._components[entity]:
            raise KeyError(f"Entity {entity} does not have component {component_type.__name__}")
        return self._components[entity][component_type]  # type: ignore[return-value]

    def has_component(self, entity: EntityId, component_type: type) -> bool:
        """Check if an entity has a specific component type."""
        if entity not in self._entities:
            return False
        return component_type in self._components[entity]

    def get_component_or_none(self, entity: EntityId, component_type: type[T]) -> T | None:
        """Get a component from an entity, or None if not present."""
        if entity not in self._entities:
            return None
        return self._components[entity].get(component_type)  # type: ignore[return-value]

    def query(self, *component_types: type, tags: set[str] | None = None) -> Iterator[EntityId]:
        """Get all entities that have ALL specified component types.

        This is O(n) where n is the number of entities. For hot paths,
        consider caching the results.

        Example:
            for entity in world.query(Position, Health):
                pos = world.get_component(entity, Position)
                hp = world.get_component(entity, Health)
        """
        for entity in self._entities:
            entity_components = self._components[entity]
            if not all(ct in entity_components for ct in component_types):
                continue
            if tags is not None and not tags.issubset(self._tags.get(entity, set())):
                continue
            yield entity

    def all_entities(self) -> Iterator[EntityId]:
        """Iterate over all existing entities."""
        for entity in self._entities:
            yield entity

    def entity_count(self) -> int:
        """Return the number of existing entities."""
        return len(self._entities)

    def get_all_components(self, entity: EntityId) -> dict[type, object]:
        """Get all components attached to an entity.

        Returns a copy to prevent external mutation.

        Raises:
            KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        return dict(self._components[entity])

    def add_tag(self, entity: EntityId, tag: str) -> None:
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        self._tags[entity].add(tag)

    def remove_tag(self, entity: EntityId, tag: str) -> None:
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        self._tags[entity].discard(tag)

    def has_tag(self, entity: EntityId, tag: str) -> bool:
        return entity in self._entities and tag in self._tags.get(entity, set())

    def tags(self, entity: EntityId) -> set[str]:
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        return set(self._tags[entity])

    def set_intent(self, entity: EntityId, intent: str) -> None:
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        self._intents[entity] = intent

    def get_intent(self, entity: EntityId) -> str | None:
        if entity not in self._entities:
            return None
        return self._intents.get(entity)

    def snapshot(self) -> WorldSnapshot:
        """Capture a complete snapshot suitable for rollback."""

        return WorldSnapshot(
            next_id=self._next_id,
            entities=frozenset(self._entities),
            components=copy.deepcopy(self._components),
            tags=copy.deepcopy(self._tags),
            intents=dict(self._intents),
        )

    def restore(self, snapshot: WorldSnapshot) -> None:
        """Restore the world to a previous snapshot."""

        self._next_id = snapshot.next_id
        self._entities = set(snapshot.entities)
        self._components = copy.deepcopy(snapshot.components)
        self._tags = copy.deepcopy(snapshot.tags)
        self._intents = dict(snapshot.intents)

    def _emit_lifecycle(self, event_type: str, entity: EntityId) -> None:
        if self._bus is None:
            return
        self._bus.emit(event_type, {"entity": entity})

    # ==================== Component Hooks ====================

    def on_component_added(self, hook: ComponentHook) -> None:
        """Register a hook to be called when a component is added."""
        self._on_component_added.append(hook)

    def on_component_removed(self, hook: ComponentRemoveHook) -> None:
        """Register a hook to be called when a component is removed."""
        self._on_component_removed.append(hook)

    # ==================== Named Snapshots ====================

    def save_snapshot(self, name: str | None = None) -> str:
        """Save a snapshot with an optional name.

        Args:
            name: Optional name for the snapshot. If None, a UUID is generated.

        Returns:
            The name/id of the saved snapshot.
        """
        snapshot_id = name if name is not None else str(uuid.uuid4())
        self._snapshots[snapshot_id] = self.snapshot()
        return snapshot_id

    def load_snapshot(self, name: str) -> None:
        """Load a previously saved snapshot by name.

        Raises:
            KeyError: If snapshot does not exist.
        """
        if name not in self._snapshots:
            raise KeyError(f"Snapshot '{name}' does not exist")
        self.restore(self._snapshots[name])

    def list_snapshots(self) -> list[str]:
        """List all saved snapshot names."""
        return list(self._snapshots.keys())

    def delete_snapshot(self, name: str) -> None:
        """Delete a saved snapshot.

        Raises:
            KeyError: If snapshot does not exist.
        """
        if name not in self._snapshots:
            raise KeyError(f"Snapshot '{name}' does not exist")
        del self._snapshots[name]

    # ==================== Entity Templates ====================

    def register_template(self, name: str, template: dict[str, Any]) -> None:
        """Register an entity template.

        Template format:
            {
                "components": {
                    "Position": {"x": 0, "y": 0},
                    "UnitStats": {"strength": 10, "armor": 5}
                },
                "tags": ["hostile", "ground_unit"],
                "intent": "A basic opposing unit"
            }

        Args:
            name: Unique template identifier.
            template: Template definition with "components", "tags", and optionally "intent".
        """
        self._templates[name] = copy.deepcopy(template)

    def get_template(self, name: str) -> dict[str, Any]:
        """Get a template by name.

        Raises:
            KeyError: If template does not exist.
        """
        if name not in self._templates:
            raise KeyError(f"Template '{name}' does not exist")
        return copy.deepcopy(self._templates[name])

    def list_templates(self) -> list[str]:
        """List all registered template names."""
        return list(self._templates.keys())

    def spawn_from_template(
        self, name: str, overrides: dict[str, Any] | None = None
    ) -> EntityId:
        """Create an entity from a registered template.

        Args:
            name: Template name.
            overrides: Optional dict to override template values.
                      Format: {"components": {"Position": {"x": 5}}, "tags": ["special"]}

        Returns:
            EntityId of the newly created entity.

        Raises:
            KeyError: If template does not exist.

        Note:
            Components are stored as dicts. In a real game, you'd want to
            instantiate actual component classes from the schema registry.
        """
        if name not in self._templates:
            raise KeyError(f"Template '{name}' does not exist")

        template = copy.deepcopy(self._templates[name])

        # Apply overrides
        if overrides:
            if "components" in overrides:
                for comp_name, comp_overrides in overrides["components"].items():
                    if comp_name in template.get("components", {}):
                        template["components"][comp_name].update(comp_overrides)
                    else:
                        template.setdefault("components", {})[comp_name] = comp_overrides
            if "tags" in overrides:
                template.setdefault("tags", []).extend(overrides["tags"])
            if "intent" in overrides:
                template["intent"] = overrides["intent"]

        # Create entity
        entity = self.create_entity()

        # Add components (as dicts for now - schema registry would convert these)
        for comp_name, comp_data in template.get("components", {}).items():
            self.add_component(entity, comp_data)

        # Add tags
        for tag in template.get("tags", []):
            self.add_tag(entity, tag)

        # Set intent
        if "intent" in template:
            self.set_intent(entity, template["intent"])

        # Emit lifecycle event and call hooks
        self._emit_lifecycle("entity_spawned", entity)
        for hook in list(self._on_spawn):
            hook(entity)

        return entity

    # ==================== Bulk Operations ====================

    def destroy_all(self) -> None:
        """Remove all entities from the world."""
        # Copy to avoid mutation during iteration
        for entity in list(self._entities):
            self.destroy_entity(entity)

    def destroy_by_tag(self, tag: str) -> int:
        """Destroy all entities with a specific tag.

        Returns:
            Number of entities destroyed.
        """
        entities_to_destroy = list(self.query_by_tag(tag))
        for entity in entities_to_destroy:
            self.destroy_entity(entity)
        return len(entities_to_destroy)

    def clone_entity(self, entity: EntityId) -> EntityId:
        """Create a deep copy of an entity with all its components and tags.

        Returns:
            EntityId of the cloned entity.

        Raises:
            KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")

        # Create new entity
        clone = self.create_entity()

        # Deep copy all components
        for component_type, component in self._components[entity].items():
            cloned_component = copy.deepcopy(component)
            self._components[clone][component_type] = cloned_component
            # Call component added hooks
            for hook in self._on_component_added:
                hook(clone, component_type, cloned_component)

        # Copy all tags
        self._tags[clone] = self._tags[entity].copy()

        # Copy intent if present
        if entity in self._intents:
            self._intents[clone] = self._intents[entity]

        # Emit lifecycle and call hooks
        self._emit_lifecycle("entity_spawned", clone)
        for hook in list(self._on_spawn):
            hook(clone)

        return clone

    # ==================== Query by Tag ====================

    def query_by_tag(self, tag: str) -> Iterator[EntityId]:
        """Get all entities that have a specific tag."""
        for entity in self._entities:
            if tag in self._tags.get(entity, set()):
                yield entity

    # ==================== Serialization ====================

    def to_dict(self) -> dict[str, Any]:
        """Serialize world state to a dictionary (for JSON export).

        Returns:
            Dictionary containing all world state.

        Note:
            Components must be serializable (e.g., dataclasses, dicts).
        """
        import dataclasses

        serialized_components: dict[int, dict[str, Any]] = {}
        for entity_id, components in self._components.items():
            serialized_components[int(entity_id)] = {}
            for comp_type, comp_data in components.items():
                comp_name = comp_type.__name__
                # Try to convert to dict if it's a dataclass
                if hasattr(comp_data, "__dataclass_fields__"):
                    serialized_components[int(entity_id)][comp_name] = dataclasses.asdict(comp_data)
                elif isinstance(comp_data, dict):
                    serialized_components[int(entity_id)][comp_name] = comp_data
                else:
                    # Fallback: store as-is and hope it's serializable
                    serialized_components[int(entity_id)][comp_name] = comp_data

        return {
            "next_id": self._next_id,
            "entities": list(self._entities),
            "components": serialized_components,
            "tags": {int(eid): list(tags) for eid, tags in self._tags.items()},
            "intents": {int(eid): intent for eid, intent in self._intents.items()},
            "templates": self._templates,
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Load world state from a dictionary (from JSON import).

        This completely replaces the current world state.
        Lifecycle hooks are NOT triggered during loading.

        Args:
            data: Dictionary containing world state (from to_dict()).
        """
        self._next_id = data["next_id"]
        self._entities = set(EntityId(e) for e in data["entities"])

        # Restore components (as dicts for now)
        self._components = {}
        for entity_id_str, components in data["components"].items():
            entity_id = EntityId(int(entity_id_str))
            self._components[entity_id] = {}
            for comp_name, comp_data in components.items():
                # Store as dict - in real usage, you'd reconstruct actual component types
                self._components[entity_id][type(comp_data)] = comp_data

        # Restore tags
        self._tags = {}
        for entity_id_str, tags in data["tags"].items():
            entity_id = EntityId(int(entity_id_str))
            self._tags[entity_id] = set(tags)

        # Restore intents
        self._intents = {}
        for entity_id_str, intent in data.get("intents", {}).items():
            entity_id = EntityId(int(entity_id_str))
            self._intents[entity_id] = intent

        # Restore templates
        if "templates" in data:
            self._templates = data["templates"]
