# 憑證與敏感資料外洩清理報告

- **產生日期**：2026-10-02
- **目標仓库**：`git@github.com:lstjks/JyscanAiI.git`（本機路徑 `C:\Users\Administrator\Desktop\JySecAI`）
- **檢查範圍**：完整版控（72,819 個追蹤檔案）
- **方法**：靜態掃描 + 版控稽核，**未對任何外部目標發送請求**

---

## 一、總結

| 嚴重度 | 項目 | 數量 |
|---|---|---|
| **P0 緊急** | 真實憑證 / Token 進版控 | 8 類 |
| **P0 緊急** | 根目錄 `config.yaml` 明文憑證進版控 | 7 組（22 個秘密欄位，內含 1 個疑似佔位符） |
| **P0 緊急** | 第三方個資與資料樣本進版控 | 2 類 |
| **P1 高** | 個案腳本（寫死目標與憑證）進版控 | 299+ 檔 |
| **P1 高** | 依賴套件（node_modules / venv）進版控 | 48,365 檔 |
| **P2 中** | Python 全域關閉 TLS 驗證 | 100+ 處 |
| **P3 低** | 根目錄金鑰命名不完整 | 2 檔 |

**本次驗證**：`go build -buildvcs=false ./...` 與 `go vet -buildvcs=false ./...` 均 exit 0。這不代表所有既有功能都沒有缺陷；此節記錄本次版控與憑證暴露處置。

### 新增 P0：`config.yaml`（commit `f574d4f39`）

根目錄 `config.yaml` 由 `f574d4f39`（`archive: include complete workspace for vulnerability verification`）帶入版本歷史並推至 `lstjks/main`。檔案含 22 個明文敏感欄位；本次稽核沒有在報告中複製任何值。

| 區段 | 欄位 | 數量 | 行號 | 判定 |
|---|---|---:|---|---|
| `ai.channels.jy-*` | `api_key` | 6 | 45、55、65、75、85、95 | 共用同一組 Jy Gateway 憑證 |
| `ai.channels.nvidia-*` | `api_key` | 10 | 105、115、125、135、145、155、165、175、185、195 | 共用同一組 NVIDIA 憑證 |
| `ai.channels.claude-35-sonnet` | `api_key` | 1 | 25 | 獨立憑證 |
| `ai.channels.huihui-cyberstrike` | `api_key` | 1 | 35 | 獨立憑證，供應商待設定擁有者確認 |
| `ai.channels.zhipu-glm-4-flash` | `api_key` | 1 | 205 | 獨立憑證 |
| `mcp` | `auth_header` / `auth_header_value` | 2 | 486、487 | header 名稱加全域 MCP 服務憑證 |
| `xss` | `token` | 1 | 726 | XSS collector 認證 |
| `knowledge.embedding` | `api_key` | 1 | 626 | 長度異常短，先確認是否為佔位符 |

實際需優先輪替約 7 組：Jy、NVIDIA、Claude、Huihui、Zhipu、MCP、XSS。操作清單見 `CREDENTIAL_ROTATION_CHECKLIST.md`。設定加密可行性與風險見 `docs/security/config-secret-migration-assessment.md`。

以下完整清單的長度與去重關係沿用使用者已確認的 metadata，本次沒有讀取或輸出值。

