from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
import json

from tooling_showcase.state_io import path_lock


class EventJournal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload: dict) -> None:
        record = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        with path_lock(self.path):
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(_normalize(record), sort_keys=True))
                handle.write("\n")

    def tail(self, limit: int = 10) -> list[dict]:
        with path_lock(self.path):
            if not self.path.exists():
                return []
            lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-limit:]]


def _normalize(value):
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value
