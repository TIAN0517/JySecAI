"""Telegram sendMessage，可扇出多 bot／群。"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from .card import telegram_send_options
from .config import CFG
from .dest import targets

log = logging.getLogger("epcr")


def send_one(token: str, chat_id: Any, text: str, case: dict[str, Any] | None = None) -> tuple[bool, str]:
    if CFG.dry_run:
        log.info("DRY_RUN chat=%s\n%s", chat_id, text)
        return True, "dry_run"
    token = (token or "").strip()
    chat = str(chat_id or "").strip()
    if not token or not chat:
        return False, "missing token/chat"
    payload: dict[str, Any] = telegram_send_options(case, text=text)
    payload["chat_id"] = chat
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace"))
            if body.get("ok"):
                return True, "ok"
            return False, str(body)[:160]
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", "replace")[:200]
        return False, f"http={exc.code} {err}"
    except Exception as exc:
        return False, str(exc)[:160]


def send(text: str, case: dict[str, Any] | None = None) -> tuple[bool, str]:
    dests = targets()
    if not dests:
        return send_one(CFG.bot_token, CFG.chat_id, text, case)
    any_ok = False
    last = "no_dest"
    for tgt in dests:
        ok, body = send_one(tgt["token"], tgt["chat_id"], text, case)
        if ok:
            any_ok = True
            log.info("PUSH tenant=%s chat=%s", tgt.get("tenant"), tgt.get("chat_id"))
        else:
            log.warning("FAIL tenant=%s chat=%s %s", tgt.get("tenant"), tgt.get("chat_id"), body[:120])
            last = body
    return (True, "ok") if any_ok else (False, last)