| 區段 | 欄位 | 長度 | 備註 |
|---|---|---:|---|
| `ai.channels.jy-53` | api_key | 54 | Jy 共用 |
| `ai.channels.jy-air` | api_key | 54 | Jy 共用 |
| `ai.channels.jy-flash` | api_key | 54 | Jy 共用 |
| `ai.channels.jy-gateway` | api_key | 54 | Jy 共用 |
| `ai.channels.jy-nano` | api_key | 54 | Jy 共用 |
| `ai.channels.jy-think` | api_key | 54 | Jy 共用 |
| `ai.channels.nvidia-deepseek-v4` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-diffusiongemma` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-gpt-oss-20b` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-ising-calibration` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-llama-33-70b` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-llama-safety-guard` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-muse-glimmer` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-nemotron-120b` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-nemotron-550b` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.nvidia-primary` | api_key | 70 | NVIDIA 共用 |
| `ai.channels.claude-35-sonnet` | api_key | 66 | 獨立 |
| `ai.channels.huihui-cyberstrike` | api_key | 37 | 獨立 |
| `ai.channels.zhipu-glm-4-flash` | api_key | 57 | 獨立 |
| `mcp` | auth_header / auth_header_value | 11 / 64 | header 名稱不是憑證；value 才是秘密 |
| `xss` | token | 64 | XSS collector |
| `knowledge.embedding` | api_key | 10 | 疑似佔位符，待擁有者確認 |

計數說明：清單共有 23 個具名欄位（MCP 一列含兩個），扣除非秘密 `auth_header` 後為 22 個秘密欄位，這 22 個已包含 embedding 的疑似佔位符。不能再把佔位符算成第 23 個秘密。實際輪替 7 組的結論不變。

目前 `.gitignore` 已包含根目錄 `config.yaml` 與 `config.yaml.backup`，但 ignore 規則不會自動取消既有追蹤。依交接約束，本次未執行 `git rm --cached config.yaml`、未修改檔內值、未輪替憑證，也未改寫 Git 歷史。

---

## 二、P0：真實憑證進版控（需立即輪替）

以下憑證已進入 Git 歷史。**即使現在從 index 移除，歷史紀錄仍可還原**，必須視為已外洩並立即輪替。

| 檔案 | 憑證類型 | 風險 |
|---|---|---|
| `broadcast_gui_core_20261001/config/tpe_service119_live.env` | 政府系統帳號 `[REDACTED]` + 密碼 `[REDACTED]`、JWT secret、live session JWT、JSESSIONID | 第三方政府系統帳密被取得 |
| `broadcast_gui_core_20261001/runtime/tpe119_token.json` | 有效 JWT + JSESSIONID（`exp: 1790835407`） | 會話劫持 |
| `broadcast_gui_core_20261001/runtime/ips_cookies.json` | 系統登入 cookies | 會話劫持 |
| `erpc/.env` | `EPCR_PASSWORD`、ADMIN 角色 JWT、Telegram Bot Token `[REDACTED]` | Telegram bot 遭接管 |
| `erpc/data/.env` | 同上 | 同上 |
| `tpe_broadcast/tpe_service119_live.env` | 同第 1 項 | 同上 |
| `.tmp-ds.key` | 平台 API key `[REDACTED]` | 平台費用盜用 |
| `data/.jy-gateway.key` | 閘道金鑰 `sk-jy-***` | 平台費用盜用 |

### 立即處置順序

1. **先輪替，再談歷史清理**（順序顛倒會失去 traceability）
   - Telegram Bot → BotFather `/revoke`
   - 平台 API key → 發卡後台撤銷重發
   - 政府系統帳密 → **依授權範圍通知對應機關**（見第五節）
2. 歷史清理（影響所有協作者，需協調）
   ```bash
   # 建議用 git-filter-repo，並在獨立分支演練
   pip install git-filter-repo
   git filter-repo --invert-paths \
     --path tpe_broadcast --path okbank_evidence --path poc_scripts \
     --path zoomeye_results --path broadcast_gui_core_20261001 \
     --path erpc --path tpe119_evidence --path _archive \
     --path-glob '*.env' --path-glob '*.key'
   ```
3. 清理後 **force-push 並通知所有協作者重新 clone**（舊 clone 仍含歷史）

---

## 三、P0：第三方個資與資料樣本

| 檔案 | 內容 |
|---|---|
| `okbank_evidence/samples/TW000635_202602061.png` 等 | 從第三方銀行系統下載之文件影像 |
| `okbank_evidence/idor_evidence.txt` | 完整枚舉結果（案件編號、日期清單） |

這是**未授權取得的第三方資料**。無論是否為授權測試，**不應存在於公開版控**。

**處置**：立即從版控移除；若該測試未經正式授權，應主動刪除本機副本並評估通知義務。

---

## 四、P1 / P2 / P3 修護項目

### P1：個案腳本進版控（299+ 檔）
`phase*.py`、`fofa_*.py`、`login_*.py`、`poc_scripts/`、`broadcast_gui_core_20261001/` 等
→ 已加入 `.gitignore` 並 `git rm --cached`

### P1：依賴套件進版控（48,365 檔）
- `node_modules/` 37,330 檔
- `venv/` / `.venv/` 11,035 檔

這些不屬於原始碼，卻讓 repo 體積暴增、供應鏈風險上升，且 `_archive` 內含第三方憑證。
→ 已加入 `.gitignore` 並移除追蹤

### P2：Python 全域關閉 TLS 驗證（100+ 處）
```python
requests.get(url, verify=False)   # fofa_*.py / phase*.py / poc_scripts/* 等
ctx.verify_mode = ssl.CERT_NONE   # broadcast_gui_core_20261001/core/tocp_tpe_broadcast.py:158
```
**風險**：攔截流量可竄改回應，掃描結果不可信。
**修護建議**：
```python
# 需要掃描自簽憑證目標時，改用明確的 CA bundle 而非全域關閉
import certifi
CA_BUNDLE = certifi.where()          # 正常驗證
INSECURE_CA = "/path/to/target-ca.pem"  # 自簽目標專用
s.get(url, verify=INSECURE_CA)
```

### P2：Go 側 `InsecureSkipVerify`
- `internal/handler/webshell.go:346` — 已有 `//nolint:gosec` 註解標記為刻意
- `internal/app/main_server_http_redirect_test.go:118` — 測試檔，可接受

