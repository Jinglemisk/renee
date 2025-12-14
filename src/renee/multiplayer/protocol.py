"""Message protocol for network multiplayer.

Defines the message format and serialization for client-server communication.
All messages are JSON-based for simplicity and debuggability.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


class MessageType:
    """Standard message types for multiplayer protocol."""

    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"

    # Game actions
    ACTION = "action"
    ACTION_RESULT = "action_result"

    # State synchronization
    STATE_UPDATE = "state_update"
    FULL_STATE = "full_state"
    TURN_CHANGE = "turn_change"

    # Errors
    ERROR = "error"
    INVALID_ACTION = "invalid_action"

    # Player management
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"


@dataclass
class Message:
    """A message in the multiplayer protocol.

    All messages have a type, payload, and timestamp. The payload format
    depends on the message type.

    Attributes:
        type: Message type from MessageType
        payload: Message-specific data (must be JSON-serializable)
        timestamp: Message creation time (Unix timestamp)
        sequence: Optional sequence number for ordering

    Example:
        msg = Message(
            type=MessageType.ACTION,
            payload={
                "action": "move",
                "params": {"entity": 42, "x": 5, "y": 5}
            }
        )
    """

    type: str
    payload: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    sequence: int | None = None

    def __post_init__(self) -> None:
        if not self.type:
            raise ValueError("Message type cannot be empty")
        if not isinstance(self.payload, dict):
            raise TypeError(f"Payload must be dict, got {type(self.payload)}")

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        """Create message from dictionary."""
        return cls(
            type=data["type"],
            payload=data["payload"],
            timestamp=data.get("timestamp", time.time()),
            sequence=data.get("sequence"),
        )


def encode_message(msg: Message) -> bytes:
    """Encode a message to bytes for network transmission.

    Uses JSON encoding with UTF-8. Messages are length-prefixed with a
    4-byte header for framing.

    Args:
        msg: Message to encode

    Returns:
        Encoded message as bytes (length-prefix + JSON)

    Example:
        data = encode_message(msg)
        socket.send(data)
    """
    # Convert to JSON
    json_str = json.dumps(msg.to_dict())
    json_bytes = json_str.encode("utf-8")

    # Length-prefix (4 bytes, big-endian)
    length = len(json_bytes)
    length_prefix = length.to_bytes(4, byteorder="big")

    return length_prefix + json_bytes


def decode_message(data: bytes) -> Message:
    """Decode a message from bytes.

    Expects length-prefixed JSON format (as produced by encode_message).

    Args:
        data: Encoded message bytes (must include length prefix)

    Returns:
        Decoded Message object

    Raises:
        ValueError: If data is malformed or too short

    Example:
        data = socket.recv(4096)
        msg = decode_message(data)
    """
    if len(data) < 4:
        raise ValueError("Data too short for length prefix")

    # Read length prefix
    length = int.from_bytes(data[:4], byteorder="big")

    if len(data) < 4 + length:
        raise ValueError(f"Data incomplete: expected {4 + length} bytes, got {len(data)}")

    # Decode JSON
    json_bytes = data[4 : 4 + length]
    json_str = json_bytes.decode("utf-8")
    msg_dict = json.loads(json_str)

    return Message.from_dict(msg_dict)


def create_connect_message(player_id: int, player_name: str | None = None) -> Message:
    """Create a connection request message.

    Args:
        player_id: Player identifier
        player_name: Optional player display name

    Returns:
        CONNECT message
    """
    return Message(
        type=MessageType.CONNECT,
        payload={"player_id": player_id, "player_name": player_name},
    )


def create_disconnect_message(player_id: int, reason: str | None = None) -> Message:
    """Create a disconnection message.

    Args:
        player_id: Player identifier
        reason: Optional disconnect reason

    Returns:
        DISCONNECT message
    """
    return Message(
        type=MessageType.DISCONNECT,
        payload={"player_id": player_id, "reason": reason},
    )


def create_action_message(action_name: str, params: dict[str, Any], player_id: int) -> Message:
    """Create an action request message.

    Args:
        action_name: Name of the action (e.g., 'move', 'attack')
        params: Action parameters
        player_id: Player performing the action

    Returns:
        ACTION message
    """
    return Message(
        type=MessageType.ACTION,
        payload={"action": action_name, "params": params, "player_id": player_id},
    )


def create_state_update_message(state: dict[str, Any], player_id: int | None = None) -> Message:
    """Create a state update message.

    Args:
        state: Game state (may be filtered for specific player)
        player_id: Target player (None for broadcast)

    Returns:
        STATE_UPDATE message
    """
    return Message(
        type=MessageType.STATE_UPDATE,
        payload={"state": state, "player_id": player_id},
    )


def create_turn_change_message(current_player: int, turn_number: int) -> Message:
    """Create a turn change notification.

    Args:
        current_player: Player whose turn it now is
        turn_number: Current turn number

    Returns:
        TURN_CHANGE message
    """
    return Message(
        type=MessageType.TURN_CHANGE,
        payload={"current_player": current_player, "turn_number": turn_number},
    )


def create_error_message(error: str, code: str | None = None) -> Message:
    """Create an error message.

    Args:
        error: Human-readable error message
        code: Optional error code for programmatic handling

    Returns:
        ERROR message
    """
    return Message(
        type=MessageType.ERROR,
        payload={"error": error, "code": code},
    )
