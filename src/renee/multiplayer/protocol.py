"""NDJSON protocol helpers (one JSON message per line)."""

from __future__ import annotations

import json
import socket
from typing import Any


def send_message(sock: socket.socket, message: dict[str, Any]) -> None:
    data = (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")
    sock.sendall(data)


def recv_message(fileobj) -> dict[str, Any] | None:
    line = fileobj.readline()
    if not line:
        return None
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    return json.loads(line)

