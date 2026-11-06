"""匯出與報告 — JSON / CSV (CSV Injection 防護)、資產分析報告。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .deduplication import fingerprint_summary
from .models import schema_fields
from .security import sanitize_mapping, rows_to_csv


def export_json(assets: list) -> str:
    """資產清單 -> JSON 字串 (先遮蔽敏感欄位)。"""
    import json
    rows = [a.to_dict() if hasattr(a, "to_dict") else a for a in assets]
    return json.dumps(sanitize_mapping(rows), ensure_ascii=False, indent=2)


def export_csv(assets: list, columns: Optional[list] = None) -> str:
    """資產清單 -> CSV 字串 (所有儲存格經 CSV Injection 防護)。"""
    cols = columns or [c for c in schema_fields() if c not in ("tls_certificate", "raw_reference")]
    rows = []
    for a in assets:
        d = a.to_dict() if hasattr(a, "to_dict") else dict(a)
        # 複合欄位攤平為安全文字
        d["source_providers"] = ",".join(d.get("source_providers") or [])
        for k in ("first_seen", "last_seen", "observed_at"):
            d[k] = str(d.get(k) or "")
        rows.append(d)
    return rows_to_csv(rows, cols)


def build_report(assets: list, *, query: str = "", scope_id: str = "",
                 providers_used: Optional[list] = None,
                 dedup_info: Optional[dict] = None,
                 errors: Optional[list] = None) -> dict:
    """資產分析報告 — 統計、指紋、來源、注意事項。"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assets_list = [a.to_dict() if hasattr(a, "to_dict") else dict(a) for a in assets]
    providers: dict = {}
    for d in assets_list:
        for p in (d.get("source_providers") or []):
            providers[p] = providers.get(p, 0) + 1
    report = {
        "generated_at": now,
        "query": query,
        "scope_id": scope_id,
        "total_unique_assets": len(assets_list),
        "providers_used": sorted(providers.keys()),
        "provider_asset_counts": providers,
        "fingerprint": fingerprint_summary(assets),
        "notes": [
            "指紋與版本為觀測資料, 未經驗證不得視為已確認弱點。",
            "衝突欄位保留雙方來源資訊, 詳見各資產 raw_reference。",
        ],
    }
    if dedup_info:
        report["deduplication"] = {
            "duplicates": dedup_info.get("duplicates", 0),
            "conflicts": len(dedup_info.get("conflicts", [])),
        }
    if errors:
        report["provider_errors"] = errors
    return sanitize_mapping(report)
