from __future__ import annotations

from pathlib import Path
from threading import RLock
import json
import os
import tempfile


_LOCKS: dict[Path, RLock] = {}
_LOCKS_GUARD = RLock()


def path_lock(path: Path) -> RLock:
    resolved = path.resolve()
    with _LOCKS_GUARD:
        lock = _LOCKS.get(resolved)
        if lock is None:
            lock = RLock()
            _LOCKS[resolved] = lock
        return lock


def read_json(path: Path, default):
    with path_lock(path):
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path_lock(path):
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            tmp_path = Path(tmp_name)
            if tmp_path.exists():
                tmp_path.unlink()


def atomic_write_json(path: Path, payload) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True))
