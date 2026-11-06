# JySecAI Asset Intelligence MCP — CHANGELOG

## 2026-10-20 (v1.0.0)

### 新增
- 完整 MCP 服務: 10 個資產情報工具
  - `asset_search` (跨 FOFA / ZoomEye 並行)
  - `asset_details`
  - `asset_fingerprint`
  - `asset_deduplicate`
  - `asset_history`
  - `asset_changes`
  - `provider_health`
  - `provider_quota`
  - `asset_export` (JSON / CSV)
  - `asset_report`
- FOFA Provider: v1 `/api/v1/search/all` + `/api/v1/info/my` (0 點消耗)
- ZoomEye Provider: v2 `/v2/search` (POST) + `/v1/quotas/user/`
- 統一 Asset Schema (asset_id / ip / domain / hostname / port / protocol / service / product / version / banner / tls_certificate / source_providers / first_seen / last_seen / observed_at / confidence / raw_reference / authorization_scope_id)
- 授權範圍白名單 (CIDR / 域名 / wildcard / 精確 IP)
- SQLite 儲存 (WAL + busy_timeout 5s + 交易式批次寫入)
- 快取 (TTL 可配, 預設 10 分鐘)
- 查詢歷史 (provider / 額度 / 耗時 / scope)
- 快照與變更比較
- 跨平台去重 (asset_id 穩定、衝突保留、原始證據不刪除)
- API 配額與限流 (DailyBudget + RateLimiter, 並行安全)
- 金鑰遮蔽 (hex32/40/64、JWT、sk-*、xox*)
- CSV Injection 防護
- 三端 MCP 設定片段 (Cursor / Hermes / Claude Code)
- 安裝 / 回滾腳本 (Windows)
- 99 個離線測試 (Mock 為主)
- 驗收報告

### 未實作
- JySecAI Web 整合 (獨立 PR)
- 真實 API 驗收 (需金鑰)
