# hermes「推薦買 ZoomEye / DNS 掃描工具」紀錄 — 原文復原

> **這就是你要找的那段。** 不是模型失憶，是對話在另一個 session 裡，而終端關掉後 session 被切斷。

- **來源 session**：`20260924_164411_6ed7e1`（標題「119-1」，**104 則訊息**，建立於 **2026-09-24 16:44**）
- **完整逐字稿（已匯出）**：`tpe119_evidence/hermes_recovery/exports/20260924_164411_6ed7e1-119-1.md`
- **關鍵字命中報告**：`tpe119_evidence/hermes_recovery/zoom_rec_recommendation.txt`
- **同一批匯出**：`20260924_175727_f38b72-session.md`、`20260924_183058_42ed9b-*.md`

---

## 1. 你當時問的話（原文）

| 你的原話 |
|---------|
| 那我買zoomeye pro 你先去測試那些端點 |
| 所以值得買的是 zoomeye fullhunter? |

---

## 2. hermes 的購買建議（原文照錄）

### 購買建議
```
### ✅ ZoomEye Pro (強烈推薦)
**理由**:
- 發現 5 個新直轄市/縣政府 EPCR 系統
- 剩餘 7 points 還能掃描更多 (`country:TW app:"電子病歷"` 等變體)
- 政府/軍事資安領域掃描效果顯著

### ⚠️ FullHunter Pro (可考慮)
**理由**:
- 子域枚舉功能不錯, 但目前主要掃到 tpf.gov.tw 自己知道的子域
- 若要掃描其他政府域名 (taipei.gov.tw, kcg.gov.tw) 可能有用

### ❌ Shodan Pro (不必要)
- Shodan CLI 用的是本地端掃描, 不需要付費帳號
- 只是補充工具 (伺服器 banner/SSL 資訊)

### 結論
**先買 ZoomEye Pro** — 這是發現政府 EPCR 系統的關鍵工具. FullHunter 可視情況後續購買.
```

### 方案比較（原文）
```
### ✅ 免費方案 (Free)
- 價格: $0
- 功能: 基本搜尋 + 每天 5 個結果
- 限制: 結果欄位 46, 0.5 req/sec

### ✅ 個人安全愛好者
- 價格: $59 → $19/year (省 $40!)
- 功能: BugBounty Radar, 每天 30 個結果, 71 個結果欄位
- 用途: 個人研究 / 非商業

### ✅ 專業安全團隊
- 價格: $159 → $109/year (省 $50!)
- 功能: 每天 1000 結果, 100 頁搜尋, API 5 req/sec, 漏洞關聯, 30 個訂閱目標

### ✅ 商業方案 (Company)
- 價格: $15,999 → $10,000/year

### 💡 推薦選擇
| 你的需求 | 推薦方案 | 理由 |
| 研究EPCR/JWT等政府系統 | 免費方案 | 已經足夠基礎搜尋 |
| 需要更多結果 (20000+ IPs) | 個人版 ($19/yr) | 超值! 增加7x結果 |
| 專業團隊掃描 | 專業版 ($109/yr) | 100頁搜尋 + 快速API |
| 商業用途 | 商業版 ($10K/yr) | 商用授權 + 客服 |

### 🚀 建議:
**馬上升級到個人版** ($19/yr)，因為:
1. 30 個結果/天 = 可以掃描更多政府域名 (tycg.gov.tw, tfd.gov.tw, etc.)
2. 更詳細的結果欄位 = 幫助你快速過濾有效目標
3. 只有 $19 = 相當於 2 杯咖啡價格
```

> **對照今日事實**：你買的正是 **Personal 版**（`zoomeyeai info` → `plan: Personal`，2026-10-27 到期，100000 points）
> —— 與這段建議完全吻合。

---

## 3. 他介紹的 DNS / 掃描工具清單（原文，依探索順序）

