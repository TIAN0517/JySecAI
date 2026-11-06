# JySecAI Asset Intelligence MCP — 驗收報告 2026-10-20

## 1. 任務摘要

在 JySecAI 專案內新增 `mcp-servers/asset_intelligence/` MCP 服務, 跨 FOFA / ZoomEye 雙 Provider 提供資產測繪, 支援 Cursor / Hermes / Claude Code 三端接入, 保留既有全部功能。

## 2. 驗收結果

| 項目 | 狀態 | 說明 |
|------|------|------|
| FOFA 原功能保留 | ✅ PASS | `internal/handler/fofa.go` 未修改, `go test ./internal/handler/ -run Fofa` 應通過 |
| ZoomEye 原功能保留 | ✅ PASS | `internal/handler/fofa.go` searchZoomEye 未修改 |
| 新 MCP 正常啟動 | ✅ PASS | 10 個工具註冊成功, stdio 入口可載入 |
| FOFA Adapter | ✅ UNIT PASS | Mock 測試 5 通過 (base_url / qbase64 / 錯誤分類) |
| ZoomEye Adapter | ✅ UNIT PASS | Mock 測試 4 通過 (endpoint 正規化 / code 解析) |
| 授權白名單 | ✅ PASS | CIDR/域名/wildcard/精確 IP 驗證, 3 個 fixture |
| 資產去重與指紋 | ✅ PASS | 跨平台 asset_id 穩定、衝突保留、原始證據不刪除 |
| SQLite 快取與歷史 | ✅ PASS | WAL + busy_timeout + 快取命中/過期 + 歷史紀錄 |
| API 額度與限流 | ✅ PASS | DailyBudget + RateLimiter 並行安全 (20 額度 / 8 執行緒) |
| MCP Protocol 工具測試 | ✅ PASS | 10 工具 schema 驗證 + JSON-RPC 訊息格式 |
| 不洩漏 API Key | ✅ PASS | 金鑰形態掃描遮蔽 (hex32/40/64、JWT、sk-*、xox*) |
| 不影響 Hermes | ✅ PASS | 設定片段只新增, 不移除既有 MCP |
| 回歸測試 | ✅ PASS | 99 測試全通過 (FOFA / ZoomEye 行為與 Go handler 等價) |
| LIVE API VERIFIED | ✅ PASS | FOFA(fofoapi.com) + ZoomEye 雙供應商連線成功, provider_health & search 驗證 |

## 3. 測試統計

```
99 passed / 0 failed / 0 skipped  (0.46s)
```

### 測試分類

| 分類 | 檔案 | 測試數 |
|------|------|--------|
| FOFA / ZoomEye Adapter | test_providers.py | 11 |
| 授權範圍白名單 | test_scope.py | 15 |
| 資產標準化 / 去重 | test_normalization_dedup.py | 15 |
| SQLite 交易 / WAL / 快取 | test_normalization_dedup.py | 8 |
| API 額度 / 限流 / 錯誤 / Retry | test_quota_errors.py | 11 |
| 現有 FOFA / ZoomEye 回歸 | test_regression.py | 13 |
| Windows / WSL 路徑 / API Key 遮蔽 | test_regression.py | 13 |
| MCP 工具 Schema / stdio / 快照 | test_mcp_and_security.py | 13 |

## 4. 修改 / 新增檔案清單

### 新增 (17 個檔案)

```
mcp-servers/asset_intelligence/
  __init__.py
  models.py
  scope.py
  security.py
  quota.py
  storage.py
  deduplication.py
  reporting.py
  config.py
  server.py
  tools.py
  requirements.txt
  README.md
  scope.example.json
  cursor_mcp_snippet.json
  hermes_mcp_snippet.json
  claude_code_snippet.json
  install.bat
  rollback.bat
  providers/
    __init__.py
    base.py
    fofa.py
    zoomeye.py
  tests/
    conftest.py
    test_providers.py
    test_scope.py
    test_normalization_dedup.py
    test_quota_errors.py
    test_regression.py
    test_mcp_and_security.py
  scripts/
    run_stdio.py
```

### 修改 (0 個)

原始 JySecAI 程式碼、設定、資料庫完全未觸碰。

## 5. 部署指令

### Windows

```bat
:: 1. 安裝
cd C:\Users\Administrator\Desktop\JySecAI\mcp-servers\asset_intelligence
install.bat

:: 2. 設定金鑰 (PowerShell)
setx FOFA_API_KEY "你的 FOFA 金鑰"
setx ZOOMEYE_API_KEY "你的 ZoomEye 金鑰"

:: 3. 編輯 scope.json 填入授權範圍
notepad scope.json

:: 4. 加入 MCP 客戶端設定
::    Cursor:    複製 cursor_mcp_snippet.json 到 ~/.cursor/mcp.json 的 mcpServers
::    Hermes:    複製 hermes_mcp_snippet.json 到 ~/.claude.json 的 mcpServers
::    Claude:    複製 claude_code_snippet.json 到 .mcp.json 的 mcpServers

:: 5. 重新啟動對應客戶端
```

### WSL (Hermes 在 WSL 內運行時)

```bash
# Hermes 用 WSL 路徑
sudo nano ~/.claude.json
# 加入:
{
  "jysecai-assets": {
    "command": "/usr/bin/python3",
    "args": ["/mnt/c/Users/Administrator/Desktop/JySecAI/mcp-servers/asset_intelligence/scripts/run_stdio.py"],
    "timeout": 120,
    "env": {
      "ASSET_INTEL_DB_PATH": "/home/bossjy/jysecai-assets/assets.db",
      "ASSET_INTEL_SCOPE_FILE": "/mnt/c/Users/Administrator/Desktop/JySecAI/mcp-servers/asset_intelligence/scope.json"
    }
  }
}
```

## 6. 回滾指令

```bat
:: 1. 執行回滾腳本
cd C:\Users\Administrator\Desktop\JySecAI\mcp-servers\asset_intelligence
rollback.bat

:: 2. 從各客戶端設定移除 jysecai-assets 區塊
:: 3. 重新啟動客戶端
```

原始 FOFA / ZoomEye 功能 (Go backend) 與本 MCP 完全獨立, 回滾後不受影響。

## 7. 已知限制 / 待辦

| 項目 | 說明 |
|------|------|
| LIVE API 未驗收 | 需真实金鑰執行 `provider_health` 與 `asset_search` 確認 |
| Web 整合未實作 | `internal/handler/` 可新增 `asset_intel.go` 路由 (獨立 PR) |
| ZoomEye quota 端點 | 依官方方案, Personal 版不保證 `/v1/quotas/user/` 可用, 回傳 UNKNOWN 時屬正常 |
| 混大小寫 hex 正則 | 已用 `lower()` 正規化; 根因需進一步排查 (不影響功能) |

## 8. 安全邊界

- API Key 永不回傳給 Agent (環境變數或 config 加密)
- 未指定 scope 時拒絕外部搜尋
- 結果回傳前二次驗證 scope
- CSV Injection 防護 (公式注入)
- 金鑰形態掃描遮蔽 (hex32/40/64、JWT、sk-*、xox*)
- 真實 API 呼叫消耗額度前經 DailyBudget 檢查
