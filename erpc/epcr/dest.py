"""推播目標：指定客戶群。試車群預設停用，驗收卡不提群組數量。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import ROOT, _flag


def dest_path() -> Path:
    return ROOT / "data" / "destinations.json"


def load_destinations() -> dict[str, Any]:
    path = dest_path()
    if not path.is_file():
        return {"customers": [], "test": {}, "mirror_test": True, "push_customers": True}
    return json.loads(path.read_text(encoding="utf-8"))


def targets() -> list[dict[str, Any]]:
    blob = load_destinations()
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    if blob.get("push_customers", True) and _flag("EPCR_PUSH_CUSTOMERS", "1"):
        for row in blob.get("customers") or []:
            if not row.get("active", True):
                continue
            token = str(row.get("token") or "").strip()
            chat = str(row.get("chat_id") or "").strip()
            if not token or not chat:
                continue
            key = (token, chat)
            if key in seen:
                continue
            seen.add(key)
            out.append(row)
    test = blob.get("test") or {}
    mirror = bool(blob.get("mirror_test", True)) and _flag("EPCR_MIRROR_TEST", "1")
    if mirror:
        token = str(test.get("token") or "").strip()
        chat = str(test.get("chat_id") or "").strip()
        key = (token, chat)
        if token and chat and key not in seen:
            out.append({**test, "tenant": test.get("tenant") or "test"})
    return out
