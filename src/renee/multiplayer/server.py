"""Standalone game server for network multiplayer.

Provides a complete game server implementation with lobby management,
matchmaking, and game session hosting.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from renee.multiplayer.network import NetworkServer
from renee.multiplayer.protocol import (
    Message,
    MessageType,
    create_error_message,
    decode_message,
    encode_message,
)

if TYPE_CHECKING:
    from renee.ecs.world import World
    from renee.turns.manager import TurnManager

logger = logging.getLogger(__name__)


@dataclass
class PlayerInfo:
    """Information about a connected player."""

    player_id: int
    player_name: str | None = None
    connected: bool = True
    ready: bool = False
    game_id: str | None = None


@dataclass
class GameRoom:
    """A game room with players and game state."""

    room_id: str
    game_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    host_player: int = 0
    players: list[int] = field(default_factory=list)
    max_players: int = 4
    started: bool = False
    server: NetworkServer | None = None

    def is_full(self) -> bool:
        """Check if room is at max capacity."""
        return len(self.players) >= self.max_players

    def can_start(self) -> bool:
        """Check if room has enough players to start."""
        return len(self.players) >= 2


class GameServer:
    """Full-featured game server with lobby and matchmaking.

    Manages:
    - Player connections
    - Game room creation and joining
    - Matchmaking
    - Game session hosting

    Example:
        # Create server
        server = GameServer(port=8080)

        # Run server
        await server.run()
    """

    def __init__(
        self,
        port: int = 8080,
        max_rooms: int = 100,
    ):
        """Initialize game server.

        Args:
            port: Port to listen on
            max_rooms: Maximum number of concurrent game rooms
        """
        self._port = port
        self._max_rooms = max_rooms

        # Server state
        self._running = False
        self._server: asyncio.Server | None = None

        # Players and rooms
        self._players: dict[int, PlayerInfo] = {}
        self._rooms: dict[str, GameRoom] = {}
        self._matchmaking_queue: list[int] = []

        # Network connections
        self._connections: dict[int, tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}

    async def run(self) -> None:
        """Start the server and run until stopped."""
        self._server = await asyncio.start_server(
            self._handle_connection, "0.0.0.0", self._port
        )
        self._running = True

        logger.info(f"Game server started on port {self._port}")

        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        """Stop the server."""
        self._running = False

        # Close all connections
        for player_id, (reader, writer) in self._connections.items():
            writer.close()
            await writer.wait_closed()

        # Close server
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Game server stopped")

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a new client connection.

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

                # Route message
                if msg.type == MessageType.CONNECT:
                    player_id = msg.payload.get("player_id")
                    player_name = msg.payload.get("player_name")
                    await self._handle_connect(player_id, player_name, reader, writer)

                elif msg.type == MessageType.DISCONNECT:
                    await self._handle_disconnect(player_id)
                    break

                elif player_id is not None:
                    await self._route_message(player_id, msg)

        except asyncio.CancelledError:
            logger.info(f"Connection handler cancelled for player {player_id}")
        except Exception as e:
            logger.error(f"Error handling connection for player {player_id}: {e}")
        finally:
            if player_id is not None:
                await self._cleanup_player(player_id)

    async def _handle_connect(
        self,
        player_id: int,
        player_name: str | None,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle player connection.

        Args:
            player_id: Player identifier
            player_name: Player display name
            reader: Client stream reader
            writer: Client stream writer
        """
        # Register player
        self._players[player_id] = PlayerInfo(player_id=player_id, player_name=player_name)
        self._connections[player_id] = (reader, writer)

        logger.info(f"Player {player_id} ({player_name}) connected")

        # Send welcome message
        welcome = Message(
            type="welcome",
            payload={
                "player_id": player_id,
                "server_version": "1.0.0",
                "available_rooms": len([r for r in self._rooms.values() if not r.started]),
            },
        )
        await self._send_to_player(player_id, welcome)

    async def _handle_disconnect(self, player_id: int | None) -> None:
        """Handle player disconnection.

        Args:
            player_id: Player identifier
        """
        if player_id and player_id in self._players:
            self._players[player_id].connected = False
            logger.info(f"Player {player_id} disconnected")

    async def _cleanup_player(self, player_id: int) -> None:
        """Clean up player resources.

        Args:
            player_id: Player identifier
        """
        # Remove from rooms
        for room in self._rooms.values():
            if player_id in room.players:
                room.players.remove(player_id)
                logger.info(f"Removed player {player_id} from room {room.room_id}")

        # Remove from matchmaking
        if player_id in self._matchmaking_queue:
            self._matchmaking_queue.remove(player_id)

        # Close connection
        if player_id in self._connections:
            reader, writer = self._connections[player_id]
            writer.close()
            await writer.wait_closed()
            del self._connections[player_id]

        # Remove player info
        if player_id in self._players:
            del self._players[player_id]

    async def _route_message(self, player_id: int, msg: Message) -> None:
        """Route a message to the appropriate handler.

        Args:
            player_id: Player who sent the message
            msg: Message to route
        """
        if msg.type == "create_room":
            await self._handle_create_room(player_id, msg)
        elif msg.type == "join_room":
            await self._handle_join_room(player_id, msg)
        elif msg.type == "leave_room":
            await self._handle_leave_room(player_id, msg)
        elif msg.type == "start_game":
            await self._handle_start_game(player_id, msg)
        elif msg.type == "list_rooms":
            await self._handle_list_rooms(player_id)
        elif msg.type == "join_matchmaking":
            await self._handle_join_matchmaking(player_id, msg)
        elif msg.type == "leave_matchmaking":
            await self._handle_leave_matchmaking(player_id)
        else:
            # Unknown message type
            error = create_error_message(f"Unknown message type: {msg.type}", "unknown_message")
            await self._send_to_player(player_id, error)

    async def _handle_create_room(self, player_id: int, msg: Message) -> None:
        """Handle room creation request.

        Args:
            player_id: Player creating the room
            msg: Create room message
        """
        if len(self._rooms) >= self._max_rooms:
            error = create_error_message("Server is full", "server_full")
            await self._send_to_player(player_id, error)
            return

        # Create room
        room_id = str(uuid.uuid4())[:8]
        max_players = msg.payload.get("max_players", 4)

        room = GameRoom(
            room_id=room_id,
            host_player=player_id,
            players=[player_id],
            max_players=max_players,
        )
        self._rooms[room_id] = room
        self._players[player_id].game_id = room_id

        logger.info(f"Player {player_id} created room {room_id}")

        # Send confirmation
        response = Message(
            type="room_created",
            payload={
                "room_id": room_id,
                "host_player": player_id,
                "players": room.players,
                "max_players": max_players,
            },
        )
        await self._send_to_player(player_id, response)

    async def _handle_join_room(self, player_id: int, msg: Message) -> None:
        """Handle room join request.

        Args:
            player_id: Player joining the room
            msg: Join room message
        """
        room_id = msg.payload.get("room_id")

        if room_id not in self._rooms:
            error = create_error_message("Room not found", "room_not_found")
            await self._send_to_player(player_id, error)
            return

        room = self._rooms[room_id]

        if room.is_full():
            error = create_error_message("Room is full", "room_full")
            await self._send_to_player(player_id, error)
            return

        if room.started:
            error = create_error_message("Game already started", "game_started")
            await self._send_to_player(player_id, error)
            return

        # Add player to room
        room.players.append(player_id)
        self._players[player_id].game_id = room_id

        logger.info(f"Player {player_id} joined room {room_id}")

        # Notify all players in room
        notification = Message(
            type=MessageType.PLAYER_JOINED,
            payload={
                "player_id": player_id,
                "room_id": room_id,
                "players": room.players,
                "player_count": len(room.players),
            },
        )
        await self._broadcast_to_room(room_id, notification)

    async def _handle_leave_room(self, player_id: int, msg: Message) -> None:
        """Handle room leave request.

        Args:
            player_id: Player leaving the room
            msg: Leave room message
        """
        player_info = self._players.get(player_id)
        if not player_info or not player_info.game_id:
            return

        room_id = player_info.game_id
        if room_id not in self._rooms:
            return

        room = self._rooms[room_id]
        if player_id in room.players:
            room.players.remove(player_id)
            player_info.game_id = None

            logger.info(f"Player {player_id} left room {room_id}")

            # Notify remaining players
            notification = Message(
                type=MessageType.PLAYER_LEFT,
                payload={
                    "player_id": player_id,
                    "room_id": room_id,
                    "players": room.players,
                    "player_count": len(room.players),
                },
            )
            await self._broadcast_to_room(room_id, notification)

            # Delete room if empty
            if not room.players:
                del self._rooms[room_id]
                logger.info(f"Deleted empty room {room_id}")

    async def _handle_start_game(self, player_id: int, msg: Message) -> None:
        """Handle game start request.

        Args:
            player_id: Player starting the game (must be host)
            msg: Start game message
        """
        player_info = self._players.get(player_id)
        if not player_info or not player_info.game_id:
            error = create_error_message("Not in a room", "not_in_room")
            await self._send_to_player(player_id, error)
            return

        room_id = player_info.game_id
        room = self._rooms.get(room_id)

        if not room:
            error = create_error_message("Room not found", "room_not_found")
            await self._send_to_player(player_id, error)
            return

        if player_id != room.host_player:
            error = create_error_message("Only host can start game", "not_host")
            await self._send_to_player(player_id, error)
            return

        if not room.can_start():
            error = create_error_message("Need at least 2 players", "not_enough_players")
            await self._send_to_player(player_id, error)
            return

        # Start the game
        room.started = True

        logger.info(f"Game started in room {room_id}")

        # Notify all players
        notification = Message(
            type="game_started",
            payload={
                "room_id": room_id,
                "game_id": room.game_id,
                "players": room.players,
            },
        )
        await self._broadcast_to_room(room_id, notification)

    async def _handle_list_rooms(self, player_id: int) -> None:
        """Handle list rooms request.

        Args:
            player_id: Player requesting room list
        """
        available_rooms = [
            {
                "room_id": room.room_id,
                "host_player": room.host_player,
                "player_count": len(room.players),
                "max_players": room.max_players,
                "started": room.started,
            }
            for room in self._rooms.values()
            if not room.started and not room.is_full()
        ]

        response = Message(
            type="room_list",
            payload={"rooms": available_rooms, "total": len(available_rooms)},
        )
        await self._send_to_player(player_id, response)

    async def _handle_join_matchmaking(self, player_id: int, msg: Message) -> None:
        """Handle matchmaking join request.

        Args:
            player_id: Player joining matchmaking
            msg: Join matchmaking message
        """
        if player_id not in self._matchmaking_queue:
            self._matchmaking_queue.append(player_id)
            logger.info(f"Player {player_id} joined matchmaking queue")

        # Try to match players
        await self._try_matchmaking()

    async def _handle_leave_matchmaking(self, player_id: int) -> None:
        """Handle matchmaking leave request.

        Args:
            player_id: Player leaving matchmaking
        """
        if player_id in self._matchmaking_queue:
            self._matchmaking_queue.remove(player_id)
            logger.info(f"Player {player_id} left matchmaking queue")

    async def _try_matchmaking(self) -> None:
        """Attempt to create matches from the matchmaking queue."""
        # Simple matchmaking: pair up first 2 players
        while len(self._matchmaking_queue) >= 2:
            player1 = self._matchmaking_queue.pop(0)
            player2 = self._matchmaking_queue.pop(0)

            # Create room
            room_id = str(uuid.uuid4())[:8]
            room = GameRoom(
                room_id=room_id,
                host_player=player1,
                players=[player1, player2],
                max_players=2,
            )
            self._rooms[room_id] = room

            self._players[player1].game_id = room_id
            self._players[player2].game_id = room_id

            logger.info(f"Matched players {player1} and {player2} in room {room_id}")

            # Notify both players
            notification = Message(
                type="match_found",
                payload={
                    "room_id": room_id,
                    "players": [player1, player2],
                },
            )
            await self._send_to_player(player1, notification)
            await self._send_to_player(player2, notification)

    async def _send_to_player(self, player_id: int, msg: Message) -> None:
        """Send a message to a specific player.

        Args:
            player_id: Target player
            msg: Message to send
        """
        if player_id not in self._connections:
            return

        reader, writer = self._connections[player_id]
        data = encode_message(msg)
        writer.write(data)
        await writer.drain()

    async def _broadcast_to_room(self, room_id: str, msg: Message) -> None:
        """Broadcast a message to all players in a room.

        Args:
            room_id: Target room
            msg: Message to broadcast
        """
        room = self._rooms.get(room_id)
        if not room:
            return

        for player_id in room.players:
            await self._send_to_player(player_id, msg)
