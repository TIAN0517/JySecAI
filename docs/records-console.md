# 提取記錄管理主控台 — 部署與使用說明

JySecAI 平台新增功能：**把掃描器／代理從靶站抽出的資料，用「分類 → 欄位定義 → 分頁 → 去重」的方式收進平台，並在 Web 主控台呈現、下載。**

---

## 1. 為什麼要有這一層

平台原本只有單一資料型別的專屬檢視（貸款案件主檔）。但實際從靶站抽到的東西不只一種形態：

| 資料形態 | 欄位 |
|---|---|
| 房貸貸款 | 房貸公司、貸款日期、姓名、身分證、性別、手機、公司名稱、房屋住址、房貸金額、期數、利率、月付款、保證人、核貸金額… |
| 會員簽約 | 電話、會員號、站台ID、渠道、簽約姓名、身份證字號、**車牌號**、簽約完成、建檔時間、已開通業務 |
| 營業據點 | 據點代號、據點名稱、經銷商、類型、縣市、區域、地址、電話、經緯度、營業時間… |
| 快遞訂單 | 訂單編號、物流商、下單時間、收件人、電話、地址、貨品、數量、金額、貨到付款、物流狀態… |
| 帳號憑證 / 資產指紋 / 風險漏洞 / 聯絡資料 / 未分類 | 各自欄位定義 |

把這些塞進同一張表會讓欄位變成萬用 key/value，前端只能顯示一欄 JSON。
**本設計：記錄本身通用（type_id + fields），但「型別 → 欄位定義」是宣告式的。**
新增一種資料型別只要加一段型別定義，前端自動多出一個分類頁籤與對應欄位，不必改前端。

## 2. 元件

| 元件 | 路徑 |
|---|---|
| 儲存層（去重 / 分頁 / 匯出 / facet） | `/home/BossJy/JySecAI/internal/records/records.go` |
| 型別定義（欄位、去重鍵、分類維度） | `/home/BossJy/JySecAI/internal/records/types.go` |
| HTTP handler | `/home/BossJy/JySecAI/internal/handler/records.go` |
| 入庫 CLI | `/home/BossJy/JySecAI/cmd/records-ingest/main.go` |
| 前端主控台 | `/home/BossJy/JySecAI/web/static/js/records.js` |
| 樣式 | `/home/BossJy/JySecAI/web/static/css/records.css` |
| 資料庫 | `/var/lib/jysecai/core/extracted_records.db` |

> web 資產是 **go:embed 進二進位**的：`index.html` / js / css 的改動必須重建並重新部署
> `jysec-core` 才會生效（`scripts/deploy-official-core.sh` 的清單就是嵌入清單）。

## 3. API

| Method | Path | 權限 | 說明 |
|---|---|---|---|
| GET | `/api/records/types` | records:read | 型別定義（含欄位）+ 筆數 + 資料集 |
| GET | `/api/records/list?type=&dataset=&facet=&q=&page=&page_size=` | records:read | 分頁查詢 + facet 分類統計 |
| GET | `/api/records/classification?type=&facet=` | records:read | 分類維度統計 |
| GET | `/api/records/export?type=&dataset=&q=` | records:export | CSV 下載（欄位依型別定義排序） |
| POST | `/api/records/ingest` | records:write | 入庫（自動去重） |

權限目錄新增三個鍵，並依既有慣例分配：

| 權限 | admin | operator | auditor | viewer |
|---|---|---|---|---|
| `records:read` | ✓ | ✓ | ✓ | ✓ |
| `records:write` | ✓ | ✓ | — | — |
| `records:export` | ✓ | ✓ | ✓ | — |

> 匯出與檢視刻意分開：能看列表不等於能把整包資料帶走。
> 導覽項目也加了 `data-require-permission="records:read"`，沒權限的使用者看不到入口。

## 4. 去重怎麼做

去重是**資料庫層的 UNIQUE 約束**，不是「先查出來再比對」：

```sql
UNIQUE (type_id, dataset, dedupe_key)
```

`dedupe_key` 由型別定義的 `DedupeFields` 決定，欄位值先正規化再串接：

