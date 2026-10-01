# POC/EXP — 4004 authServer Socket.IO 鉴权层不一致（Socket.IO 完全无鉴权 + Web 严格鉴权）

> 漏洞ID: `920936a9-b7a1-4663-bc8c-ee770b2d01e9`  | 嚴重度: **high** | 狀態: ignored | 目標: `https://epcr.tpf.gov.tw:4004/ Socket.IO 端点 + /captcha`

**類型**: 鉴权绕过 / Mixed Pattern

## 描述

【重复开单，canonical=182df1e4-ab82-4705-b61c-1b8546886516。战情挂在 finding/4004-mixed-pattern-auth-inconsistency + finding/4004-socketio-auth-bypass-confirmed，不另开条。】

4004 authServer Socket.IO 层完全无鉴权，与 Web 层 express-jwt 严格鉴权形成鲜明对比。Socket.IO 端点接受匿名连接并返回 SID，业务事件投递静默丢弃或主动断连。Web 端点 (/version, /config, /health, /api/login) 均 401 "No authorization token was found"，但 Socket.IO 根 NS + 9 个 NS 变体 + /captcha 均无鉴权。表明 express-jwt 中间件仅覆盖了 HTTP 路由层，未继承到 Socket.IO 层 + 未覆盖 /captcha。攻击者可绕过 HTTP 鉴权通过 Socket.IO 进行认证相关攻击。

## 前置條件

无（无需任何凭证/认证）

## POC / 復現步驟

```
步骤 1：GET https://epcr.tpf.gov.tw:4004/socket.io/?EIO=4&transport=polling
响应：200 OK + {"sid":"UNh1o27A0OKrUUsAAAAC","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":60000,"maxPayload":1000000}
set-cookie: io=UNh1o27A0OKrUUsAAAAC; HttpOnly
access-control-allow-origin: *

步骤 2：GET https://epcr.tpf.gov.tw:4004/version
响应：401 "No authorization token was found"（W/"b7-kloRtePNJdI0rdqUwM/x3w" etag 指纹）

步骤 3：GET https://epcr.tpf.gov.tw:4004/captcha
响应：200 OK + GIF89a 17646B + content-type=application/octet-stream + set-cookie: connect.sid=s%3A...

步骤 4：WS upgrade 测试
WS handshake 成功，SID RRJFltz_UNkwU18fAAAN，CONNECT(40) 包允许不踢，业务事件投递 silent timeout

步骤 5：32 种业务事件名变体测试
通用事件（subscribe/unsubscribe/join/leave/message/chat/emit/event）+ 认证事件（login/authenticate/auth/token/authorize/refresh/validate/session）+ 用户/角色查询（getUser/getUserInfo/getActivities/getPermissions/getRoles/checkToken/userInfo/whoami）→ 全部 silent timeout
client.* 前缀事件（client.subscribe/client.unsubscribe/client.login/client.authenticate）→ 触发 SSL EOF 主动断连
server.* 前缀事件（server.subscribe/server.broadcast）→ silent timeout

证据位置：sio_4004_complete.py + sio_4004_ws.py + sio_4004_ws_events.py + sio_4004_ws_remaining.py
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
