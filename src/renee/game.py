"""Game class - main orchestrator for Renee games.

The Game class coordinates all subsystems and implements the game loop.
It can run in real-time or turn-based mode with pluggable renderers.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import yaml

from renee.actions.pipeline import ActionPipeline
from renee.assets.loader import AssetLoader
from renee.assets.manifest import AssetManifest
from renee.ecs.world import World
from renee.events.bus import EventBus
from renee.input.handler import InputHandler
from renee.render.commands import RenderCommand
from renee.render.renderer import Renderer
from renee.rules.engine import RuleEngine
from renee.schema.registry import SchemaRegistry
from renee.turns.manager import TurnManager


class GameState(Enum):
    """Possible game states."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    SHUTDOWN = "shutdown"


class GameMode(Enum):
    """Game loop modes."""

    REAL_TIME = "real_time"  # Continuous update loop
    TURN_BASED = "turn_based"  # Wait for player input between turns


@dataclass
class GameConfig:
    """Configuration for a game instance.

    This is typically loaded from a game.yaml file.

    Attributes:
        title: Game title
        mode: Game mode (real_time or turn_based)
        target_fps: Target frames per second for real-time mode
        seed: Random seed for deterministic gameplay (None for random)
        renderer_config: Configuration dict for the renderer
        asset_path: Path to assets directory
        schema_files: List of schema YAML files to load
    """

    title: str = "Renee Game"
    mode: GameMode = GameMode.REAL_TIME
    target_fps: int = 60
    seed: int | None = None
    renderer_config: dict[str, Any] = field(default_factory=dict)
    asset_path: str = "assets"
    schema_files: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, filepath: str | Path) -> GameConfig:
        """Load game configuration from a YAML file.

        Args:
            filepath: Path to the YAML config file

        Returns:
            GameConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Config file is empty: {filepath}")

        # Convert mode string to enum if present
        if "mode" in data and isinstance(data["mode"], str):
            data["mode"] = GameMode(data["mode"])

        return cls(**data)


class Game:
    """Main game orchestrator that coordinates all Renee subsystems.

    The Game class initializes and manages:
    - World (ECS)
    - EventBus (event system)
    - SchemaRegistry (type introspection)
    - RuleEngine (game rules)
    - ActionPipeline (action processing)
    - TurnManager (optional, for turn-based games)
    - Renderer (pluggable - pygame, terminal, headless)
    - InputHandler (input mapping)
    - AssetLoader (optional, asset management)

    Example:
        # Create game from config
        config = GameConfig.from_yaml("game.yaml")
        game = Game(config, renderer=MyRenderer())

        # Set up game-specific logic
        @game.on_start
        def setup():
            player = game.world.create_entity()
            # ...

        # Run the game
        game.run()

    Example (manual setup):
        game = Game()
        game.world.create_entity()
        game.run()
    """

    def __init__(
        self,
        config: GameConfig | None = None,
        renderer: Renderer | None = None,
    ) -> None:
        """Initialize the game with configuration and optional renderer.

        Args:
            config: Game configuration (uses defaults if None)
            renderer: Renderer implementation (None for headless mode)
        """
        self.config = config or GameConfig()
        self._state = GameState.INITIALIZING

        # Initialize RNG with deterministic seed if provided
        if self.config.seed is not None:
            random.seed(self.config.seed)

        # Core subsystems (always present)
        self.world = World()
        self.event_bus = EventBus()
        self.schema_registry = SchemaRegistry()
        self.rule_engine = RuleEngine()
        self.action_pipeline = ActionPipeline()

        # Optional subsystems
        self.turn_manager: TurnManager | None = None
        self.renderer: Renderer | None = renderer
        self.input_handler: InputHandler | None = None
        self.asset_loader: AssetLoader | None = None

        # Lifecycle hooks
        self._on_start_hooks: list[Callable[[], None]] = []
        self._on_update_hooks: list[Callable[[float], None]] = []
        self._on_render_hooks: list[Callable[[], list[RenderCommand]]] = []
        self._on_shutdown_hooks: list[Callable[[], None]] = []

        # Game loop state
        self._running = False
        self._last_frame_time = 0.0
        self._accumulated_time = 0.0
        self._frame_count = 0

        # Load schemas if specified
        for schema_file in self.config.schema_files:
            try:
                self.schema_registry.register_from_yaml(schema_file)
            except Exception as e:
                print(f"Warning: Failed to load schema file {schema_file}: {e}")

    # === Subsystem Initialization ===

    def init_turn_manager(self, turn_manager: TurnManager) -> None:
        """Initialize turn manager for turn-based games.

        Args:
            turn_manager: Configured TurnManager instance
        """
        self.turn_manager = turn_manager

        # Sync event bus turn counter with turn manager
        self.turn_manager.on_turn_start.append(self._sync_turn_to_event_bus)

    def init_input_handler(self, input_handler: InputHandler | None = None) -> None:
        """Initialize input handler.

        Args:
            input_handler: InputHandler instance (creates default if None)
        """
        if input_handler is None:
            input_handler = InputHandler()
        self.input_handler = input_handler

    def init_asset_loader(
        self, manifest: AssetManifest | None = None, base_path: str | None = None
    ) -> None:
        """Initialize asset loader with manifest.

        Args:
            manifest: Asset manifest (creates empty if None)
            base_path: Base path for assets (uses config if None)
        """
        if manifest is None:
            manifest = AssetManifest()
        if base_path is None:
            base_path = self.config.asset_path

        self.asset_loader = AssetLoader(manifest, base_path)

    def init_renderer(self, renderer: Renderer, config: dict[str, Any] | None = None) -> None:
        """Initialize renderer with configuration.

        Args:
            renderer: Renderer implementation
            config: Renderer config (uses self.config.renderer_config if None)
        """
        self.renderer = renderer
        render_config = config if config is not None else self.config.renderer_config
        self.renderer.initialize(render_config)

        # Initialize input handler if we have a renderer
        if self.input_handler is None:
            self.init_input_handler()

    # === Lifecycle Hooks ===

    def on_start(self, func: Callable[[], None]) -> Callable[[], None]:
        """Decorator to register a function to run when the game starts.

        Example:
            @game.on_start
            def setup():
                player = game.world.create_entity()
        """
        self._on_start_hooks.append(func)
        return func

    def on_update(self, func: Callable[[float], None]) -> Callable[[float], None]:
        """Decorator to register a function to run every frame.

        The function receives delta time (dt) in seconds.

        Example:
            @game.on_update
            def update_systems(dt: float):
                # Update game logic
                pass
        """
        self._on_update_hooks.append(func)
        return func

    def on_render(
        self, func: Callable[[], list[RenderCommand]]
    ) -> Callable[[], list[RenderCommand]]:
        """Decorator to register a function to generate render commands.

        The function should return a list of RenderCommand objects.

        Example:
            @game.on_render
            def render_entities():
                commands = []
                for entity in game.world.query(Position, Sprite):
                    pos = game.world.get_component(entity, Position)
                    sprite = game.world.get_component(entity, Sprite)
                    commands.append(DrawSpriteCommand(sprite.name, pos.x, pos.y))
                return commands
        """
        self._on_render_hooks.append(func)
        return func

    def on_shutdown(self, func: Callable[[], None]) -> Callable[[], None]:
        """Decorator to register a function to run when the game shuts down.

        Example:
            @game.on_shutdown
            def cleanup():
                # Save game state, etc.
                pass
        """
        self._on_shutdown_hooks.append(func)
        return func

    # === Game State Management ===

    @property
    def state(self) -> GameState:
        """Get current game state."""
        return self._state

    def pause(self) -> None:
        """Pause the game."""
        if self._state == GameState.RUNNING:
            self._state = GameState.PAUSED

    def resume(self) -> None:
        """Resume the game from paused state."""
        if self._state == GameState.PAUSED:
            self._state = GameState.RUNNING

    def end_game(self) -> None:
        """End the game (transition to game over state)."""
        if self._state == GameState.RUNNING:
            self._state = GameState.GAME_OVER

    def is_running(self) -> bool:
        """Check if the game is currently running."""
        return self._state == GameState.RUNNING

    def is_paused(self) -> bool:
        """Check if the game is paused."""
        return self._state == GameState.PAUSED

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self._state == GameState.GAME_OVER

    # === Game Loop ===

    def run(self) -> None:
        """Run the main game loop.

        The loop mode depends on self.config.mode:
        - REAL_TIME: Continuous update loop with delta time
        - TURN_BASED: Wait for player input between turns
        """
        try:
            self._start()

            if self.config.mode == GameMode.REAL_TIME:
                self._run_realtime_loop()
            else:  # TURN_BASED
                self._run_turnbased_loop()

        except KeyboardInterrupt:
            print("\nGame interrupted by user")
        except Exception as e:
            print(f"Error in game loop: {e}")
            raise
        finally:
            self._shutdown()

    def _start(self) -> None:
        """Initialize game and call start hooks."""
        self._state = GameState.RUNNING
        self._last_frame_time = time.perf_counter()

        # Execute start hooks
        for hook in self._on_start_hooks:
            try:
                hook()
            except Exception as e:
                print(f"Error in on_start hook: {e}")
                raise

    def _run_realtime_loop(self) -> None:
        """Run continuous real-time game loop with delta time."""
        target_frame_time = 1.0 / self.config.target_fps

        while self._running and self._state != GameState.SHUTDOWN:
            frame_start = time.perf_counter()

            # Calculate delta time
            dt = frame_start - self._last_frame_time
            self._last_frame_time = frame_start

            # Process frame
            if self._state == GameState.RUNNING:
                self._process_input()
                self._update(dt)
                self._render()
                self._frame_count += 1

            # Check if renderer wants to quit (e.g., window closed)
            if self.renderer and not self.renderer.is_running():
                self._running = False
                break

            # Frame rate limiting
            frame_time = time.perf_counter() - frame_start
            if frame_time < target_frame_time:
                time.sleep(target_frame_time - frame_time)

    def _run_turnbased_loop(self) -> None:
        """Run turn-based game loop (wait for player action)."""
        while self._running and self._state != GameState.SHUTDOWN:
            # In turn-based mode, we still need to render
            if self._state == GameState.RUNNING:
                self._process_input()
                # Only update when action is taken (handled externally)
                # For now, we still call update with 0 dt for consistency
                self._update(0.0)
                self._render()

            # Check if renderer wants to quit
            if self.renderer and not self.renderer.is_running():
                self._running = False
                break

            # Sleep to avoid busy-waiting
            time.sleep(0.016)  # ~60 FPS for input responsiveness

    def _process_input(self) -> None:
        """Process input from renderer."""
        if self.renderer and self.input_handler:
            raw_input = self.renderer.get_input()
            self.input_handler.update(raw_input)

    def _update(self, dt: float) -> None:
        """Update game state.

        Args:
            dt: Delta time in seconds since last update
        """
        # Execute update hooks
        for hook in self._on_update_hooks:
            try:
                hook(dt)
            except Exception as e:
                print(f"Error in on_update hook: {e}")

    def _render(self) -> None:
        """Render the current frame."""
        if not self.renderer:
            return  # Headless mode

        # Collect render commands from hooks
        commands: list[RenderCommand] = []
        for hook in self._on_render_hooks:
            try:
                result = hook()
                if result:
                    commands.extend(result)
            except Exception as e:
                print(f"Error in on_render hook: {e}")

        # Sort commands by layer (lower layers drawn first)
        commands.sort(key=lambda cmd: cmd.layer)

        # Send to renderer
        try:
            self.renderer.render(commands)
        except Exception as e:
            print(f"Error rendering frame: {e}")

    def _shutdown(self) -> None:
        """Clean up and shutdown the game."""
        self._state = GameState.SHUTDOWN

        # Execute shutdown hooks
        for hook in self._on_shutdown_hooks:
            try:
                hook()
            except Exception as e:
                print(f"Error in on_shutdown hook: {e}")

        # Shutdown renderer
        if self.renderer:
            try:
                self.renderer.shutdown()
            except Exception as e:
                print(f"Error shutting down renderer: {e}")

    def start(self) -> None:
        """Start the game loop (non-blocking setup, call run() after)."""
        self._running = True

    def stop(self) -> None:
        """Stop the game loop."""
        self._running = False
        self._state = GameState.SHUTDOWN

    # === Utility Methods ===

    def _sync_turn_to_event_bus(self) -> None:
        """Sync turn manager's turn counter to event bus."""
        if self.turn_manager:
            self.event_bus.set_turn(self.turn_manager.current_turn)

    def get_fps(self) -> float:
        """Get current frames per second.

        Returns:
            Current FPS (0 if not running)
        """
        if self._last_frame_time == 0:
            return 0.0

        current_time = time.perf_counter()
        elapsed = current_time - self._last_frame_time
        if elapsed == 0:
            return 0.0

        return 1.0 / elapsed

    def get_frame_count(self) -> int:
        """Get total number of frames rendered.

        Returns:
            Frame count since game started
        """
        return self._frame_count

    # === State Export/Import ===

    def export_state(self) -> dict[str, Any]:
        """Export complete game state as a dictionary.

        Returns:
            Dictionary containing all game state for debugging/saving

        Example:
            state = game.export_state()
            with open('save.json', 'w') as f:
                json.dump(state, f, indent=2)
        """
        state: dict[str, Any] = {
            "game_state": self._state.value,
            "frame_count": self._frame_count,
            "world": self.world.to_dict(),
            "event_history": [
                {"type": type(e).__name__, "data": str(e)} for e in self.event_bus.get_history()
            ],
        }

        if self.turn_manager:
            state["turn_state"] = self.turn_manager.get_state()

        return state

    def export_state_json(self, filepath: str | Path | None = None, indent: int = 2) -> str:
        """Export game state as JSON.

        Args:
            filepath: Optional file path to write JSON to
            indent: JSON indentation level

        Returns:
            JSON string of game state
        """
        state = self.export_state()
        json_str = json.dumps(state, indent=indent)

        if filepath:
            path = Path(filepath)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    def __repr__(self) -> str:
        """String representation of the game."""
        return (
            f"Game(title='{self.config.title}', "
            f"state={self._state.value}, "
            f"mode={self.config.mode.value}, "
            f"entities={self.world.entity_count()})"
        )
