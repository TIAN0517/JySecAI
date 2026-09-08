# Dragon-V MCP Server

Dragon-V Triple Bot 整合套件（由 `serverall` 完整遷移）。提供離線 CVE 資料庫、
應用指紋、滲透負載與授權掃描，作為 JySecAI 的外部 MCP 伺服器。

## 遷移來源
- `serverall/serverall/mcp_server_protocol.py` → `dragon_v_mcp_server.py`（改寫為 FastMCP）
- `serverall/serverall/mcp_exploit_database.py` → `apps/exploit_database.py`（＋CVE-CVE- 修正）
- `serverall/serverall/mcp_payloads_database.py` → `apps/payloads_database.py`
- `serverall/serverall/vuln/`, `vuln_en/` → `data/cve/{zh,en}`（414+414 YAML）
- `serverall/serverall/fingerprints/` → `data/fingerprints/`（36 YAML）
- `serverall/serverall/eval/` → `data/eval/`（5 JSON）
- `serverall/serverall/dragon_v_hunter/` → `hunter/`（越南化滲透鏈）

## 資料目錄
預設為套件內 `data/`，可用環境變數 `DRAGON_V_DATA_DIR` 覆寫。

## 執行（stdio）
```bash
JYSECAI_PYTHON=python3
$JYSECAI_PYTHON mcp-servers/dragon_v/dragon_v_mcp_server.py
```

## 在 JySecAI config.yaml 註冊
```yaml
external_mcp:
  servers:
    dragon-v:
      type: stdio
      command: "${JYSECAI_PYTHON:-venv/bin/python3}"
      args: ["mcp-servers/dragon_v/dragon_v_mcp_server.py"]
      external_mcp_enable: true
      keep_alive: 30
      timeout: 180
      max_retries: 5
      terminate_duration: 120
```

## Tools
- `dragonv_search_exploits` / `dragonv_get_exploit_details` — 離線 CVE 查詢
- `dragonv_generate_payload` — 負載生成（僅授權測試）
- `dragonv_search_payloads` / `dragonv_stats` — 負載庫/統計
- `dragonv_lookup_fingerprint` — 36 種應用指紋
- `dragonv_port_scan` / `dragonv_vulnerability_scan` — nmap 包裝（args list，無 shell）
- `dragonv_hunter_scan` — Dragon-V Hunter 滲透鏈（授權目標）
- `dragonv_health` — 完整性檢查

## 安全注意
- `port_scan`/`vulnerability_scan` 使用 args list 呼叫 nmap，target 與 ports 均經過驗證。
- 所有掃描與負載產生均標記「僅供授權測試」。

## 測試
```bash
python mcp-servers/dragon_v/test_dragon_v.py
```