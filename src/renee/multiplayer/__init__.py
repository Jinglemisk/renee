"""Multiplayer session management for Renee.

Turn-based games are inherently social. This module provides first-class
multiplayer support with multiple session types:

- LocalSession: Hot-seat multiplayer (players share one device)
- NetworkSession: Client-server multiplayer (real-time)
- AsyncSession: Play-by-email style (asynchronous turns)

All session types share a common GameSession interface for consistency.
"""

from renee.multiplayer.async_session import AsyncSession, AsyncStorage, FileAsyncStorage
from renee.multiplayer.local import LocalSession
from renee.multiplayer.network import NetworkClient, NetworkServer
from renee.multiplayer.protocol import Message, MessageType, encode_message, decode_message
from renee.multiplayer.session import GameSession

__all__ = [
    "GameSession",
    "LocalSession",
    "NetworkClient",
    "NetworkServer",
    "AsyncSession",
    "AsyncStorage",
    "FileAsyncStorage",
    "Message",
    "MessageType",
    "encode_message",
    "decode_message",
]
