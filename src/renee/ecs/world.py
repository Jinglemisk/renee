"""Entity-Component-System World implementation.

The World is the container for all entities and their components.
It provides the core ECS operations: create, destroy, add, remove, get, query.
"""

from typing import Iterator, TypeVar

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

    def create_entity(self) -> EntityId:
        """Create a new entity and return its ID.

        Entity IDs are never reused to avoid the ABA problem
        (old references pointing to new entities).
        """
        eid = EntityId(self._next_id)
        self._next_id += 1
        self._entities.add(eid)
        self._components[eid] = {}
        return eid

    def destroy_entity(self, entity: EntityId) -> None:
        """Remove an entity and all its components.

        Raises:
            KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")
        self._entities.discard(entity)
        del self._components[entity]

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
        self._components[entity][type(component)] = component

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
