"""Turn order strategies for determining player sequence.

Provides various strategies for managing turn order in turn-based games.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class TurnState:
    """Current state of the turn system.

    Attributes:
        current_player: Index of the current player
        current_round: Current round number
        current_turn: Current turn number within the round
        player_count: Total number of players
        custom_data: Strategy-specific data storage
    """
    current_player: int = 0
    current_round: int = 0
    current_turn: int = 0
    player_count: int = 0
    custom_data: dict = None

    def __post_init__(self) -> None:
        if self.custom_data is None:
            self.custom_data = {}


class TurnOrderStrategy(ABC):
    """Base class for turn order strategies."""

    @abstractmethod
    def get_next_player(self, state: TurnState) -> int:
        """Determine the next player to act.

        Args:
            state: Current turn state

        Returns:
            Player index (0-based)
        """
        pass

    @abstractmethod
    def initialize(self, player_count: int) -> None:
        """Initialize the strategy with the number of players.

        Args:
            player_count: Total number of players in the game
        """
        pass

    def reset(self) -> None:
        """Reset strategy to initial state (optional hook)."""
        pass


class AlternatingOrder(TurnOrderStrategy):
    """Two players take turns alternating.

    Example: Player 0, Player 1, Player 0, Player 1, ...
    """

    def __init__(self) -> None:
        self.player_count: int = 0

    def initialize(self, player_count: int) -> None:
        """Initialize for two-player alternating turns.

        Args:
            player_count: Must be 2 for alternating order

        Raises:
            ValueError: If player_count is not 2
        """
        if player_count != 2:
            raise ValueError("AlternatingOrder requires exactly 2 players")
        self.player_count = player_count

    def get_next_player(self, state: TurnState) -> int:
        """Alternate between players 0 and 1.

        Args:
            state: Current turn state

        Returns:
            Next player index (0 or 1)
        """
        return (state.current_player + 1) % self.player_count


class ClockwiseOrder(TurnOrderStrategy):
    """Players take turns in clockwise order (multiplayer board game style).

    Example: Player 0, Player 1, Player 2, Player 0, Player 1, Player 2, ...
    """

    def __init__(self) -> None:
        self.player_count: int = 0

    def initialize(self, player_count: int) -> None:
        """Initialize with the number of players.

        Args:
            player_count: Total number of players

        Raises:
            ValueError: If player_count is less than 2
        """
        if player_count < 2:
            raise ValueError("ClockwiseOrder requires at least 2 players")
        self.player_count = player_count

    def get_next_player(self, state: TurnState) -> int:
        """Get the next player in clockwise order.

        Args:
            state: Current turn state

        Returns:
            Next player index
        """
        return (state.current_player + 1) % self.player_count


class InitiativeOrder(TurnOrderStrategy):
    """Players act based on initiative values (RPG/tactical combat style).

    Higher initiative acts first. Order is recalculated each round.
    """

    def __init__(self, get_initiative: Callable[[int], int]) -> None:
        """Initialize with initiative getter function.

        Args:
            get_initiative: Function that returns initiative value for a player index
        """
        self.get_initiative = get_initiative
        self.player_count: int = 0
        self.turn_order: list[int] = []
        self.current_index: int = 0

    def initialize(self, player_count: int) -> None:
        """Initialize with the number of players.

        Args:
            player_count: Total number of players

        Raises:
            ValueError: If player_count is less than 1
        """
        if player_count < 1:
            raise ValueError("InitiativeOrder requires at least 1 player")
        self.player_count = player_count
        self._calculate_turn_order()

    def _calculate_turn_order(self) -> None:
        """Calculate turn order based on initiative values."""
        # Create list of (player_index, initiative) tuples
        initiatives = [(i, self.get_initiative(i)) for i in range(self.player_count)]
        # Sort by initiative (descending), then by player index (ascending) for ties
        initiatives.sort(key=lambda x: (-x[1], x[0]))
        # Extract just the player indices
        self.turn_order = [player for player, _ in initiatives]
        self.current_index = 0

    def get_next_player(self, state: TurnState) -> int:
        """Get the next player based on initiative order.

        Args:
            state: Current turn state

        Returns:
            Next player index
        """
        # Recalculate turn order at the start of each round
        if state.current_turn == 0:
            self._calculate_turn_order()

        self.current_index = (self.current_index + 1) % len(self.turn_order)
        return self.turn_order[self.current_index]

    def reset(self) -> None:
        """Reset to first player in initiative order."""
        self.current_index = 0


class SimultaneousOrder(TurnOrderStrategy):
    """All players act simultaneously, then resolve together.

    In this model, all players plan their actions, then they all execute.
    This is common in simultaneous turn-based games.
    """

    def __init__(self) -> None:
        self.player_count: int = 0
        self._all_players_acted: bool = False
        self._current_acting_player: int = 0

    def initialize(self, player_count: int) -> None:
        """Initialize with the number of players.

        Args:
            player_count: Total number of players

        Raises:
            ValueError: If player_count is less than 1
        """
        if player_count < 1:
            raise ValueError("SimultaneousOrder requires at least 1 player")
        self.player_count = player_count
        self._all_players_acted = False
        self._current_acting_player = 0

    def get_next_player(self, state: TurnState) -> int:
        """Get the next player in simultaneous mode.

        In simultaneous mode, this cycles through all players for input,
        then all actions resolve together.

        Args:
            state: Current turn state

        Returns:
            Next player index, or 0 after all have acted
        """
        self._current_acting_player = (self._current_acting_player + 1) % self.player_count

        # If we've cycled back to player 0, all players have acted
        if self._current_acting_player == 0:
            self._all_players_acted = True

        return self._current_acting_player

    def all_players_acted(self) -> bool:
        """Check if all players have provided their input.

        Returns:
            True if all players have acted this round
        """
        return self._all_players_acted

    def reset(self) -> None:
        """Reset for the next simultaneous round."""
        self._all_players_acted = False
        self._current_acting_player = 0


class CustomOrder(TurnOrderStrategy):
    """Custom turn order defined by a user-provided function.

    Allows for arbitrary turn order logic.
    """

    def __init__(self, get_next_player_fn: Callable[[TurnState], int]) -> None:
        """Initialize with custom next player function.

        Args:
            get_next_player_fn: Function that determines the next player
        """
        self.get_next_player_fn = get_next_player_fn
        self.player_count: int = 0

    def initialize(self, player_count: int) -> None:
        """Initialize with the number of players.

        Args:
            player_count: Total number of players

        Raises:
            ValueError: If player_count is less than 1
        """
        if player_count < 1:
            raise ValueError("CustomOrder requires at least 1 player")
        self.player_count = player_count

    def get_next_player(self, state: TurnState) -> int:
        """Get the next player using custom logic.

        Args:
            state: Current turn state

        Returns:
            Next player index as determined by custom function
        """
        return self.get_next_player_fn(state)
