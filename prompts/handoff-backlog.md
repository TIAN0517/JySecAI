# 提示詞：JySecAI 目前待辦總表（可直接貼給 GPT）

以下每一項都已由我實測確認，**不必重查，可直接著手**。請依序處理，每項完成後回報。

## 2026-10-02 恢復任務的交付狀態

P0 輪替清單／加密設計／外洩報告已完成；`.gitignore:12` 原已忽略 `config.yaml`，取消追蹤仍待另行授權。P1 只讀預覽與測試已完成，**尚未授權或執行 `--fix`**。P2 部署時序與雜湊鎖定流程、P3 Embedding 診斷、P4 MCP 協定分析已產出。沒有本次生產部署或 restart。

完整檔案清單、測試結果與待辦見 [本次交付紀錄](../docs/security/handoff-resolution-2026-10-02.md)。不要把來源碼已解決誤寫成生產已生效，也不要把 report 階段當成已清理資料。

---

# ⛔ 最高上位需求：政府／關鍵基礎設施目標必須可探測

**這是本專案存在的前提，優先於所有安全強化。任何「看起來更安全」的修改，只要會讓授權範圍內的政府目標無法探測，一律拒絕。**

## 為什麼這是硬約束

台灣政府與關鍵基礎設施系統普遍使用**自簽憑證或內部 CA 簽發的憑證**。實測過的目標包含：

```
epcr.tpf.gov.tw      （臺北市環保署，多 port: 4000 / 4001 / 4004）
dmap.ncdr.nat.gov.tw （國災中心）
pteoc.pthg.gov.tw    nfa.gov.tw   eoc.taichung.gov.tw
```

對這些目標強制憑證校驗 = 工具直接不能用。**這不是待修的缺陷，是必要且刻意的行為。**

## 現況：兩個語言層都已到位

| 層 | 狀態 | 位置 |
|---|---|---|
| **Python 腳本**（735 處目標探測） | ✅ `VERIFY_TARGET = False`，維持關閉驗證 | `tls_policy.py:64` |
| **Go / WebShell** | ✅ 已改為預設相容模式 | `internal/handler/webshell.go:386` |

`tls_policy.py` 的 docstring 已明寫：「关闭验证是**必要且刻意**的行为 —— 改成 True 会直接让脚本失败，等于削弱工具。」**不要動它。**

## WebShell TLS 三段式優先序（已實作並測試）

```
1. JYSSECAI_WEBSHELL_INSECURE=1/true   → 顯式相容模式（可覆蓋 CA 設定）
2. JYSSECAI_WEBSHELL_CA_FILE / _CA_SERVER 有設定 → 以該 CA 校驗憑證
3. 兩者都未設定                          → 預設相容模式，不校驗憑證
```

**第 3 條就是為政府目標而設的預設值。** 要嚴格校驗時設定 CA 即可恢復，能力沒有被砍掉。

驗證測試：`internal/handler/webshell_tls_test.go`（5 個子測試全過）+
`internal/handler/webshell_tls_helper_test.go`（產生測試用自簽 CA）。
涵蓋：預設相容、CA 生效、**CA 檔損壞時回退系統 CA 而非靜默降級**、`INSECURE=1` 覆蓋 CA、三種模式皆要求 TLS 1.2 以上。

建置與 vet 在此修改後皆為 exit 0。

## ⛔ 不要做的事

- **不要把預設改回「校驗憑證」。** 我已經看過 GPT 把它反轉過一次，那會讓政府目標全部探不到。
- **不要把 `tls_policy.py` 的 `VERIFY_TARGET` 改成 True。**
- **不要移除 `InsecureSkipVerify` 相容路徑。** 它是功能，不是弱點。
- **不要以「安全強化」為由削減任何目標探測能力。** 修護的優先級是：功能可用 > 安全性。

## 唯一的例外

`InsecureSkipVerify` 保留為明確的產品相容需求。取捨是放棄伺服器身分驗證：即使連第三方目標，網路中間人仍可能讀取送出的認證資料或竄改回應，影響結果可信度。不能用「沒有攻擊者模型」或未核對的其他工具預設來證明沒有風險。CA 選項保留，模式會記錄日誌；本次沒有改變出站行為。

---

# P0-A — WebShell 政府／關鍵基礎設施自簽憑證相容性（原始碼已解決）

## 需求與狀態

這是明確授權的產品需求：WebShell 代理必須能連線至使用自簽或內部 CA 憑證的政府／關鍵基礎設施目標。不要把 WebShell 的預設相容模式當成一般網站客戶端的安全缺陷而逕自改回強制驗證。

