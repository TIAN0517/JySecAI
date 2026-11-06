"""MCP 工具註冊 — 10 個資產情報工具。

安全約束:
- 未指定授權目標 (scope 為空) 時, 拒絕執行外部資產搜尋。
- 結果回傳前二次驗證 scope。
- 金鑰永不回傳給 Agent。
- Trace ID 與 API 消耗量記錄於每次回應。
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any

from .deduplication import compute_changes, deduplicate_assets, fingerprint_summary
from .models import Asset, utc_now_iso, validate_cidr, validate_domain, validate_ip
from .providers.base import BaseProvider
from .quota import DailyBudget, RateLimiter
from .reporting import build_report, export_csv, export_json
from .scope import Scope, ScopeDenied
from .security import sanitize_mapping

MAX_OUTPUT_ASSETS = 200  # 單次回傳資產上限 (其餘留在 DB)

ERROR_CODES = {
    "SCOPE_REQUIRED": "未提供授權範圍 (scope) 或 scope 無效",
    "SCOPE_DENIED": "目標不在授權範圍內",
    "NO_CREDENTIAL": "Provider 未設定 API 金鑰 (經環境變數設定, 不經 Agent 傳遞)",
    "INVALID_INPUT": "輸入參數驗證失敗",
    "RATE_LIMITED": "速率限制 / 額度不足",
    "PROVIDER_ERROR": "上游 Provider 錯誤",
}


def _trace_id() -> str:
    return uuid.uuid4().hex[:16]


def _err(trace: str, code: str, message: str, **extra) -> dict:
    body = {"ok": False, "error_code": code, "message": message,
            "trace_id": trace, "timestamp": utc_now_iso()}
    body.update(extra)
    return body


def _validate_query_target(target: str) -> str:
    """分類查詢目標: ip | domain | cidr | query (自由查詢)"""
    t = (target or "").strip()
    if not t:
        return ""
    if validate_ip(t):
        return "ip"
    if validate_cidr(t):
        return "cidr"
    if validate_domain(t):
        return "domain"
    return "query"


def register(app, *, cfg, providers: dict, registry, store) -> None:
    """向 MCP app 註冊所有工具。"""
    rate_limiters = {name: RateLimiter(cfg.rate_limit_per_minute) for name in providers}
    budget = DailyBudget(cfg.daily_budget, store=store)

    def _resolve_scope(scope_id: str = "", target: str = "") -> Scope:
        """取得 scope; scope_id 未指定時用 default。找不到時丟 ScopeDenied。"""
        scope = registry.get(scope_id) if scope_id else registry.default()
        if scope is None or scope.is_empty():
            raise ScopeDenied(target or "(none)", "no authorized scope configured")
        return scope

    def _check_query_in_scope(scope: Scope, target: str) -> str:
        """查詢目標必須整體落在授權範圍; CIDR 需為授權網段的子集。"""
        kind = _validate_query_target(target)
        if kind == "ip":
            if not scope.check_ip(target):
                raise ScopeDenied(target)
            return "ip"
        if kind == "domain":
            if not scope.check_domain(target):
                raise ScopeDenied(target)
            return "domain"
        if kind == "cidr":
            target_net = validate_cidr(target)
            authorized = False
            import ipaddress
            tn = ipaddress.ip_network(target_net)
            for e in scope.entries:
                if e.kind != "cidr":
                    continue
                try:
                    an = ipaddress.ip_network(e.value)
                    if tn.subnet_of(an):
                        authorized = True
                        break
                except ValueError:
                    continue
            if not authorized:
                raise ScopeDenied(target, "CIDR is not a subset of any authorized network")
            return "cidr"
        # 自由查詢: 需含授權範圍內的 host/domain/ip 條件
        if target and any(tok in target for tok in (scope.entries[0].value,)):
            return "query"
        raise ScopeDenied(target or "(free-form query)",
                          "free-form queries must reference an authorized target")

    def _build_query(kind: str, target: str, extra_terms: str) -> str:
        target = (target or "").strip()
        extra = (extra_terms or "").strip()
        if kind == "ip":
            base = f'ip="{target}"'
        elif kind == "domain":
            base = f'domain="{target}"'
        elif kind == "cidr":
            base = f'ip="{target}"'
        else:
            base = target
        if extra:
            base = f"({base}) && ({extra})"
        return base

    def _run_provider(provider: BaseProvider, query: str, page: int, size: int,
                      scope: Scope, trace: str) -> dict:
        """執行單一 provider 查詢: 限流 -> 預算 -> 快取 -> 搜尋 -> scope 二次驗證 -> 儲存。"""
        cache_key = f"{provider.name}:{query}:{page}:{size}"
        cached = store.cache_get(cache_key)
        if cached is not None:
            cached["cache_hit"] = True
            return cached
        if not rate_limiters[provider.name].acquire(max_wait=5.0):
            return _err(trace, "RATE_LIMITED",
                        f"{provider.name} rate limit exceeded, retry later")
        if not budget.try_consume(provider.name, 1):
            return _err(trace, "QUOTA_EXHAUSTED",
                        f"daily request budget exhausted for {provider.name}")
        result = provider.search(query, page=page, size=size)
        store.record_history(
            trace_id=trace, provider=provider.name, query=query, page=page,
            ok=result.ok, error_code=result.error_code, total=result.total,
            results_count=len(result.assets), api_calls=result.api_calls,
            credits_used=result.credits_used, duration_ms=result.duration_ms,
            scope_id=scope.scope_id)
        if not result.ok:
            body = _err(trace, result.error_code or "PROVIDER_ERROR",
                        result.error_message, provider=provider.name)
            body["api_calls"] = result.api_calls
            return body
        # 結果回傳前二次驗證 scope
        allowed, denied = scope.filter_assets(result.assets)
        dedup = deduplicate_assets(allowed)
        store.upsert_assets(dedup["unique"], scope_id=scope.scope_id)
        out = {
            "ok": True, "provider": provider.name, "query": query,
            "trace_id": trace, "total": result.total,
            "returned": len(dedup["unique"]),
            "denied_out_of_scope": len(denied),
            "duplicates_removed": dedup["duplicates"],
            "conflicts": dedup["conflicts"][:20],
            "assets": [a.to_dict() for a in dedup["unique"][:MAX_OUTPUT_ASSETS]],
            "api_calls": result.api_calls, "credits_used": result.credits_used,
            "duration_ms": result.duration_ms, "cache_hit": False,
            "timestamp": utc_now_iso(),
        }
        store.cache_set(cache_key, provider.name, query, out, cfg.cache_ttl_seconds)
        return out

    # ================== 工具 1: asset_search ==================
    @app.tool(description=(
        "在授權範圍內跨 FOFA 與 ZoomEye 並行搜尋資產。需要已設定的授權範圍 (scope); "
        "未授權目標會被拒絕。target 可為 IP、域名、CIDR (須為授權網段子集)。"
        "providers: all|fofa|zoomeye。"
    ))
    def asset_search(target: str, providers_: str = "all", extra_terms: str = "",
                     page: int = 1, size: int = 100,
                     scope_id: str = "") -> dict:
        trace = _trace_id()
        target = (target or "").strip()
        if not target:
            return _err(trace, "INVALID_INPUT", "target is required")
        if len(target) > 512 or len(extra_terms) > 1024:
            return _err(trace, "INVALID_INPUT", "target/extra_terms too long")
        try:
            scope = _resolve_scope(scope_id, target)
            kind = _check_query_in_scope(scope, target)
        except ScopeDenied as exc:
            return _err(trace, "SCOPE_DENIED", str(exc), target=target)
        query = _build_query(kind, target, extra_terms)
        page = max(1, min(int(page), cfg.max_pages_per_query))
        size = max(1, min(int(size), 1000))
        names = list(providers.keys()) if providers_ in ("all", "") else [
            p.strip() for p in providers_.split(",") if p.strip() in providers]
        if not names:
            return _err(trace, "INVALID_INPUT",
                        f"providers must be one of {sorted(providers.keys())} or 'all'")
        import concurrent.futures
        started = time.monotonic()
        provider_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(names)) as pool:
            futures = {pool.submit(_run_provider, providers[n], query, page, size,
                                   scope, trace): n for n in names}
            for fut in concurrent.futures.as_completed(futures):
                provider_results[futures[fut]] = fut.result(timeout=cfg.search_timeout_seconds)
        all_ok = all(r.get("ok") for r in provider_results.values())
        merged_assets = []
        total_dupes = 0
        for r in provider_results.values():
            if r.get("ok"):
                merged_assets.extend([Asset(**{k: v for k, v in a.items()
                                              if k in Asset.__dataclass_fields__})
                                      for a in r.get("assets", [])])
                total_dupes += r.get("duplicates_removed", 0)
        dedup = deduplicate_assets(merged_assets)
        return {
            "ok": all_ok, "trace_id": trace, "query": query, "scope_id": scope.scope_id,
            "providers": provider_results,
            "unique_assets": len(dedup["unique"]),
            "duplicates_removed": total_dupes + dedup["duplicates"],
            "conflicts": dedup["conflicts"][:20],
            "assets": [a.to_dict() for a in dedup["unique"][:MAX_OUTPUT_ASSETS]],
            "duration_ms": int((time.monotonic() - started) * 1000),
            "timestamp": utc_now_iso(),
        }

    # ================== 工具 2: asset_details ==================
    @app.tool(description="以 asset_id 查詢資產完整細節 (含原始證據溯源, 已遮蔽敏感欄位)。")
    def asset_details(asset_id: str) -> dict:
        trace = _trace_id()
        asset_id = (asset_id or "").strip()
        if not asset_id or len(asset_id) > 64:
            return _err(trace, "INVALID_INPUT", "asset_id is required (<=64 chars)")
        detail = store.asset_details(asset_id)
        if not detail:
            return _err(trace, "NOT_FOUND", f"asset {asset_id} not found in local store")
        return {"ok": True, "trace_id": trace, "asset": sanitize_mapping(detail)}

    # ================== 工具 3: asset_fingerprint ==================
    @app.tool(description="整合資產指紋: 服務/產品/協定/埠分布統計。ip/domain 為本地查詢。")
    def asset_fingerprint(ip: str = "", domain: str = "") -> dict:
        trace = _trace_id()
        if not ip and not domain:
            return _err(trace, "INVALID_INPUT", "ip or domain is required")
        rows = store.find_assets(ip=ip.strip(), domain=domain.strip(), limit=1000)
        assets = [_row_to_asset(r) for r in rows]
        return {"ok": True, "trace_id": trace,
                "fingerprint": fingerprint_summary(assets),
                "query_scope": len(rows)}

    # ================== 工具 4: asset_deduplicate ==================
    @app.tool(description="對輸入資產列表 (或本地指定範圍) 執行跨平台去重, 保留衝突與證據。")
    def asset_deduplicate(assets_json: str = "", ip: str = "", domain: str = "") -> dict:
        trace = _trace_id()
        assets = []
        if assets_json:
            try:
                raw = json.loads(assets_json)
            except ValueError:
                return _err(trace, "INVALID_INPUT", "assets_json is not valid JSON")
            if not isinstance(raw, list):
                return _err(trace, "INVALID_INPUT", "assets_json must be a JSON array")
            for item in raw[:2000]:
                if isinstance(item, dict):
                    try:
                        assets.append(Asset(**{k: v for k, v in item.items()
                                               if k in Asset.__dataclass_fields__}))
                    except Exception:  # noqa: BLE001
                        continue
        else:
            rows = store.find_assets(ip=ip.strip(), domain=domain.strip(), limit=2000)
            assets = [_row_to_asset(r) for r in rows]
        dedup = deduplicate_assets(assets)
        return {
            "ok": True, "trace_id": trace,
            "input_count": len(assets),
            "unique_count": len(dedup["unique"]),
            "duplicates_removed": dedup["duplicates"],
            "conflicts": dedup["conflicts"][:50],
            "assets": [a.to_dict() for a in dedup["unique"][:MAX_OUTPUT_ASSETS]],
        }

    # ================== 工具 5: asset_history ==================
    @app.tool(description="查詢歷史搜尋紀錄 (provider、查詢、消耗、耗時)。")
    def asset_history(provider: str = "", limit: int = 30) -> dict:
        trace = _trace_id()
        provider = (provider or "").strip().lower()
        if provider and provider not in providers:
            return _err(trace, "INVALID_INPUT",
                        f"provider must be one of {sorted(providers.keys())}")
        rows = store.get_history(provider=provider, limit=min(max(int(limit), 1), 200))
        return {"ok": True, "trace_id": trace, "history": rows[:200], "count": len(rows)}

    # ================== 工具 6: asset_changes ==================
    @app.tool(description="比較兩個快照 (或快照與現況) 的資產變更: 新增/移除/欄位變更。")
    def asset_changes(before_snapshot_id: int, after_snapshot_id: int = 0) -> dict:
        trace = _trace_id()
        before = store.get_snapshot(int(before_snapshot_id))
        if not before:
            return _err(trace, "NOT_FOUND", f"snapshot {before_snapshot_id} not found")
        if after_snapshot_id:
            after = store.get_snapshot(int(after_snapshot_id))
            if not after:
                return _err(trace, "NOT_FOUND", f"snapshot {after_snapshot_id} not found")
        else:
            rows = store.find_assets(limit=5000)
            after = {"payload": [sanitize_mapping(r) for r in rows]}
        changes = compute_changes(before.get("payload") or [], after.get("payload") or [])
        return {"ok": True, "trace_id": trace,
                "before": {"snapshot_id": before_snapshot_id, "count": len(before.get("payload") or [])},
                "after": {"snapshot_id": after_snapshot_id or "current", "count": len(after.get("payload") or [])},
                **changes}

    # ================== 工具 7: provider_health ==================
    @app.tool(description="檢查 FOFA / ZoomEye API 連線健康 (不消耗查詢點數為原則)。")
    def provider_health(provider: str = "") -> dict:
        trace = _trace_id()
        provider = (provider or "").strip().lower()
        names = [provider] if provider in providers else sorted(providers.keys())
        results = {}
        for n in names:
            try:
                results[n] = providers[n].health()
            except Exception as exc:  # noqa: BLE001
                results[n] = {"provider": n, "ok": False, "error": str(exc)[:200]}
        return {"ok": all(r.get("ok") for r in results.values()),
                "trace_id": trace, "providers": results}

    # ================== 工具 8: provider_quota ==================
    @app.tool(description="查詢 provider 配額/剩餘額度與本日預算使用。")
    def provider_quota(provider: str = "") -> dict:
        trace = _trace_id()
        provider = (provider or "").strip().lower()
        names = [provider] if provider in providers else sorted(providers.keys())
        results = {}
        for n in names:
            try:
                results[n] = providers[n].quota()
            except Exception as exc:  # noqa: BLE001
                results[n] = {"provider": n, "status": "UNKNOWN", "error": str(exc)[:200]}
        return {"ok": True, "trace_id": trace, "quotas": results,
                "daily_budget": {"limit": cfg.daily_budget,
                                 "used_today": budget.usage()},
                "rate_limit_per_minute": {n: rate_limiters[n].current_usage()
                                          for n in names}}

    # ================== 工具 9: asset_export ==================
    @app.tool(description="匯出資產為 JSON 或 CSV (CSV 經公式注入防護; 敏感欄位已遮蔽)。")
    def asset_export(ip: str = "", domain: str = "", format: str = "json") -> dict:
        trace = _trace_id()
        fmt = (format or "json").strip().lower()
        if fmt not in ("json", "csv"):
            return _err(trace, "INVALID_INPUT", "format must be json or csv")
        rows = store.find_assets(ip=ip.strip(), domain=domain.strip(), limit=5000)
        assets = [_row_to_asset(r) for r in rows]
        content = export_json(assets) if fmt == "json" else export_csv(assets)
        return {"ok": True, "trace_id": trace, "format": fmt,
                "count": len(rows), "content": content}

    # ================== 工具 10: asset_report ==================
    @app.tool(description="產生資產分析報告 (指紋統計、來源分布、去重與衝突、注意事項)。")
    def asset_report(ip: str = "", domain: str = "",
                     snapshot_id: int = 0, save_snapshot: bool = False,
                     label: str = "") -> dict:
        trace = _trace_id()
        if snapshot_id:
            snap = store.get_snapshot(int(snapshot_id))
            if not snap:
                return _err(trace, "NOT_FOUND", f"snapshot {snapshot_id} not found")
            assets = [_row_to_asset(r) if isinstance(r, dict) and "asset_id" in r
                      else r for r in (snap.get("payload") or [])]
        else:
            rows = store.find_assets(ip=ip.strip(), domain=domain.strip(), limit=5000)
            assets = [_row_to_asset(r) for r in rows]
        dedup = deduplicate_assets(assets)
        scope = registry.default()
        report = build_report(
            dedup["unique"], scope_id=scope.scope_id if scope else "",
            dedup_info=dedup)
        snapshot_result = None
        if save_snapshot:
            snapshot_result = store.save_snapshot(
                scope.scope_id if scope else "default",
                (label or "auto")[:100], dedup["unique"])
        return {"ok": True, "trace_id": trace, "report": report,
                "snapshot": snapshot_result}


def _row_to_asset(row: dict) -> Asset:
    """SQLite 列 -> Asset (供指紋/去重/匯出重用)。"""
    try:
        providers = json.loads(row.get("source_providers") or "[]")
    except (ValueError, TypeError):
        providers = []
    return Asset(
        ip=row.get("ip") or "", port=row.get("port") or 0,
        protocol=row.get("protocol") or "", domain=row.get("domain") or "",
        hostname=row.get("hostname") or "", service=row.get("service") or "",
        product=row.get("product") or "", version=row.get("version") or "",
        banner=row.get("banner") or "", title=row.get("title") or "",
        country=row.get("country") or "", city=row.get("city") or "",
        confidence=float(row.get("confidence") or 0.5),
        source_providers=providers,
        observed_at=row.get("observed_at") or utc_now_iso(),
        first_seen=row.get("first_seen") or "",
        last_seen=row.get("last_seen") or "",
        authorization_scope_id=row.get("authorization_scope_id") or "",
    )
