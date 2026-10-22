"""Small append-only audit log for local service operations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class AuditLog:
    """Write metadata-only JSON Lines events when a path is configured."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._lock = Lock()

    def record(self, event: str, **details: Any) -> None:
        if self.path is None:
            return
        payload = {
            "occurred_at": datetime.now(UTC).isoformat(),
            "event": event,
            **details,
        }
        line = json.dumps(payload, sort_keys=True) + "\n"
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()


__all__ = ["AuditLog"]
