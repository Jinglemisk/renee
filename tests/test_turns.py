"""Tests for turn management."""

from renee.turns import Phase, TurnManager
from renee.types import EntityId


class TestTurnManager:
    def test_clockwise_order(self) -> None:
        tm = TurnManager([EntityId(1), EntityId(2), EntityId(3)])
        assert tm.current_player() == EntityId(1)
        tm.advance_turn()
        assert tm.current_player() == EntityId(2)
        tm.advance_turn()
        assert tm.current_player() == EntityId(3)
        tm.advance_turn()
        assert tm.current_player() == EntityId(1)

    def test_round_increments_on_wrap(self) -> None:
        tm = TurnManager([EntityId(1), EntityId(2)])
        assert tm.round_number == 0
        tm.advance_turn()  # -> player 2
        tm.advance_turn()  # -> back to player 1
        assert tm.round_number == 1

    def test_phase_and_auto_advance(self) -> None:
        tm = TurnManager(
            [EntityId(1), EntityId(2)],
            phases=[Phase("main", traits=frozenset({"single_action"})), Phase("cleanup")],
            auto_advance=True,
        )
        assert tm.current_phase().name == "main"
        tm.on_action_completed()
        assert tm.current_phase().name == "cleanup"
        tm.on_action_completed()
        assert tm.current_player() == EntityId(2)
