"""Authoritative multiplayer server (TCP, NDJSON)."""

from __future__ import annotations

from dataclasses import dataclass
import socket
import threading
from typing import Any

from renee.actions import ActionPipeline
from renee.errors import ReneeError
from renee.multiplayer.persistence import EventLog
from renee.multiplayer.protocol import recv_message, send_message
from renee.multiplayer.serialization import event_to_dict, to_jsonable, world_to_dict
from renee.turns import TurnManager
from renee.types import EntityId


@dataclass
class _Client:
    client_id: int
    sock: socket.socket
    addr: tuple[str, int]
    player: EntityId | None = None


class MultiplayerServer:
    def __init__(
        self,
        *,
        pipeline: ActionPipeline,
        host: str = "127.0.0.1",
        port: int = 8765,
        event_log_path: str | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.host = host
        self.port = port
        self._sock: socket.socket | None = None
        self._accept_thread: threading.Thread | None = None
        self._running = threading.Event()
        self._clients: dict[int, _Client] = {}
        self._clients_lock = threading.Lock()
        self._next_client_id = 1
        self._action_lock = threading.Lock()
        self._event_log = EventLog(event_log_path) if event_log_path else None

        # Replay persisted events (async mode) if available.
        if self._event_log is not None:
            for ev in self._event_log.load():
                t = str(ev.get("type", ""))
                if t.startswith("ecs.") or t.startswith("turn."):
                    self.pipeline.apply_event(ev["type"], ev.get("payload", {}), strict=False)  # type: ignore[arg-type]

    def start(self) -> None:
        if self._running.is_set():
            return
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        # If port=0, the OS picked an available port.
        self.port = int(self._sock.getsockname()[1])
        self._sock.listen()
        self._running.set()
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

    def stop(self) -> None:
        self._running.clear()
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None
        with self._clients_lock:
            for c in list(self._clients.values()):
                try:
                    c.sock.close()
                except OSError:
                    pass
            self._clients.clear()

    def _accept_loop(self) -> None:
        assert self._sock is not None
        while self._running.is_set():
            try:
                client_sock, addr = self._sock.accept()
            except OSError:
                break
            client_id = self._next_client_id
            self._next_client_id += 1
            client = _Client(client_id=client_id, sock=client_sock, addr=(addr[0], addr[1]))
            with self._clients_lock:
                self._clients[client_id] = client
            threading.Thread(target=self._client_loop, args=(client,), daemon=True).start()

    def _client_loop(self, client: _Client) -> None:
        sock = client.sock
        fileobj = sock.makefile("r", encoding="utf-8")
        try:
            while self._running.is_set():
                msg = recv_message(fileobj)
                if msg is None:
                    break
                self._handle_message(client, msg)
        finally:
            with self._clients_lock:
                self._clients.pop(client.client_id, None)
            try:
                sock.close()
            except OSError:
                pass

    def _handle_message(self, client: _Client, msg: dict[str, Any]) -> None:
        t = msg.get("type")
        if t == "join":
            self._handle_join(client)
            return
        if t == "action":
            self._handle_action(client, msg)
            return
        if t == "ping":
            send_message(client.sock, {"type": "pong"})
            return
        send_message(client.sock, {"type": "error", "error": {"message": f"Unknown message type: {t}"}})

    def _handle_join(self, client: _Client) -> None:
        turns = self.pipeline.turns
        if turns is not None:
            client.player = self._assign_player(turns)
        snapshot = {
            "world": world_to_dict(self.pipeline.world),
            "turns": turns.to_dict() if turns is not None else None,
        }
        send_message(
            client.sock,
            {
                "type": "welcome",
                "client_id": client.client_id,
                "player_id": None if client.player is None else int(client.player),
                "snapshot": to_jsonable(snapshot),
            },
        )

    def _assign_player(self, turns: TurnManager) -> EntityId | None:
        with self._clients_lock:
            assigned = {c.player for c in self._clients.values() if c.player is not None}
        for p in turns.players:
            if p not in assigned:
                return p
        return None

    def _handle_action(self, client: _Client, msg: dict[str, Any]) -> None:
        if client.player is None and self.pipeline.turns is not None:
            send_message(client.sock, {"type": "error", "error": {"message": "Client not assigned a player"}})
            return

        action = str(msg.get("action", ""))
        params = msg.get("params", {}) or {}
        if not isinstance(params, dict):
            send_message(client.sock, {"type": "error", "error": {"message": "params must be an object"}})
            return

        actor = client.player
        with self._action_lock:
            try:
                result = self.pipeline.execute(action, actor=actor, params=params)
            except ReneeError as e:
                send_message(client.sock, {"type": "error", "error": e.to_dict()})
                return
            except Exception as e:  # noqa: BLE001
                send_message(
                    client.sock,
                    {"type": "error", "error": {"message": str(e), "code": "server_error"}},
                )
                return

            events = [event_to_dict(ev) for ev in result.events]
            if self._event_log is not None:
                # Persist only the raw event dicts.
                self._event_log.append(
                    [{"type": ev["type"], "payload": ev.get("payload", {}), "meta": ev["meta"]} for ev in events]
                )
            for ev in events:
                self._broadcast({"type": "event", "event": ev})

    def _broadcast(self, message: dict[str, Any]) -> None:
        with self._clients_lock:
            clients = list(self._clients.values())
        for c in clients:
            try:
                send_message(c.sock, message)
            except OSError:
                continue
