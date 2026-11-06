"""資產標準化模型 — 跨 FOFA / ZoomEye 統一 Asset Schema。

設計原則:
- 原始證據永不刪除: 每筆 provider 原始紀錄保留在 raw_reference。
- 衝突保留: 多來源資訊衝突時保留來源、時間與差異, 不任意覆蓋。
- asset_id 為具命名空間、穩定排序的識別鍵 (sha256), 同一輸入恆得同一輸出。
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

# 私有/保留位址 — 白名單授權判斷時允許 (內網授權測試), 但需標記
_INVALID_HOSTNAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)*$")
_WILDCARD_HOSTNAME_RE = re.compile(r"^\*\.([A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)*$)")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean(value: Any, max_len: int = 512) -> str:
    """清理任意輸入為安全字串: strip、截斷、None -> 空字串。"""
    if value is None:
        return ""
    s = str(value).strip()
    if len(s) > max_len:
        s = s[:max_len]
    return s


def validate_ip(value: str) -> Optional[str]:
    """驗證並正規化 IPv4/IPv6; 無效回傳 None。"""
    v = _clean(value)
    if not v:
        return None
    try:
        ip = ipaddress.ip_address(v)
        return str(ip)
        # nosec B104 — 此為字串驗證函式, 不涉及綁定位址
    except ValueError:
        return None


def validate_domain(value: str, *, allow_wildcard: bool = False) -> Optional[str]:
    """驗證並正規化域名 (轉小寫、去尾點、允許 *. 前綴); 無效回傳 None。"""
    v = _clean(value).lower().rstrip(".")
    if not v or len(v) > 253:
        return None
    if v in ("localhost",) or v.endswith(".local") or v.endswith(".internal"):
        return v  # 內部名稱仍可保留, 由 scope 決定是否授權
    if allow_wildcard:
        if not v.startswith("*."):
            if not _INVALID_HOSTNAME_RE.match(v):
                return None
        elif not _WILDCARD_HOSTNAME_RE.match(v):
            return None
        base = v[2:] if v.startswith("*.") else v
    else:
        base = v
    if not base:
        return None
    for label in base.split("."):
        if len(label) > 63:
            return None
    if not _INVALID_HOSTNAME_RE.match(base):
        return None
    return v


def validate_port(value: Any) -> Optional[int]:
    try:
        p = int(value)
    except (TypeError, ValueError):
        return None
    if 0 < p <= 65535:
        return p
    return None


def validate_cidr(value: str) -> Optional[str]:
    """驗證 CIDR (需含前綴); 回傳正規化字串或 None。"""
    v = _clean(value)
    if "/" not in v:
        # 自動補 /32 或 /128 交由呼叫端決定 — 此處僅接受明確前綴
        return None
    try:
        net = ipaddress.ip_network(v, strict=False)
        return str(net)
    except ValueError:
        return None


@dataclass
class Asset:
    """統一資產紀錄。"""

    ip: str = ""
    port: int = 0
    protocol: str = ""          # tcp / udp / http / https
    domain: str = ""
    hostname: str = ""
    service: str = ""
    product: str = ""
    version: str = ""
    banner: str = ""
    title: str = ""
    country: str = ""
    city: str = ""
    tls_certificate: dict = field(default_factory=dict)
    confidence: float = 0.5     # 0.0 ~ 1.0
    source_providers: list = field(default_factory=list)
    observed_at: str = ""
    first_seen: str = ""
    last_seen: str = ""
    raw_reference: dict = field(default_factory=dict)  # {provider: raw_row}
    authorization_scope_id: str = ""
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.ip = validate_ip(self.ip) or ""
        self.port = validate_port(self.port) or 0
        self.domain = validate_domain(self.domain) or ""
        self.hostname = validate_domain(self.hostname) or ""
        self.protocol = _clean(self.protocol, 16).lower()
        self.service = _clean(self.service, 64)
        self.product = _clean(self.product, 128)
        self.version = _clean(self.version, 64)
        self.banner = _clean(self.banner, 4096)
        self.title = _clean(self.title, 512)
        self.observed_at = self.observed_at or utc_now_iso()
        if not self.first_seen:
            self.first_seen = self.observed_at
        if not self.last_seen:
            self.last_seen = self.observed_at

    @property
    def asset_id(self) -> str:
        """穩定識別鍵: jyai:<ip|domain>:<port>:<protocol>, sha256 後 16 hex。

        空值欄位以 '-' 佔位並於鍵中保留位置, 保證穩定排序。
        """
        ip_part = self.ip or (self.domain or self.hostname or "-")
        parts = [ip_part, str(self.port or 0), self.protocol or "-"]
        key_raw = ":".join(parts)
        return "jyai_" + hashlib.sha256(key_raw.encode("utf-8")).hexdigest()[:16]

    @property
    def is_valid(self) -> bool:
        return bool(self.ip or self.domain or self.hostname)

    def merge(self, other: "Asset") -> list:
        """合併另一筆觀測 — 衝突保留差異於 conflicts, 不覆蓋原值。

        回傳衝突描述列表。
        """
        conflicts: list = []
        if other.ip and other.ip != self.ip:
            conflicts.append({"field": "ip", "kept": self.ip, "other": other.ip})
        for fld in ("domain", "hostname", "service", "product", "version"):
            mine = getattr(self, fld)
            theirs = getattr(other, fld)
            if theirs and theirs != mine:
                if not mine:
                    setattr(self, fld, theirs)
                else:
                    conflicts.append({"field": fld, "kept": mine, "other": theirs})
        for p in other.source_providers:
            if p not in self.source_providers:
                self.source_providers.append(p)
        for prov, raw in (other.raw_reference or {}).items():
            self.raw_reference[prov] = raw  # 原始證據永遠保留最新
        if other.observed_at > self.last_seen:
            self.last_seen = other.observed_at
        if other.observed_at < self.first_seen:
            self.first_seen = other.observed_at
        if other.confidence != self.confidence:
            self.confidence = round(max(self.confidence, other.confidence), 3)
        self.conflicts = conflicts
        return conflicts

    def to_dict(self) -> dict:
        d = asdict(self)
        d["asset_id"] = self.asset_id
        d.pop("conflicts", None)
        return d


def normalize_fofa_row(row: list, fields: list, provider_meta: Optional[dict] = None) -> Optional[Asset]:
    """將 FOFA v1 results (list-of-list, 依 fields 對應) 轉為 Asset。"""
    if not isinstance(row, list) or not fields:
        return None
    m = {}
    for i, f in enumerate(fields):
        m[f] = row[i] if i < len(row) else None
    # host 欄位可能含埠 (例: "www.example.com:8443"), 先分離
    host_raw = _clean(m.get("host"))
    if host_raw and ":" in host_raw:
        host_part = host_raw.rsplit(":", 1)[0]
    else:
        host_part = host_raw
    asset = Asset(
        ip=_clean(m.get("ip")),
        port=m.get("port"),
        protocol=_clean(m.get("protocol")) or "tcp",
        domain=_clean(m.get("domain")),
        hostname=_clean(host_part),
        service=_clean(m.get("protocol")),
        product=_clean(m.get("server")),
        title=_clean(m.get("title")),
        country=_clean(m.get("country")),
        city=_clean(m.get("city") or m.get("region") or m.get("province")),
        confidence=0.7,
        source_providers=["fofa"],
    )
    if not asset.domain and asset.hostname:
        asset.domain = asset.hostname
    if not asset.is_valid:
        return None
    if provider_meta:
        asset.raw_reference["fofa"] = provider_meta
    asset.raw_reference["fofa_row"] = {f: _clean(m.get(f), 2048) for f in fields}
    return asset


def normalize_zoomeye_row(row: dict, provider_meta: Optional[dict] = None) -> Optional[Asset]:
    """將 ZoomEye v2 search row (dict) 轉為 Asset。"""
    if not isinstance(row, dict):
        return None
    port_info = row.get("port") if not isinstance(row.get("port"), dict) else row["port"].get("port")
    asset = Asset(
        ip=_clean(row.get("ip")),
        port=port_info,
        protocol=_clean(row.get("protocol")) or ("https" if str(row.get("port")) == "443" else "tcp"),
        domain=_clean(row.get("domain")),
        hostname=_clean(row.get("hostname") or row.get("host")),
        service=_clean(row.get("service") or row.get("service.name")),
        product=_clean(row.get("app") or row.get("server")),
        title=_clean(row.get("title") or (row.get("title") or {}).get("title") if isinstance(row.get("title"), dict) else row.get("title")),
        country=_clean(row.get("country") or (row.get("country") or {}).get("names") if isinstance(row.get("country"), dict) else row.get("country")),
        city=_clean(row.get("city")),
        confidence=0.7,
        source_providers=["zoomeye"],
    )
    if not asset.is_valid:
        return None
    if provider_meta:
        asset.raw_reference["zoomeye"] = provider_meta
    asset.raw_reference["zoomeye_row"] = {k: _clean(v, 2048) for k, v in row.items() if k in (
        "ip", "port", "domain", "hostname", "title", "service", "app", "server", "country", "city", "protocol",
    )}
    return asset


def schema_fields() -> list:
    """回傳統一 schema 欄位清單 (匯出/報告用)。"""
    return [
        "asset_id", "ip", "domain", "hostname", "port", "protocol", "service",
        "product", "version", "banner", "title", "country", "city",
        "tls_certificate", "source_providers", "first_seen", "last_seen",
        "observed_at", "confidence", "raw_reference", "authorization_scope_id",
    ]
