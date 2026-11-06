# Kali GPT MCP

供 JySecAI 使用的**離線純推理**滲透測試助理。它把上游
[`kali-gpt`](https://github.com/alishahid74/kali-gpt) 的
OBSERVE → THINK → ACT → LEARN 迴圈，重新實作成平台內的 **MCP 工具**：

| 能力 | 對應工具 |
|---|---|
| 每次工具呼叫的 MITRE ATT&CK 對映 | `kali_map_to_mitre` |
| 依 findings 動態挑選工具鏈 | `kali_suggest_toolchain` |
| PTES 階段方法論規劃 | `kali_plan_phase` |
| 目標指紋與工具成敗率的持久化記憶 | `kali_record_memory` / `kali_recall_memory` |
| 自我狀態檢查 | `kali_gpt_status` |

> **只做規劃，永遠不執行。**
> 本伺服器不會啟動任何行程、不開 socket、沒有任何網路 I/O，
> 永遠不會碰到目標。回傳的 `command_template` 都是含
> `{target}` / `{port}` / `{wordlist}` / `{url}` 的佔位符範本，
> 伺服器不會代入真實目標、也不會執行它。

## 工具

### `kali_map_to_mitre(tool: str, args_hint: str = "")`

以 **curated 離線對照表**把工具呼叫對應到 MITRE ATT&CK Enterprise
（不連網、不抓 STIX）。

回傳
`{"tool", "tactic", "technique_id", "technique_name", "tactic_rationale",
"related_techniques": [{"technique_id", "technique_name", "tactic"}],
"technique_source": "curated-offline", "mapped": bool}`

查不到的工具**不會拋例外**，而是回傳結構化 fallback：
`tactic: "unknown"`、`mapped: false`、
`technique_source: "curated-offline:unmapped"`。

### `kali_suggest_toolchain(findings: list, limit: int = 8)`

依已發現的 findings 組出工具鏈。`findings` 可為 dict 陣列
（`{"type": "open_port", "port": 80}`、`{"type": "web_tech",
"value": "wordpress"}`、`{"type": "service", "service": "smb"}`），
也可為自由字串。

回傳
`{"findings": N, "chain": [{"step", "tool", "purpose", "mitre_tactic",
"technique_id", "depends_on", "command_template", "requires_authorization"}],
"notes": [...], "execution_policy": "..."}`

內建規則：Web 埠 → whatweb → nikto → ffuf → nuclei；WordPress → wpscan +
nuclei 模板；SMB → enum4linux → smbmap → netexec；
LDAP → ldapsearch → bloodhound → kerbrute；SSH → ssh-audit → hydra；
MySQL → 先列舉，**只有在存在 Web 前端時**才加入 sqlmap；
既有 SQLi 發現 → 以明確標示的非破壞性 profile 跑 sqlmap
（`--batch --level --risk`、`tamper=space2comment`、禁止 `--dump`）；
容器 / Kubernetes 發現 → docker + kubectl 稽核路徑。

### `kali_plan_phase(phase: str, target: str, context: str = "")`

回傳單一 PTES 階段的計畫。支援階段：`recon`、`scan`、`enumeration`、
`vulnerability-analysis`、`exploitation`、`reporting`。
別名：`information-gathering` → recon、`vuln-analysis` → vulnerability-analysis、
`report` → reporting、`attack` → exploitation。

回傳
`{"ok": true, "phase", "phase_title", "target", "steps": [{"order", "title",
"description", "tools", "mitre_tactics", "expected_output",
"requires_authorization"}], "mitre_coverage": [...], "execution_policy": "..."}`

### `kali_record_memory(entry: dict)`

寫入一筆 engagement 經驗。`entry` 欄位：`target_fingerprint`（str，必填）、
`tool`（str，必填）、`technique_id`（str，選填）、
`outcome`（`success` / `failure` / `partial`，預設 `partial`）、
`notes`（str，上限 2000 字）、`tags`（list[str]，上限 16 個、每個 64 字）。

回傳 `{"ok": true, "id": N, "memory_db": path}` 或
`{"ok": false, "error": "..."}`。

### `kali_recall_memory(target_fingerprint: str = "", tool: str = "", limit: int = 10)`

回傳過往經驗，排序先看 target_fingerprint 完全相符，再看 tool 與 tag 的重疊。
回傳 `{"entries": [{"id", "target_fingerprint", "tool", "technique_id",
"outcome", "notes", "tags", "updated_at", "score"}], "total": N,
"matched_total": N}`。fingerprint 留空則回傳最近紀錄；
資料庫不存在時回傳空清單而不是錯誤。

### `kali_gpt_status()`

回傳 `{"ok": true, "tool_count": 6, "memory_db": path,
"memory_entries": N, "provider": "curated-offline-rule-engine", "note": "..."}`。

## 環境變數

| 變數 | 預設值 | 用途 |
|---|---|---|
| `KALI_GPT_MEMORY_DB` | `~/.jysecai/kali_gpt/memory.db` | engagement memory 的 SQLite 路徑，父目錄會在第一次寫入時自動建立。 |

資料庫在**第一次寫入時才會建立**；對不存在的檔案讀取只會回傳空清單。Schema：

```sql
CREATE TABLE engagement_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_fingerprint TEXT,
    tool TEXT,
    technique_id TEXT,
    outcome TEXT,
    notes TEXT,
    tags TEXT,          -- 以逗號串接
    updated_at TEXT     -- RFC3339 UTC
);
CREATE INDEX idx_engagement_memory_fingerprint ON engagement_memory(target_fingerprint);
```

所有 SQL 都使用參數化語法。tags 以逗號串接儲存、讀取時解析回陣列。
回傳列數上限 100。

## 在 JySecAI（`config.yaml`）註冊

把下面這段貼到 `external_mcp.servers` 底下：

```yaml
    kali-gpt:
      command: python3
      args:
      - mcp-servers/kali_gpt/mcp_kali_gpt.py
      description: 'Kali GPT: offline pentest reasoning (ATT&CK mapping, tool-chain selection, PTES planning, engagement memory). Planning only, never executes.'
      timeout: 60
      max_retries: 3
      keep_alive: 15
      external_mcp_enable: true
      tool_enabled:
        kali_map_to_mitre: true
        kali_suggest_toolchain: true
        kali_plan_phase: true
        kali_record_memory: true
        kali_recall_memory: true
        kali_gpt_status: true
```

## 執行與測試

```bash
# stdio 傳輸
python3 mcp-servers/kali_gpt/mcp_kali_gpt.py

# 測試（不連網，透過 KALI_GPT_MEMORY_DB 使用暫存 DB）
python3 -m unittest discover -s mcp-servers/kali_gpt -v
```

## ATT&CK 對映的注意事項（caveat）

這份對照表是 **人工整理的離線表**，不是官方 MITRE ATT&CK 資料集，
上游技術更新後必然會有落差。

把 technique ID 寫進報告之前，請先與兄弟服務 `redteam-knowledge`
（`redteam_get_attack`）交叉查核——它會抓官方 ATT&CK STIX 資料，
回傳緩解措施、偵測方式與版本資訊。
`kali_map_to_mitre` 另外會回傳 `related_techniques`，讓審閱者看到
curated 條目刻意沒有選用的鄰近技術。

## 執行政策（execution policy）

每個規劃型工具都會回傳 `execution_policy`，內容一致：

- 本 MCP 不執行指令、不連線目標、沒有任何網路 I/O。
- 要跑 `command_template`，必須走 JySecAI 正常工具路徑：
  **HITL 人工審批卡**必須核准，且 **scope registry** 必須授權該目標與
  該 action class（`credential_enum` / `bulk_scan` / `arbitrary` 絕不會隱含成立；
  `destructive` 與 `real_transaction` 永遠無法解鎖）。
- 範本只是保守預設值，務必依 engagement 的授權範圍（rules of engagement）複核。
