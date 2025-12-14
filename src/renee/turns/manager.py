"""Turn manager for coordinating game time flow.

Manages rounds, turns, phases, and player order in turn-based games.
"""

from typing import Callable, Optional
from dataclasses import dataclass, field

from .structure import TimeStructure, Phase
from .order import TurnOrderStrategy, TurnState


@dataclass
class TurnManagerState:
    """Internal state of the turn manager.

    Attributes:
        current_round: Current round number (0-based)
        current_turn: Current turn number within the round (0-based)
        current_phase_index: Index of the current phase (0-based)
        current_player: Index of the current player (0-based)
        actions_this_phase: Number of actions taken in current phase
        player_count: Total number of players
        phase_start_time: Timestamp when current phase started (for timed phases)
    """
    current_round: int = 0
    current_turn: int = 0
    current_phase_index: int = 0
    current_player: int = 0
    actions_this_phase: int = 0
    player_count: int = 0
    phase_start_time: Optional[float] = None


class TurnManager:
    """Manages the flow of time in a turn-based game.

    Coordinates rounds, turns, phases, and player order according to
    a defined time structure and turn order strategy.
    """

    def __init__(self, structure: TimeStructure, order: TurnOrderStrategy) -> None:
        """Initialize the turn manager.

        Args:
            structure: Time structure defining rounds, turns, phases
            order: Strategy for determining player turn order
        """
        self.structure = structure
        self.order = order
        self._state = TurnManagerState()

        # Event hooks
        self.on_turn_start: list[Callable] = []
        self.on_turn_end: list[Callable] = []
        self.on_phase_start: list[Callable] = []
        self.on_phase_end: list[Callable] = []
        self.on_round_start: list[Callable] = []
        self.on_round_end: list[Callable] = []

    # State Properties
    @property
    def current_round(self) -> int:
        """Get the current round number."""
        return self._state.current_round

    @property
    def current_turn(self) -> int:
        """Get the current turn number within the round."""
        return self._state.current_turn

    @property
    def current_phase(self) -> Phase:
        """Get the current phase object."""
        return self.structure.phases[self._state.current_phase_index]

    @property
    def current_player(self) -> int:
        """Get the current player index."""
        return self._state.current_player

    @property
    def actions_this_phase(self) -> int:
        """Get the number of actions taken in the current phase."""
        return self._state.actions_this_phase

    # Control Methods
    def start_game(self, player_count: int) -> None:
        """Start a new game with the specified number of players.

        Args:
            player_count: Number of players in the game

        Raises:
            ValueError: If player_count is invalid
        """
        if player_count < 1:
            raise ValueError("player_count must be at least 1")

        self._state = TurnManagerState(player_count=player_count)
        self.order.initialize(player_count)

        # Fire initial hooks
        self._fire_hooks(self.on_round_start)
        self._fire_hooks(self.on_turn_start)
        self._fire_hooks(self.on_phase_start)

    def end_phase(self) -> None:
        """End the current phase and advance to the next one."""
        self._fire_hooks(self.on_phase_end)

        # Move to next phase
        self._state.current_phase_index += 1
        self._state.actions_this_phase = 0
        self._state.phase_start_time = None

        # Check if we've completed all phases (end of turn)
        if self._state.current_phase_index >= len(self.structure.phases):
            self.end_turn()
        else:
            self._fire_hooks(self.on_phase_start)

    def end_turn(self) -> None:
        """End the current turn and advance to the next player."""
        self._fire_hooks(self.on_turn_end)

        # Reset phase to beginning
        self._state.current_phase_index = 0
        self._state.actions_this_phase = 0
        self._state.phase_start_time = None

        # Advance to next player
        turn_state = self._build_turn_state()
        self._state.current_player = self.order.get_next_player(turn_state)
        self._state.current_turn += 1

        # Check if we've completed a full round
        # (This is a simple implementation - games may define rounds differently)
        if self._state.current_turn % self._state.player_count == 0:
            self.end_round()
        else:
            self._fire_hooks(self.on_turn_start)
            self._fire_hooks(self.on_phase_start)

    def end_round(self) -> None:
        """End the current round and start a new one."""
        self._fire_hooks(self.on_round_end)

        self._state.current_round += 1
        self._state.current_turn = 0

        self._fire_hooks(self.on_round_start)
        self._fire_hooks(self.on_turn_start)
        self._fire_hooks(self.on_phase_start)

    def advance(self) -> None:
        """Automatically advance based on the current phase state.

        Advances the phase if it's complete, otherwise does nothing.
        """
        if self.is_phase_complete():
            self.end_phase()

    def skip_phase(self) -> bool:
        """Skip the current phase if it's skippable.

        Returns:
            True if phase was skipped, False if it couldn't be skipped
        """
        if self.current_phase.is_skippable():
            self.end_phase()
            return True
        return False

    def record_action(self) -> None:
        """Record that an action was taken in the current phase.

        This increments the action counter for phase completion logic.
        """
        self._state.actions_this_phase += 1

    # Query Methods
    def can_act(self, player: int) -> bool:
        """Check if a specific player can act in the current phase.

        Args:
            player: Player index to check

        Returns:
            True if the player can act
        """
        # Player must be the current player
        if player != self._state.current_player:
            return False

        # Check phase-specific action limits
        phase = self.current_phase

        if phase.is_single_action() and self._state.actions_this_phase >= 1:
            return False

        # Unlimited actions always allows acting
        if phase.allows_unlimited_actions():
            return True

        # Default: player can act
        return True

    def is_phase_complete(self) -> bool:
        """Check if the current phase is complete.

        Returns:
            True if the phase should end
        """
        phase = self.current_phase

        # Single action phases complete after one action
        if phase.is_single_action() and self._state.actions_this_phase >= 1:
            return True

        # Timed phases complete after duration (requires external timing)
        # This is a placeholder - actual implementation would check elapsed time
        if phase.is_timed() and self._state.phase_start_time is not None:
            # External systems should call end_phase() when time expires
            pass

        # Mandatory phases with no actions can complete immediately
        if phase.is_mandatory() and not phase.is_single_action():
            # May require at least one action, or can auto-complete
            # This is game-specific logic
            pass

        # By default, phases don't auto-complete
        # Games must explicitly call end_phase()
        return False

    def get_state(self) -> dict:
        """Get the current turn manager state as a JSON-serializable dict.

        Returns:
            Dictionary containing current state
        """
        return {
            "current_round": self._state.current_round,
            "current_turn": self._state.current_turn,
            "current_phase": self.current_phase.name,
            "current_phase_index": self._state.current_phase_index,
            "current_player": self._state.current_player,
            "actions_this_phase": self._state.actions_this_phase,
            "player_count": self._state.player_count,
            "phase_start_time": self._state.phase_start_time,
            "structure": self.structure.to_dict(),
        }

    def set_phase_start_time(self, timestamp: float) -> None:
        """Set the start time for the current phase (for timed phases).

        Args:
            timestamp: Timestamp when the phase started
        """
        self._state.phase_start_time = timestamp

    # Helper Methods
    def _build_turn_state(self) -> TurnState:
        """Build a TurnState object for the turn order strategy.

        Returns:
            TurnState with current game state
        """
        return TurnState(
            current_player=self._state.current_player,
            current_round=self._state.current_round,
            current_turn=self._state.current_turn,
            player_count=self._state.player_count,
        )

    def _fire_hooks(self, hooks: list[Callable]) -> None:
        """Fire all hooks in a list.

        Args:
            hooks: List of callable hooks to execute
        """
        for hook in hooks:
            try:
                hook()
            except Exception as e:
                # Log error but don't crash the turn system
                # In production, this should use proper logging
                print(f"Error in turn hook: {e}")

    # Additional utility methods
    def get_phase_by_name(self, name: str) -> Optional[Phase]:
        """Get a phase by its name.

        Args:
            name: Phase name to look up

        Returns:
            Phase object if found, None otherwise
        """
        return self.structure.get_phase(name)

    def jump_to_phase(self, phase_name: str) -> bool:
        """Jump directly to a specific phase.

        Args:
            phase_name: Name of the phase to jump to

        Returns:
            True if successful, False if phase not found
        """
        try:
            index = self.structure.get_phase_index(phase_name)
            self._fire_hooks(self.on_phase_end)
            self._state.current_phase_index = index
            self._state.actions_this_phase = 0
            self._state.phase_start_time = None
            self._fire_hooks(self.on_phase_start)
            return True
        except ValueError:
            return False

    def reset(self) -> None:
        """Reset the turn manager to initial state.

        Preserves player count but resets all counters.
        """
        player_count = self._state.player_count
        self._state = TurnManagerState(player_count=player_count)
        self.order.reset()

        # Fire initial hooks
        self._fire_hooks(self.on_round_start)
        self._fire_hooks(self.on_turn_start)
        self._fire_hooks(self.on_phase_start)
