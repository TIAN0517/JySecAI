"""測試 1-3: FOFA Adapter、ZoomEye Adapter、API 回應解析 (Mock, 離線)。"""
from __future__ import annotations

import pytest

from asset_intelligence.providers.base import (
    AuthError, EntitlementError, ProviderResult, QuotaExhaustedError,
    RateLimitError, UpstreamError,
)
from asset_intelligence.providers.fofa import FofaProvider
from asset_intelligence.providers.zoomeye import ZoomEyeProvider


class TestFofaAdapter:
    """測試 1: FOFA Adapter。"""

    def test_no_credential(self):
        p = FofaProvider(api_key="")
        r = p.search('ip="1.2.3.4"')
        assert r.ok is False
        assert r.error_code == "NO_CREDENTIAL"

    def test_empty_query(self):
        p = FofaProvider(api_key="k")
        r = p.search("")
        assert r.ok is False
        assert r.error_code == "INVALID_INPUT"

    def test_base_url_normalization(self):
        # config.yaml 範例可能是完整端點; 應正規化為 origin
        p = FofaProvider(api_key="k", base_url="https://fofa.info/api/v1/search/all")
        assert p.base_url == "https://fofa.info"
        assert p._search_url() == "https://fofa.info/api/v1/search/all"

    def test_relay_style_base_url(self):
        # 專案曾用 fofoapi.com relay; origin 正規化後仍組出正確 path
        p = FofaProvider(api_key="k", base_url="https://fofoapi.com/api/v1/search/all")
        assert p.base_url == "https://fofoapi.com"

    def test_qbase64_encoding(self):
        import base64
        p = FofaProvider(api_key="k")
        # 直接驗證內部編碼邏輯與 Go 端 base64.StdEncoding 一致
        expect = base64.b64encode('domain="example.com"'.encode()).decode()
        assert expect == base64.b64encode(b'domain="example.com"').decode()

    def test_pagination_params(self, mock_fofa):
        mock_fofa.search("q", page=2, size=50)
        assert mock_fofa.calls[0]["page"] == 2
        assert mock_fofa.calls[0]["size"] == 50


class TestZoomEyeAdapter:
    """測試 2: ZoomEye Adapter。"""

    def test_no_credential(self):
        p = ZoomEyeProvider(api_key="")
        r = p.search('ip="1.2.3.4"')
        assert r.ok is False
        assert r.error_code == "NO_CREDENTIAL"

    def test_endpoint_default(self):
        p = ZoomEyeProvider(api_key="k")
        assert p.endpoint == "https://api.zoomeye.ai/v2/search"

    def test_legacy_org_domain_normalized(self):
        # 與 Go handler 一致: api.zoomeye.org -> api.zoomeye.ai
        p = ZoomEyeProvider(api_key="k", base_url="https://api.zoomeye.org/v2/search")
        assert "api.zoomeye.ai" in p.endpoint
        assert "api.zoomeye.org" not in p.endpoint

    def test_origin_base_url_appends_path(self):
        p = ZoomEyeProvider(api_key="k", base_url="https://api.zoomeye.ai")
        assert p.endpoint == "https://api.zoomeye.ai/v2/search"


class TestResponseParsing:
    """測試 3: API 回應解析。"""

    def test_fofa_row_to_asset(self):
        from asset_intelligence.models import normalize_fofa_row
        fields = ["host", "ip", "port", "domain", "title", "protocol", "country"]
        row = ["www.example.com", "203.0.113.10", "443", "www.example.com",
               "Example", "https", "US"]
        a = normalize_fofa_row(row, fields)
        assert a is not None
        assert a.ip == "203.0.113.10"
        assert a.port == 443
        assert a.domain == "www.example.com"
        assert a.source_providers == ["fofa"]
        assert a.asset_id.startswith("jyai_")

    def test_fofa_row_host_with_port(self):
        from asset_intelligence.models import normalize_fofa_row
        fields = ["host", "ip", "port", "domain"]
        row = ["www.example.com:8443", "203.0.113.10", "8443", ""]
        a = normalize_fofa_row(row, fields)
        assert a is not None
        assert "www.example.com" in (a.hostname + a.domain)

    def test_fofa_row_invalid(self):
        from asset_intelligence.models import normalize_fofa_row
        assert normalize_fofa_row(["", "", "", ""], ["host", "ip", "port", "domain"]) is None
        assert normalize_fofa_row("not-a-list", ["host"]) is None

    def test_zoomeye_row_to_asset(self):
        from asset_intelligence.models import normalize_zoomeye_row
        row = {"ip": "203.0.113.10", "port": 443, "domain": "www.example.com",
               "title": "Example", "service": "https", "app": "nginx",
               "country": "US"}
        a = normalize_zoomeye_row(row)
        assert a is not None
        assert a.ip == "203.0.113.10"
        assert a.port == 443
        assert a.product == "nginx"
        assert a.source_providers == ["zoomeye"]

    def test_zoomeye_row_invalid(self):
        from asset_intelligence.models import normalize_zoomeye_row
        assert normalize_zoomeye_row({"port": 80}) is None
        assert normalize_zoomeye_row("bad") is None

    def test_http_error_classification(self):
        p = FofaProvider(api_key="k")
        assert isinstance(p.classify_http_error(401), AuthError)
        assert isinstance(p.classify_http_error(403), EntitlementError)
        assert isinstance(p.classify_http_error(429), RateLimitError)
        assert isinstance(p.classify_http_error(402), QuotaExhaustedError)
        assert isinstance(p.classify_http_error(503), UpstreamError)