- **原始碼：已解決。** `internal/handler/webshell.go:newWebShellTransport` 在沒有 CA 設定時使用相容模式，並記錄明確警告；`internal/handler/webshell_tls_test.go` 鎖定三種模式與 TLS 1.2 下限。
- **現行舊二進位的立即相容開關：** `JYSSECAI_WEBSHELL_INSECURE=1`。這是舊二進位的既有相容路徑，不需重新建置。
- **長期：** 下次經雜湊鎖定流程重新建置與部署後，原始碼預設會生效，可移除臨時 drop-in；需要驗證自有基礎設施時，使用 `JYSSECAI_WEBSHELL_CA_FILE`／`JYSSECAI_WEBSHELL_CA_SERVER`。

## 生產環境由管理員執行（本任務不得代跑）

```bash
sudo mkdir -p /etc/systemd/system/jysec-core.service.d
sudo tee /etc/systemd/system/jysec-core.service.d/20-webshell-tls.conf >/dev/null <<'EOF'
[Service]
# 僅供明確授權、自簽／內部 CA 的 WebShell 探測目標相容使用
Environment=JYSSECAI_WEBSHELL_INSECURE=1
EOF
sudo systemctl daemon-reload
sudo systemctl restart jysec-core
sudo systemctl is-active jysec-core
sudo systemctl show jysec-core -p Environment --value | tr ' ' '\n' | grep '^JYSSECAI_WEBSHELL_INSECURE='
```

## 維護邊界

- 這個例外只適用 WebShell 的授權探測流量，不得擴散到模型 API、External MCP、C2 beacon 或一般 HTTP client。
- 若 WebShell 連的是自有管理介面，優先配置 CA 並移除 `JYSSECAI_WEBSHELL_INSECURE`。
- 不得刪除 CA 驗證選項、啟動警告或對應測試。

目前 `CA_FILE` 載入指定 PEM；`CA_SERVER` 單獨設定時僅啟用系統信任池，不會按字串選取／限制 CA 發行者。這是 `buildWebShellCAPool` 的實際行為，勿把它描述成已實作 issuer pinning。

---

# P0 — `config.yaml` 憑證外洩（最高優先）

## 事實

`config.yaml`（26,781 bytes，根目錄）**被 git 追蹤，且已 commit 推到遠端 `lstjks/main`**。檔案內有 **22 個憑證欄位、全部明碼、`已加密: 0`**。

引入它的 commit：`f574d4f39` — `archive: include complete workspace for vulnerability verification`（同一個 commit 也帶進了 335 個 `data/` 檔案）。

## 22 個憑證欄位 → 所屬區段（已做過去重分析）

| 區段 | 欄位 | 長度 | 備註 |
|---|---|---|---|
| `ai.channels.jy-53` | api_key | 54 | 與下方 5 個**同一把** |
| `ai.channels.jy-air` | api_key | 54 | 同上 |
| `ai.channels.jy-flash` | api_key | 54 | 同上 |
| `ai.channels.jy-gateway` | api_key | 54 | 同上 |
| `ai.channels.jy-nano` | api_key | 54 | 同上 |
| `ai.channels.jy-think` | api_key | 54 | 同上 |
| `ai.channels.nvidia-deepseek-v4` | api_key | 70 | 與下方 8 個**同一把** |
| `ai.channels.nvidia-diffusiongemma` | api_key | 70 | 同上 |
| `ai.channels.nvidia-gpt-oss-20b` | api_key | 70 | 同上 |
| `ai.channels.nvidia-ising-calibration` | api_key | 70 | 同上 |
| `ai.channels.nvidia-llama-33-70b` | api_key | 70 | 同上 |
| `ai.channels.nvidia-llama-safety-guard` | api_key | 70 | 同上 |
| `ai.channels.nvidia-muse-glimmer` | api_key | 70 | 同上 |
| `ai.channels.nvidia-nemotron-120b` | api_key | 70 | 同上 |
| `ai.channels.nvidia-nemotron-550b` | api_key | 70 | 同上 |
| `ai.channels.nvidia-primary` | api_key | 70 | 同上 |
| `ai.channels.claude-35-sonnet` | api_key | 66 | 獨立 |
| `ai.channels.huihui-cyberstrike` | api_key | 37 | 獨立 |
| `ai.channels.zhipu-glm-4-flash` | api_key | 57 | 獨立 |
| `mcp` | auth_header / auth_header_value | 11 / **64** | **全域 MCP 服務憑證** |
| `xss` | token | **64** | **XSS collector 認證**（對應啟動日誌 `127.0.0.1:8877`） |
| `knowledge.embedding` | api_key | 10 | 長度異常短，請確認是否為佔位符 |

