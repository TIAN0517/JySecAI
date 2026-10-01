"""從 Socket.IO payload 抽出 6 欄：案號、地址、類型、分隊/車、時間、座標。"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import CFG
from .districts import is_ntpc_address, is_taipei_address

TW = timezone(timedelta(hours=8))
FIELDS = ("caseNo", "address", "type", "branch", "ambulance", "time", "coordinate")
STATUS_ID_MAP = {5: "已派遣", 6: "已出動", 7: "已到達", 8: "執行中"}
HOSP_RE = re.compile(
    r"醫院|診所|衛生所|急診|醫學中心|療養院|"
    r"榮民總醫院|榮總|長庚|馬偕|亞東|慈濟|耕莘|恩主公|"
    r"國泰|新光|台大|臺大|振興|雙和|萬芳|三軍總"
)

_CASE_KEYS = {
    "caseno": "caseNo",
    "case_no": "caseNo",
    "casesn": "caseNo",
    "casenum": "caseNo",
    "recorduuid": "caseNo",
    "record_uuid": "caseNo",
    "caseid": "caseNo",
    "case_id": "caseNo",
}
_ADDR_KEYS = {
    "address": "address",
    "realaddress": "address",
    "location": "address",
    "發生地點": "address",
    "addr": "address",
}
_TYPE_KEYS = {
    "disastermain_type": "type",
    "disastermaintype": "type",
    "casetypename": "type",
    "casetype": "type",
    "kind": "type",
    "type": "type",
    "maintype": "type",
    "派遣原因": "type",
}
_BRANCH_KEYS = {
    "branch": "branch",
    "branchname": "branch",
    "branch_name": "branch",
    "分隊": "branch",
}
_AMB_KEYS = {
    "ambulance": "ambulance",
    "ambulancecode": "ambulance",
    "ambulance_code": "ambulance",
    "licenseno": "ambulance",
    "車牌": "ambulance",
    "車編": "ambulance",
}
_TIME_KEYS = {
    "time": "time",
    "dispatchedat": "time",
    "dispatched_at": "time",
    "createdat": "time",
    "updatedat": "time",
    "departedat": "time",
    "occurredat": "time",
    "casetime": "time",
}
_COORD_KEYS = {
    "coordinate": "coordinate",
    "coordinates": "coordinate",
    "latlng": "coordinate",
    "lnglat": "coordinate",
}


def _s(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def parse_ts(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=TW)
        return value.astimezone(TW)
    if isinstance(value, (int, float)):
        number = float(value)
        if number > 1e12:
            number /= 1000.0
        if number > 1e9:
            return datetime.fromtimestamp(number, timezone.utc).astimezone(TW)
        return None
    text = _s(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        dt = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(text[:19], fmt)
                break
            except ValueError:
                continue
        if dt is None:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TW)
    return dt.astimezone(TW)


def parse_coordinate(raw: Any) -> tuple[float | None, float | None]:
    if raw is None or raw == "":
        return None, None
    if isinstance(raw, dict):
        lat = raw.get("lat") or raw.get("latitude") or raw.get("Y") or raw.get("y")
        lng = raw.get("lng") or raw.get("lon") or raw.get("longitude") or raw.get("X") or raw.get("x")
        return _as_wgs(lat, lng)
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        return _as_wgs(raw[0], raw[1])
    text = _s(raw).replace("，", ",")
    nums = re.findall(r"-?\d+\.?\d*", text)
    if len(nums) < 2:
        return None, None
    return _as_wgs(nums[0], nums[1])


def _as_wgs(a: Any, b: Any) -> tuple[float | None, float | None]:
    try:
        x, y = float(a), float(b)
    except (TypeError, ValueError):
        return None, None
    if 21 <= x <= 26.5 and 118 <= y <= 122.5:
        return x, y
    if 21 <= y <= 26.5 and 118 <= x <= 122.5:
        return y, x
    if 150000 <= x <= 400000 and 2400000 <= y <= 2900000:
        try:
            from .twd97 import tm2_121_to_wgs84

            return tm2_121_to_wgs84(x, y)
        except Exception:
            return None, None
    return None, None


def _norm_key(key: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", key.lower())


def _walk_fill(obj: Any, acc: dict[str, Any], *, depth: int = 0) -> None:
    if depth > 8:
        return
    if isinstance(obj, dict):
        # Ambulance {code, Branch:{name}}
        amb = obj.get("Ambulance") or obj.get("ambulance")
        if isinstance(amb, dict):
            if amb.get("code") and not acc.get("ambulance"):
                acc["ambulance"] = _s(amb.get("code"))
            br = amb.get("Branch") or amb.get("branch")
            if isinstance(br, dict) and br.get("name") and not acc.get("branch"):
                acc["branch"] = _s(br.get("name"))
            elif isinstance(br, str) and not acc.get("branch"):
                acc["branch"] = br.strip()
        cr = obj.get("CaseRecord") or obj.get("caseRecord")
        if isinstance(cr, dict):
            if cr.get("recordUuid") and not acc.get("caseNo"):
                acc["caseNo"] = _s(cr.get("recordUuid"))
            if cr.get("address") and not acc.get("address"):
                acc["address"] = _s(cr.get("address"))
        for key, value in obj.items():
            nk = _norm_key(str(key))
            mapped = (
                _CASE_KEYS.get(nk)
                or _ADDR_KEYS.get(nk)
                or _TYPE_KEYS.get(nk)
                or _BRANCH_KEYS.get(nk)
                or _AMB_KEYS.get(nk)
                or _TIME_KEYS.get(nk)
                or _COORD_KEYS.get(nk)
            )
            if mapped == "coordinate":
                lat, lon = parse_coordinate(value)
                if lat is not None and not acc.get("coordinate"):
                    acc["coordinate"] = f"{lon:.6f},{lat:.6f}"
                    acc["lat"] = lat
                    acc["lon"] = lon
            elif mapped == "time" and not acc.get("time"):
                dt = parse_ts(value)
                if dt:
                    acc["time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            elif mapped and not acc.get(mapped):
                text = _s(value)
                if text and not isinstance(value, (dict, list)):
                    acc[mapped] = text
            if isinstance(value, (dict, list)):
                _walk_fill(value, acc, depth=depth + 1)
        # loose lat/lng on this object
        if not acc.get("coordinate"):
            lat, lon = parse_coordinate(obj)
            if lat is None:
                lat, lon = _as_wgs(
                    obj.get("lat") or obj.get("latitude") or obj.get("currentlatitude"),
                    obj.get("lng") or obj.get("lon") or obj.get("longitude") or obj.get("currentlongitude"),
                )
            if lat is not None:
                acc["coordinate"] = f"{lon:.6f},{lat:.6f}"
                acc["lat"] = lat
                acc["lon"] = lon
    elif isinstance(obj, list):
        for item in obj:
            _walk_fill(item, acc, depth=depth + 1)


def extract_case(payload: Any, *, event: str = "") -> dict[str, Any] | None:
    acc: dict[str, Any] = {}
    _walk_fill(payload, acc)
    if event and not acc.get("type") and event not in {"join", "subscribe", "ping", "pong"}:
        # 不用 event name 當類型，避免 join/gps 誤標
        pass
    case_no = acc.get("caseNo") or ""
    addr = acc.get("address") or ""
    if not case_no and not addr:
        return None
    out = {k: acc.get(k) or "" for k in FIELDS}
    out["lat"] = acc.get("lat")
    out["lon"] = acc.get("lon")
    out["event"] = event
    out["fingerprint"] = fingerprint(out)
    return out


def parse_case_main(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    addr = _s(
        inner.get("address")
        or inner.get("ADDRESS")
        or inner.get("LOCATION")
        or inner.get("realAddress")
    )
    kind = _s(
        inner.get("DISASTERMAIN_TYPE")
        or inner.get("DisasterMainType")
        or inner.get("CaseTypeName")
        or inner.get("caseTypeName")
    )
    lat, lon = parse_coordinate(
        inner.get("COORDINATE") or inner.get("Coordinate") or inner.get("coordinate")
    )
    if lat is None:
        lat, lon = parse_coordinate(
            {"lat": inner.get("lat") or inner.get("Y"), "lng": inner.get("lng") or inner.get("X")}
        )
    return {"address": addr, "kind": kind, "lat": lat, "lon": lon, "raw": inner}


def merge_case_main(case: dict[str, Any], main: dict[str, Any]) -> dict[str, Any]:
    if not main:
        return case
    if main.get("address"):
        if not case.get("address") or len(_s(main["address"])) > len(_s(case.get("address"))):
            case["address"] = main["address"]
    if main.get("kind"):
        case["sub"] = main["kind"]
        case["kind"] = main["kind"]
    if main.get("lat") is not None:
        case["lat"] = main["lat"]
        case["lon"] = main["lon"]
        try:
            case["coordinate"] = f"{float(main['lon']):.6f},{float(main['lat']):.6f}"
        except (TypeError, ValueError):
            pass
    return case


def summarize_dispatch(row: dict) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    uuid = _s(row.get("uuid") or row.get("Uuid") or row.get("id"))
    amb = row.get("Ambulance") if isinstance(row.get("Ambulance"), dict) else {}
    case = row.get("CaseRecord") if isinstance(row.get("CaseRecord"), dict) else {}
    try:
        status_id = int(row.get("StatusId") or row.get("statusId") or 0)
    except (TypeError, ValueError):
        status_id = 0
    if status_id not in CFG.go_status_ids:
        return None
    branch_obj = amb.get("Branch") if isinstance(amb.get("Branch"), dict) else {}
    branch = _s(branch_obj.get("name") if isinstance(branch_obj, dict) else "")
    ambulance = _s(amb.get("code") or row.get("ambulanceCode"))
    case_no = _s(case.get("recordUuid") or row.get("caseNo") or row.get("CaseNo"))
    address = _s(row.get("realAddress") or case.get("address") or row.get("address"))
    dispatched = row.get("dispatchedAt") or row.get("dispatchedAT")
    dt = parse_ts(dispatched) or parse_ts(row.get("departedAt")) or parse_ts(row.get("createdAt"))
    time_norm = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else datetime.now(TW).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "dispatch_uuid": uuid,
        "case_no": case_no,
        "caseNo": case_no,
        "status_id": status_id,
        "status": STATUS_ID_MAP.get(status_id, "處理中"),
        "ambulance": ambulance,
        "branch": branch,
        "address": address,
        "time_norm": time_norm,
        "time": time_norm,
        "ts": dt.timestamp() if dt else datetime.now(TW).timestamp(),
        "left_at": row.get("leftAt") or row.get("left_at"),
        "main": "緊急救護",
        "sub": "",
        "lat": None,
        "lon": None,
        "coordinate": "",
    }


def fingerprint(case: dict[str, Any]) -> str:
    slim = {k: case.get(k) or "" for k in FIELDS}
    return json.dumps(slim, ensure_ascii=False, sort_keys=True)


def should_push(
    case: dict[str, Any],
    *,
    ntpc_only: bool = False,
    taipei_only: bool = False,
    allow_empty_address: bool = False,
) -> tuple[bool, str]:
    addr = _s(case.get("address"))
    if not addr:
        if allow_empty_address and (_s(case.get("caseNo")) or case.get("coordinate")):
            return True, "ok"
        return False, "no_address"
    if HOSP_RE.search(addr):
        return False, "hosp_addr"
    if ntpc_only and not is_ntpc_address(addr):
        return False, "non_ntpc"
    if taipei_only and not is_taipei_address(addr):
        return False, "non_taipei"
    if not _s(case.get("caseNo")) and not addr:
        return False, "empty"
    return True, "ok"


def cases_from_event(pkt: dict[str, Any]) -> list[dict[str, Any]]:
    name = str(pkt.get("name") or "")
    args = pkt.get("args") or []
    found: list[dict[str, Any]] = []
    seen_fp: set[str] = set()
    for arg in args:
        one = extract_case(arg, event=name)
        if one and one["fingerprint"] not in seen_fp:
            seen_fp.add(one["fingerprint"])
            found.append(one)
        if isinstance(arg, list):
            for item in arg:
                one = extract_case(item, event=name)
                if one and one["fingerprint"] not in seen_fp:
                    seen_fp.add(one["fingerprint"])
                    found.append(one)
    return found
