# Skills 指南

Skills 用於給 Agent 提供可按需載入的專題能力、流程說明、模板和參考資料。它適合承載穩定方法論，而不是一次性任務輸入。

## 目錄結構

預設目錄：

```yaml
skills_dir: skills
```

推薦結構：

```text
skills/
  api-security-testing/
    SKILL.md
  ssrf-testing/
    SKILL.md
  jysecai-eino-demo/
    SKILL.md
    REFERENCE.md
    assets/
```

每個 Skill 至少包含 `SKILL.md`。

## SKILL.md

`SKILL.md` 使用 YAML front matter：

```markdown
---
name: ssrf-testing
description: SSRF 漏洞識別、驗證、繞過和修復建議流程
---

# SSRF Testing

當任務涉及服務端請求偽造、URL 回撥、雲後設資料訪問或內網探測時使用本技能。
```

`description` 很重要，Agent 會根據它判斷何時載入。

## 漸進式披露

Eino Skills 支援按需載入。配置：

```yaml
multi_agent:
  eino_skills:
    disable: false
    filesystem_tools: true
    skill_tool_name: skill
```

Agent 初始只看到技能名稱和描述，真正需要時再呼叫 `skill` 讀取詳情，減少上下文佔用。

## 適合寫成 Skill 的內容

- 某類漏洞測試流程。
- 安全審計 checklist。
- 報告模板。
- 工具組合方法。
- 內部規範。
- 常見誤報判斷。

不適合：

- 臨時目標資訊。
- API Key、密碼、Cookie。
- 經常變化的掃描結果。
- 大量無結構原始日誌。

## 附屬檔案

Skill 可以帶附屬檔案，如 `REFERENCE.md`、模板、字典或示例。`SKILL.md` 中應說明何時讀取這些檔案。

建議：

- 主檔案保持短而清晰。
- 參考資料按主題拆分。
- 大檔案只在必要時讀取。

## 與角色繫結

角色可以提示 Agent 使用某類 Skill；Skill 也可以透過頁面管理和角色形成繫結關係。建議：

- 通用技能保持不繫結，按描述自動觸發。
- 高風險技能繫結到專用角色。
- 同類技能不要描述過度重疊。

## 開發建議

Skill 內容結構：

1. 觸發場景。
2. 目標和邊界。
3. 操作步驟。
4. 工具建議。
5. 輸出格式。
6. 風險和禁止事項。
7. 參考資料。

寫法要讓 Agent 能執行，而不是隻給人閱讀。

## 排錯

Skill 沒被使用：

- `description` 過窄或過模糊。
- 任務沒有觸發關鍵詞。
- `multi_agent.eino_skills.disable: true`。
- Skill 檔案 front matter 格式錯誤。

Skill 讀取太多：

- 拆分附屬檔案。
- 在 `SKILL.md` 中明確“只有在需要 X 時讀取 Y”。
- 刪除重複內容。

## Skill 設計深水區

Skill 的核心價值不是“讓 Agent 知道一個概念”，而是讓 Agent 在正確時機拿到一套可執行的程式。寫 Skill 時要特別關注觸發條件和退出條件。

推薦結構：

```markdown
## When to use
明確觸發場景。

## Preconditions
需要使用者提供什麼、目標必須滿足什麼。

## Procedure
按步驟執行，每步說明工具、輸入和判斷標準。

## Stop conditions
什麼情況下停止、升級審批或轉人工。

## Output
最終結果格式。
```

## 反模式

| 反模式 | 後果 | 改法 |
| --- | --- | --- |
| 描述過泛：`用於安全測試` | 幾乎所有任務都觸發 | 寫具體漏洞、場景、訊號 |
| 內容像百科 | Agent 不知道下一步做什麼 | 改成流程和決策樹 |
| 把敏感配置寫進 Skill | 洩露和誤用 | 用執行時配置或使用者輸入 |
| 一個 Skill 裝所有內容 | 讀取成本高，召回混亂 | 按漏洞/任務拆分 |
| 沒有停止條件 | Agent 可能持續擴大範圍 | 寫明何時停止和審批 |

## Skill 與知識庫的區別

- Skill：指導 Agent 怎麼做，強調流程。
- 知識庫：提供事實、案例和參考，強調檢索。

例如 SSRF：

- Skill 寫“如何測試 SSRF、如何判定、何時停止”。
- 知識庫寫“雲廠商 metadata 地址、歷史繞過、修復方案”。

## 本地檔案工具風險

`filesystem_tools: true` 會暴露讀寫和執行能力。它對開發和自動化很有用，但也是安全邊界。生產環境建議：

- 配合 `workspace_root_dir` 限制工作目錄。
- 對寫入和執行動作使用 HITL。
- 不把 `execute` 加入全域性白名單。
- Skill 中明確禁止讀寫授權範圍外檔案。

## 原始碼錨點

- Skill 包校驗：`internal/skillpackage/validate.go`
- Skill 服務：`internal/skillpackage/service.go`
- Eino Skills 接入：`internal/multiagent/eino_skills.go`
- Skills Handler：`internal/handler/skills.go`