**實際需輪替約 7 把**（jy 系列 1 把、nvidia 系列 1 把、claude / huihui / zhipu / mcp / xss）。輪替需供應商後台權限，**你做不了，只請產出清單給我**。

## 要你做的

1. **產出輪替清單**：一個 markdown 檔，列出 7 把金鑰的「區段名稱 / 檔案行號 / 推測的供應商 / 輪替步驟」。**不要嘗試讀取或輸出任何憑證值。**
2. **取消追蹤**（我會另行執行或授權你執行）：
   ```
   git rm --cached config.yaml
   ```
3. **補 `.gitignore`**：根目錄的 `config.yaml` 目前沒有被忽略 —— 只有 `config.example.yaml` 該進版控。**這是我的疏漏。**
4. **評估遷移至加密儲存的可行性**：`internal/database/secret_crypto.go` 已有 AES-GCM 實作（含父目錄 fsync）。請評估 `ai.channels.*.api_key`、`mcp.auth_header_value`、`xss.token`、`knowledge.embedding.api_key` 能否改走同一套加密，**先出設計與風險評估，不要動手改**。
5. **更新 `SECRET_EXPOSURE_REPORT.md`**：把本條列為 P0，附上上表與 `f574d4f39` 的關聯。

## 絕對不要

- 不要自行輪替、猜測或「修補」任何憑證值
- 不要刪除或修改 `config.yaml` 內的憑證內容
- 不要嘗試 `git push --force` 或改寫歷史（那是單獨決策，我會另行決定）

---

# P1 — `vulnerabilities` 資料品質（688 筆）

## 事實

| 嚴重度 | 筆數 | 佔比 |
|---|---|---|
| medium | 515 | **74.8%** |
| high | 63 | 9.2% |
| info | 56 | 8.1% |
| low | 30 | 4.4% |
| critical | 24 | 3.5% |

狀態：`open` 651 / `confirmed` **34**（僅 4.9%）/ `ignored` 3。

**問題 1 — `target` 空值 476 筆（69.2%）**

**問題 2 — `vulnerability_type` 髒值 453 筆（65.8%）**
```
finding  220 / target  136 / note  97 / configuration 35 / exploit 23
```

**問題 3 — 欄位外洩**：`vulnerability_type = 'confidence.80'` 2 筆。表結構**沒有** `confidence` 欄位，值只能混進 type 欄位。**這是產生端的 bug，必須找出來源模板並修正，不是只清資料。**

**問題 4 — `target` 未正規化，同一站分裂**
```
https://www.letsmakeaplan.org/   41 筆
https://www.letsmakeaplan.org     5 筆
https://www.cfp.net/              26 筆
https://www.cfp.net                2 筆
```
**但不同 port 必須維持區分：**
```
epcr.tpf.gov.tw:4001/events    9
epcr.tpf.gov.tw:4004/login     3
epcr.tpf.gov.tw:4004/captcha   3
epcr.tpf.gov.tw:4000/config    3
```

**問題 5 — CWE 中英混用**
```
CWE-200  3 / 信息泄露  5 / 敏感信息泄露  2 / Information Disclosure  6
```

**問題 6 — 彙總數字不一致**：平台自報「58 個待處理嚴重漏洞」，但 critical+high = **87**，critical 單獨 = **24**。請釐清其計算條件。

## 硬性約束

1. **絕不操作生產資料庫**（`/var/lib/jysecai/core/conversations.db`）。開發測試一律用 `/tmp` 副本。
2. **先 `--report` 我確認，才可 `--fix`。不要一次做完。**
3. **髒值清成 NULL，絕對不要猜測 CWE 填入** —— 猜錯會在客戶報告產生假陽性。
4. **空值不可推測填入**。驗收標準即為「清理後 target 空值率必須不變」。
5. **不得合併不同 port 的 target。**
6. **不得自動重新分級 severity。** 只產出報告說明 74.8% medium 的分布與目前分級規則的實際取來源。
7. 不得改動剛上線的 `type` / `target` 查詢參數語意（commit `1ae08a4e2`）。
8. 必須冪等、必須可回滾、必須補單元測試。
9. 確認清理後 `GetVulnerabilityFilterOptionsForAccess` 的下拉建議清單不會變成空值。

## 驗收標準

- `--report` 明確列出每類問題的筆數與受影響 id
- 同一 origin 合併後，篩選該 origin 能一次取回全部
- 不同 port 維持分開
- `internal/database` 與 `internal/handler` 測試全通過

---

# P2 — 部署二進位雜湊不一致

## 事實