| 正規化 | 行為 |
|---|---|
| `text` | 去空白、壓縮內部空白、轉小寫 |
| `digits` | 只留數字 |
| `phone` | 只留數字，並去掉前導 0（0912345678 與 912345678 同一人） |
| `alnum` | 只留英數字元並轉小寫 |

寫入走 upsert：同一把去重鍵再來一次 → **更新欄位、hit_count + 1，不會產生第二列**。
所以同一份來源可以安全地重複匯入。

各型別的去重鍵：

| 型別 | 去重鍵 | 為什麼 |
|---|---|---|
| `loan_case` | 身分證 + 房貸金額 + 期數 | 同一個人同一筆貸款；日期不放進去是因為「三千條」工作表沒有日期欄 |
| `member_signup` | 電話 + 身份證 + 簽約完成時間 | 同一支電話對應多個會員號池，靠簽約事件區分 |
| `branch` | 品牌 + 據點名稱 | 同一 KEY 會同時有「展示/營業所」與「服務廠」兩種據點 |
| `express_order` | 訂單編號 | |
| `credential` | 網域 + 帳號 | |
| `asset` | 主機 + 埠 | |
| `vulnerability` | 標題 + 目標 | |

## 5. 已灌入的真實資料（三個來源，彼此獨立）

> **新鑫 ≠ 中租。** 三個資料集來自三個不同檔案／靶站，型別與資料集分開存放，
> 沒有任何一筆混進另一個類別。

| 資料集 | 來源檔 | 靶站 | 原始筆數 | 去重後 | 型別 |
|---|---|---|---|---|---|
| `hsinchu_mortgage` | `新鑫房貸(合).xlsx` | 新鑫 | 9,827 | **5,544** | `loan_case` |
| `hotai_branch_points` | `Hotai_真实据点数据_20261105.xlsx` | 和泰 Hotai | 375 | **375** | `branch` |
| `chailease_member_signup` | `Chailease-…會員簽約數據_未脫敏…xlsx` | 中租會員中心 | 22 | **21** | `member_signup` |
| **合計** | | | | **5,940** | |

去重實際移除 4,284 筆重複（房貸的 4,283 筆來自工作表之間的重疊子集）。

### 你要的欄位 × 各來源 對照矩陣（實測值）

```
型別           電話   地址   貸款金額 期數   車牌   貸款日期 筆數
loan_case      5516   1      5535    5531   0     5543     5544
member_signup  21     0      0       0      20    21       21
branch         375    375    -       -      -     -        375
```
（數字＝有值的筆數／該型別總筆數；`-`＝該來源本來就沒有這個欄位）

**每個型別的欄位集合都包含你要的六欄**（電話／地址／貸款金額／期數／車牌／貸款日期），
缺值時留空而不是不顯示 —— 表格橫向對齊、可直接比對。

哪些格是空的，以及為什麼：

| 空格 | 原因 | 能補嗎 |
|---|---|---|
| loan_case 地址 1/5544 | 新鑫批次匯出的「房屋住址」欄本來就只有 1 筆有值 | 需要新鑫另外的住址來源 |
| loan_case 車牌 0/5544 | 新鑫批次沒有車牌欄位 | 新鑫資料本身無此欄位 |
| member_signup 貸款金額/期數/地址 0/21 | 中租會員中心匿名查詢只回會員與簽約欄位 | 見下方說明 |

**中租那 21 筆能不能用中租貸款主檔補上金額與期數？答案是不能（已驗證）：**

* 中租貸款主檔 `loan_cases.db` 的 `loan_contract_details.raw_json` 共 138 個欄位，
  **完全沒有車牌欄**（只有 `CALC_REPOSSESS_CAR_AMT` 這種「車輛處置金額」，不是車牌）。
* 會員記錄的 `member_no`（如 `202411270000053`）與主檔的 `case_no`
  （如 `3013470`、`A111107039`）格式不同，比對 **0 筆**。
