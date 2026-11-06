---
name: vuln-triage-automation
description: >-
  漏洞自动分诊与报告循环：定时批次队列每轮自动复核漏洞证据、归類嚴重等級、寫回結論、產出 Markdown 報告。
  Use when 定时漏洞分诊轮次执行时、用户要求批量复核/定性漏洞、按标准归類嚴重度、或生成漏洞报告时。
metadata:
  tags: [vulnerability, triage, severity, report, automation]
---

# 授权与纪律（每轮开始先默读）

- 本 skill 仅用于授权范围（ROE 与平台审批链）内的漏洞复核与定性。
- 分诊轮次默认只做**证据复核与定性**，不主动发起新的攻击动作；确需主动重测时，必须 ROE 明确允许且逐条走平台 HITL 审批。
- 绝不虚构或美化证据；不确定就降级标注，而不是删除或拍脑袋定级。

# 每轮标准流程（定时队列任务提示词直接引用本节）

1. `list_vulnerabilities`（scope=project，status=open）分页取全；再用 status=undetermined 取一轮。
2. 逐条 `get_vulnerability` 复核：证据是否可复现、severity 是否符合下方分级标准、confidence 是否如实。
3. 用 `update_vulnerability` 写回结论（severity/status/confidence/retest_notes）。
4. 调 `vuln_triage_report` 生成当轮报告并取回路径。**零待处理时同样生成**（报告会写明 0 条），保证审计链完整。
5. 回复：报告文件路径 + 本轮统计（处理条数、各状态变化、升/降级清单）。

# 嚴重度分級標準

| 等级 | 判定基准（满足即归级） |
|---|---|
| critical | 未鑑權 RCE；鑑權繞過直接接管主機/域控/核心資料庫；可大規模蠕蟲化的鏈 |
| high | 鑑權後 RCE；SQL 注入取得敏感資料；打高權限帳號的儲存型 XSS；任意檔案讀取；SSRF 觸及內網敏感服務 |
| medium | 需互動的 XSS；關鍵操作上的 CSRF；輔助利用鏈的資訊洩露；低權限任意檔案讀片段 |
| low | 低危害資訊洩露；缺危害閉環的注入點徵兆；安全配置缺陷 |
| info | 指紋/版本資訊；強化建議；無直接危害的觀察 |

升降級規則：

- 證據已閉環可利用（差異響應/OOB 回連/算術求值）→ 上調一級，並把閉環證據寫進 evidence。
- 需要罕見前置（多因素、物理接觸、非預設配置）→ 下調一級，理由寫進 retest_notes。
- 只有報錯回顯、無資料或執行閉環 → 不超過 medium。

# status 與 confidence 語義（平台閘門強制）

- `confirmed` 只在客觀證據可復現時使用，confidence >= 95（系統閘門會把低信心 confirmed 壓回 open，記錄不丟）。
- 盲注無判定通道（OOB 關閉時的 XXE/SSRF/Log4j2/Fastjson/Shiro）→ `undetermined` + 如實 confidence。
- 明確誤報 → `false_positive`，理由必須寫進 retest_notes。
- 修復且復測通過 → `fixed`，retest_notes 寫清驗證方式（期望狀態碼/響應差異）。
- 證據互相矛盾 → 保持 open 並在 retest_notes 記錄矛盾點，留給人工裁決。

# 去重與合併

- 系統按 target+type 等價去重；update 撞到「已存在相同漏洞记录」時，先 `get_vulnerability` 取舊記錄，把新舊證據**合并后整体提交** evidence，不要硬重試。

# 报告结构（vuln_triage_report 已固化）

概述（時間/範圍/納入狀態）→ 按狀態分組明細 → 嚴重度×數量總覽表。檔案落在工作區 `reports/vulnerability-triage-report-<時間戳>.md`。

# 7x24 定时化（一次性设定，之后全自动）

1. 让 agent 调 `batch_task_create`：title=「漏洞自动分诊」，tasks=[下方提示词]，schedule_mode=cron，cron_expr=`23 */2 * * *`（每 2 小时，错峰分钟），concurrency=1，execute_now=false。
2. 调 `batch_task_schedule_enabled` 开启调度；此后每轮自动创建独立会话执行。
3. 任务提示词模板：

```text
定时漏洞分诊轮次：严格按 vuln-triage-automation skill 的「每轮标准流程」执行。
scope=project；处理所有 open 与 undetermined 漏洞；按分级标准写回 update_vulnerability；
最后调用 vuln_triage_report（include_details=true）生成报告，回复报告路径与本轮统计。
本轮无待处理项时，也要生成报告并回复「本轮零新增」。不要主动发起新的攻击动作。
```

4. 人工只需看报告：批队列界面看每轮会话，工作区 reports/ 看归档，`critical/high` 升降级会在回复统计里点名。
