# 技能市場（Skills Marketplace）

JySecAI 的技能（Skills）存放在 `skills/` 目錄，遵循 [agentskills.io](https://agentskills.io) 標準：每個技能一個子目錄 + `SKILL.md`（YAML front matter：`name` / `description` / 可選 `metadata`）。多代理會話透過內建 `skill` 工具漸進載入（配置見 `multi_agent.eino_skills`）。

## 當前技能清單

- **內建技能（26 個）**：滲透流程、方法論與輸出規範（如 `pentest-blackboard`、`pentest-output-standards`、`web-attack-methods`、`cloud-attack-methods`、`post-exploitation`、`dragon-v-pentest` 等）。
- **市場匯入（22 個）**：來源 [SpecterOps/skills](https://github.com/SpecterOps/skills) 與 [trailofbits/skills](https://github.com/trailofbits/skills)。
  - 程式碼審計：`cwe-code-review`、`openssf-python-review`、`owasp-security-code-review`
  - C2：`cobalt-strike-aggressor-development`、`cobalt-strike-aggressor-reference`、`cobalt-strike-malleable-c2-development`
  - 偵察：`nmap-parse`、`osint-recon`、`shodan`
  - BloodHound / 目錄分析：`bloodhound-query`、`bloodhound-analysis`、`bloodhound-ad-analysis`、`bloodhound-opengraph`、`azurehound-analysis`、`openhound-development`、`openhound-github`、`openhound-jamf`、`openhound-okta`
  - 報告時間線：`timeline-consolidator`、`timeline-workflow`
  - TrailOfBits：`burpsuite-project-parser`、`yara-rule-authoring`

匯入記錄（含來源、提交、依賴 MCP）儲存在 `skills/.marketplace-manifest.json`。

## 同步工具

```bash
# 預設集匯入（specterops: starter / c2 / recon / bloodhound / timeline / code-review；trailofbits: audit）
python scripts/sync-skill-marketplaces.py --preset starter

# 指定來源全量
python scripts/sync-skill-marketplaces.py --source specterops

# 從本地路徑匯入（例如自定義技能目錄）
python scripts/sync-skill-marketplaces.py --import path/to/skill_dir

# 常用選項
#   --dry-run      只列印將匯入的內容，不寫盤
#   --update       強制重新拉取市場倉庫（預設增量）
#   --skills-dir   目標目錄（預設 skills/）
#   --cache-dir    克隆快取（預設 scripts/.marketplace-cache/，已 gitignore）
```

匯入時會自動：目錄名 == front matter `name` 規範化；注入 `metadata.marketplace` / `metadata.source` 溯源欄位；更新 manifest。

## 依賴 MCP 的技能（重要）

部分市場技能依賴外部 MCP server 才能發揮完整能力，對應關係見 manifest 的 `deps_mcp` 欄位：

| MCP | 宣告位置（config.yaml） | 對應技能 |
|---|---|---|
| `bloodhound` | `external_mcp.servers.bloodhound` | bloodhound-query / bloodhound-analysis / bloodhound-ad-analysis / azurehound-analysis 等 |
| `dragon-v` | `external_mcp.servers.dragon-v` | dragon-v-pentest（及 agents/dragon-v.md 子代理） |
| `vuln-intel` | `external_mcp.servers.vuln-intel` | CVE/KEV 線上交叉驗證 |

### 啟用語義（必讀）

`config.yaml` 載入時會做歸一化：**未設 `disabled: true` 的外部 MCP server 一律視為啟用**（見 `internal/config/config.go`）。因此：

- 停用 = `disabled: true`（官方 MCP 欄位）
- 啟用 = 刪除 `disabled` 或改為 `false`（也可在 Web UI「外部 MCP」頁管理，UI 會寫回 `external_mcp_enable`）

主配置預設宣告 6 個 server（`bloodhound` + 倉庫自帶 5 個 Python MCP：`reverse-shell` / `vuln-intel` / `redteam-knowledge` / `dragon-v` / `pent-claude-agent`），**全部預設停用**。Python MCP 原始碼在 `mcp-servers/<name>/`，命令支援 `${VAR}` / `${VAR:-default}` 環境變數展開（如 `${JYSECAI_PYTHON:-python}`）。

## 載入規則與供應鏈建議

- Eino skill loader 只掃描 `skills_dir` **第一層**子目錄的 `SKILL.md`（`*/SKILL.md`）；任何一個第一層 SKILL.md 解析失敗都會導致整個技能列表載入失敗。
- `skills/.marketplace-manifest.json`、`skills/.eino/`（plantask 執行時）均不影響載入。
- 建議匯入前審查 SKILL.md 內容與引用的指令碼；匯入後可用 `python scripts/sync-skill-marketplaces.py --dry-run --update` 對比上游變更再決定升級。
- 技能內容即提示詞：市場技能的措辭（含授權假設）會進入會話上下文，接入生產前請人工審閱。