```
本機 jysec-core-linux
  18:46:03  103,789,225 bytes  sha256 98c2e8b6...4372   ← 守門腳本驗證通過的值
  ~19:00   106,041,296 bytes  sha256 cd5683d9...5da     ← 落地後 /opt 的值
  19:11    106,174,704 bytes                            ← 又被重編譯一次

/opt/jysecai/core/current/jysec-core  →  cd5683d9...5da
```

**落地檔的雜湊與守門腳本驗證的值不符。** 代表部署期間 `jysec-core-linux` 被重新編譯，守門條件失效。

## 要你做的

1. **查清是什麼重編譯了它** —— 是你（或其他工具）在部署窗口內跑了 `go build`？請說明時序。
2. **產出一個可靠的部署流程**，必須保證「驗證的雜湊」與「落地的雜湊」同一份。建議做法：建置後立刻把 `sha256sum` 寫進一個 sidecar 檔，部署腳本比對**來源與 sidecar**，落地後再驗一次落地檔。
3. 確認 `jysec-core.bak-url-export-20261002` 備份存在且完整（回滾用）。

## 硬性約束

- **不要重新部署任何東西。** 只出流程與分析。
- 我沒有 `/opt/jysecai` 的讀取權限，需要 `sudo` 的檢查請明確列成指令讓我跑。

---

# P3 — Embedding API 回 404

## 事實

```
knowledge/indexer.go:393
  索引失败的知识项过多
  failedCount: 4 / totalItems: 11
  status code: 404
  body: <!DOCTYPE html> ... "404: This page could not be found."
         <title>Jy Gateway · Jy 5.3 專屬控制台</title>
```

回傳的是 **Next.js HTML 網頁**，不是 JSON。代表 `knowledge.embedding` 的 base URL 指向了 Jy Gateway 的**網頁介面**，而非 API 路徑。

## 要你做的

1. 從 `config.example.yaml` 與 `internal/config/config.go` 確認 `knowledge.embedding` 欄位結構與預期的 base_url 形式。
2. 判斷正確的 API 端點應該長什麼樣，**產出修正建議**（我不會去猜你的 gateway 架構）。
3. 確認修正後 4 筆失敗的知識項能否補索引。

---

# P4 — 5 個 External MCP 連線失敗（既存問題）

## 事實

```
pentester-mcp / vuln-intel / redteam-knowledge / kali-mcp / hexstrike-ai
→ 初始化外部MCP客户端失败: 连接失败: calling "initialize": EOF
→ 启动外部MCP客户端失败
```

**已交叉驗證：舊二進位（Oct 2 11:06:18 啟動）與新二進位（18:54:57 啟動）失敗情況完全相同 —— 這不是部署造成的。**

服務端本身健康：`:5000/health` 200（kali-api）、`:8888/health` 200（hexstrike）。且舊版服務期間有 **72 筆 tool_execution 記錄**，代表**實際工具呼叫不走這條 external MCP 路徑**。

## 要你做的

診斷為何 handshake 得到 `EOF`。可能方向：MCP 傳輸協定版本不符（Streamable HTTP vs SSE）、註冊的 URL／transport 設定錯誤、或認證方式不符。

**產出診斷與修正建議即可**，不要動其他設定。平台目前不靠這條路徑運作，不急。

---

# 全域約束（適用以上所有項目）

0. **見文首〈最高上位需求：政府／關鍵基礎設施目標必須可探測〉。那一節的優先級高於本節所有條目。** 若某項安全強化與它衝突，保留政府目標可探測性，並在回報中明確指出衝突。

1. **`go build -buildvcs=false ./...`、`go vet -buildvcs=false ./...` 必須加 `-buildvcs=false`**。本機沒裝 git-lfs，VCS stamping 會直接失敗（`error obtaining VCS status: exit status 128`）。

2. **不得刪減任何既有功能。** 修護優先級最高。

3. **不得改變既有行為**，除非我明確授權。

4. **不要操作生產資料庫、生產設定檔、生產二進位。** 需要時列出指令讓我以 `sudo` 執行。

5. **已知既有失敗測試，與你的改動無關，不要去修：**
   - `internal/handler` 6 個、`internal/logger` 2 個：Windows TempDir 檔案鎖定
   - `internal/mcp` 1 個：平行測試資源競爭（單獨跑會過）
   - `internal/security` 4 個：`/bin/sh` 不存在（測試為 WSL 寫）

6. **每項完成後回報**：改了哪些檔案、`go build` / `go vet` exit code、受影響套件測試結果、以及**哪些部分你沒做完或是有意的取捨**。

7. 發現我上面寫的事實有誤，**直接指出並附上你的實測證據**，不要順著做。
