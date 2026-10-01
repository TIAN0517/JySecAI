"""EMIC 378 KML 備援（新北緊急救護、處理中、年齡上限）。"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any

from .config import CFG
from .districts import is_ntpc_address
from .models import fingerprint, parse_coordinate, should_push
from .seen import Seen
from . import telegram
from .card import fmt_card

log = logging.getLogger("epcr")
TW = timezone(timedelta(hours=8))


def _field(desc: str, label: str) -> str:
    m = re.search(rf"{re.escape(label)}\s*</td>\s*<td[^>]*>\s*([^<]*)", desc, re.I)
    return m.group(1).strip() if m else ""


def parse_kml(text: str) -> list[dict[str, Any]]:
    now = datetime.now(TW)
    out: list[dict[str, Any]] = []
    for block in re.findall(r"<Placemark>(.*?)</Placemark>", text, re.I | re.S):
        dm = re.search(r"<description>(.*?)</description>", block, re.I | re.S)
        if not dm:
            continue
        desc = unescape(dm.group(1))
        place = _field(desc, "案件地點")
        if "新北" not in place:
            continue
        main = _field(desc, "主要類別")
        sub = _field(desc, "次要類別")
        if "火" in main:
            continue
        st = _field(desc, "處理狀態") or _field(desc, "狀態")
        if st and st not in {"處理中", "已出勤", "已出動", "已派遣"}:
            continue
        tm = _field(desc, "發生時間") or _field(desc, "時間")
        lat = lon = None
        cm = re.search(r"<coordinates>\s*([-\d.]+)\s*,\s*([-\d.]+)", block, re.I)
        if cm:
            try:
                lon, lat = float(cm.group(1)), float(cm.group(2))
            except ValueError:
                lat = lon = None
        dt = None
        t2 = (tm or "").replace("-", "/")[:19]
        for fmt in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
            try:
                dt = datetime.strptime(t2, fmt).replace(tzinfo=TW)
                break
            except ValueError:
                continue
        if dt:
            age = (now - dt).total_seconds() / 60.0
            if age > CFG.emic_max_age_min or age < -5:
                continue
        else:
            continue
        case = {
            "caseNo": f"378|{dt.strftime('%Y%m%d%H%M%S')}|{place[:24]}",
            "address": place,
            "type": sub or main or "緊急救護",
            "branch": "",
            "ambulance": "",
            "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "lat": lat,
            "lon": lon,
            "coordinate": f"{lon:.6f},{lat:.6f}" if lat is not None and lon is not None else "",
        }
        case["fingerprint"] = fingerprint(case)
        out.append(case)
    return out


class EmicFeed:
    def __init__(self, seen: Seen | None = None) -> None:
        self.seen = seen or Seen(CFG.seen_path)
        self._last_hb = 0.0
        self.pushed = 0

    def tick(self) -> int:
        path = CFG.emic_kml
        if not path.is_file():
            return 0
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return 0
        rows = parse_kml(text)
        now = time.time()
        if now - self._last_hb >= 60:
            self._last_hb = now
            log.info("emic hb rows=%d pushed=%d", len(rows), self.pushed)
        n = 0
        for case in rows:
            ok, reason = should_push(case, ntpc_only=CFG.ntpc_only)
            if not ok:
                continue
            key = f"emic|{case['caseNo']}"
            if self.seen.has(key):
                continue
            sent, body = telegram.send(fmt_card(case), case)
            if sent:
                self.seen.mark(key, case.get("fingerprint") or "")
                self.seen.save()
                self.pushed += 1
                n += 1
                log.info("PUSH emic %s %s", case.get("type"), (case.get("address") or "")[:40])
            else:
                log.warning("FAIL emic %s", body[:120])
        return n
