"""Multiplayer client (TCP, NDJSON)."""

from __future__ import annotations

import socket
import threading
from typing import Any

from renee.actions import ActionPipeline
from renee.errors import ReneeError, ValidationError
from renee.multiplayer.protocol import recv_message, send_message
from renee.multiplayer.serialization import world_from_dict
from renee.turns import TurnManager
from renee.types import EntityId


class MultiplayerClient:
    def __init__(
        self,
        *,
        pipeline: ActionPipeline,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.pipeline = pipeline
        self.host = host
        self.port = port
        self.player_id: EntityId | None = None
        self._sock: socket.socket | None = None
        self._fileobj = None
        self._recv_thread: threading.Thread | None = None
        self._running = threading.Event()
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self.last_error: ReneeError | None = None

    @property
    def events(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events)

    def connect(self) -> None:
        if self._running.is_set():
            return
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self.host, self.port))
        self._fileobj = self._sock.makefile("r", encoding="utf-8")
        self._running.set()

        send_message(self._sock, {"type": "join"})
        welcome = recv_message(self._fileobj)
        if welcome is None or welcome.get("type") != "welcome":
            raise ValidationError("handshake_failed", "Did not receive welcome from server.")

        pid = welcome.get("player_id")
        self.player_id = None if pid is None else EntityId(int(pid))

        snapshot = welcome.get("snapshot", {}) or {}
        world_data = snapshot.get("world", {})
        turns_data = snapshot.get("turns")

        # Replace local state with snapshot.
        self.pipeline.world = world_from_dict(world_data, schemas=self.pipeline.schemas)
        if turns_data is not None:
            self.pipeline.turns = TurnManager.from_dict(turns_data)

        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def disconnect(self) -> None:
        self._running.clear()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def send_action(self, action: str, params: dict[str, Any]) -> None:
        if self._sock is None:
            raise ValidationError("not_connected", "Client is not connected.")
        send_message(self._sock, {"type": "action", "action": action, "params": params})

    def _recv_loop(self) -> None:
        assert self._fileobj is not None
        try:
            while self._running.is_set():
                msg = recv_message(self._fileobj)
                if msg is None:
                    break
                self._handle_message(msg)
        finally:
            self._running.clear()

    def _handle_message(self, msg: dict[str, Any]) -> None:
        t = msg.get("type")
        if t == "event":
            event = msg.get("event", {}) or {}
            if not isinstance(event, dict):
                return
            with self._lock:
                self._events.append(event)
            et = str(event.get("type", ""))
            payload = event.get("payload", {}) or {}
            if (et.startswith("ecs.") or et.startswith("turn.")) and isinstance(payload, dict):
                self.pipeline.apply_event(et, payload, strict=True)
            return

        if t == "error":
            err = msg.get("error", {}) or {}
            self.last_error = ReneeError(
                code=str(err.get("code", "remote_error")),
                message=str(err.get("message", "Remote error")),
                hint=err.get("hint"),
                context=err.get("context"),
            )
            self._running.clear()
            return
