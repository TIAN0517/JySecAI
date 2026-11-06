"""pytest 共用 fixture — 隔離環境、Mock Provider。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# 讓測試可匯入 asset_intelligence 套件
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from asset_intelligence.config import AssetIntelConfig  # noqa: E402
from asset_intelligence.providers.base import (  # noqa: E402
    AuthError, EntitlementError, ProviderResult, QuotaExhaustedError,
    RateLimitError, UpstreamError,
)
from asset_intelligence.providers.fofa import FofaProvider  # noqa: E402
from asset_intelligence.providers.zoomeye import ZoomEyeProvider  # noqa: E402
from asset_intelligence.scope import Scope  # noqa: E402
from asset_intelligence.server import create_app  # noqa: E402
from asset_intelligence.storage import AssetStore  # noqa: E402

TEST_DB = None


@pytest.fixture()
def store(tmp_path):
    """隔離的暫存 SQLite store。"""
    db = tmp_path / "test_assets.db"
    s = AssetStore(str(db))
    yield s
    s.close()


@pytest.fixture()
def authorized_scope() -> Scope:
    scope = Scope(scope_id="test")
    scope.add_cidr("203.0.113.0/24", "TEST-NET-3")
    scope.add_domain("example.com")
    scope.add_domain("*.example.com")
    scope.add_ip("198.51.100.7")
    assert len(scope.entries) == 4
    return scope


@pytest.fixture()
def cfg(tmp_path) -> AssetIntelConfig:
    return AssetIntelConfig(
        fofa_api_key="test-fofa-key",
        zoomeye_api_key="test-ze-key",
        db_path=str(tmp_path / "cfg_assets.db"),
        daily_budget=10,
        rate_limit_per_minute=100,
        cache_ttl_seconds=60,
        scopes={"default": {"cidrs": ["203.0.113.0/24"],
                            "domains": ["example.com", "*.example.com"],
                            "ips": ["198.51.100.7"]}},
    )


class MockFofaProvider(FofaProvider):
    """以 monkeypatch 替換 HTTP 層的 FOFA Provider。"""

    def __init__(self, response_factory=None, **kw):
        super().__init__(api_key="mock-key", **kw)
        self._factory = response_factory
        self.calls = []

    def search(self, query, *, page=1, size=100, fields="", full=False):
        self.calls.append({"query": query, "page": page, "size": size})
        if self._factory:
            return self._factory(query, page, size)
        fields_list = fields.split(",") if fields else ["host", "ip", "port", "domain"]
        rows = [
            ["www.example.com", "203.0.113.10", "443", "www.example.com"],
            ["api.example.com", "203.0.113.11", "8443", "api.example.com"],
            ["203.0.113.12", "203.0.113.12", "22", ""],
        ]
        from asset_intelligence.models import normalize_fofa_row
        assets = [normalize_fofa_row(r, fields_list) for r in rows]
        assets = [a for a in assets if a]
        return ProviderResult(provider="fofa", query=query, ok=True, assets=assets,
                              total=len(assets), page=page, duration_ms=5,
                              api_calls=1, credits_used=1)


class MockZoomEyeProvider(ZoomEyeProvider):
    def __init__(self, response_factory=None, **kw):
        super().__init__(api_key="mock-key", **kw)
        self._factory = response_factory
        self.calls = []

    def search(self, query, *, page=1, size=100, fields="", full=False):
        self.calls.append({"query": query, "page": page, "size": size})
        if self._factory:
            return self._factory(query, page, size)
        rows = [
            {"ip": "203.0.113.10", "port": 443, "domain": "www.example.com",
             "hostname": "www.example.com", "title": "Example",
             "service": "https", "app": "nginx", "country": "US"},
            {"ip": "203.0.113.10", "port": 443, "domain": "www.example.com",
             "hostname": "alt.example.com", "title": "Example",
             "service": "https", "app": "nginx", "country": "US"},
        ]
        from asset_intelligence.models import normalize_zoomeye_row
        assets = [normalize_zoomeye_row(r) for r in rows]
        assets = [a for a in assets if a]
        return ProviderResult(provider="zoomeye", query=query, ok=True, assets=assets,
                              total=len(assets), page=page, duration_ms=7,
                              api_calls=1, credits_used=1)


@pytest.fixture()
def mock_fofa():
    return MockFofaProvider()


@pytest.fixture()
def mock_zoomeye():
    return MockZoomEyeProvider()


def make_error_result(provider: str, code: str, message: str) -> ProviderResult:
    return ProviderResult(provider=provider, query="q", ok=False,
                          error_code=code, error_message=message)
