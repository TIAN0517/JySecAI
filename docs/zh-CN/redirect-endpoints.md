# 受控跳轉（回連）端點

[English](../en-US/redirect-endpoints.md)

開放式跳轉（open redirect）的漏洞記錄裡，復現步驟與證據通常帶著攻擊者自己的網域 —— `https://evil.example.com/steal`、`?redirect=https://evil.com`。照這樣複測，回連會送到別人的伺服器，結果既無法歸因、也拿不到能當證據的東西。

`redirect` 把回連目標變成平台層級的設定：受控端點只要設定一次，儲存的 payload 就能整批換掉。

## 設定

```yaml
redirect:
  enabled: true
  urls:
    - https://97y.me/tjneJ
    - https://97y.me/tjneK
```

| 欄位 | 意義 |
| --- | --- |
| `enabled` | 端點清單的總開關。 |
| `urls` | 受控回連端點清單；每一個都會被當成跳轉 payload。 |

規則：

- 沒有 `http`/`https` scheme 的項目會被丟掉，空白項忽略，重複項依輸入順序去重。
- `enabled` 為 `true` **或** `urls` 非空即視為啟用。這個規則只有一條，而且初次註冊與設定熱套用後的重新註冊都依它判斷。
- 清單為空且 `enabled` 關閉時，`redirect_probe` 根本不註冊，Agent 不會看到一個沒有端點可用的工具。

`PUT /api/config` 接受同一段設定，不必重啟：

```json
{
  "redirect": {
    "enabled": true,
    "urls": ["https://97y.me/tjneJ"]
  }
}
```

存檔會把值寫回 `config.yaml`、更新記憶體設定，並立即重新註冊工具；把清單清空則會把工具下架。

## `redirect_probe` 工具

`redirect_probe` 用受控端點對目標做開放式跳轉探測。

| 參數 | 必需 | 意義 |
| --- | --- | --- |
| `target_url` | 是 | 要測的端點。 |
| `param` | 否 | 跳轉參數名；省略時依常見參數名逐一嘗試，命中即停。 |
| `method` | 否 | `GET`（預設）或 `POST`。 |
| `urls` | 否 | 本次呼叫要用的端點清單，覆蓋平台設定。 |
| `vulnerability_id` | 否 | 把結果寫回該筆漏洞紀錄。 |
| `target_urls` | 否 | 要批次測的端點清單；給多筆時一次跑完並回傳每筆結果。 |
| `auto_record` | 否 | 驗證成功時自動建立漏洞紀錄（預設 false）。 |
| `proxy` | 否 | 代理出口；支援 http、https、socks5、socks5h、socks4、socks4a。 |

行為：

- payload 會被塞進目標的 query；既有 query 與 fragment 都保留，同名參數則改寫其值。
- 每次嘗試只送一次請求，而且**絕不跟隨重新導向**。證據就是 `Location` 標頭；跟著跳下去只看得到最終頁面。
- 判定命中的方式是比對主機名是否完全相同：`victim.com.evil.example` 不會被當成 `evil.example`，受害者自己的主機也永遠不算命中。
- 省略 `param` 時，工具會依序試 `url`、`redirect`、`redirect_uri`、`returnUrl`、`next`、`goto`、`u` 等常見參數名，命中就停。明確指定 `param` 可以避免這輪連打。

權限沿用平台既有規則：探測本身需要 `agent:execute`；寫回漏洞紀錄另外需要該筆紀錄的 `vulnerability:write`，與 `update_vulnerability` 的檢查相同。權限不足會明確回報錯誤，且不會寫入任何內容。

### 寫回結果

帶 `vulnerability_id` 時，工具會在該筆紀錄的 `evidence` 追加一段探測結果，並在 `retest_notes` 追加一行摘要。既有的內容都會保留，不會被整段取代。

## 批次跳轉驗證控制台

單筆複測（`redirect_probe`）一次只測一個端點。實際工作裡，站點是一批來的：先從 FOFA / ZoomEye 找到 SEO、賭博類站點，再巡站找出站上真的存在的跳轉入口，最後一次把整批送驗。**批次跳轉驗證**控制台把這四段串成一條線。

### 流程

```
情蒐（FOFA / ZoomEye / Quake / Shodan）／既有漏洞匯入 → 巡站發掘跳轉參數 → 批次驗證 → 自動上鍊 → 報告
```

1. **情蒐**：在控制台選來源、輸入搜索表達式（例如 SEO 站、賭博站的關鍵字），搜尋結果的主機會匯入「目標清單」。搜尋沿用既有的 `/api/fofa/search`，權限是 `fofa:execute`。
2. **巡站發掘**：對目標清單裡的站點走訪頁面，挑出**帶著跳轉參數的連結**（`url`、`redirect`、`next`、`returnUrl`、`goto`…），候選 URL 會匯入目標清單。
3. **既有漏洞複測**：按「匯入既有漏洞目標」會呼叫 `GET /api/vulnerabilities/export-urls`，把既有漏洞紀錄裡的目標 URL 匯入清單（需要 `vulnerability:export` 權限）。批次驗證時會**自動把受控端點代入這些 URL 的跳轉參數**，等於用自己的端點把整批既有發現重跑一次。既有紀錄的 `Target` 不會被改寫 —— 原始 URL 是該筆發現的證據。
4. **批次驗證**：指定「跳轉目標」（受控端點）後一次跑完整批。
5. **自動上鍊**：驗證成功的目標會自動建立漏洞紀錄（開放式重定向，CWE-601），含證據與複測紀錄，並歸屬本次指定的專案／對話。
6. **報告**：批次結束後可下載 Markdown 或 CSV 報告。

