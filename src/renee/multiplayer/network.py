"""Network multiplayer session for client-server play.

Provides NetworkClient for connecting to game servers and NetworkServer
for hosting authoritative game sessions over the network.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable

from renee.multiplayer.protocol import (
    Message,
    MessageType,
    create_action_message,
    create_connect_message,
    create_disconnect_message,
    create_error_message,
    create_state_update_message,
    create_turn_change_message,
    decode_message,
    encode_message,
)
from renee.multiplayer.session import GameSession

if TYPE_CHECKING:
    from renee.actions.action import Action
    from renee.actions.result import ActionResult
    from renee.ecs.world import World
    from renee.turns.manager import TurnManager

logger = logging.getLogger(__name__)


class NetworkClient(GameSession):
    """Client for network multiplayer.

    Connects to a NetworkServer and sends/receives game state updates.
    The server is authoritative - all actions are validated server-side.

    Example:
        # Create and connect
        client = NetworkClient("localhost", 8080, player_id=0)
        await client.connect()

        # Submit actions
        result = client.submit_action(move_action)

        # Get current state
        state = client.get_game_state()

        # Disconnect when done
        await client.disconnect()
    """

    def __init__(self, host: str, port: int, player_id: int, player_name: str | None = None):
        """Initialize network client.

        Args:
            host: Server hostname or IP address
            port: Server port
            player_id: This client's player ID
            player_name: Optional display name
        """
        self._host = host
        self._port = port
        self._player_id = player_id
        self._player_name = player_name
        self._connected = False

        # Connection
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._receive_task: asyncio.Task | None = None

        # State
        self._game_state: dict = {}
        self._current_player = 0
        self._player_count = 0
        self._pending_actions: dict[int, asyncio.Future] = {}
        self._action_counter = 0

        # Callbacks
        self._state_callbacks: list[Callable[[dict], None]] = []

        # Reconnection
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 2.0

    async def connect(self) -> bool:
        """Connect to the game server.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
            self._connected = True

            # Send connect message
            connect_msg = create_connect_message(self._player_id, self._player_name)
            await self._send_message(connect_msg)

            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(f"Connected to server at {self._host}:{self._port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        if not self._connected:
            return

        try:
            # Send disconnect message
            disconnect_msg = create_disconnect_message(self._player_id)
            await self._send_message(disconnect_msg)

            # Close connection
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()

            # Cancel receive task
            if self._receive_task:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass

            self._connected = False
            logger.info("Disconnected from server")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def get_player_count(self) -> int:
        """Get the number of players in this session."""
        return self._player_count

    def get_current_player(self) -> int:
        """Get the player whose turn it currently is."""
        return self._current_player

    def is_local_player_turn(self) -> bool:
        """Check if it's the local player's turn."""
        return self._current_player == self._player_id

    def submit_action(self, action: Action) -> ActionResult:
        """Submit an action to the server.

        This is a synchronous wrapper around the async _submit_action_async.
        For async code, use _submit_action_async directly.

        Args:
            action: The action to execute

        Returns:
            ActionResult from server
        """
        # Create event loop if needed
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context - this shouldn't be called
            raise RuntimeError("Use await client._submit_action_async() in async context")
        except RuntimeError:
            # No event loop - create one
            return asyncio.run(self._submit_action_async(action))

    async def _submit_action_async(self, action: Action) -> ActionResult:
        """Submit an action to the server (async version).

        Args:
            action: The action to execute

        Returns:
            ActionResult from server
        """
        from renee.actions.result import ActionResult

        if not self._connected:
            return ActionResult.error_result(action, "Not connected to server")

        # Create action message
        action_msg = create_action_message(action.name, action.params, self._player_id)
        action_msg.sequence = self._action_counter
        self._action_counter += 1

        # Create future to wait for response
        future: asyncio.Future = asyncio.Future()
        self._pending_actions[action_msg.sequence] = future

        # Send to server
        await self._send_message(action_msg)

        # Wait for response
        try:
            result_data = await asyncio.wait_for(future, timeout=10.0)
            # Convert result_data to ActionResult
            return ActionResult(
                success=result_data.get("success", False),
                action=action,
                cancelled=result_data.get("cancelled", False),
                cancel_reason=result_data.get("cancel_reason"),
                error=result_data.get("error"),
                events=result_data.get("events", []),
            )
        except asyncio.TimeoutError:
            return ActionResult.error_result(action, "Action timeout")

    def get_game_state(self) -> dict:
        """Get the current game state (filtered for this player)."""
        return self._game_state.copy()

    def on_state_changed(self, callback: Callable[[dict], None]) -> None:
        """Register a callback for state changes."""
        self._state_callbacks.append(callback)

    async def _send_message(self, msg: Message) -> None:
        """Send a message to the server.

        Args:
            msg: Message to send
        """
        if not self._writer:
            raise RuntimeError("Not connected")

        data = encode_message(msg)
        self._writer.write(data)
        await self._writer.drain()

    async def _receive_loop(self) -> None:
        """Continuously receive messages from server."""
        try:
            while self._connected and self._reader:
                # Read length prefix
                length_data = await self._reader.readexactly(4)
                length = int.from_bytes(length_data, byteorder="big")

                # Read message
                msg_data = await self._reader.readexactly(length)
                full_data = length_data + msg_data

                # Decode and handle
                msg = decode_message(full_data)
                await self._handle_message(msg)

        except asyncio.CancelledError:
            logger.info("Receive loop cancelled")
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
            self._connected = False
            # Attempt reconnection
            await self._try_reconnect()

    async def _handle_message(self, msg: Message) -> None:
        """Handle a message from the server.

        Args:
            msg: Message to handle
        """
        if msg.type == MessageType.STATE_UPDATE:
            self._game_state = msg.payload.get("state", {})
            self._notify_state_changed()

        elif msg.type == MessageType.TURN_CHANGE:
            self._current_player = msg.payload.get("current_player", 0)
            self._notify_state_changed()

        elif msg.type == MessageType.ACTION_RESULT:
            # Complete pending action future
            sequence = msg.sequence
            if sequence is not None and sequence in self._pending_actions:
                future = self._pending_actions.pop(sequence)
                future.set_result(msg.payload)

        elif msg.type == MessageType.ERROR:
            logger.error(f"Server error: {msg.payload.get('error')}")

        elif msg.type == MessageType.PLAYER_JOINED:
            self._player_count = msg.payload.get("player_count", self._player_count)
            logger.info(f"Player joined. Total players: {self._player_count}")

        elif msg.type == MessageType.PLAYER_LEFT:
            self._player_count = msg.payload.get("player_count", self._player_count)
            logger.info(f"Player left. Total players: {self._player_count}")

    def _notify_state_changed(self) -> None:
        """Notify all registered callbacks of a state change."""
        for callback in self._state_callbacks:
            try:
                callback(self._game_state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")

    async def _try_reconnect(self) -> None:
        """Attempt to reconnect to the server."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return

        self._reconnect_attempts += 1
        logger.info(f"Reconnection attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}")

        await asyncio.sleep(self._reconnect_delay)

        success = await self.connect()
        if success:
            self._reconnect_attempts = 0
            logger.info("Reconnected successfully")


class NetworkServer:
    """Authoritative game server for network multiplayer.

    Manages game state, validates actions, and synchronizes state to all clients.

    Example:
        server = NetworkServer(world, turn_manager, port=8080)
        await server.start()

        # Server runs until stopped
        await server.stop()
    """

    def __init__(
        self,
        world: World,
        turn_manager: TurnManager,
        port: int,
        action_pipeline: object | None = None,
    ):
        """Initialize network server.

        Args:
            world: The ECS World containing game state
            turn_manager: Turn manager for coordinating player turns
            port: Port to listen on
            action_pipeline: Optional action pipeline for executing actions
        """
        self._world = world
        self._turn_manager = turn_manager
        self._port = port
        self._action_pipeline = action_pipeline

        # Server state
        self._running = False
        self._server: asyncio.Server | None = None

        # Connected clients
        self._clients: dict[int, tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
        self._client_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the server and begin accepting connections."""
        self._server = await asyncio.start_server(self._handle_client, "0.0.0.0", self._port)
        self._running = True

        logger.info(f"Server started on port {self._port}")

        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        """Stop the server and disconnect all clients."""
        self._running = False

        # Cancel all client tasks
        for task in self._client_tasks:
            task.cancel()
        await asyncio.gather(*self._client_tasks, return_exceptions=True)

        # Close all client connections
        for reader, writer in self._clients.values():
            writer.close()
            await writer.wait_closed()

        # Close server
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Server stopped")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a connected client.

        Args:
            reader: Client stream reader
            writer: Client stream writer
        """
        player_id: int | None = None

        try:
            while self._running:
                # Read message
                length_data = await reader.readexactly(4)
                length = int.from_bytes(length_data, byteorder="big")
                msg_data = await reader.readexactly(length)
                full_data = length_data + msg_data

                msg = decode_message(full_data)

                # Handle message
                if msg.type == MessageType.CONNECT:
                    player_id = msg.payload.get("player_id")
                    self._clients[player_id] = (reader, writer)
                    logger.info(f"Player {player_id} connected")

                    # Send initial state
                    await self._send_full_state(player_id)

                elif msg.type == MessageType.DISCONNECT:
                    logger.info(f"Player {player_id} disconnected")
                    break

                elif msg.type == MessageType.ACTION:
                    if player_id is not None:
                        await self._handle_action(msg, player_id)

        except asyncio.CancelledError:
            logger.info(f"Client handler cancelled for player {player_id}")
        except Exception as e:
            logger.error(f"Error handling client {player_id}: {e}")
        finally:
            if player_id is not None and player_id in self._clients:
                del self._clients[player_id]

    async def _handle_action(self, msg: Message, player_id: int) -> None:
        """Handle an action from a client.

        Args:
            msg: Action message
            player_id: Player who sent the action
        """
        # Validate it's this player's turn
        if not self.validate_action(player_id, None):
            error_msg = create_error_message("Not your turn", "invalid_turn")
            await self._send_to_client(player_id, error_msg)
            return

        # Execute action
        from renee.actions.action import Action

        action = Action(
            name=msg.payload.get("action"),
            params=msg.payload.get("params", {}),
            source=player_id,
        )

        if self._action_pipeline is not None:
            result = self._action_pipeline.execute(action, self._world)
        else:
            from renee.actions.result import ActionResult

            result = ActionResult.success_result(action)

        # Send result back to client
        result_msg = Message(
            type=MessageType.ACTION_RESULT,
            payload={
                "success": result.success,
                "cancelled": result.cancelled,
                "cancel_reason": result.cancel_reason,
                "error": result.error,
                "events": result.events,
            },
            sequence=msg.sequence,
        )
        await self._send_to_client(player_id, result_msg)

        # Broadcast state update if successful
        if result.success:
            await self.broadcast_state()

    def validate_action(self, player: int, action: Action | None) -> bool:
        """Validate if a player can perform an action.

        Args:
            player: Player ID
            action: Action to validate (can be None for turn check only)

        Returns:
            True if action is valid
        """
        # Check if it's this player's turn
        return self._turn_manager.can_act(player)

    async def broadcast_state(self) -> None:
        """Send updated state to all connected clients."""
        for player_id in self._clients.keys():
            await self._send_filtered_state(player_id)

    async def _send_full_state(self, player_id: int) -> None:
        """Send complete game state to a client.

        Args:
            player_id: Target player
        """
        state = self._get_state_for_player(player_id)
        msg = Message(type=MessageType.FULL_STATE, payload={"state": state})
        await self._send_to_client(player_id, msg)

    async def _send_filtered_state(self, player_id: int) -> None:
        """Send filtered state update to a client.

        Args:
            player_id: Target player
        """
        state = self._get_state_for_player(player_id)
        msg = create_state_update_message(state, player_id)
        await self._send_to_client(player_id, msg)

    def _get_state_for_player(self, player_id: int) -> dict:
        """Get game state filtered for a specific player.

        Args:
            player_id: Player to filter for

        Returns:
            Filtered game state
        """
        # For now, return full state
        # Real implementation would filter hidden information
        return {
            "world": self._world.to_dict(),
            "turn": self._turn_manager.get_state(),
            "player_id": player_id,
        }

    async def _send_to_client(self, player_id: int, msg: Message) -> None:
        """Send a message to a specific client.

        Args:
            player_id: Target player
            msg: Message to send
        """
        if player_id not in self._clients:
            return

        reader, writer = self._clients[player_id]
        data = encode_message(msg)
        writer.write(data)
        await writer.drain()
