# 批次开放式跳转验证

[English](../en-US/redirect-batch-verify.md)

单笔 `redirect_probe` 一次只能复测一个目标。批次验证把整条流程串成一条流水线：

```
情蒐（FOFA / ZoomEye / Quake / Shodan）→ 巡站发掘跳转参数 → 批次验证（受控端点）→ 自动上链（漏洞记录）→ 报告
```

「跳转目标」是操作者自己的受控回连端点，默认 `https://97y.me/tjneJ`（即平台 `redirect.urls` 的受控端点）。探测时把受控端点代入目标的跳转参数，只读回应的 `Location` 标头判断目标是否真的跳向你的端点；**绝不跟随重新导向**，所以证据永远是原始的 `Location`。

端点清单本身见 [受控跳转（回连）端点](redirect-endpoints.md)。

## 控制台

「资产 / 安全防护」区的「批次跳转验证」页面（路由 `redirect-verify`）提供四个动作：

| 动作 | 说明 |
| --- | --- |
| 情蒐导入 | 走 `/api/fofa/search`（多 provider），把结果主机名汇入目标清单 |
| 巡站发掘 | 走 `/api/redirect-verify/crawl`，抓 `<a href>` / `<form action>` / `<link href>`，query 含常见跳转参数名的 URL 视为候选 |
| 汇入既有漏洞 | 走 `/api/vulnerabilities/export-urls`，把已有漏洞记录的目标 URL 直接拿来重跑 |
| 开始批次验证 | 走 `/api/redirect-verify/runs`，跑完自动上链并可下载报告 |

页面载入时会调用 `/api/redirect-verify/endpoints` 取平台配置的受控端点，并预填第一笔到「跳转目标」输入框；清单为空时提示自行填写回连地址。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/redirect-verify/runs` | 建立批次：`targets[]`、`endpoints[]`、`param`、`method`、`project_id`、`conversation_id`、`auto_record`、`concurrency`、`timeout_seconds`、`proxy`、`proxy_group`；立即回 `202` 与 `run`，背景执行 |
| POST | `/api/redirect-verify/runs/:id/cancel` | 请求取消；后台 worker 观察取消旗标，在下一个目标前停下 |
| GET | `/api/redirect-verify/runs/:id` | 进度 + 结果清单（`run` 与 `results`） |
| GET | `/api/redirect-verify/runs` | 批次列表（`limit` 默认 50，上限 200，按权限过滤） |
| GET | `/api/redirect-verify/runs/:id/report` | 报告，`format=markdown`（默认）/ `csv` / `json` |
| GET | `/api/redirect-verify/endpoints` | 平台已配置的受控端点清单 |
| POST | `/api/redirect-verify/crawl` | 巡站发掘：`seeds[]`、`max_pages`、`max_depth`、`same_host_only`、`proxy`、`proxy_group` |

### 受控端点从哪来

顺序固定，三段都拿不到就直接报错、不发出任何请求：

1. 本次请求的 `endpoints`；
2. 平台设置里的 `redirect.urls`；
3. 没有 → `400`。

```yaml
redirect:
  enabled: true
  urls:
    - https://97y.me/tjneJ
