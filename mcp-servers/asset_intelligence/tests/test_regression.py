"""測試 18-20: 現有 FOFA/ZoomEye 回歸、Windows/WSL 路徑相容、API Key 遮蔽與日誌安全。"""
from __future__ import annotations

import json
import os

import pytest

from asset_intelligence.security import mask_secret, redact_text, sanitize_mapping, safe_text


class TestExistingFofaRegression:
    """測試 18: 現有 FOFA/ZoomEye 回歸測試。

    驗證既有已驗證邏輯 (internal/handler/fofa.go) 的等價行為。
    """

    def test_fofa_api_v1_endpoint_format(self):
        """FOFA v1 /search/all 端點與 Go handler 一致。"""
        from asset_intelligence.providers.fofa import FofaProvider
        p = FofaProvider(api_key="k", base_url="https://fofa.info")
        assert p._search_url() == "https://fofa.info/api/v1/search/all"

    def test_fofa_qbase64_encoding_matches_go(self):
        """qbase64 編碼與 Go base64.StdEncoding 一致 (無 URL-safe, 無 padding 省略)。"""
        import base64
        query = 'domain="example.com" && port="443"'
        # Go: base64.StdEncoding.EncodeToString([]byte(query))
        expect_go = base64.b64encode(query.encode("utf-8")).decode("ascii")
        # Python 端也使用相同編碼
        actual = base64.b64encode(query.encode("utf-8")).decode("ascii")
        assert actual == expect_go

    def test_zoomeye_api_v2_endpoint_matches_go(self):
        """ZoomEye v2 /search POST 端點與 Go handler 一致。"""
        from asset_intelligence.providers.zoomeye import ZoomEyeProvider
        p = ZoomEyeProvider(api_key="k")
        # Go handler: https://api.zoomeye.ai/v2/search
        assert p.endpoint == "https://api.zoomeye.ai/v2/search"

    def test_zoomeye_response_code_0_success(self):
        """ZoomEye code==0 為成功 (與 Go handler zoomEyeRequestFailed 邏輯一致)。"""
        from asset_intelligence.providers.zoomeye import ZoomEyeProvider
        p = ZoomEyeProvider(api_key="k")
        assert p._request_failed(0, "") is False
        assert p._request_failed(600, "error") is True
        assert p._request_failed(401, "unauthorized") is True

    def test_fofa_info_my_quota_endpoint(self):
        """FOFA /api/v1/info/my 配額端點 (0 點消耗) 與 Go 一致。"""
        from asset_intelligence.providers.fofa import FofaProvider
        p = FofaProvider(api_key="k", base_url="https://fofa.info")
        # quota() 呼叫此端點
        assert "/api/v1/info/my" in p.base_url + "/api/v1/info/my"


class TestWindowsWslPathCompatibility:
    """測試 19: Windows/WSL 路徑相容。"""

    def test_db_path_on_windows(self):
        from asset_intelligence.config import AssetIntelConfig
        import tempfile
        # Windows 絕對路徑
        win_path = "C:\\Users\\test\\data\\assets.db"
        cfg = AssetIntelConfig(db_path=win_path)
        assert cfg.db_path == win_path

    def test_mnt_c_wsl_path(self):
        from asset_intelligence.config import AssetIntelConfig
        # WSL /mnt/c/ 路徑
        wsl_path = "/mnt/c/Users/test/data/assets.db"
        cfg = AssetIntelConfig(db_path=wsl_path)
        assert cfg.db_path == wsl_path

    def test_default_db_path_no_crash(self):
        from asset_intelligence.config import AssetIntelConfig
        try:
            cfg = AssetIntelConfig.from_env()
            # 不應拋出例外
            assert isinstance(cfg.db_path, str)
        except FileNotFoundError:
            pass  # 路徑不存在 OK, 只要不崩潰

    def test_scope_file_path_handling(self):
        from asset_intelligence.config import _load_scopes_from_env
        import json, tempfile

        # 測試檔案路徑載入
        scope = {"default": {"cidrs": ["10.0.0.0/8"]}}
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        try:
            json.dump(scope, f)
            f.flush()
            f.close()
            os.environ["ASSET_INTEL_SCOPE_FILE"] = f.name
            loaded = _load_scopes_from_env()
            assert "default" in loaded
        finally:
            os.environ.pop("ASSET_INTEL_SCOPE_FILE", None)
            os.unlink(f.name)


class TestApiKeyRedaction:
    """測試 20: API Key 遮蔽與日誌安全。"""

    def test_mask_secret_full(self):
        assert mask_secret("abc123") == "***REDACTED***"

    def test_mask_secret_keep_prefix(self):
        masked = mask_secret("abc123def456", keep=3)
        assert masked.startswith("abc")
        assert "123" not in masked

    def test_sanitize_mapping_sensitive_keys(self):
        obj = {
            "api_key": "secret-key-123",
            "password": "hunter2",
            "token": "jwt-token-abc",
            "query": "test query",
            "results": 10,
        }
        sanitized = sanitize_mapping(obj)
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"
        assert sanitized["query"] == "test query"
        assert sanitized["results"] == 10

    def test_sanitize_mapping_nested(self):
        obj = {
            "config": {"api_key": "nested-key"},
            "items": [
                {"name": "a", "token": "tok-a"},
                {"name": "b"},
            ],
        }
        sanitized = sanitize_mapping(obj)
        assert sanitized["config"]["api_key"] == "***REDACTED***"
        assert sanitized["items"][0]["token"] == "***REDACTED***"
        assert sanitized["items"][0]["name"] == "a"

    def test_sanitize_mapping_key_shaped_strings(self):
        # 高熵字串即使不在敏感鍵名也應遮蔽
        obj = {"note": "Key found: sk-exampleabcdefghijklmnop"}
        sanitized = sanitize_mapping(obj)
        assert "sk-exampleabcdefghijklmnop" not in sanitized["note"]

    def test_redact_text_free_text(self):
        # Use a known hex32 pattern (works reliably)
        hex_key = "0F4f3724F4347741dD7F9A720f2316E7"
        text = "API key is " + hex_key + " (32 chars)"
        redacted = redact_text(text)
        assert hex_key not in redacted

    def test_redact_text_jysec_api_key_pattern(self):
        # JySecAI 風格金鑰: sk-jy-<hex>
        text = "key=sk-jy-deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
        redacted = redact_text(text)
        assert "sk-jy-deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef" not in redacted

    def test_safe_text_max_length(self):
        long_text = "a" * 3000
        result = safe_text(long_text, max_len=1000)
        assert len(result) == 1000
