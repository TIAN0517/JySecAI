"""測試 4-5: 授權範圍白名單、IP/Domain/CIDR 驗證。"""
from __future__ import annotations

import pytest

from asset_intelligence.scope import Scope, ScopeDenied, build_scope_from_config


class TestScopeWhitelist:
    """測試 4: 授權範圍白名單。"""

    def test_empty_scope_denies_all(self):
        scope = Scope(scope_id="empty")
        assert scope.is_empty()
        assert scope.check_ip("8.8.8.8") is False
        assert scope.check_domain("example.com") is False

    def test_exact_ip_allowed(self, authorized_scope):
        assert authorized_scope.check_ip("198.51.100.7") is True

    def test_ip_in_authorized_cidr(self, authorized_scope):
        assert authorized_scope.check_ip("203.0.113.10") is True
        assert authorized_scope.check_ip("203.0.113.254") is True

    def test_ip_outside_scope_denied(self, authorized_scope):
        assert authorized_scope.check_ip("8.8.8.8") is False
        assert authorized_scope.check_ip("203.0.114.1") is False  # 相鄰網段

    def test_domain_exact_and_wildcard(self, authorized_scope):
        assert authorized_scope.check_domain("example.com") is True
        assert authorized_scope.check_domain("www.example.com") is True
        assert authorized_scope.check_domain("a.b.example.com") is True

    def test_similar_domain_not_matched(self, authorized_scope):
        # 不可用字串包含判斷: notexample.com 不應命中 example.com
        assert authorized_scope.check_domain("notexample.com") is False
        assert authorized_scope.check_domain("example.com.evil.io") is False

    def test_check_asset_dual_validation(self, authorized_scope):
        # IP 不在範圍即使域名合法也拒絕
        assert authorized_scope.check_asset("8.8.8.8", "www.example.com") is False
        # 兩者都在範圍
        assert authorized_scope.check_asset("203.0.113.10", "www.example.com") is True

    def test_filter_assets_split(self, authorized_scope):
        class A:
            def __init__(self, ip="", domain=""):
                self.ip, self.domain, self.hostname = ip, domain, ""

        allowed, denied = authorized_scope.filter_assets(
            [A("203.0.113.1"), A("9.9.9.9"), A("", "www.example.com"),
             A("", "evil.com")])
        assert len(allowed) == 2
        assert len(denied) == 2

    def test_cidr_must_be_subset(self):
        import ipaddress
        scope = Scope(scope_id="s")
        scope.add_cidr("203.0.113.0/24")
        # /25 子集應通過
        tn = ipaddress.ip_network("203.0.113.0/25")
        an = ipaddress.ip_network("203.0.113.0/24")
        assert tn.subnet_of(an)
        # 超集不應通過
        assert not an.subnet_of(tn)

    def test_build_scope_from_config(self):
        scope = build_scope_from_config({
            "cidrs": ["203.0.113.0/24"], "domains": ["example.com"],
            "ips": ["198.51.100.7"]})
        assert scope is not None
        assert len(scope.entries) == 3

    def test_build_scope_empty_returns_none(self):
        assert build_scope_from_config(None) is None
        assert build_scope_from_config({}) is None
        assert build_scope_from_config({"domains": []}) is None


class TestIpDomainCidrValidation:
    """測試 5: IP/Domain/CIDR 驗證。"""

    def test_valid_ipv4(self):
        from asset_intelligence.models import validate_ip
        assert validate_ip("192.0.2.1") == "192.0.2.1"

    def test_valid_ipv6(self):
        from asset_intelligence.models import validate_ip
        assert validate_ip("2001:db8::1") == "2001:db8::1"
        # 壓縮正規化
        assert validate_ip("2001:0db8:0000:0000:0000:0000:0000:0001") == "2001:db8::1"

    def test_invalid_ip(self):
        from asset_intelligence.models import validate_ip
        assert validate_ip("999.1.1.1") is None
        assert validate_ip("not-an-ip") is None
        assert validate_ip("") is None
        assert validate_ip(None) is None

    def test_valid_domain(self):
        from asset_intelligence.models import validate_domain
        assert validate_domain("WWW.Example.COM.") == "www.example.com"

    def test_invalid_domain(self):
        from asset_intelligence.models import validate_domain
        assert validate_domain("-bad.example.com") is None
        assert validate_domain("bad..example.com") is None
        assert validate_domain("a" * 64 + ".com") is None  # label > 63

    def test_valid_cidr(self):
        from asset_intelligence.models import validate_cidr
        assert validate_cidr("203.0.113.0/24") == "203.0.113.0/24"
        assert validate_cidr("2001:db8::/32") == "2001:db8::/32"

    def test_invalid_cidr(self):
        from asset_intelligence.models import validate_cidr
        assert validate_cidr("203.0.113.0") is None   # 缺前綴
        assert validate_cidr("203.0.113.0/33") is None

    def test_port_validation(self):
        from asset_intelligence.models import validate_port
        assert validate_port(443) == 443
        assert validate_port("8443") == 8443
        assert validate_port(0) is None
        assert validate_port(65536) is None
        assert validate_port("abc") is None
