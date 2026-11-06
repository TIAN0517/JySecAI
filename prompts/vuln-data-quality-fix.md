# 提示詞：修正 vulnerabilities 資料品質問題（可直接貼給 GPT）

---

## 目標

修正 `vulnerabilities` 表的資料品質問題，讓剛上線的 `vulnerability_type` / `target` 篩選功能（commit `1ae08a4e2`）真正可用，並讓「待處理嚴重漏洞」這種彙總數字與資料一致。

**這是資料品質修復，不是重新分級。嚴重度與 CWE 對映一律不要自動猜測。**

---

## 一、已確認的事實（不必重查，直接用）

`vulnerabilities` 表目前 688 筆。實測結果：

### 1.1 `target` 空值率 69.2%

```
target 為空: 476 / 688  (69.2%)
```

### 1.2 `vulnerability_type` 有 66% 是無意義值

| 值 | 筆數 | 說明 |
|---|---|---|
| `finding` | 220 | 不是漏洞類型，是結構性標記誤填 |
| `target` | 136 | 這是欄位名，被填進類型欄位 |
| `note` | 97 | 筆記，不是漏洞分類 |
| `configuration` | 35 | 過於籠統 |
| `exploit` | 23 | 這是階段，不是類型 |

前三項合計 453 筆（65.8%）。

### 1.3 欄位外洩：`confidence.80`

```
vulnerability_type = 'confidence.80'   → 2 筆
```

`vulnerabilities` 表結構**沒有** `confidence` 欄位，所以信心分數只能混進 `vulnerability_type`。這是產生端的模板或解析 bug，**需要找出來源並修正，不是只清資料**。

### 1.4 `target` 未正規化，同一站被拆成多組

```
https://www.letsmakeaplan.org/     41 筆
https://www.letsmakeaplan.org      5 筆    ← 少尾部斜線
https://www.cfp.net/                26 筆
https://www.cfp.net                 2 筆
```

新篩選用 `LOWER(target) LIKE LOWER(?)`，所以搜尋框可用，但**精確篩選不可靠**，且統計會分裂。

**重要例外：不同 port 是不同服務，不可合併。**
```
epcr.tpf.gov.tw:4001/events      9
epcr.tpf.gov.tw:4004/login       3
epcr.tpf.gov.tw:4004/captcha     3
epcr.tpf.gov.tw:4000/config      3
epcr.tpf.gov.tw:4004/ssoLogin    2
epcr.tpf.gov.tw:4001/videoData   2
```
這些 port 不同（4000/4001/4004），必須維持區分。

### 1.5 漏洞類型中英混用，同一類問題分裂成四種標籤

```
CWE-200                          3
信息泄露                          5
敏感信息泄露                       2
Information Disclosure           6
```

台灣交付報告需要 CWE 編號，這種分裂直接影響報告品質。另有 `CVE-2020-11022`、`CWE-937`、`CWE-830`、`CWE-707`、`CWE-829`、`CWE-1321` 等混雜其間。

### 1.6 嚴重度分布不正常

```
medium     515  (74.8%)
high        63  ( 9.2%)
info        56  ( 8.1%)
low         30  ( 4.4%)
critical    24  ( 3.5%)
```

74.8% 集中在 medium 不符合正常評估的分布。**這是「分級未校準」的訊號，不是可以直接自動修正的資料。**

狀態分布：`open` 651 / `confirmed` **34** / `ignored` 3。僅 4.9% 經過複驗。

### 1.7 平台的彙總數字與資料對不上

平台自報「58 個待處理的嚴重漏洞」，但資料庫實際上 `critical + high = 87`，`critical` 單獨為 24。**彙總邏輯本身有問題，需一併釐清它用的是什麼條件。**

---

## 二、要做的事

### 2.1 找出 `confidence.80` 的來源（優先，這是唯一的真 bug）

定位是哪個 prompt 模板、parser 或 tool output 轉換器，把 confidence 欄位寫進了 `vulnerability_type`。修正那個來源，不要只在資料層面清掉。

### 2.2 `target` 正規化

規則（保守，不得改變語意）：

1. 僅當 **host 與 port 相同** 時才做合併
2. 移除 **path 結尾**的單一 `/`（根路徑 `/` 除外）
3. host 轉小寫
4. **保留 port**（`epcr.tpf.gov.tw:4001` ≠ `:4004`）
5. **保留 path 與 query**（`/events` ≠ `/login`）
6. 空值維持空值，**不可用 conversation 或其他欄位推測填入**

### 2.3 清理 `vulnerability_type` 髒值

對 `finding` / `target` / `note` / `exploit` 這類值：

- **清成 NULL，不要猜測一個 CWE 塞進去。** 猜錯會在客戶報告裡產生假陽性發現，專業上不可接受。
- 若你認為這些值有保留價值（例如需要追蹤來源），提出一個**明確的替代方案**（例如搬到獨立欄位或標記欄位）讓我決定，不要自行決定。

### 2.4 CWE 對映表

建立**明確、可審閱**的對映表（不要用啟發式自動推斷），把中文／英文別名統一到 CWE 編號。至少涵蓋：

```
信息泄露 / 敏感信息泄露 / Information Disclosure  → CWE-200
```

對映表要以檔案形式產出讓人檢視，並支援 `--report` 預覽。

### 2.5 彙總邏輯

找出「待處理嚴重漏洞」目前的計算條件，釐清為何得出 58。**先回報差異原因，不要先改邏輯。**

### 2.6 嚴重度

**不要自動重新分級。** 只產出一份報告，說明 74.8% medium 這個分布，並列出分級規則目前的實際取來源。

---

## 三、硬性約束

1. **絕對不要操作生產資料庫。** 開發與測試一律用 `/tmp` 下的副本。
2. 所有清理操作**必須可重跑且冪等**。
3. **必須先出 `--report` 讓我確認影響範圍，確認後我才會給你 `--fix` 的授權。** 不要一次做完。
4. **不得改動剛上線的篩選功能行為。** `type` 與 `target` 查詢參數的語意必須維持。
5. 不得刪減任何既有功能或欄位。
6. `vulnerability_type` 清理若會影響 `GetVulnerabilityFilterOptionsForAccess` 的建議清單（下拉選項來源），要一併確認不會產生空的下拉選單。
7. 修正後必須補單元測試，涵蓋：尾部斜線合併、不同 port 不合併、空值不推測、中英別名對映。

---

## 四、建置與測試環境注意事項（本機已知的坑）

```
go build -buildvcs=false ./...
go vet   -buildvcs=false ./...
```

`-buildvcs=false` **必須加**，本機沒裝 git-lfs，VCS stamping 會直接失敗（`error obtaining VCS status: exit status 128`）。

已知的既有失敗測試，與你的改動無關，不要去動它們：
- `internal/handler` 6 個、`internal/logger` 2 個：Windows TempDir 檔案鎖定
- `internal/mcp` 1 個：平行測試資源競爭（單獨跑會過）
- `internal/security` 4 個：`/bin/sh` 不存在（測試是為 WSL 寫的）

## 五、驗收標準

1. `--report` 輸出能明確列出每一類問題的筆數與受影響的 `id`
2. `--fix` 後重新查詢：`target` 空值率**不變**（不可為了降低空值率去猜測填值）
3. 原本同一 origin 的記錄合併後，篩選該 origin 能一次取回全部
4. 不同 port 的記錄**必須維持分開**
5. `internal/database` 與 `internal/handler` 測試全數通過
6. `go build` / `go vet` exit 0
7. 產出**可回滾方案**（例如保留原始值到新增欄位，或提供反向腳本）
