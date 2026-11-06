"""Provider 抽象基底類別 — 錯誤分類、標準化結果、健康狀態。"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from ..models import Asset


class ProviderError(Exception):
    """Provider 呼叫失敗的基底例外。"""

    default_code = "PROVIDER_ERROR"

    def __init__(self, message: str, *, code: Optional[str] = None,
                 status: Optional[int] = None, retry_after: Optional[float] = None):
        super().__init__(message)
        self.code = code or self.default_code
        self.status = status
        self.retry_after = retry_after


class AuthError(ProviderError):
    default_code = "AUTH_FAILED"          # 401 / 金鑰無效


class EntitlementError(ProviderError):
    default_code = "ENTITLEMENT_REQUIRED"  # 403 / 方案不支援


class RateLimitError(ProviderError):
    default_code = "RATE_LIMITED"          # 429


class QuotaExhaustedError(ProviderError):
    default_code = "QUOTA_EXHAUSTED"       # 額度用盡


class UnsupportedError(ProviderError):
    default_code = "UNSUPPORTED"           # 端點/功能此方案不提供


class UpstreamError(ProviderError):
    default_code = "UPSTREAM_ERROR"        # 5xx / 回應格式錯誤


class TimeoutError(ProviderError):
    default_code = "TIMEOUT"


@dataclass
class ProviderResult:
    provider: str
    query: str
    ok: bool
    assets: list = field(default_factory=list)      # list[Asset]
    total: int = 0
    page: int = 1
    error_code: str = ""
    error_message: str = ""
    duration_ms: int = 0
    api_calls: int = 0
    credits_used: int = 0                            # 消耗的查詢點數/額度 (可得時)
    raw_meta: dict = field(default_factory=dict)

    def to_dict(self, include_assets: bool = True, sanitized=None) -> dict:
        d = {
            "provider": self.provider,
            "query": self.query,
            "ok": self.ok,
            "total": self.total,
            "page": self.page,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "api_calls": self.api_calls,
            "credits_used": self.credits_used,
            "assets_count": len(self.assets),
        }
        if include_assets:
            d["assets"] = [a.to_dict() for a in self.assets]
        if sanitized:
            d = sanitized(d)
        return d


class BaseProvider(ABC):
    """Provider 介面 — 子類別實作搜尋、配額、健康檢查。"""

    name: str = "base"

    def __init__(self, *, timeout: float = 30.0, max_retries: int = 2) -> None:
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.stats = {"requests": 0, "errors": 0, "credits_used": 0,
                      "total_latency_ms": 0, "assets_found": 0}

    # ---- 子類別必須實作 ----

    @abstractmethod
    def search(self, query: str, *, page: int = 1, size: int = 100,
               fields: str = "", full: bool = False) -> ProviderResult:
        """執行一次搜尋; 必須自行處理重試與錯誤分類。"""

    @abstractmethod
    def quota(self) -> dict:
        """回傳配額資訊; 不可得時回傳 {"status": "UNKNOWN"}。"""

    @abstractmethod
    def health(self) -> dict:
        """輕量連線健康檢查, 不消耗查詢點數為原則。"""

    # ---- 共用工具 ----

    def _record(self, latency_ms: int, credits: int = 0, ok: bool = True,
                assets: int = 0) -> None:
        self.stats["requests"] += 1
        if not ok:
            self.stats["errors"] += 1
        self.stats["credits_used"] += credits
        self.stats["total_latency_ms"] += latency_ms
        self.stats["assets_found"] += assets

    def stats_summary(self) -> dict:
        s = self.stats
        req = s["requests"] or 1
        return {
            "provider": self.name,
            "requests": s["requests"],
            "errors": s["errors"],
            "success_rate": round(1 - s["errors"] / req, 3) if s["requests"] else None,
            "avg_latency_ms": round(s["total_latency_ms"] / req) if s["requests"] else None,
            "credits_used": s["credits_used"],
            "assets_found": s["assets_found"],
        }

    @staticmethod
    def classify_http_error(status: int, body: str = "", retry_after: Optional[float] = None) -> ProviderError:
        """HTTP 狀態碼 -> 分類錯誤。"""
        if status == 401:
            return AuthError(f"authentication failed (401): {body[:200]}")
        if status == 403:
            return EntitlementError(f"plan does not permit this API (403): {body[:200]}")
        if status == 429:
            return RateLimitError(f"rate limited (429): {body[:200]}", retry_after=retry_after)
        if status == 402:
            return QuotaExhaustedError(f"quota/payment required (402): {body[:200]}")
        if 500 <= status < 600:
            return UpstreamError(f"upstream error ({status}): {body[:200]}")
        return ProviderError(f"http error ({status}): {body[:200]}")

    @staticmethod
    def retry_backoff(attempt: int, base: float = 0.8, cap: float = 8.0) -> float:
        """指數退避 + 隨機抖動。"""
        import random
        return min(cap, base * (2 ** attempt)) * (0.5 + random.random() * 0.5)
