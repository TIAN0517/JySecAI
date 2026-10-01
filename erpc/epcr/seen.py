"""去重。key → fingerprint；成功推播才標記。"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

log = logging.getLogger("epcr")


class Seen:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, dict] = {}
        self._dirty = False
        if path.exists():
            try:
                blob = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                log.warning("seen load fail: %s", exc)
                blob = {}
            if isinstance(blob, dict):
                for key, value in blob.items():
                    if isinstance(value, dict):
                        self._data[str(key)] = value
                    else:
                        self._data[str(key)] = {"ts": float(value), "fp": ""}

    def fp(self, key: str) -> str:
        row = self._data.get(key) or {}
        return str(row.get("fp") or "")

    def has(self, key: str) -> bool:
        return bool(key) and key in self._data

    def changed(self, key: str, fingerprint: str) -> bool:
        if not key:
            return True
        return self.fp(key) != fingerprint

    def mark(self, key: str, fingerprint: str = "") -> None:
        if not key:
            return
        self._data[key] = {"ts": time.time(), "fp": fingerprint}
        self._dirty = True

    def save(self, *, prune_days: float = 3.0) -> None:
        if not self._dirty:
            return
        cutoff = time.time() - prune_days * 86400
        self._data = {
            k: v for k, v in self._data.items() if float(v.get("ts") or 0) >= cutoff
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
        self._dirty = False
