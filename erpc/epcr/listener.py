"""Socket.IO 長連線 → 新案件或 6 欄變更就推播。"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from . import telegram
from .card import fmt_card
from .config import CFG
from .models import cases_from_event, should_push
from .seen import Seen
from .socketio import iter_events

log = logging.getLogger("epcr")


class Listener:
    def __init__(self) -> None:
        self.seen = Seen(CFG.seen_path)
        self.events = 0
        self.pushed = 0
        self._last_hb = 0.0
        self._last_pkt = 0.0

    def _on_packet(self, pkt: dict[str, Any]) -> None:
        now = time.time()
        self._last_pkt = now
        kind = pkt.get("kind")
        if kind == "event":
            self.events += 1
            log.info(
                "event name=%s args=%s",
                pkt.get("name"),
                json.dumps(pkt.get("args"), ensure_ascii=False, default=str)[:500],
            )
        elif kind in {"open", "ns_connect", "ns_error", "disconnect"}:
            log.info("eio %s %s", kind, {k: pkt.get(k) for k in ("sid", "ns", "data", "error") if pkt.get(k)})
        if now - self._last_hb >= 60:
            self._last_hb = now
            log.info(
                "hb events=%d pushed=%d dest=%s",
                self.events,
                self.pushed,
                "dry" if CFG.dry_run else (CFG.chat_id or "none"),
            )

    def handle_event(self, pkt: dict[str, Any]) -> int:
        n = 0
        for case in cases_from_event(pkt):
            ok, reason = should_push(case, ntpc_only=CFG.ntpc_only)
            if not ok:
                log.info("skip %s %s", reason, case.get("caseNo") or case.get("address"))
                continue
            key = f"epcr|{case.get('caseNo') or case.get('address')}"
            fp = case.get("fingerprint") or ""
            if not self.seen.changed(key, fp):
                continue
            card = fmt_card(case)
            sent, body = telegram.send(card, case)
            if sent:
                self.seen.mark(key, fp)
                self.seen.save()
                self.pushed += 1
                n += 1
                log.info("PUSH %s %s", case.get("caseNo"), (case.get("address") or "")[:40])
            else:
                log.warning("FAIL %s %s", key, body[:120])
        return n

    def run_forever(self) -> None:
        log.info(
            "epcr socket listen ws=%s proxy=%s ntpc_only=%s",
            CFG.ws_url,
            CFG.proxy,
            CFG.ntpc_only,
        )
        for pkt in iter_events(on_packet=self._on_packet):
            try:
                self.handle_event(pkt)
            except Exception:
                log.exception("handle event")


def listen_seconds(
    seconds: float,
    *,
    dump_all: bool = True,
    upgrade: bool = False,
) -> list[dict[str, Any]]:
    """polling 握手拿 sid，再抓一段時間的 packet。"""
    from .polling import Capture, summarize

    cap = Capture()
    packets = cap.run(seconds=seconds, upgrade=upgrade, emit=False)
    if dump_all:
        for pkt in packets:
            slim = {k: pkt.get(k) for k in ("kind", "via", "name", "args", "ns", "data", "raw", "status", "error") if k in pkt}
            print(json.dumps(slim, ensure_ascii=False, default=str)[:2000], flush=True)
        print(json.dumps(summarize(packets), ensure_ascii=False), flush=True)
    path = CFG.data_dir / "capture.jsonl"
    path.write_text(
        "\n".join(json.dumps(p, ensure_ascii=False, default=str) for p in packets) + "\n",
        encoding="utf-8",
    )
    log.info("wrote %s (%d packets)", path, len(packets))
    return packets
