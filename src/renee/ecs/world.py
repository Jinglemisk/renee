"""Entity-Component-System World implementation.

The World is the container for all entities and their components.
It provides the core ECS operations: create, destroy, add, remove, get, query.
"""

import copy
import uuid
from typing import Any, Callable, Iterator, TypeVar

from renee.types import EntityId

T = TypeVar("T")


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

    def __init__(self) -> None:
        self._next_id: int = 0
        self._entities: set[int] = set()
        self._components: dict[int, dict[type, object]] = {}

        # Entity tags
        self._tags: dict[int, set[str]] = {}

        # Entity templates
        self._templates: dict[str, dict] = {}

        # Snapshots
        self._snapshots: dict[str, dict[str, Any]] = {}

        # Lifecycle hooks
        self.on_entity_created: list[Callable[[EntityId], None]] = []
        self.on_entity_destroyed: list[Callable[[EntityId], None]] = []
        self.on_component_added: list[Callable[[EntityId, type, Any], None]] = []
        self.on_component_removed: list[Callable[[EntityId, type], None]] = []

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

        # Trigger lifecycle hooks
        for callback in self.on_entity_created:
            callback(eid)

        return eid

    def destroy_entity(self, entity: EntityId) -> None:
        """Remove an entity and all its components.

        Raises:
            KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")

        # Trigger lifecycle hooks
        for callback in self.on_entity_destroyed:
            callback(entity)

        self._entities.discard(entity)
        del self._components[entity]
        del self._tags[entity]

    def entity_exists(self, entity: EntityId) -> bool:
        """Check if an entity exists."""
        return entity in self._entities

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

        # Trigger lifecycle hooks
        for callback in self.on_component_added:
            callback(entity, component_type, component)

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

        # Trigger lifecycle hooks
        for callback in self.on_component_removed:
            callback(entity, component_type)

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

    def query(self, *component_types: type) -> Iterator[EntityId]:
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
            if all(ct in entity_components for ct in component_types):
                yield EntityId(entity)

    def all_entities(self) -> Iterator[EntityId]:
        """Iterate over all existing entities."""
        for entity in self._entities:
            yield EntityId(entity)

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

    # ==================== Entity Tags ====================

    def add_tag(self, entity: EntityId, tag: str) -> None:
        """Add a tag to an entity.

        Raises:
            KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        self._tags[entity].add(tag)

    def remove_tag(self, entity: EntityId, tag: str) -> None:
        """Remove a tag from an entity.

        Raises:
            KeyError: If entity does not exist or does not have the tag.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        if tag not in self._tags[entity]:
            raise KeyError(f"Entity {entity} does not have tag '{tag}'")
        self._tags[entity].discard(tag)

    def has_tag(self, entity: EntityId, tag: str) -> bool:
        """Check if an entity has a specific tag."""
        if entity not in self._entities:
            return False
        return tag in self._tags[entity]

    def get_tags(self, entity: EntityId) -> set[str]:
        """Get all tags attached to an entity.

        Returns a copy to prevent external mutation.

        Raises:
            KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        return set(self._tags[entity])

    def query_by_tag(self, tag: str) -> Iterator[EntityId]:
        """Get all entities that have a specific tag."""
        for entity in self._entities:
            if tag in self._tags[entity]:
                yield EntityId(entity)

    # ==================== Entity Templates ====================

    def register_template(self, name: str, template: dict) -> None:
        """Register an entity template.

        Template format:
            {
                "components": {
                    "Position": {"x": 0, "y": 0},
                    "Health": {"current": 100, "max": 100}
                },
                "tags": ["enemy", "goblin"]
            }

        Args:
            name: Unique template identifier.
            template: Template definition with "components" and optionally "tags".
        """
        self._templates[name] = copy.deepcopy(template)

    def spawn_from_template(self, name: str, overrides: dict | None = None) -> EntityId:
        """Create an entity from a registered template.

        Args:
            name: Template name.
            overrides: Optional dict to override template values.
                      Format: {"components": {"Position": {"x": 5}}, "tags": ["special"]}

        Returns:
            EntityId of the newly created entity.

        Raises:
            KeyError: If template does not exist.
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

        # Create entity
        entity = self.create_entity()

        # Add components
        for comp_name, comp_data in template.get("components", {}).items():
            # Component data could be a dict (we'll leave it as a dict for now)
            # In a real system, you'd want to instantiate the actual component class
            self.add_component(entity, comp_data)

        # Add tags
        for tag in template.get("tags", []):
            self.add_tag(entity, tag)

        return entity

    # ==================== Bulk Operations ====================

    def destroy_all(self) -> None:
        """Remove all entities from the world."""
        # Copy to avoid mutation during iteration
        for entity in list(self._entities):
            self.destroy_entity(EntityId(entity))

    def destroy_by_tag(self, tag: str) -> None:
        """Destroy all entities with a specific tag."""
        entities_to_destroy = list(self.query_by_tag(tag))
        for entity in entities_to_destroy:
            self.destroy_entity(entity)

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
            # Bypass add_component to avoid triggering hooks twice
            self._components[clone][component_type] = cloned_component
            # But still trigger the hook for the clone
            for callback in self.on_component_added:
                callback(clone, component_type, cloned_component)

        # Copy all tags
        self._tags[clone] = self._tags[entity].copy()

        return clone

    # ==================== Snapshot/Rollback ====================

    def snapshot(self) -> str:
        """Save complete world state and return a snapshot ID.

        Returns:
            Unique snapshot identifier.
        """
        snapshot_id = str(uuid.uuid4())

        # Deep copy all world state
        snapshot_data = {
            "next_id": self._next_id,
            "entities": copy.deepcopy(self._entities),
            "components": copy.deepcopy(self._components),
            "tags": copy.deepcopy(self._tags),
        }

        self._snapshots[snapshot_id] = snapshot_data
        return snapshot_id

    def restore(self, snapshot_id: str) -> None:
        """Restore world to a previous snapshot.

        This completely replaces the current world state.
        Lifecycle hooks are NOT triggered during restoration.

        Raises:
            KeyError: If snapshot does not exist.
        """
        if snapshot_id not in self._snapshots:
            raise KeyError(f"Snapshot '{snapshot_id}' does not exist")

        snapshot_data = self._snapshots[snapshot_id]

        # Restore all state with deep copies for isolation
        self._next_id = snapshot_data["next_id"]
        self._entities = copy.deepcopy(snapshot_data["entities"])
        self._components = copy.deepcopy(snapshot_data["components"])
        self._tags = copy.deepcopy(snapshot_data["tags"])

    def list_snapshots(self) -> list[str]:
        """List all snapshot IDs."""
        return list(self._snapshots.keys())

    def delete_snapshot(self, snapshot_id: str) -> None:
        """Remove a snapshot.

        Raises:
            KeyError: If snapshot does not exist.
        """
        if snapshot_id not in self._snapshots:
            raise KeyError(f"Snapshot '{snapshot_id}' does not exist")
        del self._snapshots[snapshot_id]

    # ==================== Serialization ====================

    def to_dict(self) -> dict:
        """Serialize world state to a dictionary (for JSON export).

        Returns:
            Dictionary containing all world state.

        Note:
            Components must be serializable (e.g., dataclasses, dicts).
        """
        # Convert components to serializable format
        serialized_components = {}
        for entity_id, components in self._components.items():
            serialized_components[int(entity_id)] = {}
            for comp_type, comp_data in components.items():
                comp_name = comp_type.__name__
                # Try to convert to dict if it's a dataclass
                if hasattr(comp_data, "__dataclass_fields__"):
                    import dataclasses
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
            "templates": self._templates,
        }

    def from_dict(self, data: dict) -> None:
        """Load world state from a dictionary (from JSON import).

        This completely replaces the current world state.
        Lifecycle hooks are NOT triggered during loading.

        Args:
            data: Dictionary containing world state (from to_dict()).
        """
        self._next_id = data["next_id"]
        self._entities = set(data["entities"])

        # Restore components (as dicts for now)
        self._components = {}
        for entity_id_str, components in data["components"].items():
            entity_id = int(entity_id_str)
            self._components[entity_id] = {}
            for comp_name, comp_data in components.items():
                # Store as dict - in real usage, you'd want to reconstruct actual component types
                self._components[entity_id][type(comp_data)] = comp_data

        # Restore tags
        self._tags = {}
        for entity_id_str, tags in data["tags"].items():
            entity_id = int(entity_id_str)
            self._tags[entity_id] = set(tags)

        # Restore templates
        if "templates" in data:
            self._templates = data["templates"]
