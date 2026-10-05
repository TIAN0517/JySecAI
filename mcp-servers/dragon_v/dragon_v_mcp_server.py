#!/usr/bin/env python3
"""Dragon-V MCP server for JySecAI — offline CVE/指紋/負載庫 + 授權掃描包裝。

遷移自 serverall `mcp_server_protocol.py`，並依據 platform 慣例改寫為
FastMCP（mcp SDK 1.x/2.x 相容）。修正與強化：
- port_scan / vulnerability_scan：subprocess 改 args list、禁用 shell、
  驗證 target 與 ports，消除命令注入。
- generate_payload：cve_id 正規化（修復「CVE-CVE-」雙前綴）。
- 所有資料載入改用相對路徑（DRAGON_V_DATA_DIR 可覆寫）。
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

try:  # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:  # MCP SDK 1.x compatibility
    from mcp.server.fastmcp import FastMCP as _MCPServer

from apps import cve_sync as _cve_sync
from apps.exploit_database import MCPExploitDatabase, default_data_dir
from apps.payloads_database import MCPPayloadsDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("dragon_v")

_DATA_DIR: Path = default_data_dir()
_FINGERPRINT_DIR: Path = _DATA_DIR / "fingerprints"
_EVAL_DIR: Path = _DATA_DIR / "eval"

_EXPLOIT_DB = MCPExploitDatabase(_DATA_DIR)
_PAYLOAD_DB = MCPPayloadsDatabase()

_NMAP_TIMEOUT = 120
_IP_OR_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PORT_SPEC_RE = re.compile(r"^[0-9,\-\s]+$")
_HTTP_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _validate_target(target: str) -> str:
    value = (target or "").strip()
    if not value:
        raise ValueError("target 不能為空")
    if any(ch in value for ch in ";|&`$<>()\n\r\"'"):
        raise ValueError("target 包含不允許的字元")
    if not _IP_OR_HOST_RE.fullmatch(value):
        raise ValueError("target 必須是 IP 或 hostname（例如 127.0.0.1 或 example.com）")
    return value


def _expand_port_list(ports: str) -> str:
    """驗證並正規化埠號規格（逗號/範圍，1-65535），回傳 nmap 可接受的字串。"""
    value = (ports or "1-1000").strip().replace(" ", "")
    if not _PORT_SPEC_RE.fullmatch(value):
        raise ValueError("ports 只能包含數字、逗號與範圍線段（例如 80,443,1-1000）")
    seen = set()
    tokens: list[str] = []
    for part in value.split(","):
        if "-" in part:
            lo_s, _, hi_s = part.partition("-")
            lo, hi = int(lo_s), int(hi_s)
            if lo < 1 or hi > 65535 or lo > hi:
                raise ValueError("埠號範圍必須在 1-65535 且低值在前")
            seen.update(range(lo, hi + 1))
            tokens.append(f"{lo}-{hi}")
        else:
            port = int(part)
            if port < 1 or port > 65535:
                raise ValueError(f"埠號 {port} 超出 1-65535")
            seen.add(port)
            tokens.append(str(port))
    if len(seen) > 10000:
        raise ValueError("埠號範圍過大（最多 10000 個埠）")
    return ",".join(tokens)


def _validate_http_url(target_url: str) -> str:
    value = (target_url or "").strip()
    if not _HTTP_URL_RE.fullmatch(value):
        raise ValueError("target_url 必須以 http:// 或 https:// 開頭")
    if any(ch in value for ch in ";|&`$ \t\n\r"):  # 空格/控制字元加入 f" 樣板會造成錯誤參數
        raise ValueError("target_url 包含不允許的字元")
    parsed = urlparse(value)
    if not parsed.hostname:
        raise ValueError("target_url 缺少主機名稱")
    return value


def _run_nmap(args: list[str], scan_kind: str) -> Dict[str, Any]:
    exe = shutil.which("nmap")
    if not exe:
        raise RuntimeError("找不到 nmap，請先安裝（https://nmap.org）")
    scan_id = f"{scan_kind}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    result = subprocess.run(
        [exe, *args],
        capture_output=True,
        text=True,
        timeout=_NMAP_TIMEOUT,
        check=False,
    )
    return {
        "scan_id": scan_id,
        "command": [exe, *args],
        "output": result.stdout,
        "error": result.stderr,
        "success": result.returncode == 0,
    }


def _load_fingerprint_yamls() -> list[Dict[str, Any]]:
    fingerprints: list[Dict[str, Any]] = []
    if not _FINGERPRINT_DIR.is_dir():
        return fingerprints
    for yaml_file in sorted(_FINGERPRINT_DIR.rglob("*.yaml")):
        try:
            import yaml

            with yaml_file.open("r", encoding="utf-8") as fh:
                doc = yaml.safe_load(fh)
            if isinstance(doc, dict):
                doc.setdefault("file", yaml_file.stem)
                fingerprints.append(doc)
        except Exception:
            continue
    return fingerprints


app = _MCPServer(
    name="dragon-v",
    instructions=(
        "Dragon-V 整合：離線 CVE（中/英 YAML）、應用指紋、滲透負載與授權掃描。 "
        "所有掃描僅供已授權的滲透測試；generate_payload 產生的負載只能在授權目標與受控環境使用。"
    ),
)


@app.tool(description="搜尋 Dragon-V 離線 CVE 資料庫（中文+英文合併去重，筆數以 dragonv_stats 為準）")
def dragonv_search_exploits(keyword: str, limit: int = 50) -> Dict[str, Any]:
    if not keyword or not keyword.strip():
        raise ValueError("keyword 不能為空")
    return {"query": keyword, "results": _EXPLOIT_DB.search_exploits(keyword, limit)}


@app.tool(description="取得單一 CVE 的詳細資訊（含 CVSS、修護建議、參考來源）")
def dragonv_get_exploit_details(cve_id: str) -> Dict[str, Any]:
    if not cve_id or not cve_id.strip():
        raise ValueError("cve_id 不能為空")
    details = _EXPLOIT_DB.get_exploit_by_cve(cve_id)
    if not details:
        return {"cve_id": cve_id, "found": False}
    return {"cve_id": details["cve"], "found": True, **details}


@app.tool(description="針對指定 CVE 生成利用負載（reverse_shell/web_shell/sql_injection/xss；僅供授權測試）")
def dragonv_generate_payload(
    cve_id: str,
    payload_type: str = "reverse_shell",
    attacker_ip: str = "127.0.0.1",
    attacker_port: int = 4444,
) -> Dict[str, Any]:
    allowed = {"reverse_shell", "web_shell", "sql_injection", "xss"}
    if payload_type not in allowed:
        raise ValueError(f"payload_type 必須是 {sorted(allowed)} 之一")
    payload = _EXPLOIT_DB.generate_exploit_payload(cve_id, payload_type, attacker_ip, attacker_port)
    return {
        "cve_id": cve_id,
        "payload_type": payload_type,
        "payload": payload,
        "authorized_testing_only": True,
    }


@app.tool(description="搜尋滲透負載資料庫（SQLi / XSS / 命令執行）")
def dragonv_search_payloads(keyword: str, limit: int = 20) -> Dict[str, Any]:
    if not keyword or not keyword.strip():
        raise ValueError("keyword 不能為空")
    return {"query": keyword, "results": _PAYLOAD_DB.search_payloads(keyword, limit)}


@app.tool(description="Dragon-V 離線資料庫統計（CVE 數、應用數、嚴重度分布、年度分布、負載數、同步狀態）")
def dragonv_stats() -> Dict[str, Any]:
    stats = _EXPLOIT_DB.stats()
    stats["payload_counts"] = _PAYLOAD_DB.get_all_payloads_count()
    stats["fingerprint_count"] = len(_load_fingerprint_yamls())
    stats["eval_datasets"] = [p.name for p in _EVAL_DIR.glob("*.json")] if _EVAL_DIR.is_dir() else []
    stats["data_dir"] = str(_DATA_DIR)
    stats["last_synced"] = _cve_sync.read_sync_state(_DATA_DIR).get("last_synced")
    years: Dict[str, int] = {}
    for cve_id in _EXPLOIT_DB.cve_index:
        match = re.match(r"CVE-(\d{4})-", cve_id)
        if match:
            years[match.group(1)] = years.get(match.group(1), 0) + 1
    stats["cve_years"] = dict(sorted(years.items()))
    return stats


@app.tool(description="從 NVD API 2.0 增量同步 AI/LLM 應用 CVE 到離線武器庫（keywords 逗號分隔可選、省略時用 fingerprints+內建清單；dry_run 只統計不寫檔；需網路，無 NVD_API_KEY 時限速 5 req/30s）")
def dragonv_sync_cves(
    keywords: str = "",
    max_per_keyword: int = 20,
    dry_run: bool = False,
) -> Dict[str, Any]:
    if max_per_keyword < 1 or max_per_keyword > 200:
        raise ValueError("max_per_keyword 必須在 1-200 之間")
    keyword_list = (
        [k.strip() for k in keywords.split(",") if k.strip()]
        if keywords and keywords.strip()
        else None
    )
    result = _cve_sync.sync_cves(
        keyword_list,
        max_per_keyword=max_per_keyword,
        dry_run=dry_run,
        data_dir=_DATA_DIR,
    )
    if not dry_run and result.get("total_new"):
        global _EXPLOIT_DB  # 重新載入，讓 search/details/stats 立即涵蓋同步進來的 CVE
        _EXPLOIT_DB = MCPExploitDatabase(_DATA_DIR)
    return result


@app.tool(description="查詢應用指紋庫（AI/LLM 應用，含子目錄，如 anythingllm、comfyui、fastapi），回傳特徵、CVE 對應與探測路徑")
def dragonv_lookup_fingerprint(app_name: str = "") -> Dict[str, Any]:
    fingerprints = _load_fingerprint_yamls()
    query = app_name.strip().lower()
    matched = [
        fp
        for fp in fingerprints
        if not query or query in fp.get("file", "").lower() or query in str(fp.get("name", "")).lower()
    ]
    return {"query": app_name, "count": len(matched), "fingerprints": matched[:20]}


@app.tool(description="執行授權 nmap 埠掃描（target 驗證 + 無 shell 的 args list 呼叫）")
def dragonv_port_scan(target: str, ports: str = "1-1000") -> Dict[str, Any]:
    host = _validate_target(target)
    port_spec = _expand_port_list(ports)
    try:
        result = _run_nmap(["-sS", "-Pn", "-p", port_spec, host, "-oX", "-"], "port_scan")
    except subprocess.TimeoutExpired:
        return {"target": host, "ports": port_spec, "success": False, "error": f"掃描超過 {_NMAP_TIMEOUT}s"}
    except (OSError, RuntimeError) as exc:
        return {"target": host, "ports": port_spec, "success": False, "error": str(exc)}
    return {"target": host, "ports": port_spec, **result}


@app.tool(description="執行授權 nmap 漏洞腳本掃描（--script vuln；target 驗證 + args list）")
def dragonv_vulnerability_scan(target: str) -> Dict[str, Any]:
    host = _validate_target(target)
    try:
        result = _run_nmap(["-sV", "--script", "vuln", "-Pn", host], "vuln_scan")
    except subprocess.TimeoutExpired:
        return {"target": host, "success": False, "error": f"掃描超過 {_NMAP_TIMEOUT}s"}
    except (OSError, RuntimeError) as exc:
        return {"target": host, "success": False, "error": str(exc)}
    return {"target": host, **result}


@app.tool(description="執行 Dragon-V Hunter 業務邏輯滲透鏈（授權目標專用；需 aiohttp/cryptography/dnspython/pandas）")
def dragonv_hunter_scan(target_url: str, timeout_seconds: int = 120) -> Dict[str, Any]:
    url = _validate_http_url(target_url)
    if timeout_seconds < 10 or timeout_seconds > 600:
        raise ValueError("timeout_seconds 必須在 10-600 之間")
    import asyncio

    hunter_dir = Path(__file__).resolve().parent / "hunter"
    if hunter_dir not in sys.path:
        sys.path.insert(0, str(hunter_dir))
    try:
        from main import DragonVHunter
    except ImportError as exc:
        missing = str(exc)
        return {
            "target_url": url,
            "success": False,
            "error": f"hunter 依賴缺失：{missing}（需要 aiohttp、cryptography、dnspython、pandas）",
        }
    try:
        hunter = DragonVHunter()
        result = asyncio.run(hunter.full_chain_penetration(url))
    except Exception as exc:
        return {"target_url": url, "success": False, "error": str(exc)}
    result["success"] = True
    result["authorized_testing_only"] = True
    return result


@app.tool(description="檢查 nmap 是否可用，以及各資料庫是否載入成功")
def dragonv_health() -> Dict[str, Any]:
    return {
        "ok": True,
        "nmap_available": bool(shutil.which("nmap")),
        "data_dir": str(_DATA_DIR),
        "cve_count": len(_EXPLOIT_DB.cve_index),
        "fingerprint_count": len(_load_fingerprint_yamls()),
        "payload_total": _PAYLOAD_DB.get_all_payloads_count().get("total", 0),
    }


if __name__ == "__main__":
    app.run(transport="stdio")