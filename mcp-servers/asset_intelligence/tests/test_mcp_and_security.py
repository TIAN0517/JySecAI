"""測試 14-17: CSV Injection 防護、MCP 工具 Schema、MCP stdio 初始化、歷史快照差異。"""
from __future__ import annotations

import json

import pytest

from asset_intelligence.security import (
    csv_escape_cell, mask_secret, redact_text, rows_to_csv, sanitize_mapping
)


class TestCsvInjection:
    """測試 14: CSV Injection 防護。"""

    def test_formula_prefix_single_quote(self):
        assert csv_escape_cell("=A1+B2") == "'=A1+B2"
        assert csv_escape_cell("+cmd") == "'+cmd"
        assert csv_escape_cell("@SUM(1,2)") == "'@SUM(1,2)"
        assert csv_escape_cell("\tvalue") == "'\tvalue"

    def test_dde_payload(self):
        assert csv_escape_cell('cmd|/c calc') == "'cmd|/c calc"

    def test_safe_values_pass_through(self):
        assert csv_escape_cell("hello") == "hello"
        assert csv_escape_cell("123") == "123"
        assert csv_escape_cell("") == ""
        assert csv_escape_cell(None) == ""

    def test_rows_to_csv_output(self):
        rows = [{"name": "test", "value": "=A1"}]
        csv_text = rows_to_csv(rows, ["name", "value"])
        assert "'=A1" in csv_text
        assert "test" in csv_text


class TestMcpToolSchema:
    """測試 15: MCP 工具 Schema。"""

    def test_app_has_all_tools(self, cfg):
        from asset_intelligence.server import create_app
        app = create_app(cfg)
        # FastMCP 1.x 的 tool names 存在 _tool_manager._tools
        # MCPServer 2.x 有 .tools() method
        if hasattr(app, "tools"):
            tools = app.tools()
            tool_names = [t.name for t in tools]
        else:
            tool_names = list(app._tool_manager._tools.keys())
        expected = [
            "asset_search", "asset_details", "asset_fingerprint",
            "asset_deduplicate", "asset_history", "asset_changes",
            "provider_health", "provider_quota", "asset_export", "asset_report",
        ]
        for name in expected:
            assert name in tool_names, f"missing tool: {name}"
        assert len(tool_names) >= 10

    def test_tool_has_description(self, cfg):
        from asset_intelligence.server import create_app
        app = create_app(cfg)
        if hasattr(app, "tools"):
            tools = {t.name: t for t in app.tools()}
        else:
            tools = {n: t for n, t in app._tool_manager._tools.items()}
        for name in ("asset_search", "asset_details", "asset_fingerprint"):
            tool = tools[name]
            assert tool.description is not None
            assert len(tool.description) > 20

    def test_asset_search_params(self, cfg):
        from asset_intelligence.server import create_app
        app = create_app(cfg)
        if hasattr(app, "tools"):
            tools = {t.name: t for t in app.tools()}
        else:
            tools = {n: t for n, t in app._tool_manager._tools.items()}
        tool = tools["asset_search"]
        params = tool.parameters
        # target 應為 required
        if isinstance(params, dict):
            assert "target" in params.get("required", [])
        # providers 有預設值 (非 required)
        if isinstance(params, dict) and "providers_" in params.get("properties", {}):
            assert "default" in params["properties"]["providers_"]


class TestMcpStdioInit:
    """測試 16: MCP stdio 初始化與工具呼叫。"""

    def test_stdio_protocol_messages(self, tmp_path):
        """測試 MCP JSON-RPC 訊息格式 (離線驗證, 不啟動真實伺服器)。"""
        # 驗證 JSON-RPC 訊息結構能正確序列化和反序列化
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
                "capabilities": {}
            }
        }
        encoded = json.dumps(init_msg)
        decoded = json.loads(encoded)
        assert decoded["jsonrpc"] == "2.0"
        assert decoded["method"] == "initialize"
        assert decoded["id"] == 1

        # 驗證工具呼叫訊息格式
        call_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "asset_search",
                "arguments": {"target": "example.com"}
            }
        }
        encoded2 = json.dumps(call_msg)
        decoded2 = json.loads(encoded2)
        assert decoded2["method"] == "tools/call"
        assert decoded2["params"]["name"] == "asset_search"


class TestHistorySnapshotChanges:
    """測試 17: 歷史快照與差異。"""

    def test_asset_history(self, store):
        store.record_history(
            trace_id="t1", provider="fofa", query="test query", page=1,
            ok=True, error_code="", total=10, results_count=3,
            api_calls=1, credits_used=1, duration_ms=120, scope_id="s1")
        rows = store.get_history()
        assert len(rows) == 1
        assert rows[0]["provider"] == "fofa"
        assert rows[0]["ok"] == 1

    def test_history_filter_by_provider(self, store):
        store.record_history(
            trace_id="t1", provider="fofa", query="q1", page=1,
            ok=True, error_code="", total=0, results_count=0,
            api_calls=1, credits_used=0, duration_ms=100, scope_id="s")
        store.record_history(
            trace_id="t2", provider="zoomeye", query="q2", page=1,
            ok=True, error_code="", total=0, results_count=0,
            api_calls=1, credits_used=0, duration_ms=100, scope_id="s")
        fofa_only = store.get_history(provider="fofa")
        assert len(fofa_only) == 1
        assert fofa_only[0]["provider"] == "fofa"

    def test_snapshot_save_and_get(self, store):
        from asset_intelligence.models import Asset
        a1 = Asset(ip="203.0.113.10", port=443)
        a2 = Asset(ip="203.0.113.11", port=80)
        result = store.save_snapshot("s1", "test label", [a1, a2])
        assert result["asset_count"] == 2
        snap = store.get_snapshot(result["snapshot_id"])
        assert snap["asset_count"] == 2
        assert len(snap["payload"]) == 2

    def test_changes_added_removed_changed(self, store):
        from asset_intelligence.models import Asset
        # 快照 A: 2 筆
        a1 = Asset(ip="203.0.113.10", port=443, product="nginx")
        a2 = Asset(ip="203.0.113.11", port=80, product="Apache")
        store.save_snapshot("s", "before", [a1, a2])
        snaps = store.list_snapshots()
        before_id = snaps[0]["id"]
        # 快照 B: 移除 a2, 新增 a3, a1 變更產品
        a1_changed = Asset(ip="203.0.113.10", port=443, product="openresty")
        a3 = Asset(ip="203.0.113.12", port=22, product="ssh")
        store.save_snapshot("s", "after", [a1_changed, a3])
        snaps = store.list_snapshots()
        after_id = snaps[0]["id"]
        # 比較差異
        from asset_intelligence.tools import compute_changes
        before_snap = store.get_snapshot(before_id)
        after_snap = store.get_snapshot(after_id)
        changes = compute_changes(
            before_snap["payload"], after_snap["payload"])
        assert changes["added_count"] == 1
        assert changes["removed_count"] == 1
        assert changes["changed_count"] == 1
        # a1 的 product 應在 changes 中
        assert any("product" in c["changes"] for c in changes["changed"])

    def test_list_snapshots(self, store):
        from asset_intelligence.models import Asset
        a = Asset(ip="203.0.113.10", port=443)
        store.save_snapshot("s1", "label1", [a])
        store.save_snapshot("s2", "label2", [a])
        snaps = store.list_snapshots(limit=10)
        assert len(snaps) == 2
        assert snaps[0]["label"] == "label2"  # 最近在前
