# JySecAI RBAC 使用與管理指南

[English](../en-US/rbac.md)

JySecAI 是可執行 Agent、MCP、WebShell、C2 和批次任務的安全自動化平臺。RBAC 不僅控制頁面是否可見，還會貫穿 HTTP API、資源查詢、Agent 上下文、內建/外部 MCP 工具、後臺任務和機器人執行鏈路。

---

## 一、先區分兩種“角色”

| 概念 | 管理入口 | 作用 |
|------|----------|------|
| **平臺角色（RBAC Role）** | 左側 **平臺許可權** | 決定使用者能呼叫哪些功能、能訪問哪些資源 |
| **AI 測試角色（Agent Role）** | 左側 **角色** / `roles/*.yaml` | 決定 Agent 的提示詞、測試方法和可選工具集合 |

AI 測試角色不是安全授權邊界。即使選擇了“滲透測試”角色，使用者仍必須擁有對應的平臺許可權；反過來，RBAC 有許可權也不會自動改變 Agent 提示詞。

---

## 二、授權模型

一次訪問同時滿足以下條件才會放行：

```text
有效賬號
  + 路由/工具所需 permission
  + 該 permission 對應的 scope
  + 目標資源 owner / 顯式授權 / 父資源繼承
  + 全域性操作的額外限制
```

處理鏈路：

1. 登入後簽發 Bearer Token，會話包含使用者、角色、許可權和逐許可權 Scope。
2. HTTP 中介軟體把路由對映為許可權，例如 `GET /api/projects` → `project:read`。
3. 對帶資源 ID 的請求繼續校驗 owner、顯式資源授權或父資源繼承。
4. Agent 啟動時把不可變 Principal 寫入 `context.Context`。
5. 內建 MCP 工具根據工具和引數再次檢查許可權與資源；外部 MCP 也有獨立限制。
6. 拒絕事件寫入 RBAC/審計日誌。

前端隱藏按鈕只用於改善體驗，不構成安全邊界；真正的拒絕發生在服務端。

---

## 三、內建平臺角色

| 角色 | Scope | 預設能力 |
|------|-------|----------|
| **管理員 `admin`** | `all` | 所有已知許可權，包括 RBAC、配置、終端、審計刪除和全域性定義管理 |
| **操作員 `operator`** | `assigned` | 日常讀寫與執行能力；不含 RBAC、核心配置、終端、審計管理、外部 MCP 執行和部分全域性定義寫許可權 |
| **審計員 `auditor`** | `all` | 各模組只讀許可權和 `audit:read`，不執行寫操作 |
| **只讀使用者 `viewer`** | `assigned` | 各模組只讀許可權，僅檢視被授權範圍 |

系統角色不可修改或刪除，升級時會按當前版本的許可權目錄重新構建授權，避免舊版本殘留許可權。需要不同組合時建立自定義角色。

沒有分配任何角色的賬號仍可登入，但基本沒有業務許可權；不要依賴“無角色”作為完整崗位配置。

---

## 四、許可權命名與目錄

許可權使用 `模組:動作` 命名。常見動作：

- `read`：檢視、列表、查詢、匯出。
- `write`：建立、更新、執行或管理。
- `delete`：刪除。
- `execute`：執行 Agent、終端、工作流或特定能力。

當前許可權按模組分組如下；執行版本的權威目錄以“平臺許可權”頁面或 `GET /api/rbac/metadata` 為準。

