# JySecAI 審計提示詞庫

完整的審計、漏洞檢測與敏感數據隔離提示詞，可直接用於 AI Coding Agent 或對話。

---

## 1️⃣ XSS 與路徑穿越漏洞修復審計

### 用途
檢查 Web 控制台的 XSS 修復和 /result 端點的路徑穿越防護。

### 提示詞
```
執行保守模式安全審計：驗證 XSS 與路徑穿越漏洞修復

目標倉庫：[repo-owner/repo-name]

檢查項目（不做風險定級，只做修復驗證）：

## XSS 修復驗證
1. web/static/js/c2.js line 481 - copyBtn onclick 屬性
   - 原始風險：JSON.stringify(value) 直接插入 onclick="..."
   - 預期修復：改用 data-c2-copy-value attribute + escapeAttr() + addEventListener
   - 檢查：是否已從 onclick 屬性移除 JSON.stringify？

2. web/static/js/c2.js line 2788-2789 - 文件列表 onclick
   - 原始風險：onclick='C2.openDirectory(${JSON.stringify(entry.name)})'
   - 預期修復：改用 data attribute + delegated event handler
   - 檢查：是否已移除不安全的 onclick 屬性？

3. web/static/js/c2.js line 2794 - 錯誤訊息 innerHTML
   - 原始風險：container.innerHTML = `<div class="c2-error">${data.error}</div>`
   - 預期修復：escapeHtml(data.error) 後才插入 HTML
   - 檢查：是否有 escapeHtml() 對 error 訊息進行轉義？

## Path Traversal 防護驗證
1. internal/c2/manager.go - blob_suffix allowlist
   - 原始風險：後綴任意可控，允許 ../../../ 穿越
   - 預期修復：switch case 白名單（.bin, .png, .jpg, .jpeg）
   - 檢查：normalizeResultBlobSuffix() 是否實現了白名單？

2. internal/c2/manager.go - 邊界檢查
   - 原始風險：filepath.Join(dir, taskID+suffix) 無邊界驗證
   - 預期修復：ensurePathInDir() 確保最終路徑在 results 目錄內
   - 檢查：是否調用了邊界驗證函數？

3. internal/c2/manager.go - Symlink 防護
   - 原始風險：symlink 可繞過邊界檢查
   - 預期修復：filepath.EvalSymlinks() + IsSymlink 檢測
   - 檢查：是否有 symlink 檢查邏輯？

## /result 端點強化驗證
1. internal/c2/listener_http.go - 明文 JSON 回退
   - 原始風險：DecryptAESGCM 失敗時 json.Unmarshal(body, &report)
   - 預期修復：解密失敗直接拒絕，返回 400
   - 檢查：是否移除了明文 JSON fallback？

2. internal/c2/manager.go - Task 狀態驗證
   - 原始風險：任何狀態的 task 都能接收結果
   - 預期修復：只接受 TaskSent 或 TaskRunning 狀態
   - 檢查：IngestTaskResult() 是否有狀態校驗？

3. internal/c2/manager.go - Task 歸屬驗證
   - 原始風險：任意 task_id 都能被提交
   - 預期修復：IngestTaskResultForSession() / IngestTaskResultForListener()
   - 檢查：是否綁定了 session/listener 歸屬驗證？

## 測試覆蓋驗證
- 是否存在單元測試？
- Go 測試：suffix 白名單、path traversal 防護、symlink 邊界
- 前端測試：特殊字符（< > " ' 等）不產生可執行 HTML

輸出：
A. 修復項檢查清單（✅/❌）
B. 代碼片段對比（修復前後）
C. 測試覆蓋狀況
D. 未完成項或遺留問題
```

---

## 2️⃣ 敏感數據隔離審計（保守模式）

### 用途
掃描倉庫中是否存在派遣系統、GPS、貸款等敏感數據，只列出候選項，由使用者確認後再評級。

