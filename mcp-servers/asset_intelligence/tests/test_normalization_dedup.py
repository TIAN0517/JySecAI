"""測試 6-9: 資產標準化、跨平台去重、SQLite 交易/WAL、快取。"""
from __future__ import annotations

import json
import sqlite3
import threading
import time

import pytest

from asset_intelligence.deduplication import compute_changes, deduplicate_assets, fingerprint_summary
from asset_intelligence.models import Asset


class TestNormalization:
    """測試 6: 資產標準化。"""

    def test_asset_id_stable(self):
        a1 = Asset(ip="203.0.113.10", port=443, protocol="https")
        a2 = Asset(ip="203.0.113.10", port=443, protocol="https")
        assert a1.asset_id == a2.asset_id

    def test_asset_id_differs_by_port(self):
        a1 = Asset(ip="203.0.113.10", port=443, protocol="tcp")
        a2 = Asset(ip="203.0.113.10", port=8443, protocol="tcp")
        assert a1.asset_id != a2.asset_id

    def test_asset_id_differs_by_protocol(self):
        a1 = Asset(ip="203.0.113.10", port=443, protocol="http")
        a2 = Asset(ip="203.0.113.10", port=443, protocol="https")
        assert a1.asset_id != a2.asset_id

    def test_empty_values_normalized(self):
        a = Asset(ip="", port=None, protocol=None)
        assert a.ip == ""
        assert a.port == 0
        assert a.observed_at  # 自動補時間

    def test_ipv6_asset(self):
        a = Asset(ip="2001:db8::1", port=443, protocol="https")
        assert a.ip == "2001:db8::1"
        assert a.is_valid

    def test_hostname_multi_values_kept(self):
        # 同一服務多 hostname: merge 保留衝突
        a1 = Asset(ip="203.0.113.10", port=443, protocol="https", hostname="www.example.com")
        a2 = Asset(ip="203.0.113.10", port=443, protocol="https", hostname="alt.example.com")
        conflicts = a1.merge(a2)
        assert len(conflicts) == 1
        assert conflicts[0]["field"] == "hostname"

    def test_raw_reference_preserved(self):
        a1 = Asset(ip="203.0.113.10", port=443)
        a1.raw_reference["fofa"] = {"row": [1, 2, 3]}
        a2 = Asset(ip="203.0.113.10", port=443)
        a2.raw_reference["zoomeye"] = {"row": {"ip": "203.0.113.10"}}
        a1.merge(a2)
        assert "fofa" in a1.raw_reference
        assert "zoomeye" in a1.raw_reference


class TestCrossPlatformDedup:
    """測試 7: 跨平台去重。"""

    def test_same_ip_port_dedup(self):
        a1 = Asset(ip="203.0.113.10", port=443, protocol="https", source_providers=["fofa"])
        a2 = Asset(ip="203.0.113.10", port=443, protocol="https", source_providers=["zoomeye"])
        result = deduplicate_assets([a1, a2])
        assert len(result["unique"]) == 1
        assert result["duplicates"] == 1
        assert set(result["unique"][0].source_providers) == {"fofa", "zoomeye"}

    def test_conflict_keeps_both_sources(self):
        a1 = Asset(ip="203.0.113.10", port=443, product="nginx",
                   source_providers=["fofa"])
        a2 = Asset(ip="203.0.113.10", port=443, product="Apache",
                   source_providers=["zoomeye"])
        result = deduplicate_assets([a1, a2])
        assert len(result["unique"]) == 1
        conflicts = result["conflicts"]
        assert any(c["field"] == "product" for c in conflicts)
        # 原始證據都保留
        assert set(result["unique"][0].raw_reference.keys()) >= {"fofa", "zoomeye"} or \
            set(result["unique"][0].source_providers) == {"fofa", "zoomeye"}

    def test_hostname_multi_ip_different_assets(self):
        # 同 hostname 不同 IP 應為兩筆資產 (資產識別以 ip:port:protocol 為主)
        a1 = Asset(ip="203.0.113.10", port=443, hostname="www.example.com")
        a2 = Asset(ip="203.0.113.11", port=443, hostname="www.example.com")
        result = deduplicate_assets([a1, a2])
        assert len(result["unique"]) == 2

    def test_time_ordering_kept(self):
        a1 = Asset(ip="203.0.113.10", port=443, observed_at="2026-10-01T00:00:00Z")
        a2 = Asset(ip="203.0.113.10", port=443, observed_at="2026-10-02T00:00:00Z")
        result = deduplicate_assets([a1, a2])
        u = result["unique"][0]
        assert u.first_seen == "2026-10-01T00:00:00Z"
        assert u.last_seen == "2026-10-02T00:00:00Z"

    def test_fingerprint_summary(self):
        assets = [
            Asset(ip="203.0.113.10", port=443, protocol="https", service="https", product="nginx"),
            Asset(ip="203.0.113.11", port=22, protocol="tcp", service="ssh", product="OpenSSH"),
            Asset(ip="203.0.113.12", port=443, protocol="https", service="https", product="nginx"),
        ]
        fp = fingerprint_summary(assets)
        assert fp["total"] == 3
        assert fp["services"][0]["name"] == "https"
        assert fp["products"][0]["count"] == 2