| 模組 | 許可權 |
|------|------|
| 賬號 | `auth:self` |
| 儀表盤 | `dashboard:read` |
| 對話 | `chat:read`、`chat:write`、`chat:delete` |
| Agent | `agent:execute`、`agent:local-execute` |
| HITL | `hitl:read`、`hitl:write` |
| 任務 | `tasks:read`、`tasks:write`、`tasks:delete` |
| 專案 | `project:read`、`project:write`、`project:delete` |
| 漏洞 | `vulnerability:read`、`vulnerability:write`、`vulnerability:delete` |
| WebShell | `webshell:read`、`webshell:write`、`webshell:delete` |
| C2 | `c2:read`、`c2:write`、`c2:delete` |
| MCP | `mcp:read`、`mcp:execute`、`mcp:write`、`mcp:external:execute` |
| 知識庫 | `knowledge:read`、`knowledge:write`、`knowledge:delete` |
| Skills | `skills:read`、`skills:write`、`skills:delete` |
| Markdown Agents | `agents:read`、`agents:write`、`agents:delete` |
| AI 測試角色 | `roles:read`、`roles:write`、`roles:delete` |
| 工作流 | `workflow:read`、`workflow:execute`、`workflow:write`、`workflow:delete` |
| 系統配置 | `config:read`、`config:write` |
| 終端 | `terminal:execute` |
| 審計 | `audit:read`、`audit:delete` |
| RBAC | `rbac:read`、`rbac:write` |
| 通知 | `notification:read`、`notification:write` |
| 機器人 | `robot:read`、`robot:write` |
| 檔案 | `files:read`、`files:write`、`files:delete` |
| 攻擊鏈 | `attackchain:read`、`attackchain:write` |
| 網路空間測繪 / 資訊收集 | `fofa:execute` |
| OpenAPI | `openapi:read` |
| 執行監控 | `monitor:read`、`monitor:write`、`monitor:delete` |

特殊許可權說明：

- `fofa:execute` 為相容舊版本保留許可權名，現在保護 **資訊收集** 頁中的 FOFA、ZoomEye、Quake、Shodan 查詢。

- `agent:execute` 允許執行 Agent，但不自動允許本地檔案系統、Shell 或任意配置命令。
- `agent:local-execute` 是本地執行兜底許可權，應僅授予可信操作員。
- `mcp:execute` 用於訪問認證後的 MCP HTTP 入口。
- `mcp:external:execute` 用於 Agent 呼叫外部 MCP 工具，當前還要求該許可權的 Scope 為 `all`。
- 管理外部 MCP 配置使用 `mcp:write`，與執行外部工具是兩項許可權。
- `robot:write` 管理機器人配置和測試入口；機器人聊天本身使用繫結使用者或服務賬號的業務許可權。

---

## 五、資源 Scope

每個角色包含一個 Scope：

| Scope | 含義 | 適合場景 |
|-------|------|----------|
| `all` | 訪問該許可權覆蓋的所有資源 | 管理員、全域性審計員 |
| `assigned` | 訪問管理員指定的資源及系統支援的父資源繼承範圍 | 專案成員、指定資產操作員 |
| `own` | 以本人建立/歸屬資源為主；部分資源仍可透過顯式授權或父資源關係訪問 | 個人工作區、機器人獨立身份 |

許可權和 Scope 是繫結在一起計算的。一個使用者可擁有多個角色，許可權取並集；**同一個許可權**的 Scope 取最寬值：

```text
all > assigned > own
```

示例：

- “全域性審計”角色：`project:read` + `all`
- “個人專案編輯”角色：`project:write` + `own`

最終結果是：

```text
project:read  → all
project:write → own
```

全域性讀取不會把無關的寫許可權擴大為全域性寫入。服務端授權必須使用 `ScopeFor(permission)`，不能使用使用者的最寬總 Scope。

### 全域性物件限制

部分物件是程序級共享定義，沒有 owner。即使使用者擁有 `write`，若該許可權 Scope 不是 `all`，服務端仍拒絕修改。例如：

- AI 測試角色、Skills、Markdown Agents。
- 外部 MCP 配置。
- 機器人配置。
- 工作流定義。
- 知識庫寫操作（搜尋除外）。
- HITL 全域性白名單、預設稽核方和審計策略。
- C2 Profile 寫操作。
- 部分全域性監控統計。

---

## 六、資源歸屬、顯式授權與繼承

可在“平臺許可權 → 成員詳情 → 資源授權”中給使用者分配資源。當前可直接選擇的主要型別：

- 專案 `project`
- 對話 `conversation`
- 漏洞 `vulnerability`
- WebShell `webshell`
- 批次任務佇列 `batch_task`
- C2 Listener `c2_listener`

一次批次授權最多 100 個資源。重複授權會跳過，不會建立重複記錄。

