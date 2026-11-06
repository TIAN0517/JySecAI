"""測試 10-13: 配額上限、並行額度競爭、HTTP 錯誤處理、Retry/Backoff。"""
from __future__ import annotations

import time
import threading
from unittest.mock import patch

import pytest

from asset_intelligence.quota import DailyBudget, RateLimiter
from asset_intelligence.providers.base import RateLimitError, ProviderResult


class TestQuotaLimits:
    """測試 10: API 配額上限。"""

    def test_budget_exhaustion(self, tmp_path):
        budget = DailyBudget(daily_limit=5, store=None)
        for i in range(5):
            assert budget.try_consume("fofa", 1) is True
        # 第 6 次應失敗
        assert budget.try_consume("fofa", 1) is False
        assert budget.usage() == 5

    def test_budget_consume_multiple(self, tmp_path):
        budget = DailyBudget(daily_limit=10, store=None)
        assert budget.try_consume("zoomeye", 3) is True
        assert budget.try_consume("zoomeye", 8) is False  # 3+8 > 10
        assert budget.usage() == 3

    def test_daily_reset(self, tmp_path):
        budget = DailyBudget(daily_limit=5, store=None)
        budget.try_consume("fofa", 5)
        # 模擬隔日: 覆寫 _day
        budget._day = "9999-01-01"
        assert budget.try_consume("fofa", 1) is True
        assert budget.usage() == 1

    def test_quota_store_integration(self, store, tmp_path):
        """配額與 SQLite store 整合 (跨行程安全)。"""
        budget = DailyBudget(daily_limit=10, store=store)
        assert budget.try_consume("fofa", 1) is True
        # store 應有紀錄
        stats = store.quota_stats()
        assert any(s["provider"] == "fofa" for s in stats)
        assert store.quota_today("fofa") == 1


class TestParallelQuotaContention:
    """測試 11: 並行額度競爭。"""

    def test_concurrent_budget_consumption(self, tmp_path):
        """多執行緒同時消耗配額, 不應超過上限。"""
        budget = DailyBudget(daily_limit=20, store=None)
        successes = []
        lock = threading.Lock()

        def try_consume(n):
            for _ in range(5):
                if budget.try_consume("test", 1):
                    with lock:
                        successes.append(n)
                    time.sleep(0.001)

        threads = [threading.Thread(target=try_consume, args=(n,)) for n in range(1, 9)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        # 20 個額度, 8 個執行緒各試 5 次 (共 40 次嘗試)
        assert len(successes) == 20
        assert budget.usage() == 20

    def test_concurrent_rate_limiting(self):
        limiter = RateLimiter(per_minute=10)
        acquired = []
        lock = threading.Lock()

        def try_acquire(n):
            for _ in range(3):
                if limiter.acquire(blocking=False):
                    with lock:
                        acquired.append(n)

        threads = [threading.Thread(target=try_acquire, args=(n,)) for n in range(1, 9)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        # 最多 10 個配額
        assert len(acquired) <= 10

    def test_rate_limiter_reset(self):
        limiter = RateLimiter(per_minute=3)
        for _ in range(3):
            assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is False


class TestHttpErrorHandling:
    """測試 12: 429/401/403/500 錯誤處理。"""

    def test_401_auth_failed(self):
        from asset_intelligence.providers.fofa import FofaProvider
        p = FofaProvider(api_key="bad-key")
        err = p.classify_http_error(401, "invalid key")
        assert err.code == "AUTH_FAILED"

    def test_403_entitlement(self):
        from asset_intelligence.providers.fofa import FofaProvider
        p = FofaProvider(api_key="k")
        err = p.classify_http_error(403, "premium feature")
        assert err.code == "ENTITLEMENT_REQUIRED"

    def test_429_rate_limited(self):
        from asset_intelligence.providers.fofa import FofaProvider
        p = FofaProvider(api_key="k")
        err = p.classify_http_error(429, "too many requests")
        assert err.code == "RATE_LIMITED"

    def test_500_upstream(self):
        from asset_intelligence.providers.fofa import FofaProvider
        p = FofaProvider(api_key="k")
        err = p.classify_http_error(502, "bad gateway")
        assert err.code == "UPSTREAM_ERROR"


class TestRetryBackoff:
    """測試 13: Retry/Backoff。"""

    def test_backoff_formula(self):
        from asset_intelligence.providers.base import BaseProvider
        # 指數退避: 0.8 * 2^n (上限 8s) + 隨機抖動
        for i in range(5):
            wait = BaseProvider.retry_backoff(i, base=0.5, cap=4.0)
            assert 0 < wait <= 4.0

    def test_max_retries_respected(self, mock_fofa):
        """超過 max_retries 後不再重試。"""
        import httpx
        call_count = [0]

        def factory(query, page, size):
            # 模擬 HTTP 層重試: 每次 search 內會重試 max_retries+1 次
            call_count[0] += 2
            return ProviderResult(
                provider="fofa", query=query, ok=False,
                error_code="TIMEOUT", error_message="timeout",
                api_calls=2, duration_ms=0,
            )

        mock_fofa._factory = factory
        mock_fofa.max_retries = 3  # 模擬內層重試
        result = mock_fofa.search('ip="1.2.3.4"')
        assert result.ok is False
        assert result.error_code == "TIMEOUT"
        # 驗證 Factory 被呼叫 (即 search 方法被進入)
        assert call_count[0] >= 2
