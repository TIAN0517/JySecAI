"""主源：每 10 秒 GET /DispatchRecords StatusId 5/6（剛派遣／已出動）。"""
from __future__ import annotations

import logging
import time
from typing import Any

from . import telegram
from .card import fmt_card
from .client import EpcrClient
from .config import CFG
from .dest import targets
from .models import (
    extract_case,
    fingerprint,
    merge_case_main,
    parse_case_main,
    should_push,
    summarize_dispatch,
)
from .seen import Seen
from .tokens import TokenManager

log = logging.getLogger("epcr")


def _enrich(client: EpcrClient, case: dict[str, Any], cache: dict[str, dict]) -> dict[str, Any]:
    case_no = case.get("case_no") or case.get("caseNo") or ""
    if not case_no:
        return case
    cached = cache.get(case_no)
    if cached is None:
        cached = {}
        code, data = client.case_main(case_no)
        if code == 200:
            cached = parse_case_main(data)
        if not cached.get("kind"):
            t_code, t_data = client.case_type_name(case_no)
            if t_code == 200 and isinstance(t_data, dict):
                cached["kind"] = str(t_data.get("CaseTypeName") or "").strip()
        if not cached.get("address"):
            d_code, d_data = client.case_description(case_no)
            if d_code == 200:
                extra = extract_case(d_data) or {}
                if extra.get("address"):
                    cached["address"] = extra["address"]
                if extra.get("type") and not cached.get("kind"):
                    cached["kind"] = extra["type"]
        cache[case_no] = cached
    return merge_case_main(case, cached)


def to_card(case: dict[str, Any]) -> dict[str, Any]:
    out = {
        "caseNo": case.get("case_no") or case.get("caseNo") or "",
        "address": case.get("address") or "",
        "type": case.get("sub") or case.get("kind") or case.get("type") or "緊急救護",
        "branch": case.get("branch") or "",
        "ambulance": case.get("ambulance") or "",
        "time": case.get("time_norm") or case.get("time") or "",
        "coordinate": case.get("coordinate") or "",
        "lat": case.get("lat"),
        "lon": case.get("lon"),
    }
    if not out["coordinate"] and out["lat"] is not None and out["lon"] is not None:
        try:
            out["coordinate"] = f"{float(out['lon']):.6f},{float(out['lat']):.6f}"
        except (TypeError, ValueError):
            pass
    out["fingerprint"] = fingerprint(out)
    return out


class EpcrFeed:
    def __init__(self, tokens: TokenManager | None = None) -> None:
        self.tokens = tokens or TokenManager()
        self.client = EpcrClient(self.tokens)
        self.seen = Seen(CFG.seen_path)
        self._seeded = any(str(k).startswith("epcr|") for k in self.seen._data)
        self._main_cache: dict[str, dict] = {}
        self._last_hb = 0.0
        self.pushed = 0
        self.last_ok = False

    def tick(self) -> int:
        if not self.tokens.ensure():
            self.last_ok = False
            return 0
        code, raw = self.client.go_dispatches()
        if code != 200:
            self.last_ok = False
            log.warning("DispatchRecords http=%s", code)
            return 0
        self.last_ok = True
        rows = []
        allowed = set(CFG.go_status_ids)
        for item in raw:
            if not isinstance(item, dict):
                continue
            if item.get("leftAt") or item.get("left_at"):
                continue
            try:
                sid = int(item.get("StatusId") or item.get("statusId") or 0)
            except (TypeError, ValueError):
                sid = 0
            summary = summarize_dispatch(item)
            if not summary and sid in allowed:
                extra = extract_case(item)
                if extra:
                    summary = {
                        "case_no": extra.get("caseNo"),
                        "address": extra.get("address"),
                        "ambulance": extra.get("ambulance"),
                        "branch": extra.get("branch"),
                        "time_norm": extra.get("time"),
                        "lat": extra.get("lat"),
                        "lon": extra.get("lon"),
                        "coordinate": extra.get("coordinate"),
                        "status_id": sid,
                        "left_at": None,
                    }
            if summary:
                rows.append(summary)
        if not self._seeded:
            n = 0
            for row in rows:
                cid = row.get("case_no") or row.get("dispatch_uuid")
                if cid:
                    self.seen.mark(f"epcr|{cid}", "seed")
                    n += 1
            self.seen.save()
            self._seeded = True
            log.info(
                "epcr seed %d (不推現有進行中) http=200 rows=%d API 200 但本輪 0 筆新案 remaining=%.0fs",
                n,
                len(rows),
                self.tokens.remaining(),
            )
            return 0
        pushed = 0
        for row in rows:
            cid = row.get("case_no") or row.get("dispatch_uuid")
            if not cid:
                continue
            key = f"epcr|{cid}"
            if self.seen.has(key):
                continue
            row = _enrich(self.client, row, self._main_cache)
            case = to_card(row)
            ok, reason = should_push(
                case,
                ntpc_only=CFG.ntpc_only,
                taipei_only=CFG.taipei_only,
            )
            if not ok:
                log.info("epcr skip %s %s %s", reason, cid, (case.get("address") or "")[:36])
                if reason in {"non_ntpc", "non_taipei", "hosp_addr"}:
                    self.seen.mark(key, reason)
                continue
            sent, body = telegram.send(fmt_card(case), case)
            if sent:
                self.seen.mark(key, case.get("fingerprint") or "")
                self.seen.save()
                self.pushed += 1
                pushed += 1
                log.info("PUSH epcr %s %s", case.get("type"), (case.get("address") or "")[:40])
            else:
                log.warning("FAIL epcr %s %s", key, body[:120])
        if pushed == 0:
            log.info(
                "epcr poll http=%s rows=%d new=0 API 200 但本輪 0 筆新案 remaining=%.0fs dests=%s",
                code,
                len(rows),
                self.tokens.remaining(),
                len(targets()),
            )
        else:
            log.info(
                "epcr poll http=%s rows=%d new=%d remaining=%.0fs dests=%s",
                code,
                len(rows),
                pushed,
                self.tokens.remaining(),
                len(targets()),
            )
        return pushed