部分子資源會繼承父資源訪問能力：

| 子資源 | 可繼承的父資源 |
|--------|----------------|
| 對話 | 所屬專案 |
| 漏洞 | 所屬專案或關聯對話 |
| 訊息、過程詳情、攻擊鏈 | 所屬對話 |
| C2 Session | Listener |
| C2 Task / 檔案 /事件 | Session、Task 或 Listener 鏈路 |

因此，給使用者授權一個專案，通常不需要再逐個授權該專案中的每條對話和漏洞。仍應以具體頁面/API 的服務端檢查結果為準。

---

## 七、Web 管理流程

### 7.1 建立使用者

1. 使用管理員進入左側 **平臺許可權**。
2. 建立平臺使用者，設定使用者名稱、顯示名稱、至少 8 位密碼和啟用狀態。
3. 分配一個或多個平臺角色。
4. 若角色 Scope 為 `assigned`，繼續配置資源授權。
5. 讓使用者重新登入並在右上角使用者選單確認角色、許可權數量和 Scope。

### 7.2 建立自定義角色

1. 新建平臺角色並填寫清晰的崗位名稱與說明。
2. 選擇 `all`、`assigned` 或 `own`。
3. 只勾選崗位實際需要的許可權。
4. 先用測試賬號驗證列表、詳情、寫操作、刪除和 Agent 工具呼叫。
5. 再批次分配給正式使用者。

系統角色不可編輯；複製其思路建立自定義角色即可。

### 7.3 許可權變更何時生效

- 更新使用者、密碼、啟用狀態或角色後，該使用者現有會話會被撤銷，需要重新登入。
- 更新或刪除自定義角色後，平臺會撤銷全部現有會話，所有使用者需重新登入。
- 機器人每條訊息實時解析繫結使用者/服務賬號許可權；使用者禁用或角色調整會立即影響下一條訊息。
- 後臺批次任務會根據任務 owner 重新解析 Principal，不應依賴建立任務時的前端狀態。

---

## 八、推薦角色模板

以下是起點，不是固定策略。

### 只讀專案成員

```text
Scope: assigned
dashboard:read
chat:read
project:read
vulnerability:read
files:read
attackchain:read
```

### 日常安全操作員

```text
Scope: assigned
agent:execute
chat:read / chat:write
project:read / project:write
vulnerability:read / vulnerability:write
tasks:read / tasks:write
files:read / files:write
hitl:read / hitl:write
```

只有確實需要本機命令時才增加 `agent:local-execute` 或 `terminal:execute`；需要刪除時再增加對應 `:delete`。

### 機器人專用賬號

```text
Scope: own（獨立工作區）或 assigned（指定專案）
agent:execute
chat:read / chat:write
按需增加 project、vulnerability、knowledge 等許可權
```

也可使用 `admin` 作為機器人服務賬號，但傳送者仍需精確白名單；白名單內每個人都會獲得完整許可權並共享 admin 資料。詳見[機器人指南](robot.md)。

---

## 九、Agent、MCP 與機器人邊界

### Agent

HTTP 登入使用者會被轉換為不可變 Principal，傳入單 Agent、多 Agent、工作流和工具執行上下文。長任務脫離 SSE 連線後仍保留身份，但不會因為前端按鈕可見而繞過服務端許可權。

### 內建 MCP

每個內建工具必須有顯式授權策略。例如 WebShell 工具會同時檢查 `webshell:read/write/delete` 和 `connection_id` 的資源訪問；漏洞、專案、任務與 C2 工具也會檢查引數指向的資源。

未登記授權策略的內建工具預設拒絕。普通本地/配置工具需要 `agent:local-execute`。

### 外部 MCP

Agent 呼叫外部 MCP 工具需要 `mcp:external:execute`，且當前要求 Scope 為 `all`。這是因為外部服務的資源模型通常不受本地 owner/assignment 約束。

### 機器人

- `user_binding`：平臺傳送者繫結自己的 RBAC 使用者。
- `service_account`：精確白名單傳送者統一使用一個 RBAC 使用者。
- 平臺驗籤只做來源認證，不代替業務授權。
- 傳送 `身份` / `whoami` 可檢查實際 Principal。

