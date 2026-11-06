"""FOFA Provider — 重用專案已驗證的 FOFA v1 API 邏輯。

來源依據:
- internal/handler/fofa.go Search(): GET {base}/api/v1/search/all?key=&qbase64=&size=&page=&fields=&full=
- tools/fofa_search.yaml: 相同端點, 環境變數 FOFA_API_KEY 注入
- tls_policy.py: 第三方 API 一律驗證 TLS (JYSSECAI_CA_BUNDLE 可覆寫)

本 Provider 不內嵌任何金鑰; 金鑰由 config.py 統一解析 (環境變數優先)。
"""
from __future__ import annotations

import base64
import time
from typing import Optional
from urllib.parse import quote, urlparse, urlunparse

import httpx

from ..models import Asset, normalize_fofa_row
from .base import (
    BaseProvider, AuthError, EntitlementError, ProviderError, ProviderResult,
    QuotaExhaustedError, RateLimitError, UpstreamError,
)

DEFAULT_FIELDS = "host,ip,port,domain,title,protocol,country,region,city,server"


def _normalize_fofa_fields(raw: str) -> str:
    """FOFA 回傳欄位已改用 region，舊表單仍可能送 province。"""
    seen = set()
    out = []
    for part in (raw or "").split(","):
        field = part.strip()
        if field == "province":
            field = "region"
        if field and field not in seen:
            seen.add(field)
            out.append(field)
    return ",".join(out)


