"""Base GameSession interface for multiplayer.

All multiplayer session types (local, network, async) implement this interface
for consistency and interchangeability.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from renee.actions.action import Action
    from renee.actions.result import ActionResult


class GameSession(ABC):
    """Base class for all multiplayer session types.

    A GameSession manages the multiplayer state of a game, including:
    - Player management (who's in the game, whose turn it is)
    - Action submission and validation
    - State synchronization (with visibility filtering)
    - Turn progression

    Different session types provide different multiplayer experiences:
    - LocalSession: Hot-seat play on one device
    - NetworkClient/NetworkServer: Real-time networked play
    - AsyncSession: Turn-based asynchronous play

    Example:
        # Create a session
        session = LocalSession(world, turn_manager)

        # Check whose turn it is
        if session.is_local_player_turn():
            # Submit an action
            result = session.submit_action(move_action)
            if result.success:
                print("Move successful!")

        # Get current game state (filtered for this player)
        state = session.get_game_state()
    """

    @abstractmethod
    def get_player_count(self) -> int:
        """Get the number of players in this session.

        Returns:
            Number of active players
        """
        pass

    @abstractmethod
    def get_current_player(self) -> int:
        """Get the player whose turn it currently is.

        Returns:
            Player ID of the current player
        """
        pass

    @abstractmethod
    def is_local_player_turn(self) -> bool:
        """Check if it's the local player's turn.

        For local sessions, this is always True (any player can act).
        For network sessions, this checks if it's this client's turn.

        Returns:
            True if the local player can act
        """
        pass

    @abstractmethod
    def submit_action(self, action: Action) -> ActionResult:
        """Submit an action for execution.

        The action is validated, executed, and the result is returned.
        Behavior varies by session type:
        - LocalSession: Immediate execution
        - NetworkClient: Sent to server for validation
        - AsyncSession: Saved for next state update

        Args:
            action: The action to execute

        Returns:
            ActionResult indicating success/failure

        Example:
            result = session.submit_action(Action(
                name='move',
                params={'entity': player_id, 'x': 5, 'y': 5}
            ))
        """
        pass

    @abstractmethod
    def get_game_state(self) -> dict:
        """Get the current game state.

        The state is filtered based on the session type and player:
        - LocalSession: Full state (all players see everything)
        - NetworkClient: Filtered state (hidden info removed)
        - AsyncSession: State for current player only

        Returns:
            Dictionary containing game state

        Example:
            state = session.get_game_state()
            entities = state.get('entities', {})
        """
        pass

    @abstractmethod
    def on_state_changed(self, callback: Callable[[dict], None]) -> None:
        """Register a callback for state changes.

        The callback is invoked whenever the game state changes
        (action executed, turn changed, etc.).

        Args:
            callback: Function to call with new state

        Example:
            def on_update(state):
                print(f"Turn: {state.get('turn', 0)}")

            session.on_state_changed(on_update)
        """
        pass

    def get_session_type(self) -> str:
        """Get the type of this session.

        Returns:
            Session type name ('local', 'network', 'async')
        """
        return self.__class__.__name__.replace("Session", "").lower()

    def is_game_over(self) -> bool:
        """Check if the game has ended.

        Default implementation returns False. Subclasses can override
        to provide game-specific win/loss detection.

        Returns:
            True if game is over
        """
        return False

    def get_winner(self) -> int | None:
        """Get the winning player (if game is over).

        Default implementation returns None. Subclasses can override
        to provide game-specific winner detection.

        Returns:
            Player ID of winner, or None if no winner yet
        """
        return None
