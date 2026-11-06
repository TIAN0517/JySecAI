"""配額與速率限制管理 — 並行安全 (threading.Lock + 原子扣減)。"""
from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    """滑動視窗速率限制器 — 每 provider 獨立。"""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = max(1, per_minute)
        self._events: deque = deque()
        self._lock = threading.Lock()

    def acquire(self, blocking: bool = True, max_wait: float = 60.0) -> bool:
        """取得一個請求配額; blocking=True 時最多等待 max_wait 秒。"""
        deadline = time.monotonic() + max_wait
        while True:
            with self._lock:
                now = time.monotonic()
                while self._events and now - self._events[0] > 60.0:
                    self._events.popleft()
                if len(self._events) < self.per_minute:
                    self._events.append(now)
                    return True
                wait_needed = 60.0 - (now - self._events[0]) + 0.05
            if not blocking or time.monotonic() >= deadline:
                return False
            time.sleep(min(wait_needed, 1.0))

    def current_usage(self) -> int:
        with self._lock:
            now = time.monotonic()
            while self._events and now - self._events[0] > 60.0:
                self._events.popleft()
            return len(self._events)


class DailyBudget:
    """每日請求預算 — 並行安全計數, 避免多 Agent 同時超耗。

    底層可選接 AssetStore (SQLite 原子扣減, 跨行程安全);
    記憶體模式用於單一行程內的快速保護。
    """

    def __init__(self, daily_limit: int, store=None) -> None:
        self.daily_limit = max(1, daily_limit)
        self._store = store
        self._count = 0
        self._day = self._today()
        self._lock = threading.Lock()

    @staticmethod
    def _today() -> str:
        return time.strftime("%Y-%m-%d", time.gmtime())

    def try_consume(self, provider: str, n: int = 1) -> bool:
        """嘗試消耗 n 個請求; 超出預算回 False。"""
        with self._lock:
            today = self._today()
            if today != self._day:
                self._day = today
                self._count = 0
        # SQLite 模式: 跨行程安全 (與其他 Agent/伺服器共享預算)
        if self._store is not None:
            return self._store.quota_consume(provider, n)
        # 記憶體模式
        with self._lock:
            if self._count + n > self.daily_limit:
                return False
            self._count += n
            return True

    def usage(self) -> int:
        if self._store is not None:
            total = 0
            for row in self._store.quota_stats():
                total += int(row.get("requests") or 0)
            return total
        with self._lock:
            if self._today() != self._day:
                return 0
            return self._count
