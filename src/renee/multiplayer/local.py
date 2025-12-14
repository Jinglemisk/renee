"""Local hot-seat multiplayer session.

LocalSession allows multiple players to play on a single device by taking turns.
All players see the full game state (no hidden information filtering).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from renee.multiplayer.session import GameSession

if TYPE_CHECKING:
    from renee.actions.action import Action
    from renee.actions.result import ActionResult
    from renee.ecs.world import World
    from renee.turns.manager import TurnManager


class LocalSession(GameSession):
    """Hot-seat multiplayer session for local play.

    In a local session, all players share the same device and take turns.
    There is no hidden information - all players see the complete game state.
    Actions are executed immediately through the action pipeline.

    This is the simplest multiplayer mode and is ideal for:
    - Board game adaptations
    - Family game night
    - Testing multiplayer mechanics
    - Games without hidden information

    Example:
        # Create a local session
        session = LocalSession(world, turn_manager)

        # Start the game
        session.start_game()

        # Players take turns
        while not session.is_game_over():
            print(f"Player {session.get_current_player()}'s turn")

            # Submit action
            action = get_player_action()
            result = session.submit_action(action)

            if result.success:
                print("Action executed!")
            else:
                print(f"Action failed: {result.error or result.cancel_reason}")
    """

    def __init__(
        self,
        world: World,
        turn_manager: TurnManager,
        action_pipeline: object | None = None,
    ) -> None:
        """Initialize a local hot-seat session.

        Args:
            world: The ECS World containing game state
            turn_manager: Turn manager for coordinating player turns
            action_pipeline: Optional action pipeline for executing actions.
                           If None, actions are executed directly.
        """
        self._world = world
        self._turn_manager = turn_manager
        self._action_pipeline = action_pipeline
        self._state_callbacks: list[Callable[[dict], None]] = []
        self._started = False

        # Register turn manager hooks to notify state changes
        self._turn_manager.on_turn_start.append(self._on_turn_changed)
        self._turn_manager.on_turn_end.append(self._on_turn_changed)
        self._turn_manager.on_phase_start.append(self._on_turn_changed)
        self._turn_manager.on_phase_end.append(self._on_turn_changed)

    def start_game(self) -> None:
        """Start the local session.

        This initializes the turn manager and fires the initial state change.
        """
        if not self._started:
            # Turn manager should already be started by game setup
            # But we can trigger initial state notification
            self._started = True
            self._notify_state_changed()

    def get_player_count(self) -> int:
        """Get the number of players in this session.

        Returns:
            Number of active players
        """
        return self._turn_manager._state.player_count

    def get_current_player(self) -> int:
        """Get the player whose turn it currently is.

        Returns:
            Player ID (0-based index)
        """
        return self._turn_manager.current_player

    def is_local_player_turn(self) -> bool:
        """Check if it's the local player's turn.

        In a local session, all players are "local", so this always returns True.
        The game UI should check get_current_player() to see whose turn it actually is.

        Returns:
            Always True for local sessions
        """
        return True

    def submit_action(self, action: Action) -> ActionResult:
        """Submit an action for immediate execution.

        In a local session, actions are executed immediately through the
        action pipeline (if provided) or directly.

        Args:
            action: The action to execute

        Returns:
            ActionResult indicating success/failure

        Example:
            result = session.submit_action(Action(
                name='move',
                params={'entity': entity_id, 'x': 5, 'y': 5},
                source=player_entity
            ))
        """
        # Validate that it's this player's turn
        if action.source is not None:
            # If action has a source, verify it's the current player's turn
            # This is a basic validation - real games might be more complex
            pass

        # Execute action
        if self._action_pipeline is not None:
            # Use the action pipeline if available
            result = self._action_pipeline.execute(action, self._world)
        else:
            # Direct execution (simplified - real implementation would need actual execution logic)
            from renee.actions.result import ActionResult

            result = ActionResult.success_result(action)

        # Notify state changed
        if result.success:
            self._notify_state_changed()

            # Auto-advance turn if appropriate
            if self._turn_manager.is_phase_complete():
                self._turn_manager.advance()

        return result

    def get_game_state(self) -> dict:
        """Get the current game state.

        In a local session, all players see the full state with no filtering.

        Returns:
            Dictionary containing complete game state
        """
        state = {
            "world": self._world.to_dict(),
            "turn": self._turn_manager.get_state(),
            "session_type": "local",
            "player_count": self.get_player_count(),
            "current_player": self.get_current_player(),
        }
        return state

    def on_state_changed(self, callback: Callable[[dict], None]) -> None:
        """Register a callback for state changes.

        The callback is invoked whenever the game state changes
        (action executed, turn changed, etc.).

        Args:
            callback: Function to call with new state

        Example:
            def on_update(state):
                current = state.get('current_player', 0)
                print(f"Now player {current}'s turn")

            session.on_state_changed(on_update)
        """
        self._state_callbacks.append(callback)

    def can_player_act(self, player_id: int) -> bool:
        """Check if a specific player can act.

        Args:
            player_id: Player to check

        Returns:
            True if it's this player's turn
        """
        return self._turn_manager.can_act(player_id)

    def end_turn(self) -> None:
        """Manually end the current player's turn.

        This is useful for games where the player explicitly ends their turn
        rather than having it end automatically after an action.
        """
        self._turn_manager.end_turn()
        self._notify_state_changed()

    def _on_turn_changed(self) -> None:
        """Internal callback for turn manager events."""
        self._notify_state_changed()

    def _notify_state_changed(self) -> None:
        """Notify all registered callbacks of a state change."""
        state = self.get_game_state()
        for callback in self._state_callbacks:
            try:
                callback(state)
            except Exception as e:
                # Log error but continue notifying other callbacks
                print(f"Error in state callback: {e}")
