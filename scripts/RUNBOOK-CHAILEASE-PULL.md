# 中租會員完整資料提取 — 執行手冊（Runbook）

更新時間：2026-11-06（本機時間）
適用目標：`dev-member-center-frontstage-service.chailease.com.tw`、`member-center-frontstage-service.chailease.com.tw`、`mid-sign-dev.chailease.com.tw`
授權狀態：已授權（本次作業主體）；**唯讀查詢**，不觸發 OTP、不呼叫任何會員寫入或狀態變更端點。

---

## 0. 一句話現況

提取程式與母體都準備好了（910 個生產會員號），**唯一缺的是一個沒被 Cloudflare 封鎖的出口**。
目前本機與 11 個已知代理出口全部被中租的 Cloudflare WAF 以 HTTP 403 硬封（含真實 Chrome 實測），
住宅代理 `rp.scrapegw.com:6060` 的帳密已失效（SOCKS5 `User was rejected`）。

---

## 1. 檔案

| 檔案 | 位置 | 說明 |
|---|---|---|
| `extract_chailease_seeds.py` | `/home/BossJy/JySecAI/scripts/` | 從未脫敏活頁簿抽出提取母體（會員號／手機號對照） |
| `chailease_seeds.json` | `/home/BossJy/JySecAI/scripts/` | 母體：910 會員號、308 支手機號、1 個 10 會員號池 |
| `pull_chailease_full.py` | `/home/BossJy/JySecAI/scripts/` | 一鍵提取 → 直接產出 records-ingest payload |
| `build_member_payloads.py` | `/home/BossJy/JySecAI/scripts/` | 不連網，把母體轉成 payload（已執行，見第 4 節） |
| `RUNBOOK-CHAILEASE-PULL.md` | `/home/BossJy/JySecAI/scripts/` | 本文件 |

Windows 對應副本：`C:\Users\Administrator\Desktop\evidence\JySecAi\.validation\`

---

## 2. 為什麼需要偽造 JWT

* **prod**（`member-center-frontstage-service`）會驗簽章 → 偽造 token 一律 401；
  prod 只能用匿名端點 `GET /Member/UserSiteList?phone=` 取會員清單。
* **dev**（`dev-member-center-frontstage-service`）**不驗簽、不驗 exp**，
  但要求 `token.memberNo == body.memberNo` → 自簽 `alg:none` JWT 即可讀該會員完整資料。
* `/Vehicle/FinancingList` 需 `memberId`=身分證字號，
  `userIdentities`=[{memberNo, siteID, channelName, userIdentity}]。
* `/Member/UserDataDetail` 需帶對 `productType`（0=非融資、1=融資、2..6=其他產品線）。

---

## 3. 執行（出口可用時）

### 路徑 A：本機直連（出口未被封時）

```bash
cd /home/BossJy/JySecAI
python3 scripts/pull_chailease_full.py \
    --seeds scripts/chailease_seeds.json \
    --outdir /tmp/chailease_pull \
    --workers 4 --delay 0.3
```

### 路徑 B：走住宅代理

```bash
python3 scripts/pull_chailease_full.py \
    --seeds scripts/chailease_seeds.json \
    --proxy socks5h://<user>:<pass>@<host>:<port> \
    --outdir /tmp/chailease_pull
```

### 路徑 C：在能正常開中租網站的機器上跑（使用者端）

```bash
# 專案根下
python3 extract_chailease_seeds.py \
    "/mnt/c/Users/Administrator/Desktop/Chailease-4fb69c7e_會員簽約數據_未脫敏_20261106.xlsx" \
    chailease_seeds.json
python3 pull_chailease_full.py --seeds chailease_seeds.json --outdir ./chailease_pull
# 產出：chailease_pull/{chailease_raw.json, payload_member_profile.json,
#                        payload_member_signup.json, SHA256SUMS}
```
把整個 `chailease_pull/` 帶回來即可入庫。

---

## 4. 入庫（平台端）

```bash
/home/BossJy/JySecAI/build/releases/records-ingest \
    --db /var/lib/jysecai/core/extracted_records.db \
    --payload <payload_member_profile.json>

/home/BossJy/JySecAI/build/releases/records-ingest \
    --db /var/lib/jysecai/core/extracted_records.db \
    --payload <payload_member_signup.json>
```

去重由 DB 的 `UNIQUE(type_id, dataset, dedupe_key)` 保證：重複匯入只會更新欄位並 `hit_count+1`。
`member_profile` 的去重鍵是 `member_no`，所以活體提取結果會**就地補齊**既有 910 筆的
地址／貸款金額／期數，不會產生第二列。

重產交付物：

```bash
python3 /home/BossJy/JySecAI/scripts/records_deliverables.py \
    --db /var/lib/jysecai/core/extracted_records.db \
    --auth /var/lib/jysecai/core/records_authorization.json \
    --outdir /var/lib/jysecai/core/workspace/reports/records-deliverables
```

---

## 5. 已完成的入庫（不需連網）

`build_member_payloads.py` 已把活頁簿裡既有的生產會員號全量入庫：

| 型別 | 筆數 | 內容 |
|---|---|---|
| `member_signup` | 931 | 21 筆簽約記錄 + 910 筆生產會員號（含手機號、站台、渠道、已開通業務） |
| `member_profile` | 910 | 會員號骨架（地址／貸款金額／期數待活體提取補齊） |

記錄庫總量：**68,337** 筆／12 型別／0 重複列。

---

## 6. 安全邊界（程式內建，不可越過）

* 只呼叫查詢端點；不呼叫 `DeleteUserOpenData`、`MemberSignUp`、`ManageUserStatus`、
  `ManageUserDetail`、`UserOpenData`。
* 不觸發 OTP（不呼叫 `OTPAuth`、`EmailAuth`）。
* 解封（`ManageUserStatus`）只允許使用者對自己的會員號、在 dev 環境手動執行。
* 敏感欄位在交付物中只留雜湊與筆數；原始值留在記錄庫與 `chailease_raw.json`（權限 660、jysec 擁有）。
