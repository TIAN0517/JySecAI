"""設定載入 — 環境變數優先, 其次 JySecAI config.yaml (解密 enc:cfg:v1)。

金鑰安全: 值僅存於記憶體, 錯誤訊息與日誌永不輸出原始金鑰。
"""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or default


def _env_int(name: str, default: int, lo: int = 0, hi: int = 10**9) -> int:
    try:
        return max(lo, min(int(os.environ.get(name, "").strip() or default), hi))
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


@dataclass
class AssetIntelConfig:
    # Provider 金鑰 (僅記憶體)
    fofa_api_key: str = ""
    zoomeye_api_key: str = ""
    fofa_base_url: str = "https://fofa.info"
    zoomeye_base_url: str = "https://api.zoomeye.ai/v2/search"
    # 行為
    timeout_seconds: float = 30.0
    max_retries: int = 2
    max_pages_per_query: int = 5          # 分頁硬性上限
    rate_limit_per_minute: int = 30       # 每 provider 每分鐘
    daily_budget: int = 500               # 每日請求預算 (每 provider)
    search_timeout_seconds: float = 120.0  # 整體查詢超時
    # 儲存
    db_path: str = ""                      # 空 -> 預設 data/asset_intelligence.db
    cache_ttl_seconds: int = 3600
    # TLS — 與 tls_policy.py 相同策略
    verify_tls: bool = True
    ca_bundle: str = ""
    # 授權範圍: {scope_id: {cidrs:[], domains:[], ips:[]}}
    scopes: dict = field(default_factory=dict)

    @staticmethod
    def default_db_path() -> str:
        """預設 DB 路徑: 專案 data/ 下 (與 .gitignore 的 data/ 一致, 不入版控)。"""
        env_path = _env("ASSET_INTEL_DB_PATH")
        if env_path:
            return env_path
        candidates = [
            Path(os.environ.get("JYSECAI_ROOT", "")) / "data" if os.environ.get("JYSECAI_ROOT") else None,
            Path.cwd() / "data",
            Path(__file__).resolve().parent.parent.parent / "data",  # mcp-servers/../data
        ]
        for c in candidates:
            if c and c.is_dir():
                return str(c / "asset_intelligence.db")
        return str(Path.cwd() / "data" / "asset_intelligence.db")

    @classmethod
    def from_env(cls) -> "AssetIntelConfig":
        # TLS 策略: 與 tls_policy.py 完全一致
        ca_bundle = _env("JYSSECAI_CA_BUNDLE")
        insecure = _env("JYSSECAI_INSECURE_TLS").lower() in ("1", "true", "yes")
        verify = False if insecure else True
        return cls(
            fofa_api_key=_resolve_secret("FOFA_API_KEY"),
            zoomeye_api_key=_resolve_secret("ZOOMEYE_API_KEY"),
            fofa_base_url=_env("FOFA_BASE_URL", "https://fofa.info"),
            zoomeye_base_url=_env("ZOOMEYE_BASE_URL", "https://api.zoomeye.ai/v2/search"),
            timeout_seconds=float(_env_int("ASSET_INTEL_TIMEOUT", 30, 5, 300)),
            max_retries=_env_int("ASSET_INTEL_MAX_RETRIES", 2, 0, 5),
            max_pages_per_query=_env_int("ASSET_INTEL_MAX_PAGES", 5, 1, 20),
            rate_limit_per_minute=_env_int("ASSET_INTEL_RATE_LIMIT", 30, 1, 600),
            daily_budget=_env_int("ASSET_INTEL_DAILY_BUDGET", 500, 1, 100000),
            search_timeout_seconds=float(_env_int("ASSET_INTEL_SEARCH_TIMEOUT", 120, 10, 3600)),
            db_path=cls.default_db_path(),
            cache_ttl_seconds=_env_int("ASSET_INTEL_CACHE_TTL", 3600, 0, 86400 * 7),
            verify_tls=verify,
            ca_bundle=ca_bundle,
            scopes=_load_scopes_from_env(),
        )


def _resolve_secret(env_name: str) -> str:
    """金鑰解析: 環境變數優先; 支援 enc:cfg:v1 (JySecAI AES-GCM 設定加密) 解密。

    解密金鑰來源與 internal/config/secret_protection.go 一致:
    JYSECAI_CONFIG_KEY / JYSECAI_CREDENTIAL_KEY / {config}.secrets.key 檔案。
    """
    raw = _env(env_name)
    if not raw:
        return ""
    if not raw.startswith("enc:cfg:v1:"):
        return raw
    return _decrypt_cfg_v1(raw)


def _decrypt_cfg_v1(protected: str) -> str:
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise RuntimeError(
            "cryptography package required to decrypt enc:cfg:v1 secrets; "
            "pip install cryptography"
        )
    key = _load_config_key()
    payload = base64.RawStdEncoding.b64decode(protected[len("enc:cfg:v1:"):])
    nonce, sealed = payload[:12], payload[12:]
    aes = AESGCM(key)
    plain = aes.decrypt(nonce, sealed, None)
    return plain.decode("utf-8")


def _load_config_key() -> bytes:
    """與 secret_protection.go decodeConfigSecretKey 相同: base64/hex 編碼的 32 bytes。"""
    key_text = os.environ.get("JYSECAI_CONFIG_KEY", "").strip() or \
        os.environ.get("JYSECAI_CREDENTIAL_KEY", "").strip()
    if not key_text:
        key_path = os.environ.get("JYSECAI_CONFIG_PATH", "config.yaml").rstrip(".") + ".secrets.key"
        candidate = Path(key_path)
        # 常見相對路徑: 以專案根為基準
        if not candidate.is_file():
            project_root = Path(__file__).resolve().parent.parent.parent
            candidate = project_root / (key_path if not Path(key_path).is_absolute() else key_path).lstrip("./")
            key_path = str(project_root / (os.environ.get("JYSECAI_CONFIG_PATH", "config.yaml") + ".secrets.key"))
            candidate = Path(key_path)
        if candidate.is_file():
            key_text = candidate.read_text(encoding="utf-8").strip()
    if not key_text:
        raise RuntimeError("enc:cfg:v1 secret present but JYSECAI_CONFIG_KEY not set and key file not found")
    for decoder in (base64.b64decode, base64.urlsafe_b64decode, bytes.fromhex):
        try:
            key = decoder(key_text)
            if len(key) == 32:
                return key
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError("config key must encode exactly 32 bytes (base64 or hex)")


def _load_scopes_from_env() -> dict:
    """從環境變數載入授權範圍: ASSET_INTEL_SCOPE (JSON) 或 ASSET_INTEL_SCOPE_FILE。"""
    import json

    raw = _env("ASSET_INTEL_SCOPE")
    file_path = _env("ASSET_INTEL_SCOPE_FILE")
    data = None
    if raw:
        try:
            data = json.loads(raw)
        except ValueError:
            return {}
    elif file_path and Path(file_path).is_file():
        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        except ValueError:
            return {}
    if isinstance(data, dict) and ("cidrs" in data or "domains" in data or "ips" in data):
        return {"default": data}
    if isinstance(data, dict):
        return data  # {scope_id: {...}}
    return {}
