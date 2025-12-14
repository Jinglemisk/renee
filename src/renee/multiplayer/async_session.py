"""Asynchronous multiplayer session for play-by-email style games.

AsyncSession allows players to take turns without being online simultaneously.
Game state is persisted between turns, and players are notified when it's their turn.
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from renee.multiplayer.session import GameSession

if TYPE_CHECKING:
    from renee.actions.action import Action
    from renee.actions.result import ActionResult
    from renee.ecs.world import World
    from renee.turns.manager import TurnManager


class AsyncStorage(ABC):
    """Abstract storage backend for async games.

    Async games need to persist state between sessions. This interface
    defines the operations needed to save/load game state and action history.

    Implementations can use:
    - File system (FileAsyncStorage)
    - Database (SQLAsyncStorage)
    - Cloud storage (S3AsyncStorage)
    - etc.
    """

    @abstractmethod
    def save_state(self, game_id: str, state: dict) -> None:
        """Save the current game state.

        Args:
            game_id: Unique game identifier
            state: Complete game state to save
        """
        pass

    @abstractmethod
    def load_state(self, game_id: str) -> dict | None:
        """Load game state.

        Args:
            game_id: Unique game identifier

        Returns:
            Game state dict, or None if not found
        """
        pass

    @abstractmethod
    def save_action(self, game_id: str, action: Action) -> None:
        """Save an action to the history.

        Args:
            game_id: Unique game identifier
            action: Action to save
        """
        pass

    @abstractmethod
    def get_action_history(self, game_id: str) -> list[Action]:
        """Get all actions for a game.

        Args:
            game_id: Unique game identifier

        Returns:
            List of actions in chronological order
        """
        pass

    @abstractmethod
    def list_games(self) -> list[str]:
        """List all game IDs in storage.

        Returns:
            List of game IDs
        """
        pass

    @abstractmethod
    def delete_game(self, game_id: str) -> None:
        """Delete a game and all its data.

        Args:
            game_id: Unique game identifier
        """
        pass

    @abstractmethod
    def get_metadata(self, game_id: str) -> dict | None:
        """Get game metadata (players, turn, etc.).

        Args:
            game_id: Unique game identifier

        Returns:
            Metadata dict, or None if not found
        """
        pass

    @abstractmethod
    def save_metadata(self, game_id: str, metadata: dict) -> None:
        """Save game metadata.

        Args:
            game_id: Unique game identifier
            metadata: Metadata to save
        """
        pass


class FileAsyncStorage(AsyncStorage):
    """File-based storage for async games.

    Stores each game in a separate directory with JSON files for:
    - state.json: Current game state
    - actions.json: Action history
    - metadata.json: Game metadata (players, turn, etc.)

    Example:
        storage = FileAsyncStorage("./games")
        storage.save_state("game-123", state)
    """

    def __init__(self, base_path: str | Path):
        """Initialize file storage.

        Args:
            base_path: Directory to store game data
        """
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _game_dir(self, game_id: str) -> Path:
        """Get the directory for a game.

        Args:
            game_id: Game identifier

        Returns:
            Path to game directory
        """
        game_dir = self._base_path / game_id
        game_dir.mkdir(parents=True, exist_ok=True)
        return game_dir

    def save_state(self, game_id: str, state: dict) -> None:
        """Save game state to state.json."""
        game_dir = self._game_dir(game_id)
        state_file = game_dir / "state.json"

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self, game_id: str) -> dict | None:
        """Load game state from state.json."""
        game_dir = self._game_dir(game_id)
        state_file = game_dir / "state.json"

        if not state_file.exists():
            return None

        with open(state_file, "r") as f:
            return json.load(f)

    def save_action(self, game_id: str, action: Action) -> None:
        """Append action to actions.json."""
        game_dir = self._game_dir(game_id)
        actions_file = game_dir / "actions.json"

        # Load existing actions
        actions = []
        if actions_file.exists():
            with open(actions_file, "r") as f:
                actions = json.load(f)

        # Append new action
        action_data = {
            "name": action.name,
            "params": action.params,
            "source": action.source,
            "timestamp": time.time(),
        }
        actions.append(action_data)

        # Save
        with open(actions_file, "w") as f:
            json.dump(actions, f, indent=2)

    def get_action_history(self, game_id: str) -> list[Action]:
        """Load all actions from actions.json."""
        from renee.actions.action import Action

        game_dir = self._game_dir(game_id)
        actions_file = game_dir / "actions.json"

        if not actions_file.exists():
            return []

        with open(actions_file, "r") as f:
            actions_data = json.load(f)

        return [
            Action(name=a["name"], params=a["params"], source=a.get("source"))
            for a in actions_data
        ]

    def list_games(self) -> list[str]:
        """List all game directories."""
        if not self._base_path.exists():
            return []

        return [d.name for d in self._base_path.iterdir() if d.is_dir()]

    def delete_game(self, game_id: str) -> None:
        """Delete a game directory and all its files."""
        import shutil

        game_dir = self._base_path / game_id
        if game_dir.exists():
            shutil.rmtree(game_dir)

    def get_metadata(self, game_id: str) -> dict | None:
        """Load game metadata from metadata.json."""
        game_dir = self._game_dir(game_id)
        metadata_file = game_dir / "metadata.json"

        if not metadata_file.exists():
            return None

        with open(metadata_file, "r") as f:
            return json.load(f)

    def save_metadata(self, game_id: str, metadata: dict) -> None:
        """Save game metadata to metadata.json."""
        game_dir = self._game_dir(game_id)
        metadata_file = game_dir / "metadata.json"

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)


class AsyncSession(GameSession):
    """Asynchronous multiplayer session.

    Players don't need to be online at the same time. Each player takes
    their turn when convenient, and other players are notified.

    This is ideal for:
    - Play-by-email style games
    - Games with long turns
    - Players in different time zones
    - Mobile games

    Example:
        # Create session
        storage = FileAsyncStorage("./games")
        session = AsyncSession("game-123", storage, player_id=0)

        # Load existing game or start new one
        session.load_game()

        # Take turn if it's yours
        if session.is_local_player_turn():
            result = session.submit_action(action)

        # Check for games waiting for you
        pending = session.get_pending_games(player_id=0)
    """

    def __init__(
        self,
        game_id: str,
        storage: AsyncStorage,
        player_id: int,
        world: World | None = None,
        turn_manager: TurnManager | None = None,
        action_pipeline: object | None = None,
    ):
        """Initialize async session.

        Args:
            game_id: Unique game identifier
            storage: Storage backend
            player_id: This player's ID
            world: Optional World (will be loaded from storage if None)
            turn_manager: Optional TurnManager (will be loaded if None)
            action_pipeline: Optional action pipeline
        """
        self._game_id = game_id
        self._storage = storage
        self._player_id = player_id
        self._world = world
        self._turn_manager = turn_manager
        self._action_pipeline = action_pipeline

        # State
        self._loaded = False
        self._state_callbacks: list[Callable[[dict], None]] = []

    def load_game(self) -> bool:
        """Load game state from storage.

        Returns:
            True if game was loaded successfully
        """
        state = self._storage.load_state(self._game_id)
        if not state:
            return False

        # Restore world
        if self._world is not None:
            self._world.from_dict(state.get("world", {}))

        # Restore turn manager state (simplified - would need full restoration)
        # This is a placeholder - real implementation needs proper deserialization

        self._loaded = True
        return True

    def save_game(self) -> None:
        """Save current game state to storage."""
        if not self._world or not self._turn_manager:
            return

        state = {
            "world": self._world.to_dict(),
            "turn": self._turn_manager.get_state(),
            "last_updated": time.time(),
        }
        self._storage.save_state(self._game_id, state)

        # Update metadata
        metadata = {
            "current_player": self._turn_manager.current_player,
            "player_count": self._turn_manager._state.player_count,
            "last_action": time.time(),
        }
        self._storage.save_metadata(self._game_id, metadata)

    def get_player_count(self) -> int:
        """Get the number of players in this session."""
        if self._turn_manager:
            return self._turn_manager._state.player_count
        metadata = self._storage.get_metadata(self._game_id)
        return metadata.get("player_count", 0) if metadata else 0

    def get_current_player(self) -> int:
        """Get the player whose turn it currently is."""
        if self._turn_manager:
            return self._turn_manager.current_player
        metadata = self._storage.get_metadata(self._game_id)
        return metadata.get("current_player", 0) if metadata else 0

    def is_local_player_turn(self) -> bool:
        """Check if it's the local player's turn."""
        return self.get_current_player() == self._player_id

    def submit_action(self, action: Action) -> ActionResult:
        """Submit an action for execution.

        The action is executed immediately, then state is saved to storage.
        Other players will see the updated state when they next load the game.

        Args:
            action: The action to execute

        Returns:
            ActionResult indicating success/failure
        """
        from renee.actions.result import ActionResult

        # Verify it's this player's turn
        if not self.is_local_player_turn():
            return ActionResult.error_result(action, "Not your turn")

        # Verify world and turn manager are loaded
        if not self._world or not self._turn_manager:
            return ActionResult.error_result(action, "Game not loaded")

        # Execute action
        if self._action_pipeline is not None:
            result = self._action_pipeline.execute(action, self._world)
        else:
            result = ActionResult.success_result(action)

        # Save if successful
        if result.success:
            self._storage.save_action(self._game_id, action)
            self.save_game()
            self._notify_state_changed()

            # Auto-advance turn if appropriate
            if self._turn_manager.is_phase_complete():
                self._turn_manager.advance()
                self.save_game()

        return result

    def get_game_state(self) -> dict:
        """Get the current game state for this player.

        State is filtered to show only information this player should see.
        """
        if not self._world or not self._turn_manager:
            # Try to load from storage
            state = self._storage.load_state(self._game_id)
            return state if state else {}

        return {
            "world": self._world.to_dict(),
            "turn": self._turn_manager.get_state(),
            "session_type": "async",
            "game_id": self._game_id,
            "player_id": self._player_id,
            "is_your_turn": self.is_local_player_turn(),
        }

    def on_state_changed(self, callback: Callable[[dict], None]) -> None:
        """Register a callback for state changes."""
        self._state_callbacks.append(callback)

    def get_pending_games(self, player_id: int) -> list[str]:
        """Get games where it's this player's turn.

        Args:
            player_id: Player to check

        Returns:
            List of game IDs waiting for this player
        """
        pending = []

        for game_id in self._storage.list_games():
            metadata = self._storage.get_metadata(game_id)
            if metadata and metadata.get("current_player") == player_id:
                pending.append(game_id)

        return pending

    def end_turn(self) -> None:
        """Manually end the current player's turn."""
        if self._turn_manager:
            self._turn_manager.end_turn()
            self.save_game()
            self._notify_state_changed()

    def _notify_state_changed(self) -> None:
        """Notify all registered callbacks of a state change."""
        state = self.get_game_state()
        for callback in self._state_callbacks:
            try:
                callback(state)
            except Exception as e:
                print(f"Error in state callback: {e}")

    @staticmethod
    def create_new_game(
        game_id: str,
        storage: AsyncStorage,
        world: World,
        turn_manager: TurnManager,
        player_count: int,
    ) -> None:
        """Create a new async game.

        Args:
            game_id: Unique game identifier
            storage: Storage backend
            world: Initial world state
            turn_manager: Turn manager
            player_count: Number of players
        """
        # Start the game
        turn_manager.start_game(player_count)

        # Save initial state
        state = {
            "world": world.to_dict(),
            "turn": turn_manager.get_state(),
            "created": time.time(),
        }
        storage.save_state(game_id, state)

        # Save metadata
        metadata = {
            "current_player": 0,
            "player_count": player_count,
            "created": time.time(),
            "last_action": time.time(),
        }
        storage.save_metadata(game_id, metadata)
