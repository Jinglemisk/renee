"""Tests for spatial helpers."""

from renee.spatial import Grid
from renee.types import Position


class TestGrid:
    def test_a_star_basic(self) -> None:
        grid = Grid(5, 5)
        path = grid.a_star(Position(0, 0), Position(4, 0))
        assert path[0] == Position(0, 0)
        assert path[-1] == Position(4, 0)
        assert len(path) == 5

    def test_a_star_respects_blocked(self) -> None:
        grid = Grid(5, 5)
        grid.set_blocked(Position(1, 0), True)
        grid.set_blocked(Position(2, 0), True)
        grid.set_blocked(Position(3, 0), True)
        path = grid.a_star(Position(0, 0), Position(4, 0))
        assert path  # still possible by going around
        assert Position(1, 0) not in path

    def test_line_of_sight(self) -> None:
        grid = Grid(5, 5)
        assert grid.line_of_sight(Position(0, 0), Position(4, 4))
        grid.set_blocked(Position(2, 2), True)
        assert not grid.line_of_sight(Position(0, 0), Position(4, 4))

    def test_tiles_in_manhattan_range(self) -> None:
        grid = Grid(5, 5)
        tiles = grid.tiles_in_manhattan_range(Position(2, 2), 1)
        assert Position(2, 2) in tiles
        assert Position(3, 2) in tiles
        assert Position(4, 4) not in tiles