```

### 命中判定

- 只读 `Location` 标头，不跟随重新导向；
- 主机名必须与受控端点**完全相同**：`victim.com.97y.me` 不算 `97y.me`，受害站点自己的主机永远不算命中；
- 未指定 `param` 时，依常见参数名（`url`、`redirect`、`redirect_uri`、`returnUrl`、`next`、`goto`、`u` …）逐一尝试，命中即停。

## 自动上链

批次结果 `confirmed=true` 且 `auto_record=true` 时，为每个确认的目标自动建立一条「开放式跳转（受控跳转验证确认）」漏洞记录：

- 标题：`开放性重定向（受控跳转验证确认）- <host>`；
- 类型码 `open-redirect`，严重度 `medium`，状态 `confirmed`；
- 证据包含请求 URL、状态码、`Location`、受控端点与参数名；复测记录另起一行；
- 归属性：优先 `project_id`，其次 `conversation_id`；两者都没有则不建记录，只在摘要里说明原因。

建记录需要 `vulnerability:write`；权限不足时结果仍会保留，但不落库。

## 进度与结果

批次状态为 `pending` / `running` / `completed` / `cancelled` / `failed`。结果每笔落库（`redirect_verify_runs` 与 `redirect_verify_results`），页面刷新、重新登入都不会消失。代理网址带帐密的，落库前遮蔽；原始值只留在执行行程的记忆体里。

## 安全边界

- 批次只针对使用者明确提供、或经情蒐 / 巡站取得的目标。平台既有 `tool_guard.scope` 与专案 scope 仍会在拦截层把关；范围外的政府与关键基础设施仍会被拦截。
- 探测不跟随重新导向，只读 `Location`；报告与漏洞记录不含凭证。
- 端点是操作者自己的回连位址，请指向自己控制的伺服器，并为每个目标保留不同的路径段落以利归因。
- 代理出口有两种：直接贴代理网址，或改用平台代理池的群组（`proxy_group`）。代理池未启用时使用 `proxy_group` 会直接回错。

## 批次改写既有漏洞的受控端点

漏洞记录里的跳转 payload 几乎都带着攻击者自己的网域。`POST /api/vulnerabilities/rewrite-controlled-endpoints` 把 payload 位置上的外部网址换成受控端点，让整批记录可以用同一组端点复测。

```json
{
  "endpoint": "https://97y.me/tjneJ",
  "dry_run": false,
  "limit": 500,
  "project_id": ""
}
```

- `endpoint` 必填：只接受 http/https 的受控端点。
- `dry_run` 为 true 时只统计会改什么、不写入数据库 —— 先跑一次 dry run 确认范围再实跑。
- 实际能改到哪些记录由登入者的 RBAC 范围决定（列出来的清单已经过滤）。

改写规则只动 payload 位置，不会整段取代：

| 位置 | 例子 | 是否改写 |
| --- | --- | --- |
| 跳转参数值 | `?url=https://evil.example/steal`、`url=https://evil.example/steal` | 改 |
| `Location` 标头值 | `Location: https://evil.example/land` | 改 |
| 样本 / 设定指派 | `targetUrl="https://evil.example/"`、`"callbackUrl":"https://evil.example/cb"` | 改 |
| 受控端点标签文字 | `受控端點：https://evil.example/cb` | 改 |
| 目标站自己的网址 | `https://victim.example/style.js`、`https://www.victim.example/...` | 不改 |
| 描述性文字里的外链 | 影响段落提到的第三方站 | 不改 |
| 已经是受控端点的值 | `https://97y.me/tjneJ` | 不改（因此可以重复执行） |

范围是 Description、Reproduction steps、Evidence、Retest notes 四个栏位；Impact 与 Recommendation 不动。

控制台：「批次跳转验证」页的「批次改写漏洞端点」按钮会用输入框里的端点调用这个 API。

## 来源锚点

- 配置结构：`internal/config/config.go`
- 纯逻辑：`internal/redirect/redirect.go`（探测原语）、`internal/redirect/batch.go`（批次引擎）、`internal/redirect/crawl.go`（巡站）
- REST API：`internal/handler/redirect_verify.go`
- 持久化：`internal/database/redirect_verify.go`
- 漏洞记录组装：`internal/redirectverify/record.go`
- MCP 工具：`internal/app/redirect_tools.go`、`internal/app/redirect_batch_tools.go`
- 控制台：`web/static/js/redirect-verify.js`、`web/static/css/redirect-verify.css`、`web/templates/index.html`
- 设计规格：`docs/superpowers/specs/2026-11-01-redirect-batch-verify-design.md`
