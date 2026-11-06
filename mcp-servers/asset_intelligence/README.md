# JySecAI Asset Intelligence MCP

統一資產測繪 MCP — 跨 **FOFA** 與 **ZoomEye** 的授權資產搜尋、標準化、去重、快取、歷史與報告。

以 MCP stdio 提供服務,可同時接入 **Cursor**、**Hermes**、**Claude Code**。

## 設計原則

- **重用既有已驗證邏輯**:FOFA 對齊 `internal/handler/fofa.go` 的 Search();ZoomEye 對齊同檔 `searchZoomEye()` 與 `tools/zoomeye_search.yaml`(端點 `https://api.zoomeye.ai/v2/search`,header `API-KEY`)。
- **TLS**:第三方 API 一律驗證憑證鏈(與 `tls_policy.py` 一致;`JYSSECAI_CA_BUNDLE` 可指定自訂 CA,`JYSSECAI_INSECURE_TLS=1` 為明確逃生艙)。
- **授權範圍**:未設定 scope 時拒絕一切外部搜尋;查詢前、結果回傳前雙重驗證;CIDR 須為授權網段子集。
- **金鑰安全**:金鑰僅由環境變數(`FOFA_API_KEY` / `ZOOMEYE_API_KEY`)注入,或使用 JySecAI `enc:cfg:v1` 加密格式;**永不**經 Agent 參數、日誌或報告傳遞,輸出前一律經遮蔽。
- **證據保留**:去重不刪除原始觀測;來源衝突保留雙方於 `conflicts` 與 `raw_reference`。

## 安裝

```bash
# Windows (系統 Python 3.11 已含 mcp 1.30.0 / httpx / cryptography)
pip install -r requirements.txt

# 或 Kali WSL
python3 -m pip install -r requirements.txt
```

## 設定

環境變數(全部可選,但無金鑰時對應 provider 回 `NO_CREDENTIAL`):

| 變數 | 說明 | 預設 |
|---|---|---|
| `FOFA_API_KEY` | FOFA 金鑰(或 `enc:cfg:v1:...` 加密格式) | 空 |
| `ZOOMEYE_API_KEY` | ZoomEye 金鑰(同上) | 空 |
| `FOFA_BASE_URL` | FOFA origin | `https://fofa.info` |
| `ZOOMEYE_BASE_URL` | ZoomEye 端點 | `https://api.zoomeye.ai/v2/search` |
| `ASSET_INTEL_SCOPE` / `ASSET_INTEL_SCOPE_FILE` | 授權範圍 JSON 或檔案 | 空(= 拒絕搜尋) |
| `ASSET_INTEL_DAILY_BUDGET` | 每日請求預算(每 provider) | 500 |
| `ASSET_INTEL_RATE_LIMIT` | 每分鐘請求上限(每 provider) | 30 |
| `ASSET_INTEL_MAX_PAGES` | 單次查詢分頁上限 | 5 |
| `ASSET_INTEL_DB_PATH` | SQLite 路徑(WAL) | `<root>/data/asset_intelligence.db` |

授權範圍範例(`scope.json`):

```json
{
  "default": {
    "cidrs": ["203.0.113.0/24"],
    "domains": ["example.com", "*.example.com"],
    "ips": ["198.51.100.7"]
  }
}
```

## 啟動(stdio)

```bash
python -m mcp_servers_asset_intel   # 見 scripts/run_stdio.py
# 或
python scripts/run_stdio.py
```

## MCP 工具(10)

| Tool | 說明 |
|---|---|
| `asset_search` | 跨 FOFA/ZoomEye 並行搜尋(scope 驗證、快取、預算、二次過濾) |
| `asset_details` | 以 asset_id 查完整細節(含遮蔽後的原始證據) |
| `asset_fingerprint` | 服務/產品/協定/埠指紋統計 |
| `asset_deduplicate` | 跨平台去重,保留衝突 |
| `asset_history` | 查詢歷史(provider、消耗、耗時) |
| `asset_changes` | 快照差異比較(新增/移除/欄位變更) |
| `provider_health` | API 連線健康 |
| `provider_quota` | 配額/額度查詢(不可得時 UNKNOWN,不推定) |
| `asset_export` | JSON/CSV 匯出(CSV Injection 防護) |
| `asset_report` | 資產分析報告 |

## 測試

```bash
python -m pytest tests/ -v          # 全部離線單元測試(Mock,無外部 API)
```

## Cursor 設定片段(`.cursor/mcp.json` 或全域 `mcp.json`)

```json
{
  "mcpServers": {
    "jysecai-assets": {
      "command": "C:\\Program Files\\Python311\\python.exe",
      "args": [
        "C:\\Users\\Administrator\\Desktop\\JySecAI\\mcp-servers\\asset_intelligence\\scripts\\run_stdio.py"
      ],
      "env": {
        "FOFA_API_KEY": "<以環境變數注入,勿提交>",
        "ZOOMEYE_API_KEY": "<以環境變數注入,勿提交>",
        "ASSET_INTEL_SCOPE_FILE": "C:\\Users\\Administrator\\Desktop\\JySecAI\\mcp-servers\\asset_intelligence\\scope.example.json"
      },
      "timeout": 120
    }
  }
}
```

## Hermes(WSL kali-linux)設定片段

Hermes 位於 `~/.hermes/hermes-agent`(WSL)。新增 MCP 時**保留**既有
`ida`、`hexstrike-ai`、`kali-mcp`、`ida-pro`、`huggingface` 設定,僅追加:

```json
{
  "jysecai-assets": {
    "command": "/usr/bin/python3",
    "args": [
      "/mnt/c/Users/Administrator/Desktop/JySecAI/mcp-servers/asset_intelligence/scripts/run_stdio.py"
    ],
    "env": {
      "FOFA_API_KEY": "<經 hermes 環境注入>",
      "ZOOMEYE_API_KEY": "<經 hermes 環境注入>"
    }
  }
}
```

## Claude Code

```bash
claude mcp add jysecai-assets -- "C:\Program Files\Python311\python.exe" ^
  "C:\Users\Administrator\Desktop\JySecAI\mcp-servers\asset_intelligence\scripts\run_stdio.py"
```

## 回滾

1. 從各客戶端 MCP 設定移除 `jysecai-assets` 條目(其他伺服器不動)。
2. 刪除 `mcp-servers/asset_intelligence/` 目錄(不影響既有 FOFA/ZoomEye 功能:
   Web UI `/api/fofa/search`、`tools/fofa_search.yaml`、`tools/zoomeye_search.yaml` 完全未修改)。
3. 資料庫 `data/asset_intelligence.db` 為獨立新檔,刪除即可,不影響既有資料。