### 判定成功

與單筆複測相同：**`Location` 標頭指向受控端點就算成功**，絕不跟隨重新導向。主機名比對是完全相同，`victim.com.evil.example` 不會被當成 `evil.example`。

批次狀態會一筆一筆更新；頁面重新整理不會中斷執行，進度可查、可取消。

### 代理出口

批次與巡站都可掛代理，支援 `http`、`https`、`socks5`、`socks5h`、`socks4`、`socks4a`：

- `socks5://user:pass@host:port` —— 帳密驗證，域名在本機解析。
- `socks5h://user:pass@host:port` —— 域名交給代理端解析。
- `socks4://user@host:port` —— SOCKS4 只認 userid（沒有密碼）。
- `socks4a://user@host:port` —— SOCKS4a，域名交給代理端解析。

代理網址會寫進批次紀錄與報告，但帳密一律遮蔽成 `********`。

也可以直接走平台既有的代理池：填 `proxy_group` 就會從 `config.yaml` 的 `proxy_pool` 依群組挑代理，不必每次呼叫重複帶帳密。

| 群組 | 用途 |
| --- | --- |
| `residential` | 住宅輪替代理（例如 ProxyScrape 的台灣出口）：每條新連線換一個出口 IP，適合情蒐與掃描，避免多個目標看到同一個來源。 |
| `dc` | 機房代理：長連線、大流量。 |

群組在 `config.yaml` 的 `proxy_pool.proxies[].group` 指定（留空視為 `dc`）。代理池自己做健康檢查與冷卻：連續失敗達 `failure_threshold` 次的端點會暫停 `cooldown_seconds` 秒再重試，所以單一代理掛掉不會讓整批中止 —— 該筆記錯誤，其餘目標照跑。

控制台有「代理群組」下拉選單，批次與巡站共用；選了群組就由代理池挑代理，代理網址欄會自動停用。

### API

| 方法 | 路徑 | 說明 |
| --- | --- | --- |
| `GET` | `/api/redirect-verify/endpoints` | 回傳平台設定的受控端點。 |
| `POST` | `/api/redirect-verify/runs` | 建立批次：`targets`、`endpoints`、`param`、`method`、`project_id`、`conversation_id`、`auto_record`、`concurrency`、`timeout_seconds`、`proxy`、`proxy_group`。立即回傳批次，背景執行。 |
| `GET` | `/api/redirect-verify/runs` | 批次列表。 |
| `GET` | `/api/redirect-verify/runs/:id` | 單一批次的進度與結果。 |
| `POST` | `/api/redirect-verify/runs/:id/cancel` | 請求取消。 |
| `GET` | `/api/redirect-verify/runs/:id/report` | 報告（`format=markdown` 或 `format=csv`）。 |
| `POST` | `/api/redirect-verify/crawl` | 巡站發掘跳轉參數：`seeds`、`max_pages`、`max_depth`、`same_host_only`、`proxy`、`proxy_group`。 |

權限沿用漏洞本體：讀取需要 `vulnerability:read`，建立批次與自動上鍊需要 `vulnerability:write`。批次與每筆結果都落資料庫，歸屬建立者；非全域範圍的帳號只看得到自己的批次。

### 邊界

- 巡站只挑**連結上帶著跳轉參數**的 URL：純前端 JS 跳轉（`location.href = ...`）不會出現在 `Location` 標頭裡，驗不出來，也不該被算成漏洞。
- 這是文字層的驗證，不能取代網路層授權檢查：它不追蹤 DNS 別名、轉址後的最終頁面或檔案裡才出現的目標。
- 只測你有權授權的目標，並維持在呼叫攔截規則設定的範圍內。

## 產生的 POC 草稿

產生的 POC 草稿會多一段「受控回連端點」，並說明複測時要把復現步驟裡的跳轉目標換成這組端點，而不是沿用原始紀錄裡的外部網域。沒有設定端點時，這一段完全不會出現。

## 運維提醒

- 端點是操作者自己的：請指向自己控制的伺服器，並為每個目標保留不同的路徑段落，這樣每條發現都能歸因。
- 每次嘗試只會對你指定的目標送一次請求。只測你有權授權的系統，並維持在工具攔截規則設定的範圍內。
- 端點清單不是機密，但會以明文寫進 `config.yaml`。請比照其他設定，限制該檔案的權限。

## 原始碼錨點

- 設定結構：`internal/config/config.go`
- 純邏輯：`internal/redirect/redirect.go`
- 批次引擎：`internal/redirect/batch.go`
- 巡站發掘：`internal/redirect/crawl.go`
- 代理：`internal/redirect/proxy.go`
- 上鍊紀錄格式：`internal/redirectverify/record.go`
- 批次 API：`internal/handler/redirect_verify.go`
- 控制台：`web/static/js/redirect-verify.js`
- MCP 工具：`internal/app/redirect_tools.go`
- 設定套用路徑：`internal/handler/config.go`
- POC 草稿：`internal/poc/poc.go`