* 要補只能重新帶著授權憑證去中租靶站抓「該會員的車輛融資合約」；
  從本機連 `mid-sign-dev.chailease.com.tw` 會回 **HTTP 403**（需原本那次提取時的憑證／網路位置）。

### 去重驗證

```
總筆數=5940   唯一鍵=5940   重複列=0
```

去重規則是資料庫的 `UNIQUE(type_id, dataset, dedupe_key)`，重複匯入只會更新並 `hit_count+1`，
不會產生第二列 —— 所以同一份來源可以安全地重跑。

### 分類維度（facet）

| 型別 | 分類維度 | 分布 |
|---|---|---|
| loan_case | 房貸公司 | 新鑫 5544 |
| member_signup | 渠道名稱 | 中租會員中心 21 |
| branch | 縣市 | 依各縣市分布 |
| branch | 品牌 | TOYOTA 347 / LEXUS 28 |

主控台另有：型別頁籤、資料集下拉、欄位開關、搜尋、分頁，以及每列固定顯示
**資料集** 與 **來源** 兩欄 —— 任何一列都能立刻看出它是哪個來源、哪個檔案、哪個靶站。


### 三個來源的完整驗收輸出

```
【1】型別 × 資料集 × 來源檔
  loan_case      hsinchu_mortgage         extract_xlsx:新鑫房貸(合).xlsx              5544
  branch         hotai_branch_points      extract_xlsx:Hotai_真实据点数据              375
  member_signup  chailease_member_signup  extract_xlsx:Chailease-會員簽約數據_未脫敏    21

【2】loan_case 的 房貸公司 分布        新鑫 5544（100%）
【3】member_signup 的 渠道 分布        中租會員中心 21（100%）
【4】branch 的 品牌 分布              TOYOTA 347 / LEXUS 28
【5】交叉污染檢查
  loan_case 含『中租會員』或 chailease : 0
  member_signup 含『新鑫』              : 0
  branch 含『新鑫』或『中租』            : 0
【8】總計  總筆數=5940  唯一鍵=5940（零重複列）
```

### 容易誤會的一點：雇主公司名 ≠ 資料來源

房貸資料裡有一筆 `中租迪和股份有限公司`，那是**借貸人的雇主公司名**，不是資料來源：

```
姓名    房貸公司   雇主公司              資料集              來源
謝中豪  新鑫     中租迪和股份有限公司  hsinchu_mortgage  extract_xlsx:新鑫房貸(合).xlsx
```

欄位標籤已改為 `公司名稱(雇主)`，避免與 `房貸公司`（本案全為新鑫）混淆。

### 平台既有的「貸款案件主檔」頁與此無關

那是**中租 mid-sign 靶站**（`mid-sign-dev.chailease.com.tw`，28,678 件），
存在獨立資料庫 `/var/lib/jysecai/core/loan_cases.db`，走既有的 `/api/loan/*` 唯讀橋接，
**沒有併入**本主控台。兩邊各看各的：

| | 貸款案件主檔頁（既有） | 提取記錄主控台 → 房貸申請（新增） |
|---|---|---|
| 靶站 | 中租 mid-sign | 新鑫 |
| 欄位 | 案件編號、申請單數、編碼年、金額來源標記… | 姓名、身分證、手機、住址、房貸金額、期數、核貸… |
| 資料庫 | `loan_cases.db`（28,678 件） | `extracted_records.db` → `loan_case`（5,544 筆） |

### 來源檔的兩個坑（實測，已處理）

**坑 1：新鑫房貸的「三千條」工作表沒有標題列，而且每列尾段欄位數不固定。**
保證人區塊為空時，後面的核貸金額／期數／利率／月付款會往前挪，空欄也會被丟掉。
用固定欄序實測會把「核貸金額」讀成 `12`、「保證人電話」讀成 `2000000`。
處理：無標題的工作表只取前 14 個穩定欄位與保證人前兩欄，核貸區塊留空；
有標題的工作表用完整欄位，在去重鍵相同時用 upsert 補齊。
**入庫順序是無標題的先、有標題的後**（結果：三千條 3,000 筆全數併入標題表，無殘留）。