---

## 十、RBAC API

所有介面使用：

```http
Authorization: Bearer <token>
```

管理介面需要 `rbac:read` 或 `rbac:write`，資源選擇器需要 `rbac:write`。

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/rbac/me` | 當前使用者、角色、許可權、總 Scope 與逐許可權 Scope |
| GET | `/api/rbac/metadata` | 許可權目錄、角色、角色許可權和 Scope 列表 |
| GET/POST | `/api/rbac/users` | 列出/建立使用者 |
| PUT/DELETE | `/api/rbac/users/:id` | 更新/刪除使用者 |
| GET/POST | `/api/rbac/roles` | 列出/建立角色 |
| PUT/DELETE | `/api/rbac/roles/:id` | 更新/刪除自定義角色 |
| GET | `/api/rbac/resources?type=project&q=...` | 分頁搜尋可授權資源 |
| GET/POST | `/api/rbac/resource-assignments` | 列出/建立資源授權 |
| DELETE | `/api/rbac/resource-assignments/:id` | 撤銷資源授權 |

建立使用者示例：

```bash
curl -X POST http://localhost:6688/api/rbac/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operator01",
    "display_name": "安全操作員 01",
    "password": "change-me-123",
    "enabled": true,
    "roles": ["operator"]
  }'
```

建立自定義角色示例：

```bash
curl -X POST http://localhost:6688/api/rbac/roles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "專案審計員",
    "description": "只讀檢視指定專案",
    "scope": "assigned",
    "permissions": ["chat:read", "project:read", "vulnerability:read"]
  }'
```

批次授權專案示例：

```bash
curl -X POST http://localhost:6688/api/rbac/resource-assignments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID",
    "resource_type": "project",
    "resource_ids": ["PROJECT_ID_1", "PROJECT_ID_2"]
  }'
```

---

## 十一、審計與運維建議

- 使用個人賬號管理平臺，避免多人共享管理員密碼。
- 自定義角色按崗位命名，描述中寫明用途和負責人。
- 高風險許可權單獨審批：`terminal:execute`、`agent:local-execute`、`c2:write/delete`、`webshell:write/delete`、`rbac:write`、`config:write`。
- 定期檢查 `all` Scope 角色、服務賬號、機器人白名單和長期未使用使用者。
- 使用者離職時先禁用賬號，再撤銷機器人繫結、資源授權和會話。
- 在日誌審計中關注 `rbac/access_denied`、角色/使用者變更、資源授權、機器人服務賬號執行。
- 配合 HITL 控制高風險工具；RBAC 允許呼叫不等於可以跳過審批。

---

## 十二、常見問題

### 頁面按鈕看不到

檢查使用者是否有對應許可權；前端會根據 `/api/rbac/me` 隱藏無權操作。直接呼叫 API 仍會由服務端拒絕。

### 有許可權但返回“無權訪問該資源”

檢查該許可權的 Scope，而不是隻看使用者總 Scope；再檢查資源 owner、顯式授權和父資源授權。

### 角色改了但使用者仍是舊許可權

角色變更會撤銷會話。讓使用者重新登入；機器人下一條訊息會重新解析許可權。

### 忘記了內建 `admin` 密碼

優先使用其他具備 `rbac:write` 許可權的管理員賬號重置。若沒有可用的管理員會話，請按[排錯指南中的管理員密碼恢復流程](troubleshooting.md#忘記-admin-密碼)在伺服器上緊急重置。

### `write` 許可權存在但全域性配置仍被拒絕

全域性物件寫操作要求對應許可權的 Scope 為 `all`。建立一個 `all` Scope 的專用管理角色，而不是擴大無關許可權。

### Agent 能對話但不能執行命令

`agent:execute` 與 `agent:local-execute` 分離。按需授予本地執行許可權，並結合 HITL、工具白名單和審計。

### 外部 MCP 提示需要 global scope

除 `mcp:external:execute` 外，該許可權的 Scope 還必須為 `all`。外部 MCP 的資料邊界不由本地資源授權自動保護。
