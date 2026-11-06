"""跨平台資產去重與指紋整合。

原則:
- 去重不刪除原始證據 — 每個 asset 保留所有來源 raw_reference。
- FOFA 與 ZoomEye 衝突時保留雙方資訊於 conflicts, 不任意覆蓋。
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Optional

from .models import Asset


def deduplicate_assets(assets: list) -> dict:
    """以 asset_id 去重; 同鍵資產合併 (merge 保留衝突)。

    回傳 {"unique": [...], "duplicates": n, "conflicts": [...]}
    """
    unique: "OrderedDict[str, Asset]" = OrderedDict()
    conflicts: list = []
    duplicates = 0
    for a in assets:
        if not getattr(a, "is_valid", False):
            continue
        key = a.asset_id
        if key in unique:
            duplicates += 1
            c = unique[key].merge(a)
            for item in c:
                item["asset_id"] = key
                conflicts.append(item)
        else:
            unique[key] = a
    return {
        "unique": list(unique.values()),
        "duplicates": duplicates,
        "conflicts": conflicts,
    }


def fingerprint_summary(assets: list) -> dict:
    """統計服務/產品/協定分布 — 指紋整合視圖。"""
    services: dict = {}
    products: dict = {}
    protocols: dict = {}
    ports: dict = {}
    for a in assets:
        s = getattr(a, "service", "") or "unknown"
        services[s] = services.get(s, 0) + 1
        p = getattr(a, "product", "") or "unknown"
        products[p] = products.get(p, 0) + 1
        pr = getattr(a, "protocol", "") or "unknown"
        protocols[pr] = protocols.get(pr, 0) + 1
        port = getattr(a, "port", 0)
        ports[str(port)] = ports.get(str(port), 0) + 1

    def top(d: dict, n: int = 10) -> list:
        return [{"name": k, "count": v} for k, v in sorted(d.items(), key=lambda x: -x[1])[:n]]

    return {
        "total": len(assets),
        "services": top(services),
        "products": top(products),
        "protocols": top(protocols),
        "ports": top(ports),
    }


def compute_changes(before: list, after: list) -> dict:
    """快照差異比較 — 新增/移除/欄位變更。

    before/after 為 asset dict 清單 (或 Asset 物件)。
    """
    def key_of(x) -> str:
        if isinstance(x, dict):
            return x.get("asset_id") or ""
        return getattr(x, "asset_id", "")

    def dict_of(x) -> dict:
        if isinstance(x, dict):
            return x
        return x.to_dict()

    before_map = {key_of(x): dict_of(x) for x in before}
    after_map = {key_of(x): dict_of(x) for x in after}
    added = [after_map[k] for k in after_map if k not in before_map]
    removed = [before_map[k] for k in before_map if k not in after_map]
    changed = []
    for k, after_d in after_map.items():
        if k not in before_map:
            continue
        before_d = before_map[k]
        diffs = {}
        for fld in ("ip", "domain", "port", "protocol", "service", "product", "version", "title"):
            b, a = before_d.get(fld), after_d.get(fld)
            if b != a:
                diffs[fld] = {"before": b, "after": a}
        if diffs:
            changed.append({"asset_id": k, "changes": diffs})
    return {"added": added, "removed": removed, "changed": changed,
            "added_count": len(added), "removed_count": len(removed),
            "changed_count": len(changed)}