webshell proxy 建議至少限制可連線的目標範圍，而非無條件跳過驗證。

### P3：根目錄金鑰命名
`.tmp-ds.key` 以 `.tmp-` 前綴偽裝成暫存檔。已補上 `/.tmp-*.key` 規則。

---

## 五、必須同步處理的合規事項

以下不是技術問題，但比技術問題嚴重：

1. **政府系統憑證外洩**：`tpe_service119_live.env` 內含台北市消防／到院前救護（EPCR）系統的帳號密碼與 JWT signing secret。若該測試**未取得正式書面授權**，此為未授權存取，應依《資通安全法》與《刑法》第 116 條等規定評估法律責任，並考慮主動通報。

2. **平台內建防護失效**：`config.example.yaml` 有政府域名保護規則（`tool_guard.government-domains`），但掃描腳本是**繞過 Agent 直接以 Python 執行**，該防護完全不生效。
   > 這是本次審查最值得修護的架構問題：防線只擋 Agent 路徑，擋不住腳本路徑。

3. **歷史已公開**：`lstjks/JyscanAiI` 若為公開倉庫，這些憑證自首次 commit 起即已公開可取。

---

## 六、已完成修護（本機）

- [x] `.gitignore` 補齊：敏感目錄、`*.env`、`*.key`、`*token*.json`、`*cookie*.json`、`*.pem`、`/.tmp-*.key`、`/data/.jy-gateway.key`
- [x] `git rm --cached` 停止追蹤（**本機檔案完整保留**）
- [x] 已驗證 `mcp-servers/` 24 個 legit Python 檔無誤刪（與 HEAD 基準一致）
- [x] Go 建置與 vet 通過，未受影響

## 七、待你決策

1. 是否執行 Git 歷史清理（`git filter-repo`）？影響所有協作者。
2. 是否輪替上述憑證？特別是 Telegram bot 與平台 API key。
3. `tpe_broadcast/` 等個案目錄改為**獨立私有倉庫**，還是維持本機 only？
4. `config.example.yaml` 建議將 `hitl.default_mode` 從 `off` 改為 `approval`（預設關閉人機協同，風險偏高）。