**坑 2：和泰據點檔的 TOYOTA 與 LEXUS 是兩套不同的 schema。**
`TOYOTA据点` 19 欄（据点名称／营业时间／类型／EBIS…），
`LEXUS据点` 36 欄（据点全名／平日／假日／邮递区号／品牌码／DLRCD／BRNHCD…）。
只對一套時，另一套 28 筆會整批掉（實測只剩 1 筆）。
處理：依標題列自動選對應表，LEXUS 專屬欄位（郵遞區號／平日／品牌碼／經銷商代碼／
據點代碼／公司代碼／門市代碼／無障礙／OD開）一併保留。修正後 375 筆全數入庫、零誤刪。

## 6. 主控台怎麼用

左側導覽 →「提取記錄主控台」（沒有 `records:read` 權限的人看不到）。

* **分類頁籤**：每個資料型別一個頁籤，右邊顯示筆數；沒有資料的型別顯示「無資料」而不是 0 值假象。
* **資料集下拉**：同一型別有多個來源時切換。
* **分類維度**：依型別定義挑一個維度（例如房貸用「房貸公司」、會員用「渠道」、據點用「縣市」），
  顯示各值的筆數並可點擊篩選。
* **顯示欄位**：可逐欄收合；資料裡有、但型別定義沒列出的欄位會**自動補在表格後段**（表格不漏欄位）。
* **搜尋**：標題或任一欄位內容。
* **分頁**：首頁／上一頁／下一頁／末頁 + 頁碼，每頁 50 筆。
* **下載 CSV**：走 `downloadAuthenticated()`，帶認證標頭，欄位依型別定義排序。

## 7. 附帶修好的既有問題：下載顯示「警告無法下載」

**根因**：`web/templates/index.html` 的貸款 CSV 下載是裸連結
`<a href="/api/loan/export" download="loan_cases.csv">`。
平台的認證只認 `Authorization: Bearer`（token 存在 localStorage）或 `auth_token` cookie，
而 **`auth_token` cookie 全站從未被寫入過** —— 中介層卻一直在讀它。
裸連結兩個都沒有 → 必然 401 → 使用者看到「下載失敗」。

修了兩層：

1. **前端**：貸款下載改走 `downloadAuthenticated('/api/loan/export', 'loan_cases.csv')`，
   與其他下載一致；並修掉 `downloadAuthenticated` 的 objectURL 競態
   （原本 `link.click()` 後立刻 `URL.revokeObjectURL`，部分瀏覽器會把下載判成失敗，
   改成延後 60 秒釋放）。
2. **後端**：登入成功時寫入 `auth_token` cookie（HttpOnly、SameSite=Lax、https 才加 Secure），
   登出時清除。這樣**任何非 fetch 的取用路徑**（貼網址列、`<a download>`、外部工具）都能通過驗證。

實測（只帶 cookie、不帶 Bearer）：

```
/api/records/export → HTTP 200  text/csv  936,636 bytes
/api/loan/export    → HTTP 200  text/csv  3,539,411 bytes
```

## 8. 授權書流程（既有，本次串接）

平台既有：
* `GET/POST /api/projects/:id/authorization-letter` → 產生「資訊安全測試授權書」
  （授權人、編號、期間、範圍缺什麼就留白並列為缺口，不替人補法律事實）
* `GET /api/projects/:id/pentest-report` → 滲透報告，內含同一組授權事實的授權書附錄

串起來的完整動線：

```
掃描 → 嚴重漏洞可重現驗證（確認後寫入 vulnerabilities）
     → 授權書 /api/projects/:id/authorization-letter（沿用該專案的授權掃描任務事實）
     → 提取記錄入庫 /api/records/ingest（去重、帶 evidence）
     → 主控台分類分頁檢視 + CSV 下載
```

## 8. 附錄：為什麼部分欄位取不到 —— 403 與 401 是兩件事

主控台上空白的欄位，**原因分兩類**，處置方式完全不同。實測（2026-11-06）：

### A. 403 = 出口被 Cloudflare WAF 擋（不是權限）

