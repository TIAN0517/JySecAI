# 設計：批次開放式跳轉驗證流水線

- 日期：2026-11-01
- 狀態：已核准（使用者勾選「全包」：FOFA/ZoomEye 自動搜尋 + 自動巡站發掘跳轉參數）
- 相關既有程式：`internal/redirect`（探測原語）、`internal/app/redirect_tools.go`（單筆 `redirect_probe` 工具）、`internal/handler/fofa.go`（多 provider 搜尋）

## 目標

把既有「單筆受控跳轉複測」擴成一條可批次、可自動入庫的流水線：

```
情蒐（FOFA/ZoomEye）→ 巡站（發掘跳轉參數）→ 批次驗證（受控端點）→ 自動上鍊（漏洞紀錄）→ 報告
```

操作者在控制台貼上多筆目標 URL（或從情蒐／巡站匯入），指定「跳轉目標」＝自己的受控端點
（預設 `https://97y.me/tjneJ`），一次跑完；驗證成功的目標自動建立漏洞紀錄並歸屬目前專案／對話。

## 已確認的決策（使用者）

| 決策 | 結論 |
| --- | --- |
| 交付範圍 | 全包：情蒐 + 巡站 + 批次 + 自動上鍊 + 控制台 + 報告 |
| 成功判定 | Location 標頭指向受控端點即算成功（沿用 `redirect.IsReflected`） |
| 自動上鍊 | 自動建立漏洞紀錄（開放式跳轉），歸屬目前專案／對話，含證據與複測紀錄 |
| 跳轉目標 | 操作者指定，預設 `https://97y.me/tjneJ`（即平台 `redirect.urls` 的受控端點） |

## 既有能力盤點（實作基礎）

- `internal/redirect`：`NormalizeURLs`、`DetectRedirectParams`（16 個常見跳轉參數名，優先既有 query）、
  `BuildProbeURL`、`ProbeWithMethod`、`IsReflected`（比對主機名，不做後綴比對）、`ProbeResult`。
- `internal/app/redirect_tools.go`：MCP 工具 `redirect_probe`，單一 `target_url`，
  可選 `param`/`method`/`urls`/`vulnerability_id`（回寫證據與複測紀錄）。
- `internal/handler/fofa.go`：`POST /api/fofa/search`，provider = fofa | zoomeye | quake | shodan，
  另有 `POST /api/fofa/parse`（自然語言轉查詢式）。
- `internal/database`：`vulnerabilities` 表、`batch_task_queues` / `batch_tasks` 表（代理任務佇列，
  非確定性 HTTP 批次，不重用）。
- `golang.org/x/net v0.53.0` 已在 go.mod → HTML 解析不需新增依賴。

## 設計

### 1. 批次驗證引擎 `internal/redirect/batch.go`

```go
type BatchOptions struct {
	Endpoints   []string        // 受控端點（跳轉目標）
	Param       string          // 指定參數名；空值則依 DetectRedirectParams 逐一試
	Method      string          // GET / POST
	Concurrency int             // 同時探測數
	Timeout     time.Duration   // 單次探測逾時
}

type BatchTargetResult struct {
	URL        string `json:"url"`
	Confirmed  bool   `json:"confirmed"`
	Param      string `json:"param"`
	RequestURL string `json:"request_url"`
	Status     int    `json:"status"`
	Location   string `json:"location"`
	Error      string `json:"error,omitempty"`
}

func VerifyTargets(ctx context.Context, client *http.Client, targets []string, opts BatchOptions) []BatchTargetResult
```

- worker pool 限制併發；`ctx` 取消即停止（剩餘項標記為取消）。
- 每個目標：指定 `Param` → 只探一次；未指定 → 依 `DetectRedirectParams` 逐一試，命中即停。
- 回應永不跟隨重新導向（沿用 `ProbeWithMethod`）。
- 目標 URL 去重、去除空白；非 http/https 直接標記錯誤。

### 2. 落庫 `internal/database/redirect_verify.go`

新表（forward-compatible migration，舊資料檔不受影響）：

- `redirect_verify_runs`：id, created_at, updated_at, status(pending|running|completed|cancelled|failed),
  endpoints, param, method, concurrency, total, completed, confirmed, project_id, conversation_id,
  user_id, auto_record, error, cancel_requested。
- `redirect_verify_results`：id, run_id, created_at, url, confirmed, param, request_url, status,
  location, error, vulnerability_id。

DAO：`CreateRedirectVerifyRun`、`UpdateRedirectVerifyRun`、`AppendRedirectVerifyResult`、
`GetRedirectVerifyRun`、`ListRedirectVerifyResults`、`ListRedirectVerifyRunsForAccess`。

