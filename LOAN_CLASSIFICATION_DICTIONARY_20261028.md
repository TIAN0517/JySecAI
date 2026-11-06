# 貸款案件分類字典（2026-10-28）

## 這份東西解決什麼

28,678 筆案件、31,730 筆申請單在 `data/loan_cases.db` 裡是**原樣的代碼**
（`APR_CASE_STAT` = A4/A7/A0/A6/A3/A5/98/99/C/A2-1/R1/R2 …），
沒有中文，沒有人知道 A4 代表什麼。這份字典把「分類」做成可交付、可稽核的形式。

## 資料血緣（如實聲明，勿改寫）

```
mid-sign-dev.chailease.com.tw（同站點既有匯出）
   └─ Desktop/888/case_master_v5_2023_2026/   （本機既有檔案，2026-10-27 00:16 組裝）
        ├─ CHAILEAse_CaseMaster_v5_2023_2026.xlsx
        ├─ csv/ 57 表（sha256 全過）
        └─ manifest.json / SHA256SUMS
             └─ scripts/import_loan_cases.py  →  data/loan_cases.db
                  ├─ scripts/export_loan_cases.py        → 貸款案件主檔.xlsx 等
                  └─ scripts/export_loan_classification.py → 貸款案件分類字典.xlsx
```

- `source_sha256_verified = 57/57`：證明「**匯入後與來源檔一致**」。
- **不證明**「來源檔本身是本次線上直拉取得的」——這次工作階段沒有重新連線拉取。
- 與其他站點的 evidence 完全分開，未混用任何非同站點資料。

## 交付物

| 檔案 | 內容 |
|---|---|
| `貸款案件分類字典.xlsx` | 10 個工作表（見下） |
| `分類/狀態代碼字典.csv` | 狀態 × 筆數／佔比／金額／期數／年度／可推得特徵 |
| `分類/類型字典.csv` · `分類/客群字典.csv` | 類型 A/B/D/E、客群 A/B |
| `分類/狀態x年度.csv` · `狀態x類型.csv` · `客群x狀態.csv` · `金額來源x年度.csv` · `類型x年度.csv` | 交叉統計 |
| `分類/案件來源表分布.csv` | 案件出現在哪些來源表（UCAR_APR_FORM / CLC04 / CLC09 / CLC01 / EU_DYN_CNTRT_ABT_FORM） |
| `分類/案件層與申請單層對照.csv` | 案件編號 → 該案件下所有申請單的狀態碼／類型（看同一案件內的狀態分歧） |

XLSX 工作表：`狀態代碼字典` · `類型字典` · `客群字典` · `狀態x年度` · `狀態x類型` ·
`客群x狀態` · `金額來源x年度` · `案件來源表分布` · `案件層與申請單層對照` · `案件狀態分歧統計` · `血緣與限制`

## 中文名稱為什麼是「待補」

`APR_CASE_STAT` / `APR_CASE_TYPE` / `APR_CUST_LEVEL` / `C01_CASE_STAT` 的中文名稱，
在中租**同站點的離線資料中不存在**：

- `case_master_v5_2023_2026/csv/` 57 表：欄名全英文、值全代碼，**零個中文欄位**（已全表掃描確認）。
- `out/mid-sign-dev.chailease.com.tw/dump/`：空目錄。
- `888/` 內 3 份同站點說明文件：無代碼對照表。
- `中租會員_真實數據_U121624811_20261016.zip`：是**會員主檔**（382,854 筆會員：memberNo/sex/birth/address…），**沒有案件狀態欄位**，是錯的方向。

所以「中文名稱」欄一律寫 `待補（同站點離線資料無中文字典）`，
只填**可由資料推得**的特徵，例如：

