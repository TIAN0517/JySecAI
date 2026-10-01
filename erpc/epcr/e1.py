"""新北 E1 公開救援圖層（免登入）。卡片走統一出勤通報模板，不外洩來源。"""
from __future__ import annotations

import json
import logging
import math
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from . import telegram
from .card import fmt_card
from .config import CFG
from .dest import targets
from .http import curl
from .models import fingerprint, should_push
from .seen import Seen

log = logging.getLogger("epcr")
TW = timezone(timedelta(hours=8))
SKIP_TYPES = {"Fire", "FireV2"}
# 舊邏輯（沒帳密也能推）：圖層上車＝有案。
# Ambulance＝往現場，案發點＝path 終點；AmbulanceBack＝送醫，案發點＝startPoint（不是醫院）。
KIND = {"Ambulance": "緊急救護", "AmbulanceBack": "緊急救護・後送"}

if "/opt/emic-push" not in sys.path:
    sys.path.append("/opt/emic-push")


def _layer_features(blob: dict) -> list:
    data = blob.get("data")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict):
        feats = data.get("features") or []
        if not feats and isinstance(data.get("layer_geojson"), str):
            try:
                feats = json.loads(data["layer_geojson"]).get("features") or []
            except json.JSONDecodeError:
                feats = []
        return feats if isinstance(feats, list) else []
    return []


def fetch_layer() -> dict | None:
    result = curl(
        CFG.e1_url,
        headers={
            "Referer": "https://e1.ntpc.gov.tw/",
            "Accept": "application/json",
        },
        timeout=15,
        retries=2,
    )
    if result.status != 200:
        log.warning("e1 http=%s %s", result.status, result.error[:120])
        return None
    try:
        return result.json()
    except Exception as exc:
        log.warning("e1 json: %s", exc)
        return None


def _path_points(p: dict[str, Any]) -> list[tuple[float, float]]:
    cl = p.get("caseList") or []
    item = cl[0] if isinstance(cl, list) and cl and isinstance(cl[0], dict) else None
    path = (item.get("path") if item else None) or []
    out: list[tuple[float, float]] = []
    if not isinstance(path, list):
        return out
    for pt in path:
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            continue
        try:
            out.append((float(pt[0]), float(pt[1])))
        except (TypeError, ValueError):
            continue
    return out


def parse_features(blob: dict) -> list[dict[str, Any]]:
    now = datetime.now(TW)
    out: list[dict[str, Any]] = []
    for f in _layer_features(blob):
        p = f.get("properties") or {}
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates") or []
        lng, lat = p.get("lng"), p.get("lat")
        if lat is None and isinstance(coords, list) and len(coords) >= 2:
            lng, lat = coords[0], coords[1]
        try:
            lat_f, lon_f = float(lat), float(lng)
        except (TypeError, ValueError):
            continue
        typ = str(p.get("type") or "")
        if typ in SKIP_TYPES or typ not in KIND:
            continue
        cl = p.get("caseList") or []
        item = cl[0] if isinstance(cl, list) and cl and isinstance(cl[0], dict) else None
        car_name = ""
        if item and item.get("startPointInfo"):
            car_name = str(item["startPointInfo"]).strip()
        pts = _path_points(p)
        if typ == "AmbulanceBack":
            start_pt = item.get("startPoint") if item else None
            if isinstance(start_pt, (list, tuple)) and len(start_pt) >= 2:
                try:
                    scene_lat, scene_lon = float(start_pt[0]), float(start_pt[1])
                except (TypeError, ValueError):
                    scene_lat, scene_lon = (pts[0] if pts else (None, None))
            else:
                scene_lat, scene_lon = (pts[0] if pts else (None, None))
        else:
            scene_lat, scene_lon = (pts[-1] if pts else (lat_f, lon_f))
            if scene_lat is None:
                scene_lat, scene_lon = lat_f, lon_f
        if scene_lat is None:
            continue
        fid = str(p.get("featureId") or f"{typ}|{scene_lat:.5f}|{scene_lon:.5f}|{car_name}")
        branch, amb = _split_unit(car_name)
        out.append(
            {
                "feature_id": fid,
                "e1_type": typ,
                "caseNo": f"E1|{fid}",
                "address": "",
                "type": KIND[typ],
                "branch": branch,
                "ambulance": amb or car_name,
                "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "lat": scene_lat,
                "lon": scene_lon,
                "veh_lat": lat_f,
                "veh_lon": lon_f,
                "coordinate": f"{scene_lon:.6f},{scene_lat:.6f}",
                "city": "新北市",
                "source": "E1",
            }
        )
    return out


def scene_keys(c: dict[str, Any]) -> list[str]:
    fid = str(c.get("feature_id") or "")
    raw = str(c.get("caseNo") or fid)
    if raw.startswith("E1|"):
        raw = raw[3:]
    keys = [f"e1|{fid or raw}"]
    addr = (c.get("address") or "").strip()
    if addr and "E1 車軌" not in addr:
        keys.append(f"p|{addr}")
    try:
        keys.append(f"xy|{float(c['lat']):.4f}|{float(c['lon']):.4f}")
    except (TypeError, ValueError, KeyError):
        pass
    return [k for k in keys if k and k not in {"e1|", "p|"}]


