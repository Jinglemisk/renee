"""Tests for ECS World."""

from dataclasses import dataclass

import pytest

from renee import World, Position, EntityId


@dataclass
class Health:
    """Test component for health."""
    current: int
    max: int


@dataclass
class Name:
    """Test component for names."""
    value: str


class TestWorldEntityLifecycle:
    """Tests for entity creation and destruction."""

    def test_create_entity(self) -> None:
        world = World()
        entity = world.create_entity()
        assert world.entity_exists(entity)

    def test_create_multiple_entities(self) -> None:
        world = World()
        e1 = world.create_entity()
        e2 = world.create_entity()
        e3 = world.create_entity()
        # IDs should be unique
        assert e1 != e2 != e3
        assert world.entity_count() == 3

    def test_destroy_entity(self) -> None:
        world = World()
        entity = world.create_entity()
        world.destroy_entity(entity)
        assert not world.entity_exists(entity)
        assert world.entity_count() == 0

    def test_destroy_nonexistent_entity_raises(self) -> None:
        world = World()
        with pytest.raises(KeyError):
            world.destroy_entity(EntityId(999))

    def test_entity_ids_never_reused(self) -> None:
        world = World()
        e1 = world.create_entity()
        world.destroy_entity(e1)
        e2 = world.create_entity()
        # e2 should NOT be the same ID as e1
        assert e1 != e2


class TestWorldComponents:
    """Tests for component operations."""

    def test_add_and_get_component(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(x=5, y=3))

        pos = world.get_component(entity, Position)
        assert pos.x == 5
        assert pos.y == 3

    def test_add_multiple_components(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(x=0, y=0))
        world.add_component(entity, Health(current=100, max=100))
        world.add_component(entity, Name(value="Player"))

        assert world.get_component(entity, Position) == Position(0, 0)
        assert world.get_component(entity, Health).current == 100
        assert world.get_component(entity, Name).value == "Player"

    def test_replace_component(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(x=0, y=0))
        world.add_component(entity, Position(x=5, y=5))  # Replace

        pos = world.get_component(entity, Position)
        assert pos == Position(5, 5)

    def test_remove_component(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(x=0, y=0))
        world.remove_component(entity, Position)

        assert not world.has_component(entity, Position)

    def test_has_component(self) -> None:
        world = World()
        entity = world.create_entity()

        assert not world.has_component(entity, Position)
        world.add_component(entity, Position(x=0, y=0))
        assert world.has_component(entity, Position)

    def test_get_component_or_none(self) -> None:
        world = World()
        entity = world.create_entity()

        assert world.get_component_or_none(entity, Position) is None
        world.add_component(entity, Position(x=1, y=2))
        assert world.get_component_or_none(entity, Position) == Position(1, 2)

    def test_get_nonexistent_component_raises(self) -> None:
        world = World()
        entity = world.create_entity()

        with pytest.raises(KeyError):
            world.get_component(entity, Position)

    def test_add_component_to_nonexistent_entity_raises(self) -> None:
        world = World()
        with pytest.raises(KeyError):
            world.add_component(EntityId(999), Position(x=0, y=0))

    def test_get_all_components(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(x=0, y=0))
        world.add_component(entity, Health(current=50, max=100))

        components = world.get_all_components(entity)
        assert len(components) == 2
        assert Position in components
        assert Health in components

    def test_destroying_entity_removes_components(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(x=0, y=0))
        world.destroy_entity(entity)

        # After destruction, has_component should return False
        assert not world.has_component(entity, Position)


class TestWorldQueries:
    """Tests for entity queries."""

    def test_query_single_component(self) -> None:
        world = World()
        e1 = world.create_entity()
        e2 = world.create_entity()
        e3 = world.create_entity()

        world.add_component(e1, Position(x=0, y=0))
        world.add_component(e2, Position(x=1, y=1))
        # e3 has no Position

        result = list(world.query(Position))
        assert len(result) == 2
        assert e1 in result
        assert e2 in result
        assert e3 not in result

    def test_query_multiple_components(self) -> None:
        world = World()
        e1 = world.create_entity()
        e2 = world.create_entity()
        e3 = world.create_entity()

        world.add_component(e1, Position(x=0, y=0))
        world.add_component(e1, Health(current=100, max=100))

        world.add_component(e2, Position(x=1, y=1))
        # e2 has no Health

        world.add_component(e3, Health(current=50, max=50))
        # e3 has no Position

        result = list(world.query(Position, Health))
        assert len(result) == 1
        assert e1 in result

    def test_query_empty_result(self) -> None:
        world = World()
        world.create_entity()
        world.create_entity()

        result = list(world.query(Position))
        assert len(result) == 0

    def test_all_entities(self) -> None:
        world = World()
        e1 = world.create_entity()
        e2 = world.create_entity()

        result = list(world.all_entities())
        assert len(result) == 2
        assert e1 in result
        assert e2 in result


class TestIntegration:
    """Integration tests showing typical usage patterns."""

    def test_basic_game_setup(self) -> None:
        """Test a typical game setup scenario."""
        world = World()

        # Create player
        player = world.create_entity()
        world.add_component(player, Position(x=0, y=0))
        world.add_component(player, Health(current=100, max=100))
        world.add_component(player, Name(value="Hero"))

        # Create enemies
        enemies = []
        for i in range(3):
            enemy = world.create_entity()
            world.add_component(enemy, Position(x=i + 5, y=i + 5))
            world.add_component(enemy, Health(current=30, max=30))
            enemies.append(enemy)

        # Verify setup
        assert world.entity_count() == 4

        # Query all entities with position and health (for combat system)
        combatants = list(world.query(Position, Health))
        assert len(combatants) == 4

        # Simulate damage to an enemy
        target = enemies[0]
        hp = world.get_component(target, Health)
        world.add_component(target, Health(current=hp.current - 10, max=hp.max))

        new_hp = world.get_component(target, Health)
        assert new_hp.current == 20

    def test_movement_pattern(self) -> None:
        """Test moving an entity by replacing its Position component."""
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(x=0, y=0))

        # Move the entity
        old_pos = world.get_component(entity, Position)
        new_pos = Position(old_pos.x + 1, old_pos.y + 2)
        world.add_component(entity, new_pos)

        result = world.get_component(entity, Position)
        assert result == Position(1, 2)
