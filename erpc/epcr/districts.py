"""臺北／新北市區碼／地址篩選。"""
from __future__ import annotations

NTPC_DISTRICTS = (
    "板橋",
    "三重",
    "中和",
    "永和",
    "新莊",
    "新店",
    "樹林",
    "鶯歌",
    "三峽",
    "淡水",
    "汐止",
    "瑞芳",
    "土城",
    "蘆洲",
    "五股",
    "泰山",
    "林口",
    "深坑",
    "石碇",
    "坪林",
    "三芝",
    "石門",
    "八里",
    "平溪",
    "雙溪",
    "貢寮",
    "金山",
    "萬里",
    "烏來",
)

_OTHER_PREFIX = (
    "桃園",
    "台北",
    "臺北",
    "基隆",
    "新竹",
    "宜蘭",
    "苗栗",
    "台中",
    "臺中",
    "台南",
    "臺南",
    "高雄",
    "彰化",
    "南投",
)


def is_ntpc_address(addr: str) -> bool:
    """回傳 True 表示是新北市地址。"""
    return _classify(addr) == "ntpc"


def is_taipei_address(addr: str) -> bool:
    """回傳 True 表示是臺北市地址（非新北）。"""
    return _classify(addr) == "taipei"


def _classify(addr: str) -> str:
    """分類地址：'ntpc'／'taipei'／'other'／''。"""
    text = (addr or "").strip()
    if not text:
        return ""
    if "新北" in text:
        return "ntpc"
    if text.startswith(_OTHER_PREFIX):
        if text.startswith(("台北", "臺北")):
            return "taipei"
        return "other"
    if text.startswith(NTPC_DISTRICTS):
        return "ntpc"
    # 沒明確前綴，預設視為臺北市
    return "taipei"