| 狀態 | 筆數 | 佔比 | 可推得特徵 |
|---|---|---|---|
| A4 | 16,737 | 52.75% | 全部具還款計畫 → 已核准放款；2023–2026；平均還款 4.7 期 |
| A7 | 6,372 | 20.08% | 全部具還款計畫 → 已核准放款；2023–2025；平均還款 1.8 期 |
| (空) | 2,755 | 8.68% | 幾乎無還款計畫 → 孤兒申請單（案件層有、申請單層缺）；2011–2026 |
| A0 | 2,635 | 8.30% | 全部具還款計畫；2023–2026；平均 37,603 期 ← 見下 |
| A6 | 1,127 | 3.55% | 全部具還款計畫；2023–2025 |

> **注意**：A0 的「平均還款期數 37,603」明顯不是期數 —— 該組的
> `loan_repay_plans.periods` 欄位語意與其他狀態不同（可能是金額而非期數）。
> 這是**資料本身的可疑之處，已如實標出**，沒有把它修成好看數字。

要拿到真正的中文名稱，唯一途徑是打到案件系統的下拉字典 API
（需該系統的認證；不是本次能離線取得的东西）。

## 平台端

新增唯讀端點 `GET /api/loan/classification`（`internal/handler/loan.go` 的 `Classification`），
回傳狀態字典／類型／客群／5 張交叉表／meta 血緣／`dictionary_gap` 說明。
前端在「貸款案件主檔」頁新增「分類字典（狀態／類型／客群）」面板
（`web/static/js/loan-cases.js` 的 `loanLoadClassification()`）。

Go 測試 `TestLoanClassificationDictionary` 守住三件事：
狀態筆數總和 == `total_applications`（總和守恆）、每筆狀態的 `cn_label` **不得為空**
（必須明確標 pending 而非留白）、`dictionary_gap` 不得為空（不隱藏字典缺口）。

## 重跑方式

```bash
cd /mnt/c/Users/Administrator/Desktop/JySecAI
/usr/bin/python3 scripts/export_loan_classification.py
# 輸出：桌面 szjy188_output/貸款案件/貸款案件分類字典.xlsx + 分類/*.csv
```

## 附帶修正：契約明細欄名錯位（2026-11-01）

同一條匯入路徑上另查出一個資料缺陷，已修好並記錄在此以保持血緣完整。

`loan_contract_details`（來源 `EU_DYN_CNTRT_ABT_DTL`）的真表是 **138 欄**
（權威：`CHAILEAse_DB_AllTables_20261023.xlsx` 表頭註記「動態契約明細 138 欄」），
但組裝 XLSX「明細_契約明細」時多塞了一個假欄名 `EU_DYN_CNTRT_ABT_DTL`（→139 名），
資料原樣帶入 → **欄名整體晚一格**。後果：

| 欄位 | 症狀 |
|---|---|
| `apply_dt` | 1,358/1,358 **全空**（真值被掛在 `APLCNT_DEPT_ID` 名下） |
| `case_no` | 存成錯位值（`'11'`、`'12'`…），**對不到案件層** → 平台案件明細頁的契約清單是空的 |
| `maj_seq_id` / `sub_seq_id` / `form_id` / `flw_id` / `stg_id` / `apprv_amt` | 全部各錯一格 |

修復 = 純改名（值不動）：`repaired[csv_hdr[k]] = DB_value[k]`，並丟棄多出的假名。

```bash
# 檢查（唯讀）
python3 scripts/fix_loan_contract_alignment.py
# 套用（備份 → 交易 → 驗證 → 提交）
python3 scripts/apply_loan_contract_alignment.py
```

- 修復前：`apply_dt` 空 1,358/1,358、`case_no` 可 join 案件層 **0/1,358**
- 修復後：`apply_dt` 空 **0/1,358**、`case_no` 可 join **1,304/1,358**、型態不符殘餘欄位 **0 個**
- 備份：`data/loan_cases.db.bak-before-align-fix-20261101T004333`
- `scripts/import_loan_cases.py` 已加防復發校正：重跑匯入會自動偵測並對齊
  （已驗證：重新匯入結果與修復後 DB 的 raw_json / 索引欄 hash 完全一致）
- 平台影響：`internal/handler/loan.go` 的契約明細查詢
  （`WHERE case_no = ?`）原本 100% 查不到資料，現在正常回傳含申請日期與金額的明細
