---
name: src-hunter
description: 国内 SRC 挖洞五阶段流水线（intake→recon→enum→hunt→report）。给定目标域名后按阶段自动推进，内置攻击 playbook、结构化 payload 与红线规则，服务于授权众测/SRC 场景。
metadata:
  author: "Jy 技術團隊"
  source: "adapted from MyuriKanao/src-hunter-skill"
---

# SRC Hunter — 五階段流水線

## 輸入解析

接受輸入：`TARGET [SCOPE_FILE] [MODE]`

- `TARGET`：主目標域名（例：`example.com`）
- `SCOPE_FILE`：可選，授權範圍清單（每行一個域名/IP）；缺省則僅測主域與常見子域
- `MODE`：`plan`（僅出計劃）| `execute`（預設，自動推進）

範例：
- `$src-hunter example.com`
- `$src-hunter example.com scope.txt execute`

## 五階段流水線

```
intake → recon → enum → hunt → report
```

### 1. intake（立案）
- 建立 `src/<target-slug>/` 工作區與 `operation-state.json`（階段/目標/時間）
- 解析 SCOPE_FILE，登記授權邊界；**超出範圍的目標一律不碰**
- 選擇 JySecAI project 並寫入事實黑板（`upsert_project_fact`：目標/範圍/委託方/期限）

### 2. recon（偵察）
- 調用 `$osint-recon <target> passive`，出站走 config.yaml `proxy_pool`
- FOFA/ZoomEye/Quake/Shodan 交叉確認（config.yaml 已有 key 配置）
- 產出：子域清單、資產指紋、歷史洩露線索 → `recon-report.md`

### 3. enum（枚舉）
- httpx 探活 → 指紋聚類 → ffuf 目錄發現（保守 wordlist）
- API 文件探測：`/swagger` `/openapi.json` `/api-docs`
- 登入點/上傳點/搜尋點標記 → 供 hunt 階段選 playbook

### 4. hunt（漏洞獵捕）
- 按指紋從 `playbooks/core-playbooks.md` 選 playbook
- payload 從 `payload/structured-payloads.md` 取，逐條驗證
- **發現+驗證=真實有效**：每個發現必須有差分/基線/marker 三件套之一佐證
- 覆蓋度矩陣收口：每個 playbook 標記「已測/未測/不適用」

### 5. report（報告）
- 模板對照 `internal/config/audit_templates/`（idor/rce/sqli_report.md 同構）
- 嚴重性定級用 CVSS；每個發現附復現步驟與修復建議
- 落盤 `src/<target-slug>/reports/`；同步寫入 project 事實黑板

## 紅線規則（每個 playbook 末尾強制執行）

| 類型 | 邊界 |
|------|------|
| SQLi | 拿到庫名/版本即停；樣本 1–3 條；禁 dump 全表、禁寫檔 |
| IDOR | 拉 1–3 條樣本即停；禁全表遍歷、禁碰他人敏感欄位 |
| RCE | 僅跑 `id`/`whoami`；禁破壞性命令、禁持久化 |
| Redis 未授權 | 僅 `INFO`；禁寫 key、禁寫檔 |
| XSS | 彈 computed 標記即可；禁掛真實釣魚 payload |
| SSRF | 僅探 DNSLog 回顯；禁內網橫向 |

## HITL 串接

- 非白名單工具的攻擊性呼叫 → 走 config.yaml `hitl`（審計 Agent 按 audit_agent_prompt 裁決）
- 紅線內的探測 payload → audit_agent_prompt「必須 approve」清單，預期放行
- 紅線外（DROP 全表/改密碼/停服務）→ 必須 reject

## 品質紀律

1. 每階段結束更新 `operation-state.json`，中斷可恢復
2. 出站請求走 proxy_pool；命中限速立即冷卻
3. 未驗證的猜測一律標 `hypothesis`，不得混入 findings
4. 報告用語：只寫「已驗證」的事實，附證據路徑
