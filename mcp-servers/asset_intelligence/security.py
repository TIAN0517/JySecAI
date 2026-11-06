"""安全防護模組 — 金鑰遮蔽、日誌安全、CSV Injection 防護。"""
from __future__ import annotations

import csv
import io
import re
from typing import Any, Iterable

# 需要遮蔽的鍵名模式 (不分大小寫)
_SENSITIVE_KEY_RE = re.compile(
    r"(api[_-]?key|apikey|secret|token|password|passwd|authorization|cookie|credential)",
    re.IGNORECASE,
)
# 高熵/金鑰形態字串 (用於自由文字掃描)
# 匹配目標: UUID(36)、hex32、hex40、hex64、JWT、sk-*、xox*
_KEY_SHAPED_RE = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"(?:"
    r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
    r"|[0-9A-Fa-f]{32,64}"
    r"|[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    r"|sk-[A-Za-z0-9-]{20,}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"
    r")"
    r"(?![A-Za-z0-9_-])",
    re.IGNORECASE
)

MASKED = "***REDACTED***"


def mask_secret(value: Any, keep: int = 0) -> str:
    """遮蔽敏感值 — 預設全遮; keep>0 時僅保留前 keep 字元。"""
    s = "" if value is None else str(value)
    if not s:
        return ""
    if keep > 0 and len(s) > keep * 2:
        return s[:keep] + "..." + MASKED
    return MASKED


def sanitize_mapping(obj: Any, _depth: int = 0) -> Any:
    """遞迴遮蔽 dict/list 中鍵名敏感或值形似金鑰的內容。

    任何要寫入日誌、報告、匯出、測試快照的資料都必須先過此函式。
    """
    if _depth > 12:
        return "..."
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            ks = str(k)
            if _SENSITIVE_KEY_RE.search(ks):
                out[ks] = MASKED
            else:
                out[ks] = sanitize_mapping(v, _depth + 1)
        return out
    if isinstance(obj, (list, tuple)):
        return [sanitize_mapping(x, _depth + 1) for x in obj]
    if isinstance(obj, str):
        return _KEY_SHAPED_RE.sub(MASKED, obj)
    return obj


def safe_text(value: Any, max_len: int = 2048) -> str:
    """自由文字欄位安全化: 遮蔽金鑰形態字串並截斷。"""
    return _KEY_SHAPED_RE.sub(MASKED, str(value or ""))[:max_len]


def csv_escape_cell(value: Any) -> str:
    """CSV Injection 防護 — 抵擋公式注入 (=, +, -, @ 開頭) 與危險字元。

    參考 OWASP CSV Injection 指引: 前置單引號使 Excel/Sheets 以文字處理。
    """
    s = str(value if value is not None else "")
    if s and s[0] in ("=", "+", "@", "\t", "\r", "\n"):
        return "'" + s
    # 防止 DDE payload 常見嵌入
    if re.match(r"^(cmd|powershell)\b", s, re.IGNORECASE) and "|" in s[:30]:
        return "'" + s
    return s


def rows_to_csv(rows: Iterable[dict], columns: list) -> str:
    """將 dict 列安全輸出為 CSV 字串 (所有儲存格經 csv_escape_cell)。"""
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([csv_escape_cell(row.get(c, "")) for c in columns])
    return buf.getvalue()


class SecretRedactingFormatter:
    """logging Formatter 包裝: 對最終訊息做金鑰形態掃描遮蔽。"""

    def __init__(self, base_formatter=None):
        self._base = base_formatter

    def format(self, record) -> str:
        if self._base is not None:
            msg = self._base.format(record)
        else:
            msg = str(record.getMessage())
        return _KEY_SHAPED_RE.sub(MASKED, msg)


def redact_text(text: str) -> str:
    """對任意文字做金鑰形態遮蔽 (stderr 日誌安全網)。"""
    return _KEY_SHAPED_RE.sub(MASKED, text or "")