### 3. REST API `internal/handler/redirect_verify.go`

| 方法 | 路徑 | 說明 |
| --- | --- | --- |
| POST | `/api/redirect-verify/runs` | 建立批次：targets[]、endpoints[]、param、method、project_id、conversation_id、auto_record；立即回 run_id，背景執行 |
| POST | `/api/redirect-verify/runs/:id/cancel` | 請求取消（背景 worker 觀察 ctx） |
| GET | `/api/redirect-verify/runs/:id` | 進度 + 結果清單 |
| GET | `/api/redirect-verify/runs` | 批次列表（含權限過濾） |
| GET | `/api/redirect-verify/runs/:id/report` | 報告（`format=markdown|csv`） |
| POST | `/api/redirect-verify/seed` | 情蒐：provider + query → 取主機清單 → 可直接建立批次 |

權限沿用既有慣例：`crudPermission(method, "vulnerability")` 之類；詳見 `internal/security/rbac_middleware.go`。

### 4. 自動上鍊

批次結果 `confirmed=true` 且 `auto_record=true` 時：

- 依 `db.CreateVulnerability` 建立「開放式跳轉」紀錄：標題、嚴重度、target、證據（請求 URL、
  狀態碼、Location）、複測紀錄（受控端點、參數名、時間）。
- 歸屬：優先 `project_id`，其次 `conversation_id`；無則不建立（回報原因）。
- 權限：需要 `vulnerability:write`；不足則只留結果不建紀錄，並在摘要標示。
- 標題模板：`開放式跳轉（受控跳轉驗證確認）- <host>`。

### 5. 自動巡站 `internal/redirect/crawl.go`

```go
type CrawlOptions struct {
	MaxPages     int
	MaxDepth     int
	SameHostOnly bool
	Timeout      time.Duration
	Concurrency  int
	UserAgent    string
}

type CrawlResult struct {
	PagesVisited int
	Candidates   []string
	Visited      []string
}

func DiscoverRedirectCandidates(ctx context.Context, client *http.Client, seeds []string, opts CrawlOptions) CrawlResult
```

- 以 `golang.org/x/net/html` 解析頁面，收集 `<a href>`、`<form action>`、`<link href>`。
- 候選判定：URL query 含 `DetectRedirectParams` 的參數名 → 視為疑似跳轉入口。
- 同主機限制預設開啟；頁數／深度上限可調；`ctx` 可取消。

### 6. 情蒐串接

- `POST /api/redirect-verify/seed` 沿用 `FofaHandler` 的多 provider 搜尋（需把既有搜尋邏輯抽出成
  可回傳結果的函式，HTTP handler 與批次匯入共用同一份）。
- 搜尋結果取 `host` 去重 → 作為巡站種子或直接作為驗證目標。

### 7. MCP 工具擴充 `internal/app/redirect_tools.go`

`redirect_probe` 新增：

- `target_urls`（字串陣列）：與 `target_url` 二擇一；給多筆時走批次驗證。
- `auto_record`（布林）：成功時自動建立漏洞紀錄（需 `vulnerability:write`）。
- 既有單筆行為與 `vulnerability_id` 回寫保持不變（向後相容）。

### 8. 前端控制台

- 新增頁面「批次跳轉驗證」（router case `redirect-verify`，導覽放在資產／安全防護區）。
- 版面：左欄「跳轉目標（受控端點）」（預填 `https://97y.me/tjneJ`）＋「目標清單」多行輸入；
  右欄「情蒐匯入」＋「巡站發掘」＋批次執行鈕、進度條、結果表（可篩選已確認）與報告下載。
- `web/static/i18n/zh-CN.json` 與 `en-US.json` 同步。

### 9. 文件

`docs/zh-CN/tool-call-guard.md` 不適用；新增 `docs/zh-CN/redirect-batch-verify.md` 與
`docs/en-US/redirect-batch-verify.md`（雙語同步）。

## 安全邊界

- 批次僅針對使用者明確提供或經情蒐取得、且落在授權範圍內的目標；平台既有 `tool_guard.scope`
  與（本次一併接好的）專案 scope 仍會在攔截層把關。
- 探測不跟隨重新導向，只讀 Location 標頭。
- 報告與漏洞紀錄不含憑證；受控端點清單來自平台設定。

## 驗證

- `go build ./...`
- `go test ./internal/redirect/... ./internal/database/... ./internal/handler/... ./internal/app/... ./internal/mcp/...`
- CI `authorization-boundaries` job 對應的 `go test -run` 表達式
