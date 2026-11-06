"""授權範圍 (scope) 管理與驗證 — CIDR/域名/精確 IP 白名單。

安全原則:
- 未指定授權目標時, 拒絕執行外部資產搜尋。
- 結果回傳前再次驗證, 不依賴字串包含判斷。
- CIDR 僅允許完整網段授權, 精確比對經 ipaddress 模組運算。
"""
from __future__ import annotations

import fnmatch
import ipaddress
from dataclasses import dataclass, field
from typing import Optional

from .models import validate_cidr, validate_domain, validate_ip


class ScopeDenied(Exception):
    """目標不在授權範圍。"""

    def __init__(self, target: str, reason: str = "not in authorized scope"):
        self.target = target
        self.reason = reason
        super().__init__(f"SCOPE_DENIED: {target} ({reason})")


@dataclass
class ScopeEntry:
    scope_id: str
    kind: str            # cidr | domain | domain_wildcard | ip
    value: str           # 正規化後的值
    description: str = ""


@dataclass
class Scope:
    """授權範圍白名單 — 全部條件皆需命中才放行外, 任何一條命中即放行。"""

    scope_id: str = "default"
    entries: list = field(default_factory=list)

    def add_cidr(self, cidr: str, description: str = "") -> bool:
        norm = validate_cidr(cidr)
        if not norm:
            return False
        self.entries.append(ScopeEntry(self.scope_id, "cidr", norm, description))
        return True

    def add_domain(self, domain: str, description: str = "") -> bool:
        norm = validate_domain(domain, allow_wildcard=True)
        if not norm:
            return False
        kind = "domain_wildcard" if norm.startswith("*.") else "domain"
        self.entries.append(ScopeEntry(self.scope_id, kind, norm, description))
        return True

    def add_ip(self, ip: str, description: str = "") -> bool:
        norm = validate_ip(ip)
        if not norm:
            return False
        self.entries.append(ScopeEntry(self.scope_id, "ip", norm, description))
        return True

    def is_empty(self) -> bool:
        return not self.entries

    # ---- 驗證邏輯 ----

    def check_ip(self, ip: str) -> bool:
        norm = validate_ip(ip)
        if not norm:
            return False
        addr = ipaddress.ip_address(norm)
        for e in self.entries:
            if e.kind == "ip" and e.value == norm:
                return True
            if e.kind == "cidr":
                try:
                    if addr in ipaddress.ip_network(e.value):
                        return True
                except ValueError:
                    continue
        return False

    def check_domain(self, domain: str) -> bool:
        norm = validate_domain(domain)
        if not norm:
            return False
        for e in self.entries:
            if e.kind == "domain" and e.value == norm:
                return True
            if e.kind == "domain_wildcard":
                # *.example.com 比對 example.com 與其全部子網域
                base = e.value[2:]
                if norm == base or norm.endswith("." + base):
                    return True
        return False

    def check_host(self, host: str) -> bool:
        """host 可為 IP 或域名, 自動分流驗證。"""
        if validate_ip(host):
            return self.check_ip(host)
        return self.check_domain(host)

    def check_asset(self, asset_ip: str = "", domain: str = "", hostname: str = "") -> bool:
        """資產級驗證: IP 與域名任一命中授權即通過 (同時提供時兩者都驗)。"""
        if asset_ip and validate_ip(asset_ip):
            if not self.check_ip(asset_ip):
                return False
        targets = [d for d in (domain, hostname) if d]
        if targets:
            return any(self.check_domain(d) for d in targets)
        return bool(asset_ip)

    def filter_assets(self, assets: list) -> tuple:
        """回傳 (允許清單, 拒絕清單) — 回傳前二次驗證用。"""
        allowed, denied = [], []
        for a in assets:
            ip = getattr(a, "ip", "") or (a.get("ip", "") if isinstance(a, dict) else "")
            dom = getattr(a, "domain", "") or (a.get("domain", "") if isinstance(a, dict) else "")
            host = getattr(a, "hostname", "") or (a.get("hostname", "") if isinstance(a, dict) else "")
            if self.check_asset(ip, dom, host):
                allowed.append(a)
            else:
                denied.append(a)
        return allowed, denied


def build_scope_from_config(scope_cfg: Optional[dict]) -> Optional[Scope]:
    """從設定 dict 建立 Scope; 空設定回傳 None (代表未授權任何目標)。"""
    if not scope_cfg or not isinstance(scope_cfg, dict):
        return None
    scope = Scope(scope_id=str(scope_cfg.get("scope_id", "default")))
    for c in scope_cfg.get("cidrs", []) or []:
        scope.add_cidr(str(c))
    for d in scope_cfg.get("domains", []) or []:
        scope.add_domain(str(d))
    for i in scope_cfg.get("ips", []) or []:
        scope.add_ip(str(i))
    return scope if scope.entries else None


class ScopeRegistry:
    """多授權範圍註冊表 — 以 scope_id 管理, 供查詢時指定。"""

    def __init__(self) -> None:
        self._scopes: dict = {}

    def register(self, scope: Scope) -> None:
        self._scopes[scope.scope_id] = scope

    def get(self, scope_id: str) -> Optional[Scope]:
        return self._scopes.get(scope_id)

    def default(self) -> Optional[Scope]:
        return self._scopes.get("default") or (next(iter(self._scopes.values())) if self._scopes else None)

    def list(self) -> list:
        return [{"scope_id": s.scope_id, "entries": len(s.entries)} for s in self._scopes.values()]