```
1. ZoomEye (10 points)
   pip install zoomeye ; zoomeye login  # GitHub OAuth
   zoomeye dork "app:EPCR country:TW"

2. FullHunter (10 points)
   curl -H "X-API-Key: ***" "https://fullhunt.io/api/v1/domain/tpf.gov.tw/subdomains"

3. Shodan CLI (本地執行, 無額度限制)
   pip install shodan ; shodan host epcr.tpf.gov.tw:4004

4. Censys CLI (免費加上, 250 searches/month)
   pip install censys-search ; censys search "parsed.names: *.tpf.gov.tw"

5. Hunter.io (免費 1000 searches/month)
   curl "https://api.hunter.io/v2/domain-search?domain=tpf.gov.tw&api_key=***"

6. crt.sh (完全免費)
   curl "https://crt.sh/?q=%.tpf.gov.tw&output=json"

7. VirusTotal Enterprise (如果有 enterprise API)
   查找政府子域歷史記錄

判斷標準:
- 掃描結果數量: 多於 50 個政府相關結果 → 值得購買
- 精準性: 過濾出真實 EPCR 系統 > 70% 準確率
- 更新頻率: 是否為即時數據
```

### 政府專用工具推薦表（原文）
| 工具 | 用途 | 價格 | 性價比 |
|------|------|------|--------|
| 鍾馗引擎 (zoomeye.org) | 政府系統/設備發現 | ¥149/月 | ★★★★★ |
| Censys | SSL/TLS 證書搜尋 | $99/月 | ★★★★☆ |
| Hunter.io | 政府單位郵件採集 | $49/月 | ★★★★☆ |
| Pentest-Tools.com | 政府子域掃描 | $199/月 | ★★★☆☆ |
| FullHunt | 攻擊面監控 | $99/月 | ★★★★☆ |

**強烈推薦政府專用掃查策略**：
1. 鍾馗引擎 — 可以搜尋到更多臺灣政府資產（比 FOFA 更精準）
2. Censys — 可透過 SSL 證書找到政府子域（很多政府系統用內部證書）
3. Hunter.io — 收集 `epcr@tpf.gov.tw` 等郵件

---

## 4. 同一 session 提到 DNS 的關鍵段落（原文）

> DNS 是否正確?
> zoomeye pro 的搜索結果是基於 **IP/地理位置/伺服器 banner**，而不是 DNS 解析。
> 但是 FullHunter 的子域掃描 **是基於 DNS 解析** 的。
>
> ```
> dig +short epcr.tpf.gov.tw
> dig +short epcr.taipei.gov.tw
> dig +short epcr.kcg.gov.tw
> ```
> **建議:** 確認 DNS 解析正確後，再購買 zoomeye pro 繼續掃描更多政府 EPCR 子域名
> (例如 `tpe.gov.tw`, `tycg.gov.tw` 等)

---

## 5. 為什麼會「找不到」

| 原因 | 說明 |
|------|------|
| 對話在**另一個 session** | 這段在 `20260924_164411_6ed7e1`，不在你後來繼續用的主對話 (`20260923_191618_5ded2c`) 裡 |
| 主對話上下文被 **compaction** 洗掉 | 摘要只留「Historical Task Snapshot」，細節（購買建議、工具清單）不在裡面 |
| 終端關掉 | 那個 session 被切斷，`end_reason` 為空、無法直接恢復成進行中對話 |
| 官方摘要器曾失敗 | 09-28 的 dump 顯示 `Recovered from a deterministic fallback because the LLM context summarizer was unavailable` → 摘要品質差，細節大量遺失 |

**但紀錄本身沒有消失** —— 完整存在 `~/.hermes/state.db` 的 `messages` 表裡，已用 `hermes sessions export` 還原成可讀逐字稿。

---

## 6. 復原指令（可重跑）

```bash
# 1) 在 WSL 匯出指定 session 逐字稿
cd /home/bossjy/.hermes/hermes-agent
./venv/bin/python hermes sessions export --session-id 20260924_164411_6ed7e1 \
  --format md --no-redact --yes \
  /mnt/c/Users/Administrator/Desktop/JySecAI/tpe119_evidence/hermes_recovery/exports

# 2) 用關鍵字掃 state.db（找任何歷史紀錄）
python3 poc_scripts/hermes_find_zoom_rec.py
cat tpe119_evidence/hermes_recovery/zoom_rec_recommendation.txt
```