class FofaProvider(BaseProvider):
    name = "fofa"

    def __init__(self, *, api_key: str = "", base_url: str = "https://fofa.info",
                 timeout: float = 30.0, max_retries: int = 2, verify_tls: bool = True,
                 ca_bundle: str = "") -> None:
        super().__init__(timeout=timeout, max_retries=max_retries)
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "https://fofa.info").rstrip("/")
        # base_url 可能已是完整 search/all 端點 (如 config.yaml 範例格式), 正規化為 origin
        if "/api/" in self.base_url:
            parsed = urlparse(self.base_url)
            self.base_url = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
        self.verify = ca_bundle if ca_bundle else (True if verify_tls else False)

    def _headers(self) -> dict:
        return {"User-Agent": "JySecAI-AssetIntel/1.0", "Accept": "application/json"}

    def _search_url(self) -> str:
        return f"{self.base_url}/api/v1/search/all"

    def search(self, query: str, *, page: int = 1, size: int = 100,
               fields: str = "", full: bool = False) -> ProviderResult:
        if not self.api_key:
            return ProviderResult(provider=self.name, query=query, ok=False,
                                  error_code="NO_CREDENTIAL",
                                  error_message="FOFA API key not configured (env FOFA_API_KEY or config)")
        if not query or not query.strip():
            return ProviderResult(provider=self.name, query=query, ok=False,
                                  error_code="INVALID_INPUT", error_message="query is empty")

        q = query.strip()
        f = _normalize_fofa_fields(fields.strip() or DEFAULT_FIELDS)
        qb64 = base64.b64encode(q.encode("utf-8")).decode("ascii")
        params = {
            "key": self.api_key,
            "qbase64": qb64,
            "size": str(min(max(int(size), 1), 10000)),
            "page": str(max(int(page), 1)),
            "fields": f,
            "full": "true" if full else "false",
        }
        started = time.monotonic()
        attempts = 0
        last_err: Optional[ProviderError] = None
        while attempts <= self.max_retries:
            attempts += 1
            try:
                with httpx.Client(timeout=self.timeout, verify=self.verify,
                                  headers=self._headers(), follow_redirects=False) as client:
                    resp = client.get(self._search_url(), params=params)
                if resp.status_code == 200:
                    return self._parse_ok(resp, q, f, page, started, attempts)
                # 錯誤分類
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
            except httpx.TimeoutException as exc:
                last_err = ProviderError(f"timeout: {exc}", code="TIMEOUT")
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
            except Exception as exc:  # noqa: BLE001 — 邊界保護
                last_err = ProviderError(f"unexpected: {exc}", code="INTERNAL")
                break

        latency = int((time.monotonic() - started) * 1000)
        self._record(latency, ok=False)
        code = last_err.code if last_err else "PROVIDER_ERROR"
        # AuthError/Entitlement 屬於帳務問題, 不重試時也需分類正確
        if isinstance(last_err, AuthError):
            code = "AUTH_FAILED"
        elif isinstance(last_err, EntitlementError):
            code = "ENTITLEMENT_REQUIRED"
        return ProviderResult(provider=self.name, query=q, ok=False, error_code=code,
                              error_message=str(last_err) if last_err else "unknown",
                              duration_ms=latency, api_calls=attempts)

    def _parse_ok(self, resp: httpx.Response, query: str, fields: str,
                  page: int, started: float, attempts: int) -> ProviderResult:
        latency = int((time.monotonic() - started) * 1000)
        try:
            data = resp.json()
        except ValueError:
            self._record(latency, ok=False)
            return ProviderResult(provider=self.name, query=query, ok=False,
                                  error_code="BAD_RESPONSE", error_message="FOFA returned non-JSON body",
                                  duration_ms=latency, api_calls=attempts)
        if data.get("error"):
            msg = str(data.get("errmsg") or data.get("message") or "FOFA error")
            code = "FOFA_ERROR"
            if "invalid" in msg.lower() or "auth" in msg.lower():
                code = "AUTH_FAILED"
            elif "vip" in msg.lower() or "permission" in msg.lower() or " privileges" in msg.lower():
                code = "ENTITLEMENT_REQUIRED"
            self._record(latency, ok=False)
            return ProviderResult(provider=self.name, query=query, ok=False,
                                  error_code=code, error_message=msg[:300],
                                  duration_ms=latency, api_calls=attempts)
        fields_list = [f.strip() for f in fields.split(",") if f.strip()]
        rows = data.get("results") or []
        assets = []
        for row in rows:
            a = normalize_fofa_row(row, fields_list)
            if a is not None:
                assets.append(a)
        size = int(data.get("size") or 0)
        self._record(latency, credits=1, assets=len(assets))
        return ProviderResult(
            provider=self.name, query=str(data.get("query") or query), ok=True,
            assets=assets, total=size, page=int(data.get("page") or page),
            duration_ms=latency, api_calls=attempts, credits_used=1,
            raw_meta={"mode": data.get("mode"), "fields": fields_list},
        )

    def quota(self) -> dict:
        """FOFA /api/v1/info/my — 回傳帳號資訊 (剩餘額度), 消耗 0 查詢點。"""
        if not self.api_key:
            return {"provider": self.name, "status": "NO_CREDENTIAL"}
        try:
            with httpx.Client(timeout=self.timeout, verify=self.verify,
                              headers=self._headers()) as client:
                resp = client.get(f"{self.base_url}/api/v1/info/my",
                                  params={"key": self.api_key})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("error"):
                    return {"provider": self.name, "status": "UNKNOWN",
                            "error": str(data.get("errmsg", ""))[:200]}
                # 只取非敏感欄位
                return {
                    "provider": self.name,
                    "status": "OK",
                    "isvip": bool(data.get("isvip")),
                    "vip_level": int(data.get("vip_level") or 0),
                    "fcoin": data.get("fcoin"),
                    "remaining_free": data.get("fofa_point") if "fofa_point" in data else data.get("remaining_free"),
                    "note": "quota fields depend on FOFA response; UNKNOWN when absent",
                }
            return {"provider": self.name, "status": "UNKNOWN",
                    "http_status": resp.status_code}
        except Exception as exc:  # noqa: BLE001
            return {"provider": self.name, "status": "UNKNOWN", "error": str(exc)[:200]}

    def health(self) -> dict:
        """以 quota 端點 (0 點消耗) 做健康檢查。"""
        started = time.monotonic()
        info = self.quota()
        latency = int((time.monotonic() - started) * 1000)
        ok = info.get("status") == "OK"
        return {"provider": self.name, "ok": ok, "latency_ms": latency,
                "detail": {k: v for k, v in info.items() if k not in ("error",)}}
