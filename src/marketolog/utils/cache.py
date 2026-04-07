"""File-based TTL cache.

Storage: ~/.marketolog/cache/<namespace>/<key_hash>.json
Each file contains: {"data": ..., "expires_at": <unix_timestamp>}
No external dependencies.
"""

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any


class FileCache:
    """Simple file-based cache with TTL per entry."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)

    def _key_path(self, namespace: str, key: str) -> Path:
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.base_dir / namespace / f"{key_hash}.json"

    def get(self, namespace: str, key: str) -> Any | None:
        """Return cached value or None if missing/expired."""
        path = self._key_path(namespace, key)
        if not path.exists():
            return None

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        if time.time() > raw.get("expires_at", 0):
            path.unlink(missing_ok=True)
            return None

        return raw.get("data")

    def set(self, namespace: str, key: str, data: Any, *, ttl_seconds: int) -> None:
        """Store value with TTL."""
        path = self._key_path(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "data": data,
            "expires_at": time.time() + ttl_seconds,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def clear(self, namespace: str) -> None:
        """Remove all entries in a namespace."""
        ns_dir = self.base_dir / namespace
        if ns_dir.exists():
            shutil.rmtree(ns_dir)
