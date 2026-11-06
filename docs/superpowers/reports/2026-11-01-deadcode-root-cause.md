# 除錯根因報告：死碼判定交集法為什麼必然漏掉真正死碼

- 日期：2026-11-01
- 對象：`jysecai`（12 個 main package）
- 結論一句話：原本用「對每個 main 的 deadcode 輸出取交集」判定死碼，在這個 repo **結構上不可能得到任何真正死碼**；改用 `go list -deps` 精確判定各 main 的依賴套件集合後，得到 151 筆真正死碼。

---

## 1. 根因

### 1.1 原本的做法

對 12 個 main 各自跑官方 `deadcode` 工具（`golang.org/x/tools v0.52.0`，`-test -json`），把每個 main 回報的「不可達函式」清單取交集：

```
dead[m] = main m 的 deadcode 不可達函式集合
真正死碼（原本的判定） = ∩ dead[m]   （對所有 m）
```

### 1.2 錯在哪

`deadcode` 對單一 main **只分析「該 main 程式裡實際存在的套件」**。因此：

| 情況 | 函式 F（屬套件 P）在該 main 的輸出裡 |
| --- | --- |
| main m import 了 P，且 F 不可達 | 出現在 `dead[m]`（不可達清單） |
| main m import 了 P，且 F 可達 | 出現在「可達清單」（不在 `dead[m]`） |
| **main m 根本沒 import P** | **兩邊都不出現 —— F「不存在」** |

交集 `∩ dead[m]` 的邏輯是「在每個 main 都不可達才算死碼」。但當某個 main 沒引入 P 時，F 只是**缺席**，而缺席被交集邏輯當成「不是不可達」→ 等同「可達(live)」→ 真正死碼被整批濾掉。

**關鍵不是實作有 bug，是資料語意被誤讀**：交集法假設「每個 main 的輸出涵蓋全 repo」，但 `deadcode` 的輸出是「該 main 視角下的可達性」，兩者語意不同。

### 1.3 這個 repo 的量化後果

用 `go list -deps` 算出各 main 的依賴套件集合後逐一套件比對：

> **60 / 60 個 `jysecai` 套件都只被「部分」main 引用。**

也就是說，**每一個套件都至少有一個 main 沒引用它** → 對每個套件，交集必然為空 → 交集法在這個 repo 必然得到 **0 筆**真正死碼。這不是「漏掉一些」，是「一筆都找不到」。

### 1.4 最小重現

`/tmp/repro_intersection.py`（可重複執行）以 `internal/app/receiver_bridge.go:316`（套件 `jysecai/internal/app`，僅 `cmd/server` 引用）為例：

```
真正 import 該套件的 main: ['server']
其餘 11 個 main 缺席 → 交集為空 → 誤判為 live
deps 感知法: relevant={server} → server 中不可達 → 真正死碼 ✅
```

---

## 2. 修正法：deps 感知判定

### 2.1 規則

候選函式 F（屬套件 P）：

```
relevant(F) = { M : P ∈ deps(M) }        # 只在「真的引入 P 的 main」集合內比較

若 relevant(F) = ∅        → F 是死碼（沒有任何 main 會用到它）
否則                      → F 死碼 ⇔ F 在「每一個」relevant(M) 都不可達
```

**含 P 的 main 缺席不得投票** —— 缺席不是「可達」的證據，只是「不適用」。

### 2.2 順帶修掉第二個根因：套件路徑比對

原本的比對用檔名推導套件路徑，得到裸路徑 `internal/handler`；而 `go list -deps` 輸出的是**完整 import path** `jysecai/internal/handler`。兩者永不相等 → 比對 100% 失敗，即使邏輯改對也拿不到結果。

修法：**直接採用 deadcode JSON 的 `Path` 欄位**（本身即 `jysecai/internal/...`），不再從檔名推導。

### 2.3 兩法並排比較結果

| 方法 | 真正死碼筆數 |
| --- | --- |
| 法 A：交集法 `∩ dead[m]` | **0** |
| 法 B：deps 感知 | **151** |
| 交集法誤判為 live 的真正死碼 | **151**（＝法 B 全集） |
| 法 A 有但法 B 無 | 0 |
| 兩法一致 | 0 |

一致性健全檢查：`deadcode 報告的套件 ⊆ deps` → 12 個 main **全部通過**（確保沒有「deps 漏了套件」造成的假死碼）。

---

## 3. 交叉驗證：151 筆分成三類

用全 repo 呼叫點檢索交叉驗證（去註解／字串，只認 `ident(` 與 `.ident(` 真呼叫點）：

| 類別 | 筆數 | 意義 | 建議 |
| --- | --- | --- | --- |
| **A：全 repo 零呼叫點** | **76** | 真的沒有人用 | 可安全刪除 |
| **B：僅測試檔呼叫** | **24** | 生產環境是死碼，但測試仍依賴 | 需先讓測試改用其他路徑，或連測試一起刪 |
| **C：生產碼仍有呼叫點** | **51** | 不可靠=deadcode 可能誤判（反射、介面、註解生成等） | 需人工判讀 |

