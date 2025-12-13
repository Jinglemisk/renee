"""Tests for semantic types."""

from renee.types import Position


class TestPosition:
    """Tests for Position type."""

    def test_create_position(self) -> None:
        pos = Position(x=5, y=3)
        assert pos.x == 5
        assert pos.y == 3

    def test_position_immutable(self) -> None:
        pos = Position(x=5, y=3)
        # Position is frozen, so this should raise
        try:
            pos.x = 10  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass  # Expected

    def test_position_add(self) -> None:
        a = Position(1, 2)
        b = Position(3, 4)
        result = a + b
        assert result == Position(4, 6)

    def test_position_subtract(self) -> None:
        a = Position(5, 7)
        b = Position(2, 3)
        result = a - b
        assert result == Position(3, 4)

    def test_manhattan_distance(self) -> None:
        a = Position(0, 0)
        b = Position(3, 4)
        assert a.manhattan_distance(b) == 7

    def test_chebyshev_distance(self) -> None:
        a = Position(0, 0)
        b = Position(3, 4)
        assert a.chebyshev_distance(b) == 4

    def test_position_equality(self) -> None:
        a = Position(1, 2)
        b = Position(1, 2)
        c = Position(1, 3)
        assert a == b
        assert a != c

    def test_position_hashable(self) -> None:
        # Positions should be usable as dict keys / set members
        positions = {Position(0, 0), Position(1, 1), Position(0, 0)}
        assert len(positions) == 2
