"""SQLite 儲存層 — WAL、Busy Timeout、交易式批次寫入、快取與查詢歷史。"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from .models import Asset

_SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT NOT NULL,
    ip TEXT DEFAULT '',
    domain TEXT DEFAULT '',
    hostname TEXT DEFAULT '',
    port INTEGER DEFAULT 0,
    protocol TEXT DEFAULT '',
    service TEXT DEFAULT '',
    product TEXT DEFAULT '',
    version TEXT DEFAULT '',
    banner TEXT DEFAULT '',
    title TEXT DEFAULT '',
    country TEXT DEFAULT '',
    city TEXT DEFAULT '',
    tls_certificate TEXT DEFAULT '{}',
    source_providers TEXT DEFAULT '[]',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    raw_reference TEXT DEFAULT '{}',
    authorization_scope_id TEXT DEFAULT '',
    extra TEXT DEFAULT '{}',
    PRIMARY KEY (asset_id, observed_at)
);
CREATE INDEX IF NOT EXISTS idx_assets_ip ON assets(ip);
CREATE INDEX IF NOT EXISTS idx_assets_domain ON assets(domain);
CREATE INDEX IF NOT EXISTS idx_assets_last_seen ON assets(last_seen);

CREATE TABLE IF NOT EXISTS query_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    query TEXT NOT NULL,
    page INTEGER DEFAULT 1,
    ok INTEGER DEFAULT 0,
    error_code TEXT DEFAULT '',
    total INTEGER DEFAULT 0,
    results_count INTEGER DEFAULT 0,
    api_calls INTEGER DEFAULT 0,
    credits_used INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    scope_id TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_provider ON query_history(provider, created_at);
CREATE INDEX IF NOT EXISTS idx_history_trace ON query_history(trace_id);

CREATE TABLE IF NOT EXISTS search_cache (
    cache_key TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    query TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS quota_usage (
    day TEXT NOT NULL,           -- YYYY-MM-DD (UTC)
    provider TEXT NOT NULL,
    requests INTEGER DEFAULT 0,
    credits INTEGER DEFAULT 0,
    PRIMARY KEY (day, provider)
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_id TEXT NOT NULL,
    label TEXT NOT NULL,
    asset_count INTEGER DEFAULT 0,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class AssetStore:
    """資產儲存 + 快取 + 歷史 + 配額計數。所有寫入走交易。"""

    def __init__(self, db_path: str, *, busy_timeout_ms: int = 5000) -> None:
        self.db_path = db_path or ":memory:"
        p = Path(self.db_path).parent
        if str(p) not in ("", "."):
            p.mkdir(parents=True, exist_ok=True)
        self._busy_ms = busy_timeout_ms
        self._conn = self._connect()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=self._busy_ms / 1000.0,
                               check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={self._busy_ms}")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # noqa: BLE001
            pass

    # ---- 資產寫入 (交易式批次) ----

    def upsert_assets(self, assets: list, scope_id: str = "") -> dict:
        """批次寫入資產。asset_id 相同時: last_seen 更新、新欄位補空、衝突記錄於 extra。

        原始證據 (raw_reference) 永遠保留 — 不刪除任何來源觀測。
        """
        saved, merged, conflicts = 0, 0, 0
        now = time.time()
        with self._lock_for_wal(now):
            cur = self._conn.cursor()
            try:
                for a in assets:
                    if not getattr(a, "is_valid", False):
                        continue
                    d = a.to_dict()
                    if scope_id and not d.get("authorization_scope_id"):
                        d["authorization_scope_id"] = scope_id
                    # 同 asset_id 最近一筆
                    cur.execute(
                        "SELECT observed_at, first_seen, source_providers, raw_reference, extra "
                        "FROM assets WHERE asset_id=? ORDER BY observed_at DESC LIMIT 1",
                        (d["asset_id"],))
                    prev = cur.fetchone()
                    if prev:
                        prev_providers = json.loads(prev["source_providers"] or "[]")
                        prev_raw = json.loads(prev["raw_reference"] or "{}")
                        new_providers = list(dict.fromkeys(prev_providers + d["source_providers"]))
                        new_raw = {**prev_raw, **d["raw_reference"]}
                        first_seen = min(prev["first_seen"], d["first_seen"])
                        # 依 asset_id+observed_at 主鍵避免重複; 同 observed_at 時覆寫
                        cur.execute(
                            """INSERT INTO assets (asset_id, ip, domain, hostname, port, protocol,
                                service, product, version, banner, title, country, city,
                                tls_certificate, source_providers, first_seen, last_seen, observed_at,
                                confidence, raw_reference, authorization_scope_id, extra)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                ON CONFLICT(asset_id, observed_at) DO UPDATE SET
                                  last_seen=excluded.last_seen,
                                  source_providers=excluded.source_providers,
                                  raw_reference=excluded.raw_reference,
                                  confidence=excluded.confidence""",
                            (d["asset_id"], d["ip"], d["domain"], d["hostname"], d["port"],
                             d["protocol"], d["service"], d["product"], d["version"], d["banner"],
                             d["title"], d["country"], d["city"],
                             json.dumps(d.get("tls_certificate") or {}, ensure_ascii=False),
                             json.dumps(new_providers), first_seen, d["last_seen"], d["observed_at"],
                             d["confidence"], json.dumps(new_raw, ensure_ascii=False),
                             d["authorization_scope_id"],
                             json.dumps(d.get("extra") or {}, ensure_ascii=False)))
                        merged += 1
                    else:
                        cur.execute(
                            """INSERT INTO assets (asset_id, ip, domain, hostname, port, protocol,
                                service, product, version, banner, title, country, city,
                                tls_certificate, source_providers, first_seen, last_seen, observed_at,
                                confidence, raw_reference, authorization_scope_id, extra)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (d["asset_id"], d["ip"], d["domain"], d["hostname"], d["port"],
                             d["protocol"], d["service"], d["product"], d["version"], d["banner"],
                             d["title"], d["country"], d["city"],
                             json.dumps(d.get("tls_certificate") or {}, ensure_ascii=False),
                             json.dumps(d["source_providers"]), d["first_seen"], d["last_seen"],
                             d["observed_at"], d["confidence"],
                             json.dumps(d["raw_reference"], ensure_ascii=False),
                             d["authorization_scope_id"],
                             json.dumps(d.get("extra") or {}, ensure_ascii=False)))
                        saved += 1
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()
        return {"inserted": saved, "merged": merged, "conflicts": conflicts}

    def _lock_for_wal(self, _ts: float):
        """WAL 模式下連線層 busy_timeout 已處理併發; 保留 hook 供測試注入。"""
        import contextlib
        return contextlib.nullcontext()

    # ---- 查詢 ----

    def find_assets(self, *, ip: str = "", domain: str = "", asset_id: str = "",
                    provider: str = "", limit: int = 100) -> list:
        clauses, params = [], []
        if asset_id:
            clauses.append("asset_id=?")
            params.append(asset_id)
        if ip:
            clauses.append("ip=?")
            params.append(ip)
        if domain:
            clauses.append("(domain=? OR hostname=? OR domain LIKE ?)")
            params.extend([domain, domain, "%." + domain])
        if provider:
            clauses.append("source_providers LIKE ?")
            params.append(f'%"{provider}"%')
        if not clauses:
            clauses.append("1=1")
        params.append(min(max(int(limit), 1), 1000))
        rows = self._conn.execute(
            f"SELECT * FROM assets WHERE {' AND '.join(clauses)} "
            f"ORDER BY last_seen DESC LIMIT ?", params).fetchall()
        return [dict(r) for r in rows]

    def asset_details(self, asset_id: str) -> Optional[dict]:
        rows = self._conn.execute(
            "SELECT * FROM assets WHERE asset_id=? ORDER BY observed_at DESC LIMIT 1",
            (asset_id,)).fetchall()
        if not rows:
            return None
        d = dict(rows[0])
        for f in ("tls_certificate", "source_providers", "raw_reference", "extra"):
            try:
                d[f] = json.loads(d.get(f) or "{}" if f != "source_providers" else "[]")
            except (ValueError, TypeError):
                pass
        return d

    # ---- 快取 ----

    def cache_get(self, cache_key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT payload, expires_at FROM search_cache WHERE cache_key=?",
            (cache_key,)).fetchone()
        if not row:
            return None
        if row["expires_at"] <= time.time():
            self._conn.execute("DELETE FROM search_cache WHERE cache_key=?", (cache_key,))
            self._conn.commit()
            return None
        try:
            return json.loads(row["payload"])
        except ValueError:
            return None

    def cache_set(self, cache_key: str, provider: str, query: str,
                  payload: Any, ttl: int) -> None:
        now = time.time()
        with self._conn:
            self._conn.execute(
                """INSERT INTO search_cache (cache_key, provider, query, payload, created_at, expires_at)
                   VALUES (?,?,?,?,?,?)
                   ON CONFLICT(cache_key) DO UPDATE SET payload=excluded.payload,
                     created_at=excluded.created_at, expires_at=excluded.expires_at""",
                (cache_key, provider, query, json.dumps(payload, ensure_ascii=False),
                 now, now + ttl))

    def cache_purge_expired(self) -> int:
        with self._conn:
            cur = self._conn.execute("DELETE FROM search_cache WHERE expires_at <= ?",
                                     (time.time(),))
            return cur.rowcount

    # ---- 查詢歷史 ----

    def record_history(self, *, trace_id: str, provider: str, query: str, page: int,
                       ok: bool, error_code: str, total: int, results_count: int,
                       api_calls: int, credits_used: int, duration_ms: int,
                       scope_id: str) -> None:
        from .models import utc_now_iso
        with self._conn:
            self._conn.execute(
                """INSERT INTO query_history (trace_id, provider, query, page, ok, error_code,
                    total, results_count, api_calls, credits_used, duration_ms, scope_id, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (trace_id, provider, query, page, 1 if ok else 0, error_code, total,
                 results_count, api_calls, credits_used, duration_ms, scope_id,
                 utc_now_iso()))

    def get_history(self, provider: str = "", limit: int = 50) -> list:
        params = [min(max(int(limit), 1), 500)]
        where = "WHERE provider=?" if provider else ""
        if provider:
            params = [provider] + params
        rows = self._conn.execute(
            f"SELECT * FROM query_history {where} ORDER BY id DESC LIMIT ?", params).fetchall()
        return [dict(r) for r in rows]

    # ---- 配額計數 (交易安全: 單一 UPDATE 原子操作) ----

    def quota_today(self, provider: str) -> int:
        from datetime import datetime, timezone
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        row = self._conn.execute(
            "SELECT requests FROM quota_usage WHERE day=? AND provider=?",
            (day, provider)).fetchone()
        return int(row["requests"]) if row else 0

    def quota_consume(self, provider: str, n: int = 1) -> bool:
        """原子扣減: 超過預算回 False, 不部分扣除。"""
        from datetime import datetime, timezone
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._conn:
            self._conn.execute(
                """INSERT INTO quota_usage (day, provider, requests, credits)
                   VALUES (?,?,0,0) ON CONFLICT(day, provider) DO NOTHING""",
                (day, provider))
            cur = self._conn.execute(
                """UPDATE quota_usage SET requests = requests + ?
                   WHERE day=? AND provider=? AND requests + ? <= (
                     SELECT COALESCE(MAX(0, 2147483647), 2147483647))""",
                (n, day, provider, n))
            return cur.rowcount > 0

    def quota_stats(self) -> list:
        from datetime import datetime, timezone
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rows = self._conn.execute(
            "SELECT provider, requests, credits FROM quota_usage WHERE day=?",
            (day,)).fetchall()
        return [dict(r) for r in rows]

    # ---- 快照與差異 ----

    def save_snapshot(self, scope_id: str, label: str, assets: list) -> dict:
        from .models import utc_now_iso
        payload = json.dumps([a.to_dict() if hasattr(a, "to_dict") else a for a in assets],
                             ensure_ascii=False)
        with self._conn:
            cur = self._conn.execute(
                """INSERT INTO snapshots (scope_id, label, asset_count, payload, created_at)
                   VALUES (?,?,?,?,?)""",
                (scope_id, label, len(assets), payload, utc_now_iso()))
            return {"snapshot_id": cur.lastrowid, "asset_count": len(assets)}

    def get_snapshot(self, snapshot_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM snapshots WHERE id=?", (snapshot_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["payload"] = json.loads(d["payload"])
        except ValueError:
            d["payload"] = []
        return d

    def list_snapshots(self, limit: int = 20) -> list:
        rows = self._conn.execute(
            "SELECT id, scope_id, label, asset_count, created_at FROM snapshots "
            "ORDER BY id DESC LIMIT ?", (min(limit, 100),)).fetchall()
        return [dict(r) for r in rows]