A 類樣例：`internal/agent/agent.go:1073 extractQuotedToolName`、`internal/agent/agent_trace.go:181 MessagesToTraceJSON`、`internal/agents/markdown.go:495 EffectiveSubAgents`。

B 類樣例：`internal/agent/agent_trace.go:110 ExtractLastUserTurnMessages`（只有 `internal/agent/agent_trace_test.go:39` 呼叫）。

C 類樣例：`internal/agents/markdown.go:434 LoadMarkdownSubAgents`（`internal/agents/markdown.go:496` 有生產呼叫點）。

> **本次未刪除任何死碼** —— 只做判定與分類，刪除與否由你決定；A 類 76 筆是明確候選。

---

## 4. 附帶完成：硬性封鎖常數收斂

盤點「重複定義的硬性封鎖常數」時找到一組**衝突點**：攔截回執格式分散在三處，任一處單獨改動都會讓另外兩處靜默失配。

| 位置 | 原本的職責 | 失配後果 |
| --- | --- | --- |
| `internal/mcp/tool_call_guard.go` | 組裝回執文字 | 模型看到非標準格式 |
| `internal/database/tool_guard_migration.go` | 解析舊紀錄以升級 blocked 狀態 | 舊紀錄不會升級成 blocked |
| `internal/mcp/execution_service.go` | 內嵌一份字面值 | 攔截統計漂移 |

收斂成單一來源 `internal/toolguard/refusal.go`：

- `BlockedPrefix`、`BlockedMetaKey`、`RefusalMessage(*Match) string`、`ParseRefusal(text) (ruleName, ruleID, matchedText string, ok bool)`
- 組裝與解析同源，`ParseRefusal` 只接受完整格式（三段齊備），半截文字一律視為非攔截回執
- 新增 `internal/toolguard/refusal_test.go`（6 個測試，全數 PASS），鎖定格式穩定性與 round-trip

---

## 5. 重現指令

```bash
# 1) 計算 12 個 main 的依賴集合（平行，全部 exit=0）
mkdir -p /tmp/deps && cd <repo> && for d in cmd/*/; do
  name=$(basename "$d")
  if [ -f "$d/main.go" ]; then
    ( timeout 3000 go list -deps "./$d" > "/tmp/deps/$name.txt" 2> "/tmp/deps/$name.err"; \
      echo "$name exit=$? lines=$(wc -l < /tmp/deps/$name.txt)" > "/tmp/deps/$name.status" ) &
  fi
done; wait

# 2) 兩法並排比較
cd /tmp && python3 deadcode_compare.py

# 3) 精確交叉驗證（A/B/C 分類）
cd /tmp && python3 verify_callsites.py

# 4) 最小重現
cd /tmp && python3 repro_intersection.py
```

### 產出檔案

| 檔案 | 內容 |
| --- | --- |
| `/tmp/deps/<main>.txt` | 各 main 依賴套件集合（`jysecai/...` 完整 import path） |
| `/tmp/deadcode_compare.json` | `method_A_intersection` / `method_B_deps_aware` / `false_live_by_intersection` |
| `/tmp/deadcode_true.json` | 151 筆真正死碼（file/line/name/pkg） |
| `/tmp/deadcode_final_verified.json` | `safe_to_delete`(76) / `test_only`(24) / `prod_referenced`(51) |
| `/tmp/repro_intersection.py` | 根因最小重現腳本 |

### 12 個 main 的依賴規模

| main | 依賴套件數 |
| --- | --- |
| server | 1169 |
| verify-drain | 1149 |
| triage-drain | 1149 |
| knowledge-doctor | 791 |
| ollama-cloud-check | 764 |
| mcp-stdio | 428 |
| vulnerability-backfill | 259 |
| test-external-mcp | 245 |
| test-config | 197 |
| test-sse-mcp-server | 190 |
| vulnerability-data-quality | 115 |
| vulnerability-classify | 115 |

---

## 6. 這份報告沒做的事

- **沒有刪除任何死碼**。A 類 76 筆可刪，但刪除屬於破壞性變更，需要另外的決策與獨立的測試驗證。
- **沒有處理 toolguard 接線**：`projects.scope_json` 接入攔截層的設計與實作計畫已寫在 `docs/superpowers/specs/2026-11-01-project-scope-toolguard-design.md` 與 `docs/superpowers/plans/2026-11-01-project-scope-toolguard.md`；`internal/toolguard` 的能力層（`TargetScope` / `CheckScoped` / `ParseScopeEntries`）已完成並測試通過，接線（project 解析 / mcp ScopeResolver / app 開關）尚未接上。
