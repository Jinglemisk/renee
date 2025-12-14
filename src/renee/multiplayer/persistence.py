"""Disk persistence for asynchronous play.

This is intentionally simple: append events to an NDJSON log, and optionally
write periodic snapshots elsewhere.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class EventLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, events: Iterable[dict[str, Any]]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, separators=(",", ":")) + "\n")

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                events.append(json.loads(line))
        return events

