"""統一 119 出勤通報模板。所有資料源都走 formatTelegramMessage。"""
from __future__ import annotations

import html as html_mod
import re
from typing import Any
from urllib.parse import quote

from .models import parse_ts

TITLE = "【119 出勤通報】"
MAP_BTN = "🗺️ 案發地圖"
COPY_BTN = "📋 一鍵複製地址"
_VEHICLE_RE = re.compile(r"([\u4e00-\u9fffA-Za-z]+?\d{2,3})\s*$")
_FLEET_PREFIX = re.compile(r"^(救護車|消防車|救護)\s*")
_E1_MARK = re.compile(r"[（(]E1\s*車軌[)）]|來源：?\s*E1", re.I)


def esc(text: Any) -> str:
    return html_mod.escape(str(text or ""), quote=False)


def format_category(case: dict[str, Any]) -> str:
    e1_type = str(case.get("e1_type") or "").strip()
    kind = str(case.get("type") or case.get("sub") or case.get("kind") or "").strip()
    if "OHCA" in kind or "雙軌" in kind:
        return kind
    if e1_type == "AmbulanceBack" or "後送" in kind:
        return "緊急救護・後送"
    if e1_type == "Ambulance":
        return kind or "緊急救護"
    return kind or "緊急救護"


def format_dispatch_time(case: dict[str, Any]) -> str:
    dt = parse_ts(case.get("time") or case.get("time_norm") or case.get("dispatch_time"))
    if dt:
        return dt.strftime("%Y/%m/%d %H:%M:%S")
    text = str(case.get("time") or "").strip()
    if not text:
        return ""
    return text.replace("-", "/")


def format_unit_name(case: dict[str, Any]) -> str:
    amb = str(case.get("ambulance") or "").strip()
    branch = str(case.get("branch") or "").strip()
    raw = amb or branch
    raw = _FLEET_PREFIX.sub("", raw).strip()
    if branch.endswith("分隊") and amb:
        raw = _FLEET_PREFIX.sub("", amb).strip() or raw
    match = _VEHICLE_RE.search(raw)
    if match:
        return f"{match.group(1)}（專責救護車）"
    if amb and branch and amb != branch:
        return f"{_FLEET_PREFIX.sub('', branch).strip()} {raw}".strip()
    return raw or "—"


def clean_address(case: dict[str, Any]) -> str:
    addr = str(case.get("address") or "").strip()
    addr = _E1_MARK.sub("", addr).strip()
    if addr.startswith("E1|"):
        return ""
    return addr


def map_url(case: dict[str, Any]) -> str:
    lat, lon = case.get("lat"), case.get("lon")
    try:
        if lat is not None and lon is not None:
            la, lo = float(lat), float(lon)
            if 21.0 <= la <= 26.5 and 118.0 <= lo <= 122.5:
                return f"https://www.google.com/maps?q={la:.6f},{lo:.6f}"
    except (TypeError, ValueError):
        pass
    addr = clean_address(case)
    if addr:
        return "https://www.google.com/maps/search/?api=1&query=" + quote(addr)
    return ""


def formatTelegramMessage(case: dict[str, Any], style: str = "full") -> str:
    """所有來源的 Telegram 正文。不含來源／案號／裸座標。"""
    del style  # 單一模板
    lines = [
        TITLE,
        f"案件類別：{esc(format_category(case))}",
        f"派遣時間：{esc(format_dispatch_time(case))}",
        f"車號描述：{esc(format_unit_name(case))}",
        f"案件地址：{esc(clean_address(case))}",
    ]
    return "\n".join(lines)


fmt_card = formatTelegramMessage


def inline_keyboard(case: dict[str, Any]) -> dict | None:
    addr = clean_address(case)
    row: list[dict] = []
    if addr:
        row.append({"text": COPY_BTN, "copy_text": {"text": addr[:256]}})
    url = map_url(case)
    if url:
        row.append({"text": MAP_BTN, "url": url})
    if not row:
        return None
    return {"inline_keyboard": [row]}


def telegram_send_options(case: dict[str, Any] | None = None, text: str | None = None) -> dict[str, Any]:
    """sendMessage 共用選項：關網址預覽，座標只在地圖按鈕。"""
    body = text if text is not None else (formatTelegramMessage(case or {}) if case else "")
    payload: dict[str, Any] = {
        "text": body[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "link_preview_options": {"is_disabled": True},
    }
    if case is not None:
        kb = inline_keyboard(case)
        if kb:
            payload["reply_markup"] = kb
    return payload
