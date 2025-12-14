"""Turn manager.

This is intentionally minimal but flexible:
- supports turn order strategies
- supports phases with simple traits
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol, Sequence

from renee.types import EntityId


@dataclass(frozen=True, slots=True)
class Phase:
    name: str
    traits: frozenset[str] = frozenset()

    def has(self, trait: str) -> bool:
        return trait in self.traits


class TurnOrderStrategy(Protocol):
    def next_index(self, *, players: Sequence[EntityId], current_index: int) -> int: ...


class ClockwiseOrder:
    def next_index(self, *, players: Sequence[EntityId], current_index: int) -> int:
        if not players:
            raise ValueError("players must be non-empty")
        return (current_index + 1) % len(players)


class TurnManager:
    """Keeps track of whose turn it is and which phase is active."""

    def __init__(
        self,
        players: Sequence[EntityId],
        *,
        phases: Sequence[Phase] = (Phase("main"),),
        order: TurnOrderStrategy | Literal["clockwise"] = "clockwise",
        auto_advance: bool = True,
    ) -> None:
        if not players:
            raise ValueError("TurnManager requires at least one player")
        if not phases:
            raise ValueError("TurnManager requires at least one phase")

        self.players: list[EntityId] = list(players)
        self.phases: list[Phase] = list(phases)
        self.current_player_index: int = 0
        self.current_phase_index: int = 0
        self.turn_number: int = 0
        self.round_number: int = 0
        self.auto_advance = auto_advance

        self._order: TurnOrderStrategy = ClockwiseOrder() if order == "clockwise" else order

    def current_player(self) -> EntityId:
        return self.players[self.current_player_index]

    def current_phase(self) -> Phase:
        return self.phases[self.current_phase_index]

    def is_players_turn(self, player: EntityId) -> bool:
        return player == self.current_player()

    def advance_phase(self) -> None:
        self.current_phase_index += 1
        if self.current_phase_index >= len(self.phases):
            self.current_phase_index = 0
            self.advance_turn()

    def advance_turn(self) -> None:
        previous_index = self.current_player_index
        self.current_player_index = self._order.next_index(
            players=self.players, current_index=self.current_player_index
        )
        self.turn_number += 1
        if self.current_player_index == 0 and previous_index != 0:
            self.round_number += 1

    def on_action_completed(self) -> None:
        if not self.auto_advance:
            return
        phase = self.current_phase()
        if phase.has("unlimited_actions"):
            return
        self.advance_phase()

    def to_dict(self) -> dict[str, Any]:
        return {
            "players": [int(p) for p in self.players],
            "phases": [{"name": p.name, "traits": sorted(p.traits)} for p in self.phases],
            "current_player_index": self.current_player_index,
            "current_phase_index": self.current_phase_index,
            "turn_number": self.turn_number,
            "round_number": self.round_number,
            "auto_advance": self.auto_advance,
            "order": "clockwise",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TurnManager":
        players = [EntityId(int(p)) for p in data.get("players", [])]
        phases = [
            Phase(name=str(p["name"]), traits=frozenset(p.get("traits", [])))
            for p in data.get("phases", [])
        ] or [Phase("main")]
        tm = cls(players, phases=phases, auto_advance=bool(data.get("auto_advance", True)))
        tm.current_player_index = int(data.get("current_player_index", 0))
        tm.current_phase_index = int(data.get("current_phase_index", 0))
        tm.turn_number = int(data.get("turn_number", 0))
        tm.round_number = int(data.get("round_number", 0))
        return tm
