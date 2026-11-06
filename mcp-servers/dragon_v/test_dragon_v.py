#!/usr/bin/env python3
"""Dragon-V MCP server smoke test（in-process，不需啟動 stdio）。"""

import importlib
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.ERROR)

PKG = Path(__file__).resolve().parent
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import dragon_v_mcp_server as server

FAILURES = []


def check(name: str, fn):
    try:
        result = fn()
        assert result is not None, f"{name}: None result"
        print(f"[OK] {name}")
        return result
    except Exception as exc:  # noqa: BLE001
        FAILURES.append(f"{name}: {exc!r}")
        print(f"[FAIL] {name}: {exc!r}")
        return None


# --- 1. 資料庫載入 ---
check("CVE index 載入", lambda: server._EXPLOIT_DB.cve_index)
stats = server._EXPLOIT_DB.stats()
print(f"      CVE 總數: {stats['total_cves']}, 應用: {stats['apps']}, 嚴重度: {stats['severities']}")
assert stats["total_cves"] >= 400, f"CVE 數量異常: {stats['total_cves']}"

# --- 2. search / details ---
res = check("dragonv_search_exploits", lambda: server.dragonv_search_exploits("anythingllm", 5))
assert res and len(res["results"]) > 0, "search 無結果"

res = check("dragonv_get_exploit_details", lambda: server.dragonv_get_exploit_details("CVE-2024-0455"))
assert res and res.get("found"), "get_exploit_details 未找到 CVE-2024-0455"

# --- 3. 雙前綴修正 ---
res = check("generate_payload 正規化", lambda: server.dragonv_generate_payload("CVE-CVE-2021-44228", "reverse_shell", "10.0.0.1", 4444))
assert res and "CVE-CVE-" not in res["payload"], "仍出現 CVE-CVE- 雙前綴"
assert "CVE" in res["payload"] or len(res["payload"]) > 10

# --- 4. 參數驗證（應拋錯） ---
for label, fn in [
    ("target 注入拒絕", lambda: server.dragonv_port_scan("1.2.3.4;rm -rf /", "80")),
    ("ports 注入拒絕", lambda: server.dragonv_port_scan("127.0.0.1", "80;whoami")),
    ("ports 越界拒絕", lambda: server.dragonv_port_scan("127.0.0.1", "70000")),
    ("attacker_ip 注入拒絕", lambda: server.dragonv_generate_payload("CVE-2021-44228", "reverse_shell", "1.2.3.4`id", 4444)),
    ("attacker_port 越界拒絕", lambda: server.dragonv_generate_payload("CVE-2021-44228", "reverse_shell", "1.2.3.4", 99999)),
    ("url 注入拒絕", lambda: server.dragonv_hunter_scan("https://x.com;cat /etc/passwd")),
]:
    try:
        fn()
        FAILURES.append(f"{label}: 未拒絕注入")
        print(f"[FAIL] {label}: 未拒絕注入")
    except (ValueError, TypeError):
        print(f"[OK] {label}")

# --- 5. 其他 tools ---
check("dragonv_payload", lambda: server.dragonv_search_payloads("SQL", 5))
check("dragonv_stats", lambda: server.dragonv_stats())
check("dragonv_lookup_fingerprint", lambda: server.dragonv_lookup_fingerprint("comfyui"))
check("dragonv_health", lambda: server.dragonv_health())

# --- 6. 工具清單可列出 ---
tools = getattr(server, "app", None)
if tools is None:
    FAILURES.append("app 不存在")
    print("[FAIL] app 不存在")
else:
    try:
        from mcp.server.fastmcp import FastMCP

        names = sorted(t.name if hasattr(t, "name") else str(t) for t in tools._tool_manager.list_tools())
        print(f"[OK] 註冊 tools: {names}")
    except Exception as exc:  # noqa: BLE001
        print(f"      tool 清單無法列舉（不影響）: {exc!r}")

if FAILURES:
    print("\n=== 失敗 ===")
    for f in FAILURES:
        print(f" - {f}")
    sys.exit(1)
print("\n=== DRAGON-V SMOKE TEST PASSED ===")