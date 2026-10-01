# 4001 /socket.io 无认证可建立长连接，CORS * 允许任意域跨域

- ID: `c56c5ab5-247a-470e-ac04-d06dabc5badb`
- Severity: **medium**
- Status: open
- Type: 未授权访问 / CORS 配置缺陷
- Target: `https://epcr.tpf.gov.tw:4001/socket.io`
- Conversation: `9f0a20d8-98b0-4f97-8e49-573ac9d822dc`
- Created: 2026-09-01 05:48:51.856780802+08:00

## Description

4001 vitalSignVideoServer 的 /socket.io 端点无认证即可建立 Socket.IO 长连接（polling + websocket 升级），且 Access-Control-Allow-Origin: *，任意域都可跨域连接。攻击者可借此监听实时事件推送（如患者生命体征、视频流状态），或向服务器发送伪造事件，形成信息泄露与数据注入双风险。

## Preconditions

公网可达 https://epcr.tpf.gov.tw:4001

## Reproduction

1. curl -sk 'https://epcr.tpf.gov.tw:4001/socket.io/?EIO=4&transport=polling'
2. 获得 sid 与 Set-Cookie: io=...
3. 用 Socket.IO 客户端连接并监听事件，或 POST 伪造事件
4. 观察是否收到实时数据推送

## Evidence

curl -sk 'https://epcr.tpf.gov.tw:4001/socket.io/?EIO=4&transport=polling' 返回 HTTP 200，body 97:0{"sid":"SCcSbjHU5ecGverDAPxD","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":60000}2:40，Set-Cookie: io=SCcSbjHU5ecGverDAPxD; Path=/; HttpOnly，Access-Control-Allow-Origin: *

## Impact

Socket.IO 层无 JWT 校验，任意域可跨域连接并监听实时事件（如患者生命体征、视频流状态）；攻击者可向服务器发送伪造事件（如 client.join/leave），影响前端实时渲染；与 4000 前端的 WebSocket 通信形成同源信任，可被利用做跨域数据窃取。

## Recommendation

给 Socket.IO 增加 JWT 鉴权中间件（如 socket.handshake.auth.token 校验）；收紧 CORS 到白名单域；对实时事件做签名或 HMAC 校验，避免伪造。
