"""Tests for semantic types."""

import random

import pytest

from renee.types import DiceRoll, Duration, Formula, Position, Probability


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


class TestProbability:
    def test_valid_probability(self) -> None:
        assert Probability(0.0) == 0.0
        assert Probability(0.5) == 0.5
        assert Probability(1.0) == 1.0

    def test_invalid_probability_raises(self) -> None:
        with pytest.raises(ValueError):
            Probability(-0.1)
        with pytest.raises(ValueError):
            Probability(1.1)


class TestDiceRoll:
    def test_parse(self) -> None:
        assert DiceRoll.parse("2d6+3") == DiceRoll(count=2, sides=6, modifier=3)
        assert DiceRoll.parse("1d20") == DiceRoll(count=1, sides=20, modifier=0)
        assert DiceRoll.parse("4d8-2") == DiceRoll(count=4, sides=8, modifier=-2)

    def test_roll_deterministic(self) -> None:
        rng = random.Random(123)
        d = DiceRoll.parse("2d6+1")
        assert d.roll(rng) == 4 + 1  # deterministic for seed 123


class TestDuration:
    def test_parse(self) -> None:
        assert Duration.parse("3") == Duration(turns=3)
        assert Duration.parse("3 turn") == Duration(turns=3)
        assert Duration.parse("3 turns") == Duration(turns=3)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            Duration(turns=-1)


class TestFormula:
    def test_evaluate(self) -> None:
        f = Formula("base + level * 2")
        assert f.evaluate({"base": 10, "level": 3}) == 16.0

    def test_disallow_unknown_name(self) -> None:
        f = Formula("missing + 1")
        with pytest.raises(NameError):
            f.evaluate({})