def _split_unit(name: str) -> tuple[str, str]:
    text = (name or "").strip()
    if not text:
        return "", ""
    m = re.match(r"^(.+?分隊)\s*(.*)$", text)
    if m:
        return m.group(1).strip(), (m.group(2) or text).strip()
    return "", text


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def mark_dual(rows: list[dict[str, Any]]) -> None:
    for i, a in enumerate(rows):
        for b in rows[i + 1 :]:
            try:
                d = haversine_m(float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"]))
            except (TypeError, ValueError, KeyError):
                continue
            if d <= 80:
                a["type"] = "疑似OHCA(雙軌)"
                b["type"] = "疑似OHCA(雙軌)"


def enrich(c: dict[str, Any]) -> None:
    try:
        from kh_reverse import enrich_public_case
    except Exception as exc:
        log.warning("reverse import: %s", exc)
        return
    if c.get("lat") is None:
        return
    row = {
        "lat": c["lat"],
        "lon": c["lon"],
        "address": "",
        "place": "",
        "raw_official_addr": "",
        "city": "新北市",
        "city_norm": "新北市",
    }
    try:
        enrich_public_case(row, city="新北市")
    except Exception as exc:
        log.warning("enrich fail %s: %s", c.get("caseNo"), exc)
        return
    addr = (row.get("address") or row.get("place") or "").strip()
    if addr:
        c["address"] = addr
        c["addr_src"] = row.get("addr_src") or ""


def to_push_case(c: dict[str, Any]) -> dict[str, Any]:
    addr = (c.get("address") or "").strip()
    if not addr:
        addr = "新北市"
    out = {
        "caseNo": c.get("caseNo") or "",
        "address": addr,
        "type": c.get("type") or "緊急救護",
        "e1_type": c.get("e1_type") or "",
        "branch": c.get("branch") or "",
        "ambulance": c.get("ambulance") or "",
        "time": c.get("time") or "",
        "coordinate": c.get("coordinate") or "",
        "lat": c.get("lat"),
        "lon": c.get("lon"),
        "source": "E1",
    }
    out["fingerprint"] = fingerprint(out)
    return out


class E1Feed:
    def __init__(self, seen: Seen | None = None) -> None:
        self.seen = seen or Seen(CFG.seen_path)
        self._seeded = any(str(k).startswith("e1|") for k in self.seen._data)
        self._last_hb = 0.0
        self.pushed = 0
        self._sample: dict[str, Any] | None = None

    def tick(self) -> int:
        blob = fetch_layer()
        dests = targets()
        feats = _layer_features(blob) if blob else []
        types: dict[str, int] = {}
        for f in feats:
            t = str((f.get("properties") or {}).get("type") or "?")
            types[t] = types.get(t, 0) + 1
        if not blob:
            log.warning("e1 poll source=E1 http=fail go=0 back=0 rows=0 new=0")
            return 0
        rows = parse_features(blob)
        mark_dual(rows)
        if rows:
            self._sample = to_push_case(rows[0])
        if not self._seeded:
            for c in rows:
                for k in scene_keys(c):
                    self.seen.mark(k, "seed")
            self.seen.save()
            self._seeded = True
            log.info(
                "e1 poll source=E1 http=200 go=%d back=%d rows=%d new=0 seed=%d dests=%d",
                types.get("Ambulance", 0),
                types.get("AmbulanceBack", 0),
                len(rows),
                len(rows),
                len(dests),
            )
            return 0
        n = 0
        for c in rows:
            keys = scene_keys(c)
            if any(self.seen.has(k) for k in keys):
                continue
            enrich(c)
            case = to_push_case(c)
            keys = scene_keys({**c, **case})
            if any(self.seen.has(k) for k in keys):
                continue
            ok, reason = should_push(
                case, ntpc_only=CFG.ntpc_only, allow_empty_address=True
            )
            if not ok:
                log.info(
                    "e1 skip %s %s %s",
                    reason,
                    c.get("e1_type"),
                    (case.get("address") or c.get("caseNo") or "")[:36],
                )
                if reason in {"non_ntpc", "hosp_addr"}:
                    for k in keys:
                        self.seen.mark(k, reason)
                continue
            sent, body = telegram.send(fmt_card(case), case)
            if sent:
                for k in keys:
                    self.seen.mark(k, case.get("fingerprint") or "")
                self.seen.save()
                self.pushed += 1
                n += 1
                self._sample = case
                log.info(
                    "PUSH e1 source=E1 %s %s %s",
                    c.get("e1_type"),
                    case.get("type"),
                    (case.get("address") or "")[:40],
                )
            else:
                log.warning("FAIL e1 %s %s", keys[0], body[:120])
        extra = ""
        if n == 0:
            extra = " 本輪 0 筆新案"
        log.info(
            "e1 poll source=E1 http=200 go=%d back=%d rows=%d new=%d dests=%d%s",
            types.get("Ambulance", 0),
            types.get("AmbulanceBack", 0),
            len(rows),
            n,
            len(dests),
            extra,
        )
        return n

    def run_forever(self) -> None:
        dests = targets()
        log.info(
            "e1 feed start interval=%ss dests=%s proxy=%s",
            CFG.e1_interval,
            ",".join(str(t.get("tenant")) for t in dests) or "none",
            CFG.proxy,
        )
        while True:
            started = time.monotonic()
            try:
                self.tick()
            except KeyboardInterrupt:
                raise
            except Exception:
                log.exception("e1 tick")
            time.sleep(max(1.0, CFG.e1_interval - (time.monotonic() - started)))