class TestSqliteTransactions:
    """測試 8: SQLite 交易與 WAL。"""

    def test_wal_mode_enabled(self, store):
        mode = store._conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"

    def test_busy_timeout_set(self, store):
        val = store._conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert val > 0

    def test_upsert_insert_and_merge(self, store):
        a1 = Asset(ip="203.0.113.10", port=443, protocol="https", product="nginx",
                   source_providers=["fofa"])
        r1 = store.upsert_assets([a1], scope_id="test")
        assert r1["inserted"] == 1
        a2 = Asset(ip="203.0.113.10", port=443, protocol="https", product="nginx",
                   source_providers=["zoomeye"])
        r2 = store.upsert_assets([a2], scope_id="test")
        assert r2["inserted"] == 1 or r2["merged"] >= 1
        rows = store.find_assets(ip="203.0.113.10")
        assert len(rows) >= 1

    def test_raw_evidence_never_deleted(self, store):
        a1 = Asset(ip="203.0.113.10", port=443)
        a1.raw_reference["fofa_row"] = {"ip": "203.0.113.10"}
        store.upsert_assets([a1])
        a2 = Asset(ip="203.0.113.10", port=443)
        a2.raw_reference["zoomeye_row"] = {"ip": "203.0.113.10"}
        store.upsert_assets([a2])
        detail = store.asset_details(a1.asset_id)
        raw = detail["raw_reference"]
        assert "fofa_row" in raw or "fofa_row" in str(raw)
        assert "zoomeye_row" in raw or "zoomeye_row" in str(raw)

    def test_concurrent_writes(self, tmp_path):
        """並行寫入安全 (WAL + busy_timeout)。"""
        from asset_intelligence.storage import AssetStore as AS
        db_path = str(tmp_path / "concurrent.db")
        errors = []

        def worker(n):
            for attempt in range(3):  # 3 次重試
                try:
                    s = AS(db_path)
                    for i in range(10):
                        a = Asset(ip=f"203.0.113.{n}", port=8000 + i, protocol="tcp")
                        s.upsert_assets([a])
                    s.close()
                    return
                except sqlite3.OperationalError as exc:
                    if attempt == 2:
                        errors.append(exc)
                    else:
                        time.sleep(0.1)
                except Exception as exc:  # noqa: BLE001
                    errors.append(exc)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(1, 6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        assert not errors, f"concurrent write errors: {errors}"
        s = AS(db_path)
        rows = s.find_assets(limit=1000)
        assert len(rows) == 50
        s.close()


class TestCache:
    """測試 9: 快取命中及過期。"""

    def test_cache_hit(self, store):
        store.cache_set("k1", "fofa", "q", {"v": 1}, ttl=60)
        assert store.cache_get("k1") == {"v": 1}

    def test_cache_miss(self, store):
        assert store.cache_get("nope") is None

    def test_cache_expiry(self, store):
        store.cache_set("k2", "fofa", "q", {"v": 2}, ttl=-1)  # 立即過期
        assert store.cache_get("k2") is None

    def test_cache_purge(self, store):
        store.cache_set("k3", "fofa", "q", {"v": 3}, ttl=-1)
        store.cache_set("k4", "fofa", "q", {"v": 4}, ttl=60)
        purged = store.cache_purge_expired()
        assert purged >= 1
        assert store.cache_get("k4") == {"v": 4}