### 提示詞
```
敏感數據審計第 1 步：候選項掃描（不做風險評級，只做發現列表）

目標倉庫：[repo-owner/repo-name]

掃描範圍：以下資料類型是否真實存在於倉庫（production-code，非測試/文檔/示例）

## 派遣系統（Dispatch）
搜索：dispatch, order, delivery, assignment, route, driver
檢查：
- 數據表（orders, deliveries, dispatch_tasks, driver_assignment）
- API 端點（/api/dispatch, /api/order, /api/delivery）
- 前端頁面（dispatch management, order tracking）
- 業務邏輯（task assignment, route optimization）

## GPS 與座標數據（Location）
搜索：gps, latitude, longitude, coordinate, geofence, tracking, position
檢查：
- 數據表（locations, gps_records, coordinates, tracking_data）
- API 端點（/api/location, /api/gps, /api/track）
- 前端功能（地圖、實時追蹤）
- 實時更新機制（WebSocket, 輪詢）

## 貸款數據（Loan）
搜索：loan, lending, credit, repayment, interest, debt, risk score
檢查：是否有完整的貸款業務模塊

## 房貸數據（Mortgage）
搜索：mortgage, property, real estate, appraisal, collateral
檢查：是否有房產抵押業務

## 支付數據（Payment）
搜索：payment, transaction, bank, invoice, refund, card, amount
檢查：是否涉及真實支付/金融交易

## 會員數據（Member）
搜索：member, user account, profile, identity, phone, email
檢查：用戶 PII 的存儲與權限

## 健康醫療（Health）
搜索：health, medical, patient, diagnosis, insurance, medication
檢查：是否含有健康/醫療相關敏感數據（非系統健康狀態）

## 通信記錄（Communication）
搜索：sms, email, message, chat, call
檢查：是否記錄用戶間通信內容

輸出格式：

A. 候選數據類型表
   資料類型 | 發現位置 | 證據類型 | 確定度 | 備註
   ---------|---------|---------|--------|--------
   派遣系統 | internal/c2/... | C2 會話追蹤 | 可能 | 僅限 Beacon，非真實派遣
   GPS 位置 | (未發現) | 無 | 未發現 | -
   ...

B. 可能誤判的候選
   - keyword-only 命中（僅關鍵字無業務邏輯）
   - 文檔示例（documentation example）
   - 測試 fixture（test data）

C. 明確未發現的
   - 貸款系統
   - 房貸系統
   - 支付/銀行系統
   - 健康醫療系統

D. 待使用者確認的選項清單
```

---

## 3️⃣ C2 會話與 Beacon 安全審計

### 用途
檢查 C2 平台的會話管理、Beacon Token、加密與權限控制。

### 提示詞
```
C2 平台安全審計：會話、Token、加密與隔離檢查

目標倉庫：[repo-owner/repo-name]

檢查項目：

## C2 會話隔離
檢查：internal/c2/manager.go, internal/c2/types.go
- c2_sessions 表結構：implant_uuid, hostname, username, os, internal_ip
- 會話唯一性：implant_uuid 是否有 UNIQUE 約束？
- 會話隔離：不同 listener 的會話是否互相隔離？
- 權限檢查：非會話所有者是否能訪問會話詳情？

## Token 與加密管理
檢查：internal/c2/crypto.go, internal/security/auth_manager.go
- Implant Token：是否用 AES-GCM 加密？
- Token 存儲：是否明文存儲在數據庫中？
- Token 轉移：Web API 返回時是否脫敏（***）？
- 加密密鑰：encryption_key 字段是否加密存儲？

## Beacon 驗證機制
檢查：internal/c2/listener_http.go
- X-Implant-Token 校驗：checkImplantToken() 邏輯
- AES-GCM 解密：是否強制加密驗證？
- 明文回退：解密失敗時是否拒絕（已修復）？

## 審計日誌
檢查：internal/c2/manager.go
- 會話上線事件：publishEvent() 是否記錄？
- 任務執行日誌：任務狀態變化是否被追蹤？
- 敏感操作日誌：Terminal 命令執行是否被記錄？

輸出：
A. 隔離機制檢查表
B. 加密強度評估
C. 權限控制驗證
D. 審計日誌完整性
```

---

## 4️⃣ 批量任務與漏洞管理審計

### 用途
檢查批量任務系統、漏洞追蹤、HITL 人機協同的數據隔離與權限控制。

