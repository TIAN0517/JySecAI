# Claude-Red Skills MCP

唯讀 MCP 伺服器：把 **Claude-Red** 紅隊方法論 skill 庫暴露給 JySecAI 代理，
並與 JySecAI 自己的本地 `skills/` 函式庫**合併**成一體。

它只做「取文字」：回傳 skill 索引、觸發詞與完整 `SKILL.md` 內容。
**不會**執行任何指令、**不會**下載 payload、**不會**碰目標、**不會**開子行程。

每一列結果都會標註來源：

- `"source": "local"` — 來自 JySecAI 套件庫的 `skills/<name>/SKILL.md`
- `"source": "upstream"` — 來自上游 Claude-Red 專案

## 上游出處與授權

| 項目 | 內容 |
|---|---|
| 專案 | [Claude-Red](https://github.com/SnailSploit/Claude-Red) |
| 作者 | SnailSploit / Kai Aizen |
| 授權 | MIT |
| 目錄 | `claude-skills.json`（上游 `v0.3.0` 為 78 個 skill / 23 個分類） |
| 版面 | `Skills/<category>/<skill-name>/SKILL.md` |

上游專案是在執行時透過 HTTPS **唯讀**抓取（`raw.githubusercontent.com` /
`api.github.com`），本儲存庫**不內嵌**任何上游程式碼。上游方法論文字適用其
MIT 授權。

## MCP 工具（5 支）

| Tool | 參數 | 回傳 |
|---|---|---|
| `redteam_list_skill_categories` | — | `{"categories":[{"name","skill_count","sources":["local","upstream"]}], "total":N, "sources":{"local":x,"upstream":y}}` |
| `redteam_list_skills` | `category: str = ""`、`limit: int = 50` | `{"skills":[{"name","description","category","source","triggers":[…],"local_path","upstream_path"}], "total":N, "category":…,"limit":…}` |
| `redteam_get_skill` | `name: str` | `{"ok":true,"skill":{"name","category","source","content","description"}}` 或 `{"ok":false,"error":"…"}` |
| `redteam_search_skills` | `query: str`、`limit: int = 10` | `{"query":…,"results":[…],"total":N}` |
| `redteam_match_skills` | `text: str`、`limit: int = 10` | `{"text":…,"matches":[{"name","score","reason","source"}],"total":N}` |

說明：

- `total` 是**套用 `limit` 之前**的命中筆數。
- `redteam_get_skill` 先查上游（需要時才抓取並快取）；上游失敗時退回本地
  `skills/<name>/SKILL.md`；兩邊都沒有就回傳結構化錯誤，**絕不丟例外**。
- `redteam_match_skills` 對應上游「skill 隨對話觸發自動載入」的機制：以觸發詞、
  skill 名稱 token、描述 token 對一段自由描述（任務／目標）評分，並回報每筆
  為什麼被命中。

## 註冊到 JySecAI `config.yaml`

在 `config.yaml` 的 `external_mcp.servers` 底下加入：

```yaml
external_mcp:
  servers:
    redteam-skills:
      type: stdio
      command: python3
      args:
      - mcp-servers/redteam_skills/mcp_redteam_skills.py
      description: 'Claude-Red skills: merged upstream methodology library (MIT) + JySecAI local skills, read-only.'
      timeout: 60
      max_retries: 3
      keep_alive: 15
      external_mcp_enable: true
      tool_enabled:
        redteam_list_skill_categories: true
        redteam_list_skills: true
        redteam_get_skill: true
        redteam_search_skills: true
        redteam_match_skills: true
```

相對路徑的 `args` 沿用本套件庫其他外部 MCP 的慣例：相對於核心程式的 working
directory（部署機上是 `/opt/jysecai/core/current/`）。若核心不是從該目錄啟動，
請改用絕對路徑：

```yaml
    redteam-skills:
      type: stdio
      command: /opt/jysecai/core/venv/bin/python
      args:
      - /opt/jysecai/core/current/mcp-servers/redteam_skills/mcp_redteam_skills.py
      description: 'Claude-Red skills: merged upstream methodology library (MIT) + JySecAI local skills, read-only.'
      timeout: 60
      max_retries: 3
      keep_alive: 15
      external_mcp_enable: true
      tool_enabled:
        redteam_list_skill_categories: true
        redteam_list_skills: true
        redteam_get_skill: true
        redteam_search_skills: true
        redteam_match_skills: true
```

> `config.yaml` 只在**啟動時讀一次**。改完務必 `systemctl restart jysec-core`，
> 否則設定不會生效。

也可以手動以 stdio 啟動：

```bash
python3 mcp_redteam_skills.py          # stdio transport
```

## 環境變數

| 變數 | 預設 | 說明 |
|---|---|---|
| `JY_TECH_SKILLS_DIR` | *(自動偵測)* | 本地 skills 根目錄。已設定且目錄存在時優先採用；否則從本檔所在目錄往上找同層／上層的 `skills/`（部署版面 `/opt/jysecai/core/current/skills/`，本檔位於 `/opt/jysecai/core/current/mcp-servers/redteam_skills/`）。 |
| `REDTEAM_SKILLS_HTTP_TIMEOUT` | `20` | 對外 HTTP 逾時秒數，會被夾在 5–60 之間。 |

找不到本地 skills 根目錄時，本地清單就是空的——伺服器仍可啟動，仍能提供上游
函式庫。

## 安全說明

- **結構上就是唯讀**：沒有 `subprocess`、沒有 `os.system`、沒有 shell、沒有
  payload 下載、沒有目標互動。單元測試會直接斷言這些東西不在原始碼裡。
- **對外 HTTP 受限**：只走 HTTPS，且 host 白名單固定為
  `{raw.githubusercontent.com, api.github.com}`。其他 host 或 protocol 會在內部
  丟出並轉成結構化錯誤。
- **回應大小上限**：單一 `SKILL.md` 4 MiB、上游目錄／git tree 8 MiB，超標直接
  拒絕。
- **每個請求都有逾時**，暫時性錯誤會重試一次。
- **執行緒安全的 TTL 快取**：上游目錄（6 小時）、上游 skill 內文（6 小時）、
  本地索引（60 秒）。
- **輸入驗證**：拒絕控制字元、限制字串長度、`limit` 夾在 `1..200`。
- **本地查詢防穿越**：skill 名稱必須符合 `^[a-z0-9][a-z0-9._-]*$`；組出路徑
  後再確認解析後的絕對路徑仍在 skills 根目錄之內（含 symlink 逃逸）。
- **Front matter 解析容錯**：優先用 YAML，YAML 壞掉時退回簡單的 `key: value`
  掃描。

## 離線行為

工具呼叫**不會**把例外丟出來。上游 GitHub 連不上時：

- `redteam_list_skill_categories` / `redteam_list_skills` /
  `redteam_search_skills` / `redteam_match_skills` 仍然可用，只是**只剩本地**
  函式庫。
- `redteam_get_skill` 對本地存在的 skill 仍回傳完整內容。
- `redteam_get_skill` 對只有上游才有的 skill 回傳
  `{"ok": false, "error": "…"}`，而不是例外。

上游失敗的結果只快取很短時間（60 秒），連線恢復後立刻就會回來。

## 本地分類對應

JySecAI 的 `skills/` 目錄是扁平的（沒有分類資料夾）。本地 skill 會用「上游分類
名最長前綴」對應到上游分類（例如 `active-directory-attack` → `active-directory`、
`web-attack-methods` → `web`），因此查某個分類時，上游與本地同一領域的 skill
會一起回來。對不上任何上游分類的本地 skill 統一歸在 `jysecai-local` 分類。

## 測試

測試套件**完全離線**——所有網路呼叫都在模組層被 monkeypatch 掉：

```bash
wsl.exe -d kali-linux -u root -- /opt/jysecai/core/venv/bin/python \
  -m unittest discover -s /mnt/c/Users/Administrator/Desktop/JySecAI/mcp-servers/redteam_skills -v
```

涵蓋：工具註冊（剛好 5 支）、本地 skill 探索、YAML front matter 解析（含壞掉
時的退路）、關鍵字檢索、觸發詞比對、路徑穿越與 symlink 逃逸拒絕、limit 夾制、
host／path 白名單、上游目錄合併、上游內文抓取，以及網路失敗的退路行為。
