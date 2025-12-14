"""Entity-Component-System World implementation.

The World is the container for all entities and their components.
It provides the core ECS operations: create, destroy, add, remove, get, query.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
from typing import Callable, Iterable, TypeVar

from renee.events import EventBus
from renee.types import EntityId

T = TypeVar("T")

SpawnHook = Callable[[EntityId], None]
DestroyHook = Callable[[EntityId], None]


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
        self._on_spawn: list[SpawnHook] = []
        self._on_destroy: list[DestroyHook] = []
        self._bus = event_bus

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