### 提示詞
```
批量任務與漏洞管理審計：權限、隔離、審計日誌

目標倉庫：[repo-owner/repo-name]

檢查項目：

## 批量任務系統隔離
檢查：internal/handler/batch_task_manager.go, internal/database/batch_task.go
- batch_tasks 表結構
- 任務隊列（batch_task_queues）與任務的關係
- 用戶隔離：不同用戶的任務隊列是否隔離？
- 項目隔離：不同項目的任務是否隔離？
- 權限檢查：執行任務時是否驗證用戶權限？

## 漏洞追蹤隔離
檢查：internal/database/vulnerability.go
- vulnerabilities 表結構：project_id, conversation_id, task_tag
- 漏洞歸屬：是否綁定到特定對話/項目？
- 訪問控制：非所有者是否能讀取漏洞詳情？
- 脫敏機制：漏洞報告是否對非授權用戶脫敏？

## HITL 人機協同審計
檢查：internal/handler/hitl_audit_agent.go
- 危險任務識別：IsDangerousTaskType() 邏輯
- 人工審批流：RequestApproval() 是否強制？
- 審批日誌：是否記錄審批者、時間、決策？
- 越權防護：已拒絕的任務是否會被強制執行？

## 敏感數據脫敏
檢查：internal/audit/sanitize.go
- SanitizeDetail() 函數：是否覆蓋了所有敏感字段？
- 白名單字段：password, api_key, secret, token, authorization...
- 脫敏強度：*** vs 部分馬賽克 vs 完全移除

輸出：
A. 隔離機制檢查表
B. 權限控制驗證
C. 審計日誌完整性
D. 脫敏規則覆蓋度
```

---

## 5️⃣ WebShell 與外部工具安全

### 用途
檢查 WebShell 連接管理、外部 MCP 工具的隔離與安全控制。

### 提示詞
```
WebShell 與外部工具安全審計

目標倉庫：[repo-owner/repo-name]

檢查項目：

## WebShell 連接隔離
檢查：internal/database/webshell_connections.go
- webshell_connections 表：password 欄位是否加密存儲？
- 連接歸屬：是否綁定到特定項目/用戶？
- 訪問控制：非所有者是否能列出/執行命令？
- 審計日誌：每次連接/命令執行是否被記錄？

## 外部 MCP 工具管理
檢查：internal/mcp/supervisor.go, internal/mcp/external_manager.go
- 工具驗證：加載外部工具時是否驗證簽名/來源？
- 權限沙盒：外部工具是否有執行權限限制？
- 進程隔離：stdio/HTTP 子進程是否隔離運行？
- 通信加密：MCP 協議是否支持 TLS？

## 機器人集成安全
檢查：internal/robot/*.go（Telegram, WeChat, Lark, DingTalk, Discord, Slack）
- Token 存儲：Bot Token 是否加密存儲？
- 消息轉發：是否會洩露敏感信息給外部 Bot？
- 認證回源：是否驗證消息來自真實機器人平台？
- Rate Limiting：是否有速率限制防止濫用？

輸出：
A. 隔離與加密檢查
B. 權限控制驗證
C. 審計日誌完整性
D. 第三方集成風險
```

---

## 使用範例

### 方式 1：直接在對話中粘貼

```
[粘貼上述任一提示詞]
目標倉庫：my-org/my-repo
請幫我檢查這些項目...
```

### 方式 2：用於 Copilot Coding Agent

```markdown
## Problem Statement

[粘貼對應的提示詞]

不要修改代碼，只生成檢查報告。
```

### 方式 3：用於另一個 GitHub 帳戶

複製整個 `AUDIT_PROMPTS.md` 文件到你的另一個倉庫，按需要調整 `目標倉庫` 欄位。

---

## 快速索引

| 審計類型 | 關鍵檢查點 | 風險等級 |
|---------|---------|--------|
| XSS 修復 | onclick attribute, innerHTML, escapeHtml | 🔴 Critical |
| Path Traversal | blob_suffix whitelist, boundary check, symlink | 🔴 Critical |
| 會話隔離 | implant_uuid uniqueness, listener isolation | 🔴 Critical |
| Token 管理 | 加密存儲, 脫敏返回, Bearer 驗證 | 🔴 Critical |
| 敏感數據隔離 | 派遣/GPS/貸款/會員 | 🟠 High |
| 權限控制 | RBAC, 項目隔離, 越權防護 | 🟠 High |
| 審計日誌 | 敏感操作追蹤, 脫敏規則 | 🟠 High |
| 外部工具 | Token 管理, 進程隔離, TLS | 🟠 High |

---

## 修改日誌

- **2026-10-01** — 初稿，整合 JySecAI 審計經驗
  - 新增 5 大審計模塊
  - 保守模式敏感數據掃描
  - 實際代碼位置與檢查清單