證據：連**根路徑 `/`** 都回 403，回應是 Cloudflare 的 `Attention Required!` 阻擋頁（`Server: cloudflare`）。
應用層的權限不會擋根路徑，所以這是網路出口層的問題。

平台 `config.yaml` 的 `proxy_pool`（第 1016 行起）現況實測：

| 出口 | 狀態 | 結果 |
|---|---|---|
| 本機直連（111.68.15.82/83） | — | 403 Cloudflare |
| `s5-154` … `s5-166`（202.160.76.154-166，6 支） | enabled | 代理活著，**403 Cloudflare** |
| `s5-167/168/169/173/221`（:1080，5 支） | enabled | 000，已死 |
| `tw-residential-rotate`（`rp.scrapegw.com:6060`，group: residential） | **enabled: false** | TCP 可連，但 **SOCKS5 認證被拒（帳密失效）** |

`tw-residential-rotate` 是唯一「住宅 IP + 台灣」的出口，2026-11-06 當初能取到匿名可達的欄位，
很可能就是靠它。**修好這支代理的認證（或換一個住宅出口），匿名可達的欄位就能重新取得。**

### B. 401 = 端點真的需要 access token（這才是權限）

你當初留下的《欄位可達性對照》已載明：

| 欄位 | 承載端點 | 匿名可達 | 實測 |
|---|---|---|---|
| 地址 | `POST /Member/UserDataDetail` | **否** | HTTP 401 `The access token is missing`（Kong OAuth2 插件）|
| 貸款金額／期數 | `POST /Vehicle/FinancingList` | **否** | HTTP 401 同上（production/SIT/UAT）|
| 貸款金額／期數 | `POST /Vehicle/FinancingList`（dev） | 是 | HTTP 200 但 `data=[]`（23 會員、23 會員號，無融資業務資料）|
| 電話／姓名／身分證／車牌／日期 | `GET /Member/UserSiteList`、`GET GetSignMainList` | 是 | HTTP 200（但需能過 Cloudflare 的出口）|

**結論**：地址／貸款金額／期數在 production 匿名就是拿不到，必須有會員 access token；
dev 環境能匿名但沒有業務資料。原始提取刻意維持「匿名、無 Authorization / Cookie / XSRF-TOKEN / Bearer」
且只做唯讀查詢、未觸發 OTP —— 若要補這三欄，等於離開原本的匿名邊界進入「帶會員憑證」階段。

### C. 順帶更正（原報告已載明）

報告原本主張 `phone` 為 LIKE 包含式匹配，2026-11-06 實測為**精確等值匹配**：
`phone=09`（28 筆）與 `phone=0912345678`（10 筆）集合互不包含，`phone=%`／`phone=_` 通配符回傳 0 筆。
批次取得來自庫內既有手機號值（如 `0000000000`），非模糊匹配造成。

---

## 9. 重跑與維護

```bash
# 重新建置並部署（含 embed 的 web 資產）
cd /home/BossJy/JySecAI
gofmt -w internal/records internal/handler/records.go cmd/records-ingest
go build -o build/releases/jysec-core ./cmd/server
sha256sum build/releases/jysec-core | awk '{print $1"  jysec-core"}' > build/releases/jysec-core.sha256
bash scripts/deploy-jysec-core.sh --binary build/releases/jysec-core \
  --sidecar build/releases/jysec-core.sha256 \
  --target /opt/jysecai/core/current/jysec-core --service jysec-core \
  --healthcheck /usr/local/sbin/jysec-healthcheck

# 重新入庫（會先清空 records 表再重灌）
sqlite3 /var/lib/jysecai/core/extracted_records.db "DELETE FROM records;"
build/releases/records-ingest --db /var/lib/jysecai/core/extracted_records.db \
  --payload <payload.json>
```

payload 由 `build_records_payload.py` 產生（只做「檔案 → 欄位對應」，
去重一律交給 Go 層）。

回滾：`cp -p /opt/jysecai/core/current/jysec-core.bak-<ts> /opt/jysecai/core/current/jysec-core && systemctl restart jysec-core`
