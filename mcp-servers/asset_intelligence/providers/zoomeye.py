"""ZoomEye Provider — 對齊專案已驗證的 api.zoomeye.ai/v2 端點。

來源依據:
- internal/handler/fofa.go searchZoomEye(): POST {base} with JSON {qbase64, page, pagesize, fields}, header "API-KEY"
- tools/zoomeye_search.yaml: 相同端點與注入方式 (ZOOMEYE_API_KEY)
- 帳號方案: Personal (見 data/HERMES_ZOOMEYE_RECOMMENDATION_RECORD.md); 方案不相關的 API 回 UNSUPPORTED/ENTITLEMENT_REQUIRED

回應結構 (spaceSearchEnvelope): {code, message, data: [...], query, total, page, pagesize}
"""
from __future__ import annotations

import base64
import time
from typing import Optional
from urllib.parse import urlparse, urlunparse

import httpx

from ..models import normalize_zoomeye_row
from .base import (
    BaseProvider, EntitlementError, ProviderError, ProviderResult,
    QuotaExhaustedError, RateLimitError, UnsupportedError, UpstreamError,
)

DEFAULT_FIELDS = "ip,port,domain,hostname,title,service,app,country,city"


class ZoomEyeProvider(BaseProvider):
    name = "zoomeye"

    def __init__(self, *, api_key: str = "",
                 base_url: str = "https://api.zoomeye.ai/v2/search",
                 timeout: float = 30.0, max_retries: int = 2, verify_tls: bool = True,
                 ca_bundle: str = "") -> None:
        super().__init__(timeout=timeout, max_retries=max_retries)
        self.api_key = (api_key or "").strip()
        base = (base_url or "https://api.zoomeye.ai/v2/search").rstrip("/")
        # 正規化舊網域 api.zoomeye.org -> api.zoomeye.ai (與 Go handler 一致)
        if "api.zoomeye.org" in base:
            base = base.replace("api.zoomeye.org", "api.zoomeye.ai")
        # 接受 origin 或完整端點; 保留既有 path (如 /v2/search)
        parsed = urlparse(base)
        if parsed.path in ("", "/"):
            base = urlunparse((parsed.scheme, parsed.netloc, "/v2/search", "", "", ""))
        self.endpoint = base
        self.verify = ca_bundle if ca_bundle else (True if verify_tls else False)

    def _headers(self) -> dict:
        return {
            "User-Agent": "JySecAI-AssetIntel/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "API-KEY": self.api_key,
        }

    def search(self, query: str, *, page: int = 1, size: int = 100,
               fields: str = "", full: bool = False) -> ProviderResult:
        if not self.api_key:
            return ProviderResult(provider=self.name, query=query, ok=False,
                                  error_code="NO_CREDENTIAL",
                                  error_message="ZoomEye API key not configured (env ZOOMEYE_API_KEY or config)")
        if not query or not query.strip():
            return ProviderResult(provider=self.name, query=query, ok=False,
                                  error_code="INVALID_INPUT", error_message="query is empty")

        q = query.strip()
        body = {
            "qbase64": base64.b64encode(q.encode("utf-8")).decode("ascii"),
            "page": max(int(page), 1),
            "pagesize": min(max(int(size), 1), 10000),
        }
        f = fields.strip() or DEFAULT_FIELDS
        if f:
            body["fields"] = f

        started = time.monotonic()
        attempts = 0
        last_err: Optional[ProviderError] = None
        while attempts <= self.max_retries:
            attempts += 1
            try:
                with httpx.Client(timeout=self.timeout, verify=self.verify,
                                  headers=self._headers(), follow_redirects=False) as client:
                    resp = client.post(self.endpoint, json=body)
                if resp.status_code == 200:
                    return self._parse_ok(resp, q, f, page, started, attempts)
                retry_after = None
                ra = resp.headers.get("Retry-After")
                if ra and ra.isdigit():
                    retry_after = float(ra)
                err = self.classify_http_error(resp.status_code, resp.text[:300], retry_after)
                if isinstance(err, RateLimitError) and attempts <= self.max_retries:
                    wait = err.retry_after if err.retry_after else self.retry_backoff(attempts)
                    time.sleep(min(wait, 30.0))
                    last_err = err
                    continue
                last_err = err
                break
            except httpx.TimeoutException:
                last_err = ProviderError("timeout", code="TIMEOUT")
                if attempts <= self.max_retries:
                    time.sleep(self.retry_backoff(attempts))
                    continue
                break
            except httpx.HTTPError as exc:
                last_err = ProviderError(f"network error: {exc}", code="NETWORK_ERROR")
                if attempts <= self.max_retries:
                    time.sleep(self.retry_backoff(attempts))
                    continue
                break
            except Exception as exc:  # noqa: BLE001
                last_err = ProviderError(f"unexpected: {exc}", code="INTERNAL")
                break

        latency = int((time.monotonic() - started) * 1000)
        self._record(latency, ok=False)
        return ProviderResult(provider=self.name, query=q, ok=False,
                              error_code=last_err.code if last_err else "PROVIDER_ERROR",
                              error_message=str(last_err) if last_err else "unknown",
                              duration_ms=latency, api_calls=attempts)

    @staticmethod
    def _request_failed(code_val, message: str) -> bool:
        """ZoomEye v2 慣例: code==0 或 code==60000 成功; 其他 4xx/5xx 表失敗。"""
        try:
            c = int(code_val)
        except (TypeError, ValueError):
            return bool(message)
        if c in (0, 60000):
            return False
        return c != 0

    def _parse_ok(self, resp: httpx.Response, query: str, fields: str,
                  page: int, started: float, attempts: int) -> ProviderResult:
        latency = int((time.monotonic() - started) * 1000)
        try:
            data = resp.json()
        except ValueError:
            self._record(latency, ok=False)
            return ProviderResult(provider=self.name, query=query, ok=False,
                                  error_code="BAD_RESPONSE", error_message="ZoomEye returned non-JSON body",
                                  duration_ms=latency, api_calls=attempts)
        code_val = data.get("code")
        message = str(data.get("message") or "")
        if self._request_failed(code_val, message):
            try:
                c = int(code_val)
            except (TypeError, ValueError):
                c = -1
            if c in (401, 403):
                code = "AUTH_FAILED" if c == 401 else "ENTITLEMENT_REQUIRED"
            elif c in (402, 407):
                code = "QUOTA_EXHAUSTED"
            elif c == 429:
                code = "RATE_LIMITED"
            elif c >= 500:
                code = "UPSTREAM_ERROR"
            else:
                code = "ZOOMEYE_ERROR"
            self._record(latency, ok=False)
            return ProviderResult(provider=self.name, query=query, ok=False,
                                  error_code=code, error_message=message[:300],
                                  duration_ms=latency, api_calls=attempts)
        rows = data.get("data") or data.get("results") or []
        assets = []
        for row in rows:
            a = normalize_zoomeye_row(row)
            if a is not None:
                assets.append(a)
        total = int(data.get("total") or data.get("total_count") or 0)
        self._record(latency, credits=1, assets=len(assets))
        return ProviderResult(
            provider=self.name, query=str(data.get("query") or query), ok=True,
            assets=assets, total=total, page=int(data.get("page") or page),
            duration_ms=latency, api_calls=attempts, credits_used=1,
            raw_meta={"endpoint": self.endpoint, "fields": fields},
        )

    def quota(self) -> dict:
        """GET /v2/info — 舊版端點; Personal 方案可能不支援時回 UNSUPPORTED, 不假造。"""
        if not self.api_key:
            return {"provider": self.name, "status": "NO_CREDENTIAL"}
        origin = self.endpoint.split("/v2/")[0]
        try:
            with httpx.Client(timeout=self.timeout, verify=self.verify,
                              headers=self._headers()) as client:
                resp = client.get(f"{origin}/v2/info")
            if resp.status_code == 401:
                return {"provider": self.name, "status": "AUTH_FAILED"}
            if resp.status_code == 403:
                return {"provider": self.name, "status": "ENTITLEMENT_REQUIRED",
                        "note": "account plan does not include quota info API"}
            if resp.status_code == 404:
                return {"provider": self.name, "status": "UNSUPPORTED",
                        "note": "quota info endpoint not available"}
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and self._request_failed(data.get("code"), str(data.get("message") or "")):
                    return {"provider": self.name, "status": "UNKNOWN",
                            "error": str(data.get("message", ""))[:200]}
                vip = (data.get("data") or {}).get("vip_info") or data.get("vip_info") or {}
                return {
                    "provider": self.name,
                    "status": "OK",
                    "plan": vip.get("plan") or "UNKNOWN",
                    "end_time": vip.get("end_time"),
                    "resources": (data.get("data") or {}).get("resources") or data.get("resources"),
                }
            return {"provider": self.name, "status": "UNKNOWN", "http_status": resp.status_code}
        except Exception as exc:  # noqa: BLE001
            return {"provider": self.name, "status": "UNKNOWN", "error": str(exc)[:200]}

    def health(self) -> dict:
        started = time.monotonic()
        info = self.quota()
        latency = int((time.monotonic() - started) * 1000)
        status = info.get("status")
        # UNSUPPORTED/ENTITLEMENT_REQUIRED 仍代表連線與金鑰驗證通過
        ok = status in ("OK", "UNSUPPORTED", "ENTITLEMENT_REQUIRED")
        return {"provider": self.name, "ok": ok, "latency_ms": latency, "detail": info}
